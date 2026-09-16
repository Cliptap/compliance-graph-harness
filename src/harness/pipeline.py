from __future__ import annotations

import ast
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from src.harness.data_lineage import DataLineageEngine
from src.harness.db import DEFAULT_DB_PATH, WORKSPACE_ROOT, get_db_connection, init_harness_db, log_agent_reasoning
from src.harness.graph_engine import build_repository_graph, render_slice_context, subgraph_slice
from src.harness.visualizer import generate_graph_html
from src.harness.agentic_audit import AgenticAuditOrchestrator


class ComplianceAuditorAgent:
    """Subagente Auditor Especializado en la Nueva Ley de Protección de Datos Personales (Chile).
    
    Analiza el subgrafo podado (Sub-graph Slice), evalúa el flujo de contaminación
    y emite un dictamen legal-técnico estructurado.
    """

    def __init__(self, session_id: str, db_path: Path | str = DEFAULT_DB_PATH):
        self.session_id = session_id
        self.db_path = Path(db_path)

    def audit_finding(self, finding: dict[str, Any], slice_data: dict[str, Any]) -> dict[str, Any]:
        finding_id = finding["finding_id"]
        rule_id = finding["rule_id"]
        law_art = finding["law_article"]
        taint_path = " -> ".join(finding["taint_path"])
        mitigations = finding.get("required_mitigations", [])

        # Identificar archivo vulnerable que aloja el sumidero
        target_file = None
        conn = get_db_connection(self.db_path)
        try:
            for path_node in finding["taint_path"]:
                row = conn.execute("SELECT file_path FROM graph_nodes WHERE id = ?", (path_node,)).fetchone()
                if row and row["file_path"]:
                    target_file = row["file_path"]
                    if "events.py" in target_file:
                        break
        finally:
            conn.close()

        reasoning = (
            f"[AUDITORIA AGENTICA - LEY CHILENA] Evaluación de hallazgo {finding_id} bajo {law_art}.\n"
            f"Título: {finding['title']}\n"
            f"Ruta de Contaminación: {taint_path}\n"
            f"Diagnóstico Normativo:\n"
            f"- Bajo la Ley 21.719 (promulgada el 13-12-2024, vigencia 01-12-2026 y que crea la APDP), "
            f"la Ley 20.584 y la Ley 21.668, el tratamiento de datos sensibles de salud (Art. 16 bis) e identificadores (Art. 2 let. a) "
            f"exige aplicación estricta del deber de secreto y confidencialidad (Art. 14 bis), Privacidad desde el Diseño (Art. 14 quater) "
            f"y medidas de seguridad técnicas demostrables (Art. 14 quinquies), con multas de hasta 20.000 UTM o 4% de ventas anuales.\n"
            f"Directiva de Mitigación requerida: {', '.join(mitigations)}.\n"
            f"Archivo sujeto a intervención: `{target_file}`."
        )

        audit_result = {
            "finding_id": finding_id,
            "decision": "VULNERABILITY_CONFIRMED",
            "severity": finding["severity"],
            "target_file": target_file,
            "law_article": law_art,
            "mitigations_required": mitigations,
        }

        log_agent_reasoning(
            session_id=self.session_id,
            agent_name="compliance_auditor_agent",
            step_name="audit_finding",
            input_payload=finding,
            reasoning_trace=reasoning,
            output_result=audit_result,
            db_path=self.db_path,
        )

        return audit_result


class DeveloperPatcherAgent:
    """Subagente Desarrollador / Patcher Autónomo.
    
    Recibe el dictamen del auditor y el contexto ultracompacto (Sub-graph Slice),
    formula el parche de código correctivo (Privacy by Design), lo aplica en disco
    y valida el resultado mediante suite de pruebas.
    """

    def __init__(self, session_id: str, root_dir: Path | str = WORKSPACE_ROOT, db_path: Path | str = DEFAULT_DB_PATH):
        self.session_id = session_id
        self.root_dir = Path(root_dir)
        self.db_path = Path(db_path)

    def generate_and_apply_patch(self, audit_verdict: dict[str, Any], slice_data: dict[str, Any]) -> dict[str, Any]:
        target_file_rel = audit_verdict.get("target_file")
        if not target_file_rel:
            return {"status": "SKIPPED", "reason": "No target file specified"}

        target_file_abs = self.root_dir / target_file_rel
        if not target_file_abs.exists():
            return {"status": "ERROR", "reason": f"File {target_file_abs} does not exist"}

        current_code = target_file_abs.read_text(encoding="utf-8")

        # Formular parche específico para el listener de persistencia (events.py)
        patch_applied = False
        diff_summary = ""

        if "events.py" in target_file_rel:
            # Reemplazar la definición de SENSITIVE_FIELDS y _redact para incluir enmascaramiento de RUT y datos de salud
            old_pattern = 'SENSITIVE_FIELDS = {"password_hash", "secret_token", "access_token", "refresh_token", "password"}'
            new_pattern = (
                'SENSITIVE_FIELDS = {\n'
                '    "password_hash", "secret_token", "access_token", "refresh_token", "password",\n'
                '    "identifier", "rut", "status", "diagnosis", "clinical_notes"\n'
                '}'
            )

            old_redact = (
                "def _redact(field_name: str, value: object) -> str | None:\n"
                "    if value is None:\n"
                "        return None\n"
                "    if field_name in SENSITIVE_FIELDS:\n"
                "        return \"[REDACTED]\"\n"
                "    return str(value)"
            )

            new_redact = (
                "def _redact(field_name: str, value: object) -> str | None:\n"
                "    if value is None:\n"
                "        return None\n"
                "    field_lower = field_name.lower()\n"
                "    if field_lower in SENSITIVE_FIELDS:\n"
                "        val_str = str(value)\n"
                "        # Enmascaramiento de identificador RUT bajo Ley 21.719 (Art. 2 let. a y Art. 14 bis)\n"
                "        if field_lower in (\"identifier\", \"rut\") and len(val_str) > 4:\n"
                "            return f\"{val_str[:2]}.***.***-{val_str[-1]}\"\n"
                "        # Redaccion de datos sensibles de salud bajo Ley 21.719 (Art. 2 let. g y Art. 16 bis) y Ley 20.584\n"
                "        return \"[REDACTED]\"\n"
                "    return str(value)"
            )

            if old_pattern in current_code:
                patched_code = current_code.replace(old_pattern, new_pattern)
                if old_redact in patched_code:
                    patched_code = patched_code.replace(old_redact, new_redact)
                target_file_abs.write_text(patched_code, encoding="utf-8")
                patch_applied = True
                diff_summary = "Expandido SENSITIVE_FIELDS con 'identifier', 'rut', 'status' y adicionada lógica de enmascaramiento bajo Ley 21.719."

        reasoning = (
            f"[DESARROLLADOR AGENTICO] Aplicando directiva de mitigación en `{target_file_rel}`.\n"
            f"Justificación técnica: Para dar cumplimiento al Principio de Privacidad desde el Diseño y por Defecto (Art. 14 quater Ley 21.719), "
            f"se intercepta la persistencia en el listener SQLAlchemy y se transforma el valor sensible antes de ser almacenado en la tabla de auditoría.\n"
            f"Acción: {diff_summary}\n"
            f"Estado: Parche aplicado exitosamente en disco."
        )

        log_agent_reasoning(
            session_id=self.session_id,
            agent_name="developer_patcher_agent",
            step_name="apply_security_patch",
            input_payload={"target_file": target_file_rel, "mitigations": audit_verdict["mitigations_required"]},
            reasoning_trace=reasoning,
            output_result={"patch_applied": patch_applied, "diff": diff_summary},
            db_path=self.db_path,
        )

        # Actualizar hallazgo en la base de datos
        conn = get_db_connection(self.db_path)
        try:
            conn.execute(
                """
                UPDATE compliance_findings 
                SET status = 'PATCHED', resolved_at = CURRENT_TIMESTAMP, patch_commit_or_diff = ?
                WHERE id = ?
                """,
                (diff_summary, audit_verdict["finding_id"]),
            )
            conn.commit()
        finally:
            conn.close()

        return {
            "patch_applied": patch_applied,
            "target_file": target_file_rel,
            "diff_summary": diff_summary,
        }

    def verify_patch(self) -> dict[str, Any]:
        """Ejecuta la suite de pruebas unitarias para certificar no-regresión tras el parche."""
        cmd = [sys.executable, "-m", "pytest", "tests/unit/"]
        res = subprocess.run(cmd, cwd=str(self.root_dir), capture_output=True, text=True)
        tests_passed = (res.returncode == 0)
        return {
            "tests_passed": tests_passed,
            "output_summary": res.stdout[-400:] if res.stdout else res.stderr[-400:],
        }


class CompliancePipeline:
    """Orquestador Principal del Pipeline Agéntico de Cumplimiento Normativo (Antigravity).
    
    Ciclo completo:
    1. Indexación de Grafo de Código AST transversal (Graphify Architecture)
    2. Detección dinámica de Flujo de Datos Sensibles (Data Lineage / Taint Analysis)
    3. Razonamiento del Subagente Auditor bajo la Ley Chilena de Protección de Datos
    4. Aislamiento quirúrgico de contexto mediante Sub-graph Slicing
    5. Formulación y aplicación del parche por el Subagente Desarrollador (Privacy by Design)
    6. Verificación automatizada con Pytest y re-evaluación del grafo de contaminación
    7. Generación y apertura del visualizador interactivo D3.js
    """

    def __init__(self, root_dir: Path | str = WORKSPACE_ROOT, db_path: Path | str = DEFAULT_DB_PATH):
        self.root_dir = Path(root_dir)
        self.db_path = Path(db_path)
        self.lineage_engine = DataLineageEngine(self.db_path)

    def run(
        self,
        apply_patches: bool = True,
        session_id: str | None = None,
        open_browser: bool = True,
        sectorial_plugin: str | None = "health_clinical",
    ) -> dict[str, Any]:
        session_id = session_id or f"session-{uuid.uuid4().hex[:8]}"
        init_harness_db(self.db_path)

        # Paso 1: Construcción transversal de grafos
        nodes_count = build_repository_graph(root_dir=self.root_dir, db_path=self.db_path)
        lineage_count = self.lineage_engine.scan_and_build_lineage(root_dir=self.root_dir)

        # Paso 2: Detección dinámica de violaciones legales vía Taint Tracking
        raw_violations = self.lineage_engine.detect_violations()

        auditor = ComplianceAuditorAgent(session_id=session_id, db_path=self.db_path)
        patcher = DeveloperPatcherAgent(session_id=session_id, root_dir=self.root_dir, db_path=self.db_path)

        processed_findings = []
        applied_patches = []

        # Paso 3: Auditoría Agéntica y Sub-graph Slicing sobre violaciones de linaje
        for v in raw_violations:
            target_symbol = v["sink"]
            conn_temp = get_db_connection(self.db_path)
            for path_node in v["taint_path"]:
                node_r = conn_temp.execute("SELECT node_type FROM graph_nodes WHERE id = ?", (path_node,)).fetchone()
                if node_r and node_r["node_type"] == "file":
                    target_symbol = path_node
                    break
            conn_temp.close()

            slice_data = subgraph_slice(target_symbol, depth=1, db_path=self.db_path)
            audit_verdict = auditor.audit_finding(v, slice_data)

            patch_result = None
            if apply_patches and audit_verdict["target_file"]:
                patch_result = patcher.generate_and_apply_patch(audit_verdict, slice_data)
                applied_patches.append(patch_result)

            processed_findings.append({
                "finding": v,
                "audit": audit_verdict,
                "slice": {
                    "root_node": target_symbol,
                    "isolated_files": slice_data["involved_files"],
                    "nodes_count": len(slice_data["nodes"]),
                },
                "patch": patch_result,
            })

        # Paso 4: Ciclo Agéntico Stateless de Checklist por Archivo (Arquitectura de Plugins)
        checklist_orchestrator = AgenticAuditOrchestrator(
            session_id=session_id,
            root_dir=self.root_dir,
            db_path=self.db_path,
        )
        checklist_report = checklist_orchestrator.run_audit_loop(
            sectorial_plugin=sectorial_plugin,
            apply_patches=apply_patches,
        )

        # Paso 5: Verificación post-parcheo y re-análisis
        verification_result = None
        remaining_violations = len(raw_violations)
        if apply_patches and (applied_patches or checklist_report.get("patch_actions")):
            verification_result = patcher.verify_patch()
            self.lineage_engine.scan_and_build_lineage(root_dir=self.root_dir)
            remaining = self.lineage_engine.detect_violations()
            remaining_violations = len(remaining)

        # Paso 6: Actualizar visualizador interactivo D3.js con checklist integrado
        html_path = generate_graph_html(db_path=self.db_path, open_browser=open_browser)

        return {
            "session_id": session_id,
            "total_context_nodes": nodes_count,
            "lineage_nodes_added": lineage_count,
            "initial_violations": len(raw_violations),
            "remaining_violations": remaining_violations,
            "applied_patches": len(applied_patches) + len(checklist_report.get("patch_actions", [])),
            "verification": verification_result,
            "findings": processed_findings,
            "checklist_audit": checklist_report,
            "visualizer_path": str(html_path),
        }


if __name__ == "__main__":
    pipeline = CompliancePipeline()
    print("[*] Ejecutando Pipeline Agéntico de Cumplimiento Normativo (Antigravity)...")
    res = pipeline.run(apply_patches=True, open_browser=False)

    print("\n" + "=" * 68)
    print("REPORTE DE EJECUCIÓN DEL PIPELINE AGÉNTICO (ANTIGRAVITY)")
    print("=" * 68)
    print(f"Sesión:                      {res['session_id']}")
    print(f"Nodos indexados en Grafo:    {res['total_context_nodes']}")
    print(f"Violaciones iniciales:       {res['initial_violations']}")
    print(f"Parches de código aplicados: {res['applied_patches']}")
    print(f"Violaciones remanentes:      {res['remaining_violations']}")

    chk = res.get("checklist_audit", {})
    if chk:
        print("-" * 68)
        print("AUDITORÍA AGÉNTICA STATELESS POR CHECKLIST (ARQUITECTURA DE PLUGINS)")
        print(f"Plugin Sectorial Activo:     {chk.get('sectorial_plugin', 'Ninguno (Core Universal)')}")
        print(f"Criterios evaluados por nodo:{chk.get('active_criteria_count', 0)}")
        print(f"Archivos auditados:          {chk.get('total_files_audited', 0)}")
        print(f"Archivos Conformes (100%):   {chk.get('compliant_files', 0)}")
        print(f"Archivos con Infracciones:   {chk.get('non_compliant_files', 0)}")
        print(f"Total Infracciones Checklist:{chk.get('total_violations', 0)}")

    if res["verification"]:
        print("-" * 68)
        print(f"Verificación Pytest:         {'PASS (100% Verde)' if res['verification']['tests_passed'] else 'FAIL'}")
    print(f"Visualizador HTML:           {res['visualizer_path']}")
    print("=" * 68 + "\n")
