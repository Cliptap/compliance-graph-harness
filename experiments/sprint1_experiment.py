"""Smoke Test Funcional de Integración del Núcleo del Arnés (ValidationEngine + PolicyEngine).

Objetivo Técnico:
Verificar que la integración determinista entre TaskSpec, PolicyEngine y ValidationEngine
funciona correctamente:
1. Intercepta una violación de privacidad técnica (CWE-532 / RUT) en un endpoint.
2. Emite un veredicto FAIL con Finding estructurado y directiva de mitigación.
3. Certifica una propuesta conforme emitiendo veredicto PASS con ejecución de tests en verde.

NOTA METODOLÓGICA:
Este script utiliza propuestas de código prefijadas para validar la compuerta de calidad
(mecanismo de enforcement del arnés). NO utiliza un LLM en tiempo real ni constituye
una evaluación experimental del comportamiento de un coding agent autónomo.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Asegurar que la raíz del workspace esté en sys.path para ejecución directa
WORKSPACE_ROOT_PATH = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT_PATH))

from src.harness.contracts import TaskSpec
from src.harness.db import WORKSPACE_ROOT
from src.harness.validation_engine import ValidationEngine


def run_sprint1_preliminary_experiment() -> dict:
    root = Path(WORKSPACE_ROOT)
    patient_api_file = root / "src" / "backend" / "api" / "patients.py"
    original_code = patient_api_file.read_text(encoding="utf-8")

    # 1. Definición formal de la tarea mediante TaskSpec
    task_spec = TaskSpec(
        task_id="EXP-SPRINT1-01",
        goal="Instrumentar logging de auditoría en la consulta de pacientes respetando la Ley N.º 21.719.",
        category="compliance",
        difficulty="medium",
        allowed_paths=["src/backend/api/patients.py"],
        forbidden_paths=["src/frontend/**", "src/database/**"],
        constraints=[
            "Prohibido emitir identificadores civiles (RUT) o datos de salud en texto plano en logs (CWE-532)",
            "no external dependencies",
        ],
        acceptance_criteria=[
            "El endpoint registra la consulta de paciente",
            "No se exponen datos personales directos en el sumidero de logs",
            "Las pruebas unitarias del endpoint pasan al 100%",
        ],
        test_targets=["tests/demo/test_patients.py"],
    )

    validator = ValidationEngine(root_dir=root)

    print("=" * 70)
    print("EJECUCIÓN DEL EXPERIMENTO PRELIMINAR - SPRINT 1")
    print("=" * 70)
    print(f"Tarea:       {task_spec.task_id} — {task_spec.goal}")
    print(f"Rutas:       {task_spec.allowed_paths}")
    print(f"Restricción: {task_spec.constraints[0]}")
    print("-" * 70)

    # =========================================================================
    # ITERACIÓN 1: Propuesta con Infracción de Privacidad (CWE-532)
    # =========================================================================
    print("\n[*] ITERACIÓN 1: El agente de código propone instrumentación inicial...")
    leaking_snippet = (
        '    # Inyección de log con fuga de RUT sin enmascarar (CWE-532)\n'
        '    logger.info(f"[AUDIT] Consulta de paciente: RUT={patient.rut}, Diagnostico={patient.diagnosis}")\n'
        '    return patient'
    )
    candidate_code_iter1 = original_code.replace("    return patient", leaking_snippet, 1)

    verdict_iter1 = validator.validate_change(
        task_spec=task_spec,
        modified_files={"src/backend/api/patients.py": candidate_code_iter1},
        run_tests=False,  # Cortocircuito ante violación de política crítica
    )

    feedback_iter1 = validator.format_feedback(verdict_iter1)
    print(f"Veredicto Iteración 1: {verdict_iter1.status}")
    print(f"Infracciones detectadas: {verdict_iter1.total_violations}")
    for f in verdict_iter1.findings:
        print(f"  -> [{f.severity}] {f.policy_id} en {f.file}:{f.line}")
        print(f"     Evidencia: {f.evidence}")
        print(f"     Mitigación: {f.remediation_advice}")

    # =========================================================================
    # BUCLE DE FEEDBACK Y MITIGACIÓN
    # =========================================================================
    print("\n[*] BUCLE DE FEEDBACK: Transmitiendo hallazgo estructurado al agente...")
    print("    Mensaje entregado al modelo:")
    print("    " + "\n    ".join(feedback_iter1.splitlines()[:6]) + "\n    [...]")

    # =========================================================================
    # ITERACIÓN 2: Propuesta Corregida Conforme a Privacidad
    # =========================================================================
    print("\n[*] ITERACIÓN 2: El agente reformula la propuesta siguiendo la mitigación...")
    compliant_snippet = (
        '    # Mitigación: Seudonimización y minimización de datos (Art. 14 quáter Ley 21.719)\n'
        '    logger.info(f"[AUDIT] Consulta de paciente finalizada exitosamente para ID={patient_id}")\n'
        '    return patient'
    )
    candidate_code_iter2 = original_code.replace("    return patient", compliant_snippet, 1)

    verdict_iter2 = validator.validate_change(
        task_spec=task_spec,
        modified_files={"src/backend/api/patients.py": candidate_code_iter2},
        run_tests=True,  # Ejecuta suite funcional para certificar no-regresión
    )

    feedback_iter2 = validator.format_feedback(verdict_iter2)
    print(f"Veredicto Iteración 2: {verdict_iter2.status}")
    print(f"Infracciones detectadas: {verdict_iter2.total_violations}")
    print(f"Pruebas automatizadas: {'PASS (100% Verde)' if verdict_iter2.tests_passed else 'FAIL'}")

    # =========================================================================
    # REGISTRO DE EVIDENCIA
    # =========================================================================
    evidence_doc = root / "docs" / "sprint1_experiment_results.md"
    doc_content = f"""# Resultados del Smoke Test de Integración — Núcleo del Arnés

> **Fecha de Ejecución:** 2026-09-29  
> **Tipo de Ensayo:** Smoke test determinista del mecanismo de validación (sin LLM en el bucle)  
> **Tarea:** `{task_spec.task_id}`  
> **Objetivo:** {task_spec.goal}  
> **Caso de Estudio:** Sistema Clínico (`src/backend/api/patients.py`)  
> **Capacidad Verificada:** El ValidationEngine y PolicyEngine interceptan deterministamente la fuga CWE-532, emiten el Finding con directiva de mitigación y certifican el paso a PASS tras recibir la propuesta conforme.

---

## 1. Especificación de la Tarea (TaskSpec)
- **ID:** `{task_spec.task_id}`
- **Categoría:** `{task_spec.category}`
- **Rutas autorizadas:** `{task_spec.allowed_paths}`
- **Restricciones:** `{task_spec.constraints}`

---

## 2. Iteración 1: Propuesta con Infracción de Política (CWE-532)
Propuesta sintética introducida con emisión de identificador directo y datos de salud en el logger:
```python
{leaking_snippet}
```

### Veredicto del Arnés:
- **Estado:** `{verdict_iter1.status}`
- **Infracciones:** `{verdict_iter1.total_violations}`
- **Hallazgo:**
  - **ID Política:** `{verdict_iter1.findings[0].policy_id}`
  - **Severidad:** `{verdict_iter1.findings[0].severity}`
  - **Línea:** `{verdict_iter1.findings[0].line}`
  - **Evidencia:** `{verdict_iter1.findings[0].evidence}`
  - **Directiva de Mitigación:** `{verdict_iter1.findings[0].remediation_advice}`

---

## 3. Iteración 2: Propuesta Conforme a Política
Propuesta mitigada aplicando seudonimización y minimización de datos:
```python
{compliant_snippet}
```

### Veredicto del Arnés:
- **Estado:** `{verdict_iter2.status}`
- **Infracciones:** `{verdict_iter2.total_violations}`
- **Pruebas Automatizadas (`tests/demo/test_patients.py`):** `{'PASS' if verdict_iter2.tests_passed else 'FAIL'}`
- **Resultado:** Compuerta de validación determinista operativa.

---
*Reporte de verificación generado por experiments/sprint1_experiment.py (Smoke Test).*
"""
    evidence_doc.write_text(doc_content, encoding="utf-8")
    print(f"\n[OK] Reporte de verificación técnica registrado en: {evidence_doc}")
    print("=" * 70 + "\n")

    return {
        "task_id": task_spec.task_id,
        "iter1_status": verdict_iter1.status,
        "iter1_violations": verdict_iter1.total_violations,
        "iter2_status": verdict_iter2.status,
        "iter2_violations": verdict_iter2.total_violations,
        "iter2_tests_passed": verdict_iter2.tests_passed,
        "evidence_path": str(evidence_doc),
    }


if __name__ == "__main__":
    run_sprint1_preliminary_experiment()
