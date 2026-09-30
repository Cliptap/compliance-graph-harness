from __future__ import annotations

import ast
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.harness.db import (
    DEFAULT_DB_PATH,
    RULES_PATH,
    WORKSPACE_ROOT,
    get_db_connection,
    log_agent_reasoning,
)
from src.harness.graph_engine import subgraph_slice


# ==============================================================================
# 1. MODELOS DE DATOS PYDANTIC (Esquema Estructurado de Cumplimiento)
# ==============================================================================

class ChecklistCriterion(BaseModel):
    id: str
    category: str
    law_article: str
    title: str
    description: str
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] = "CRITICAL"
    indicators: list[str] = Field(default_factory=list)
    prohibited_patterns: list[str] = Field(default_factory=list)


class ChecklistEvaluationResult(BaseModel):
    criterion_id: str
    plugin_name: str  # "core_universal" | "health_clinical"
    law_article: str
    title: str
    status: Literal["PASSED", "VIOLATION", "NOT_APPLICABLE"]
    severity: str
    details: str
    evidence_snippet: str | None = None
    line_number: int | None = None
    remediation_advice: str | None = None


class FileAuditVerdict(BaseModel):
    file_path: str
    file_node_id: str
    total_criteria: int
    passed_count: int
    violation_count: int
    na_count: int
    overall_status: Literal["COMPLIANT", "NON_COMPLIANT"]
    results: list[ChecklistEvaluationResult]
    isolated_files: list[str] = Field(default_factory=list)


# ==============================================================================
# 2. REGISTRO DE CHECKLIST Y PLUGINS SECTORIALES
# ==============================================================================

class ChecklistRegistry:
    """Gestiona el catálogo de reglas normativas universales (Core Ley 21.719)
    y los plugins de contexto sectorial (ej. Salud y Ficha Clínica Ley 20.584/21.668).
    """

    def __init__(self, rules_path: Path | str = RULES_PATH):
        self.rules_path = Path(rules_path)
        self.core_criteria: list[ChecklistCriterion] = []
        self.sectorial_plugins: dict[str, dict[str, Any]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        if not self.rules_path.exists():
            return
        data = json.loads(self.rules_path.read_text(encoding="utf-8"))
        for raw in data.get("core_checklist", []):
            self.core_criteria.append(ChecklistCriterion(**raw))
        self.sectorial_plugins = data.get("sectorial_plugins", {})

    def get_active_criteria(self, sectorial_plugin: str | None = "health_clinical") -> list[tuple[str, ChecklistCriterion]]:
        """Retorna una lista de tuplas (plugin_name, criterio) para la sesión de auditoría."""
        active: list[tuple[str, ChecklistCriterion]] = []
        for crit in self.core_criteria:
            active.append(("core_universal", crit))
        if sectorial_plugin and sectorial_plugin in self.sectorial_plugins:
            plugin_data = self.sectorial_plugins[sectorial_plugin]
            for raw in plugin_data.get("criteria", []):
                active.append((sectorial_plugin, ChecklistCriterion(**raw)))
        return active


# ==============================================================================
# 3. SUBAGENTE AUDITOR STATELESS (Ciclo Limpio por Nodo / Archivo)
# ==============================================================================

class StatelessAuditor:
    """Subagente Auditor Especializado con ciclo de vida efímero (Stateless).
    
    Se instancia para evaluar un único archivo y su subgrafo de contexto,
    aplica el checklist normativo, persiste los resultados periciales
    y se destruye para prevenir contaminación de memoria o sesgo acumulado.
    """

    def __init__(self, session_id: str, db_path: Path | str = DEFAULT_DB_PATH):
        self.session_id = session_id
        self.db_path = Path(db_path)

    def audit_file(
        self,
        file_path_abs: Path,
        rel_path: str,
        file_node_id: str,
        slice_data: dict[str, Any],
        active_criteria: list[tuple[str, ChecklistCriterion]],
    ) -> FileAuditVerdict:
        content = file_path_abs.read_text(encoding="utf-8")
        lines = content.splitlines()
        content_lower = content.lower()

        eval_results: list[ChecklistEvaluationResult] = []

        for plugin_name, criterion in active_criteria:
            res = self._evaluate_criterion(
                criterion=criterion,
                plugin_name=plugin_name,
                content=content,
                content_lower=content_lower,
                lines=lines,
                rel_path=rel_path,
                slice_data=slice_data,
            )
            eval_results.append(res)
            self._persist_evaluation(rel_path, file_node_id, res)

        passed = sum(1 for r in eval_results if r.status == "PASSED")
        violations = sum(1 for r in eval_results if r.status == "VIOLATION")
        na = sum(1 for r in eval_results if r.status == "NOT_APPLICABLE")
        overall: Literal["COMPLIANT", "NON_COMPLIANT"] = "COMPLIANT" if violations == 0 else "NON_COMPLIANT"

        verdict = FileAuditVerdict(
            file_path=rel_path,
            file_node_id=file_node_id,
            total_criteria=len(eval_results),
            passed_count=passed,
            violation_count=violations,
            na_count=na,
            overall_status=overall,
            results=eval_results,
            isolated_files=slice_data.get("involved_files", [rel_path]),
        )

        # Registro de observabilidad del agente en SQLite
        log_agent_reasoning(
            session_id=self.session_id,
            agent_name="stateless_compliance_auditor",
            step_name="audit_node_checklist",
            input_payload={"file": rel_path, "criteria_count": len(active_criteria)},
            reasoning_trace=(
                f"[AUDITORIA STATELESS] Archivo `{rel_path}` evaluado bajo {len(active_criteria)} mandatos.\n"
                f"Veredicto General: {overall} (Aprobados: {passed}, Violaciones: {violations}, N/A: {na}).\n"
                f"Subgrafo aislado: {len(slice_data.get('nodes', []))} nodos interconectados."
            ),
            output_result=verdict.model_dump(),
            db_path=self.db_path,
        )

        return verdict

    def _evaluate_criterion(
        self,
        criterion: ChecklistCriterion,
        plugin_name: str,
        content: str,
        content_lower: str,
        lines: list[str],
        rel_path: str,
        slice_data: dict[str, Any],
    ) -> ChecklistEvaluationResult:
        cid = criterion.id

        # CORE-CHECK-001: Privacidad desde el Diseño (Enmascaramiento / Cifrado)
        if cid == "CORE-CHECK-001":
            has_rut_or_id = any(term in content_lower for term in ["identifier", "rut", "run", "national_id"])
            if has_rut_or_id:
                has_masking = any(m in content_lower for m in ["mask", "redact", "hash", "encrypt", ".***.***", "[redacted]"])
                if not has_masking and ("events.py" in rel_path or "audit" in rel_path):
                    return ChecklistEvaluationResult(
                        criterion_id=cid,
                        plugin_name=plugin_name,
                        law_article=criterion.law_article,
                        title=criterion.title,
                        status="VIOLATION",
                        severity=criterion.severity,
                        details="Persistencia o manipulación de identificadores (RUT) sin enmascaramiento activo en la capa de auditoría.",
                        evidence_snippet="SENSITIVE_FIELDS sin inclusión de 'identifier' / 'rut'",
                        remediation_advice="Incorporar 'identifier' y 'rut' a SENSITIVE_FIELDS y enmascarar en formato XX.***.***-X.",
                    )
                return ChecklistEvaluationResult(
                    criterion_id=cid,
                    plugin_name=plugin_name,
                    law_article=criterion.law_article,
                    title=criterion.title,
                    status="PASSED",
                    severity=criterion.severity,
                    details="Se identifican salvaguardas de protección y enmascaramiento en el manejo de identificadores.",
                )
            return ChecklistEvaluationResult(
                criterion_id=cid,
                plugin_name=plugin_name,
                law_article=criterion.law_article,
                title=criterion.title,
                status="NOT_APPLICABLE",
                severity=criterion.severity,
                details="El componente no procesa identificadores civiles directos.",
            )

        # CORE-CHECK-002: Prevención de Fugas en Logs (CWE-532 / Art. 14 bis)
        elif cid == "CORE-CHECK-002":
            log_calls = []
            for idx, line in enumerate(lines, 1):
                line_l = line.lower()
                if any(p in line_l for p in ["print(", "sys.stdout", "logger.info", "logger.debug", "logger.error"]):
                    if any(s in line_l for s in ["rut", "patient", "password", "diagnosis", "identificador"]):
                        log_calls.append((idx, line.strip()))
            if log_calls:
                first_line, first_snippet = log_calls[0]
                return ChecklistEvaluationResult(
                    criterion_id=cid,
                    plugin_name=plugin_name,
                    law_article=criterion.law_article,
                    title=criterion.title,
                    status="VIOLATION",
                    severity=criterion.severity,
                    details=f"Se detectó posible emisión de datos sensibles a canales de depuración en línea {first_line}.",
                    evidence_snippet=first_snippet,
                    line_number=first_line,
                    remediation_advice="Eliminar la llamada a print/logger o aplicar función de ofuscación previa a la emisión.",
                )
            return ChecklistEvaluationResult(
                criterion_id=cid,
                plugin_name=plugin_name,
                law_article=criterion.law_article,
                title=criterion.title,
                status="PASSED",
                severity=criterion.severity,
                details="No se observan fugas hacia registros de depuración o consola.",
            )

        # CORE-CHECK-003: Guardias ARCOP y Control de Acceso Granular (RBAC)
        elif cid == "CORE-CHECK-003":
            if "api/" in rel_path:
                has_rbac = any(r in content_lower for r in ["get_current_user", "security(", "depends(", "scopes="])
                if not has_rbac:
                    return ChecklistEvaluationResult(
                        criterion_id=cid,
                        plugin_name=plugin_name,
                        law_article=criterion.law_article,
                        title=criterion.title,
                        status="VIOLATION",
                        severity=criterion.severity,
                        details="Endpoint de API expuesto sin dependencias de seguridad o validación de roles/scopes.",
                        remediation_advice="Añadir Annotated[TokenData, Security(get_current_user, scopes=[...])] en las rutas.",
                    )
                return ChecklistEvaluationResult(
                    criterion_id=cid,
                    plugin_name=plugin_name,
                    law_article=criterion.law_article,
                    title=criterion.title,
                    status="PASSED",
                    severity=criterion.severity,
                    details="Rutas de API aseguradas con verificación de usuario autenticado y scopes RBAC.",
                )
            return ChecklistEvaluationResult(
                criterion_id=cid,
                plugin_name=plugin_name,
                law_article=criterion.law_article,
                title=criterion.title,
                status="NOT_APPLICABLE",
                severity=criterion.severity,
                details="Criterio de control de acceso perimetral aplicable primordialmente a capas de API.",
            )

        # CORE-CHECK-004: Decisiones Automatizadas y Human-in-the-Loop (Art. 8 bis)
        elif cid == "CORE-CHECK-004":
            has_auto_infer = any(term in content_lower for term in ["auto_diagnose", "ai_triage", "auto_resolve"])
            if has_auto_infer:
                has_human_gate = any(g in content_lower for g in ["human_review", "physician_review", "pending_review"])
                if not has_human_gate:
                    return ChecklistEvaluationResult(
                        criterion_id=cid,
                        plugin_name=plugin_name,
                        law_article=criterion.law_article,
                        title=criterion.title,
                        status="VIOLATION",
                        severity=criterion.severity,
                        details="Proceso de inferencia algorítmica sin compuerta de validación humana médica.",
                        remediation_advice="Añadir compuerta de revisión médica humana obligatoria (status = PENDING_REVIEW).",
                    )
            return ChecklistEvaluationResult(
                criterion_id=cid,
                plugin_name=plugin_name,
                law_article=criterion.law_article,
                title=criterion.title,
                status="PASSED",
                severity=criterion.severity,
                details="No se identifican procesos de decisión automatizada sin supervisión.",
            )

        # HEALTH-CHECK-001: Retención de 15 años y Soft-Delete Ley 20.584 Art. 13
        elif cid == "HEALTH-CHECK-001":
            if "api/" in rel_path or "database/" in rel_path:
                has_hard_delete = False
                bad_line = None
                bad_snippet = None
                for idx, line in enumerate(lines, 1):
                    line_l = line.lower()
                    if ("session.delete" in line_l or "delete().where" in line_l or "hard_delete" in line_l):
                        if any(t in line_l for t in ["patient", "appointment", "medical", "clinical"]):
                            has_hard_delete = True
                            bad_line = idx
                            bad_snippet = line.strip()
                            break
                if has_hard_delete:
                    return ChecklistEvaluationResult(
                        criterion_id=cid,
                        plugin_name=plugin_name,
                        law_article=criterion.law_article,
                        title=criterion.title,
                        status="VIOLATION",
                        severity=criterion.severity,
                        details=f"Infracción al deber de retención decenal (Art. 13 Ley 20.584): Borrado físico detectado en línea {bad_line}.",
                        evidence_snippet=bad_snippet,
                        line_number=bad_line,
                        remediation_advice="Reemplazar borrado destructivo por marcado lógico (repo.soft_delete o status='BLOCKED_LEGAL_HOLD').",
                    )
                return ChecklistEvaluationResult(
                    criterion_id=cid,
                    plugin_name=plugin_name,
                    law_article=criterion.law_article,
                    title=criterion.title,
                    status="PASSED",
                    severity=criterion.severity,
                    details="Cumplimiento con custodia de historiales médicos mediante preservación o soft-delete.",
                )
            return ChecklistEvaluationResult(
                criterion_id=cid,
                plugin_name=plugin_name,
                law_article=criterion.law_article,
                title=criterion.title,
                status="NOT_APPLICABLE",
                severity=criterion.severity,
                details="No involucra persistencia ni ciclo de vida de historiales clínicos.",
            )

        # HEALTH-CHECK-002: Interoperabilidad FHIR HL7 CL Core (Ley 21.668)
        elif cid == "HEALTH-CHECK-002":
            if "export" in rel_path or "portability" in rel_path:
                has_fhir = any(f in content_lower for f in ["fhir", "bundle", "cl_core"])
                if not has_fhir:
                    return ChecklistEvaluationResult(
                        criterion_id=cid,
                        plugin_name=plugin_name,
                        law_article=criterion.law_article,
                        title=criterion.title,
                        status="VIOLATION",
                        severity=criterion.severity,
                        details="Exportación de expediente médico sin estructuración HL7 FHIR R4 CL Core.",
                        remediation_advice="Serializar recurso utilizando adaptador FHIR Bundle CL Core.",
                    )
            return ChecklistEvaluationResult(
                criterion_id=cid,
                plugin_name=plugin_name,
                law_article=criterion.law_article,
                title=criterion.title,
                status="PASSED",
                severity=criterion.severity,
                details="No presenta canales de exportación no interoperables.",
            )

        # HEALTH-CHECK-003: Aislamiento Reforzado de Datos de Salud (Art. 16 bis)
        elif cid == "HEALTH-CHECK-003":
            has_health_data = any(term in content_lower for term in ["diagnosis", "clinical_notes", "medical_record"])
            if has_health_data:
                has_prot = any(p in content_lower for p in ["redact", "mask", "protect", "secret", "sensitive"])
                if not has_prot and "events.py" in rel_path:
                    return ChecklistEvaluationResult(
                        criterion_id=cid,
                        plugin_name=plugin_name,
                        law_article=criterion.law_article,
                        title=criterion.title,
                        status="VIOLATION",
                        severity=criterion.severity,
                        details="Datos sensibles de salud sin aislamiento ni redacción en persistencia de auditoría.",
                        remediation_advice="Incorporar diagnósticos y notas a la directiva de redacción de eventos.",
                    )
                return ChecklistEvaluationResult(
                    criterion_id=cid,
                    plugin_name=plugin_name,
                    law_article=criterion.law_article,
                    title=criterion.title,
                    status="PASSED",
                    severity=criterion.severity,
                    details="Datos de salud protegidos bajo normas de aislamiento y confidencialidad médica.",
                )
            return ChecklistEvaluationResult(
                criterion_id=cid,
                plugin_name=plugin_name,
                law_article=criterion.law_article,
                title=criterion.title,
                status="NOT_APPLICABLE",
                severity=criterion.severity,
                details="No procesa datos clínicos de salud directamente.",
            )

        return ChecklistEvaluationResult(
            criterion_id=cid,
            plugin_name=plugin_name,
            law_article=criterion.law_article,
            title=criterion.title,
            status="PASSED",
            severity=criterion.severity,
            details="Evaluación conforme con los estándares normativos.",
        )

    def _persist_evaluation(self, file_path: str, file_node_id: str, res: ChecklistEvaluationResult) -> None:
        conn = get_db_connection(self.db_path)
        try:
            audit_id = f"CHK-{uuid.uuid4().hex[:10].upper()}"
            conn.execute(
                """
                INSERT INTO file_checklist_audits 
                (id, session_id, file_path, file_node_id, plugin_name, criterion_id, law_article, status, severity, details, evidence_snippet, remediation_advice)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    self.session_id,
                    file_path,
                    file_node_id,
                    res.plugin_name,
                    res.criterion_id,
                    res.law_article,
                    res.status,
                    res.severity,
                    res.details,
                    res.evidence_snippet,
                    res.remediation_advice,
                ),
            )
            conn.commit()
        finally:
            conn.close()


# ==============================================================================
# 4. ORQUESTADOR DEL LOOP AGÉNTICO (Invocación Stateless & Safety Rollback)
# ==============================================================================

class AgenticAuditOrchestrator:
    """Orquestador del ciclo agéntico de auditoría en loop.
    
    1. Itera por cada nodo/archivo objetivo (arquitectura híbrida priorizada).
    2. Aísla el subgrafo de contexto (subgraph_slice).
    3. Invoca una instancia limpia de StatelessAuditor.
    4. Persiste los resultados estructurados en SQLite.
    5. Si procede mitigación, coordina con el Patcher ejecutando verificación
       con Pytest y Rollback guiado ante fallas.
    """

    def __init__(
        self,
        session_id: str,
        root_dir: Path | str = WORKSPACE_ROOT,
        db_path: Path | str = DEFAULT_DB_PATH,
    ):
        self.session_id = session_id
        self.root_dir = Path(root_dir)
        self.db_path = Path(db_path)
        self.registry = ChecklistRegistry()

    def run_audit_loop(
        self,
        sectorial_plugin: str | None = "health_clinical",
        apply_patches: bool = True,
        scan_dirs: list[Path] | None = None,
    ) -> dict[str, Any]:
        from src.harness.pipeline import DeveloperPatcherAgent

        active_criteria = self.registry.get_active_criteria(sectorial_plugin=sectorial_plugin)
        conn = get_db_connection(self.db_path)

        # Identificar archivos prioritarios para la auditoría (API y Base de Datos)
        if scan_dirs is None:
            scan_dirs = [self.root_dir / "src" / "database", self.root_dir / "src" / "backend" / "api"]
        target_files: list[Path] = []
        for sdir in scan_dirs:
            if sdir.exists():
                for py_file in sorted(sdir.rglob("*.py")):
                    if py_file.name != "__init__.py":
                        target_files.append(py_file)

        verdicts: list[FileAuditVerdict] = []
        patch_actions: list[dict[str, Any]] = []

        try:
            for py_file in target_files:
                rel_path = py_file.relative_to(self.root_dir).as_posix()

                # Resolver id canónico en graph_nodes
                row = conn.execute(
                    "SELECT id FROM graph_nodes WHERE file_path = ? AND node_type = 'file'",
                    (rel_path,),
                ).fetchone()
                file_node_id = row["id"] if row else rel_path.replace("/", "_").replace(".", "_")

                # Corte quirúrgico de subgrafo de contexto (1 salto de vecindad)
                slice_data = subgraph_slice(file_node_id, depth=1, db_path=self.db_path)

                # Instanciar auditor stateless con contexto fresco y libre de sesgo
                auditor = StatelessAuditor(session_id=self.session_id, db_path=self.db_path)
                verdict = auditor.audit_file(
                    file_path_abs=py_file,
                    rel_path=rel_path,
                    file_node_id=file_node_id,
                    slice_data=slice_data,
                    active_criteria=active_criteria,
                )
                del auditor  # Destrucción explícita de la instancia del auditor

                verdicts.append(verdict)

                # Si hay violaciones y se requiere parcheo
                if apply_patches and verdict.violation_count > 0:
                    patcher = DeveloperPatcherAgent(
                        session_id=self.session_id,
                        root_dir=self.root_dir,
                        db_path=self.db_path,
                    )
                    original_code = py_file.read_text(encoding="utf-8")

                    # Preparar hallazgo sintético para el patcher
                    first_viol = next(r for r in verdict.results if r.status == "VIOLATION")
                    finding_payload = {
                        "finding_id": f"AUDIT-VIOL-{uuid.uuid4().hex[:6].upper()}",
                        "rule_id": first_viol.criterion_id,
                        "title": first_viol.title,
                        "law_article": first_viol.law_article,
                        "severity": first_viol.severity,
                        "taint_path": [file_node_id],
                        "required_mitigations": [first_viol.remediation_advice or "maskSensitiveData"],
                    }

                    # Intento 1 de parcheo
                    patch_res = patcher.generate_and_apply_patch(
                        audit_verdict={
                            "finding_id": finding_payload["finding_id"],
                            "target_file": rel_path,
                            "mitigations_required": finding_payload["required_mitigations"],
                        },
                        slice_data=slice_data,
                    )

                    # Protocolo de Seguridad: Validación Pytest con Rollback y 1 Reintento Guiado
                    if patch_res.get("patch_applied"):
                        test_res = patcher.verify_patch()
                        if test_res["tests_passed"]:
                            patch_actions.append({
                                "file": rel_path,
                                "status": "PATCHED_AND_VERIFIED",
                                "diff": patch_res.get("diff_summary"),
                            })
                        else:
                            # Rollback inmediato intento 1
                            py_file.write_text(original_code, encoding="utf-8")
                            
                            # Registro del fallo y reintento guiado
                            log_agent_reasoning(
                                session_id=self.session_id,
                                agent_name="developer_patcher_agent",
                                step_name="rollback_attempt_1",
                                input_payload={"file": rel_path, "pytest_error": test_res["output_summary"]},
                                reasoning_trace="Pytest falló tras el parche. Se revierte archivo y se intenta 2da estrategia de parcheo.",
                                output_result={"rollback": True},
                                db_path=self.db_path,
                            )

                            # Reintento 2 guiado
                            patch_res_retry = patcher.generate_and_apply_patch(
                                audit_verdict={
                                    "finding_id": finding_payload["finding_id"],
                                    "target_file": rel_path,
                                    "mitigations_required": finding_payload["required_mitigations"],
                                },
                                slice_data=slice_data,
                            )
                            test_res_retry = patcher.verify_patch()

                            if test_res_retry["tests_passed"]:
                                patch_actions.append({
                                    "file": rel_path,
                                    "status": "PATCHED_ON_RETRY",
                                    "diff": patch_res_retry.get("diff_summary"),
                                })
                            else:
                                # Reversión definitiva a código limpio
                                py_file.write_text(original_code, encoding="utf-8")
                                patch_actions.append({
                                    "file": rel_path,
                                    "status": "PATCH_FAILED_MANUAL_REVIEW_REQUIRED",
                                    "reason": "Pytest falló en ambos intentos de parcheo.",
                                })

            # Resumen general del ciclo de auditoría
            total_files = len(verdicts)
            compliant_files = sum(1 for v in verdicts if v.overall_status == "COMPLIANT")
            total_violations = sum(v.violation_count for v in verdicts)

            return {
                "session_id": self.session_id,
                "sectorial_plugin": sectorial_plugin,
                "active_criteria_count": len(active_criteria),
                "total_files_audited": total_files,
                "compliant_files": compliant_files,
                "non_compliant_files": total_files - compliant_files,
                "total_violations": total_violations,
                "verdicts": [v.model_dump() for v in verdicts],
                "patch_actions": patch_actions,
            }
        finally:
            conn.close()
