"""Validation Engine del Arnés de Gobernanza (Sprint 1).

Orquesta la evaluación determinista de propuestas de cambio (Diff / Candidate Files):
1. Ejecuta el PolicyEngine sobre los archivos modificados según TaskSpec.
2. Ejecuta la suite de pruebas unitarias relevante mediante pytest.
3. Emite un veredicto estructurado (ValidationVerdict) con hallazgos (Finding) detallados.
4. Genera mensajes de retroalimentación estructurados (Feedback Loop) para el agente.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from src.harness.contracts import Finding, TaskSpec, ValidationVerdict
from src.harness.db import WORKSPACE_ROOT
from src.harness.policy_engine import PolicyEngine


class ValidationEngine:
    """Motor de validación y compuerta de calidad de cambios propuestos por agentes de código."""

    def __init__(
        self,
        policy_engine: PolicyEngine | None = None,
        root_dir: Path | str = WORKSPACE_ROOT,
    ):
        self.root_dir = Path(root_dir)
        self.policy_engine = policy_engine or PolicyEngine()

    def validate_change(
        self,
        task_spec: TaskSpec,
        modified_files: dict[str, str],
        diff: str | None = None,
        run_tests: bool = True,
    ) -> ValidationVerdict:
        """Evalúa un conjunto de archivos modificados frente a políticas y pruebas automatizadas."""
        # 1. Evaluar políticas deterministas
        findings = self.policy_engine.evaluate_changes(
            task_spec=task_spec,
            modified_files=modified_files,
            diff=diff,
        )

        unrequested_changes = any(
            f.policy_id in ("scope.unauthorized_file", "scope.forbidden_path")
            for f in findings
        )

        tests_passed = True
        test_summary = "Tests omitidos por configuración."

        # 2. Ejecutar pruebas automatizadas si no hay violaciones críticas inmediatas o si se solicita
        if run_tests:
            test_targets = task_spec.test_targets or ["tests/demo/"]
            cmd = [sys.executable, "-m", "pytest"] + test_targets
            try:
                res = subprocess.run(
                    cmd,
                    cwd=str(self.root_dir),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                tests_passed = (res.returncode == 0)
                stdout_tail = res.stdout[-400:] if res.stdout else ""
                stderr_tail = res.stderr[-400:] if res.stderr else ""
                test_summary = stdout_tail or stderr_tail or f"Exit code: {res.returncode}"
            except Exception as ex:
                tests_passed = False
                test_summary = f"Fallo al invocar pytest: {ex}"

        verdict = ValidationVerdict(
            task_id=task_spec.task_id,
            status="FAIL",  # model_post_init calculará PASS o FAIL
            findings=findings,
            tests_passed=tests_passed,
            test_summary=test_summary,
            files_evaluated=list(modified_files.keys()),
            unrequested_changes_detected=unrequested_changes,
        )

        return verdict

    def format_feedback(self, verdict: ValidationVerdict) -> str:
        """Formatea el veredicto en un mensaje estructurado de retroalimentación para el agente."""
        if verdict.status == "PASS":
            return (
                f"### [VALIDACIÓN EXITOSA - PASS] Tarea: `{verdict.task_id}`\n"
                f"- **Políticas Evaluadas:** Conforme (0 infracciones).\n"
                f"- **Pruebas Automatizadas:** {'Aprobadas (100% Verde)' if verdict.tests_passed else 'Fallo'}.\n"
                f"- **Archivos Validados:** {', '.join(verdict.files_evaluated)}\n"
                f"- **Estado:** Propuesta de cambio aprobada para integración.\n"
            )

        lines = [
            f"### [VALIDACIÓN RECHAZADA - FAIL] Tarea: `{verdict.task_id}`",
            f"Se detectaron **{verdict.total_violations} infracciones de política** que impiden la integración del cambio.",
            f"- **Pruebas Unitarias:** {'PASSED' if verdict.tests_passed else 'FAILED'}",
            "\n#### Hallazgos Críticos Detectados:\n",
        ]

        for idx, f in enumerate(verdict.findings, 1):
            lines.append(f"**Hallazgo #{idx} [{f.severity}] — `{f.policy_id}`**")
            lines.append(f"- **Archivo:** `{f.file}`" + (f" (Línea {f.line})" if f.line else ""))
            lines.append(f"- **Mensaje:** {f.message}")
            if f.evidence:
                lines.append(f"- **Evidencia:** `{f.evidence}`")
            if f.remediation_advice:
                lines.append(f"- **Directiva de Mitigación:** {f.remediation_advice}")
            lines.append("")

        if not verdict.tests_passed and verdict.test_summary:
            lines.append("#### Resumen de Fallo en Pruebas:")
            lines.append(f"```\n{verdict.test_summary}\n```\n")

        lines.append(
            "**Instrucción para el Agente:** Corrige exclusivamente las líneas y archivos señalados "
            "siguiendo las directivas de mitigación antes de someter una nueva propuesta."
        )

        return "\n".join(lines)
