from __future__ import annotations

import json
import sqlite3
from pathlib import Path
import pytest

from src.harness.agentic_audit import (
    ChecklistRegistry,
    ChecklistCriterion,
    StatelessAuditor,
    AgenticAuditOrchestrator,
    FileAuditVerdict,
)
from src.harness.db import DEFAULT_DB_PATH, init_harness_db


def test_checklist_registry_separation():
    """Verifica que el registro desacople el Core universal de la Ley 21.719 del Plugin Sectorial de Salud."""
    registry = ChecklistRegistry()
    assert len(registry.core_criteria) == 4
    assert any(c.id == "CORE-CHECK-001" for c in registry.core_criteria)
    assert any(c.id == "CORE-CHECK-002" for c in registry.core_criteria)
    assert any(c.id == "CORE-CHECK-003" for c in registry.core_criteria)
    assert any(c.id == "CORE-CHECK-004" for c in registry.core_criteria)

    # Modo Universal (sin plugins sectoriales)
    universal_criteria = registry.get_active_criteria(sectorial_plugin=None)
    assert len(universal_criteria) == 4
    for plugin_name, _ in universal_criteria:
        assert plugin_name == "core_universal"

    # Modo Sectorial Clínico
    clinical_criteria = registry.get_active_criteria(sectorial_plugin="health_clinical")
    assert len(clinical_criteria) == 7
    sectorial_ids = [c.id for p, c in clinical_criteria if p == "health_clinical"]
    assert "HEALTH-CHECK-001" in sectorial_ids
    assert "HEALTH-CHECK-002" in sectorial_ids
    assert "HEALTH-CHECK-003" in sectorial_ids


def test_stateless_auditor_detects_hard_delete_violation(tmp_path):
    """Verifica que el auditor stateless detecte la infracción al deber de retención decenal (Ley 20.584)."""
    bad_code = (
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.delete('/patient/{id}')\n"
        "def remove(id: str, db):\n"
        "    session.delete(patient)\n"
        "    return {'ok': True}\n"
    )
    bad_file = tmp_path / "bad_api.py"
    bad_file.write_text(bad_code, encoding="utf-8")

    db_test = tmp_path / "test_harness.db"
    init_harness_db(db_test)

    registry = ChecklistRegistry()
    criteria = registry.get_active_criteria(sectorial_plugin="health_clinical")

    auditor = StatelessAuditor(session_id="test-session", db_path=db_test)
    verdict = auditor.audit_file(
        file_path_abs=bad_file,
        rel_path="src/backend/api/bad_api.py",
        file_node_id="src_backend_api_bad_api_py",
        slice_data={"nodes": [], "edges": [], "involved_files": []},
        active_criteria=criteria,
    )

    assert verdict.overall_status == "NON_COMPLIANT"
    hard_delete_res = next(r for r in verdict.results if r.criterion_id == "HEALTH-CHECK-001")
    assert hard_delete_res.status == "VIOLATION"
    assert "Art. 13 Ley 20.584" in hard_delete_res.details
    assert "session.delete" in hard_delete_res.evidence_snippet


def test_stateless_auditor_compliant_file(tmp_path):
    """Verifica que un componente sin infracciones obtenga estado COMPLIANT."""
    clean_code = (
        "from fastapi import APIRouter, Security, Depends\n"
        "from src.backend.security.dependencies import get_current_user\n"
        "router = APIRouter()\n"
        "@router.get('/items')\n"
        "def get_items(user = Security(get_current_user)):\n"
        "    return []\n"
    )
    clean_file = tmp_path / "clean_api.py"
    clean_file.write_text(clean_code, encoding="utf-8")

    db_test = tmp_path / "test_harness.db"
    init_harness_db(db_test)

    registry = ChecklistRegistry()
    criteria = registry.get_active_criteria(sectorial_plugin="health_clinical")

    auditor = StatelessAuditor(session_id="test-clean", db_path=db_test)
    verdict = auditor.audit_file(
        file_path_abs=clean_file,
        rel_path="src/backend/api/clean_api.py",
        file_node_id="src_backend_api_clean_api_py",
        slice_data={"nodes": [], "edges": [], "involved_files": []},
        active_criteria=criteria,
    )

    assert verdict.overall_status == "COMPLIANT"
    assert verdict.violation_count == 0


def test_orchestrator_execution(tmp_path):
    """Verifica la orquestación del loop agéntico sobre los archivos del workspace."""
    session_id = "test-orchestrator-run"
    orchestrator = AgenticAuditOrchestrator(
        session_id=session_id,
        db_path=DEFAULT_DB_PATH,
    )
    report = orchestrator.run_audit_loop(sectorial_plugin="health_clinical", apply_patches=False)

    assert report["total_files_audited"] > 0
    assert report["active_criteria_count"] == 7
    assert len(report["verdicts"]) == report["total_files_audited"]

    # Verificar persistencia en base de datos
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    rows = conn.execute("SELECT COUNT(*) FROM file_checklist_audits WHERE session_id = ?", (session_id,)).fetchone()[0]
    conn.close()
    assert rows > 0
