import pytest
from src.harness.contracts import TaskSpec, Finding
from src.harness.validation_engine import ValidationEngine

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]


def test_validation_engine_pass_scenario():
    spec = TaskSpec(
        task_id="EXP-01",
        goal="Validación limpia",
        allowed_paths=["src/backend/api/patients.py"],
        test_targets=["tests/demo/test_patients.py"],
    )
    engine = ValidationEngine()

    clean_code = (
        "def get_clean_data(rut: str):\n"
        "    return {'status': 'active'}\n"
    )

    verdict = engine.validate_change(
        task_spec=spec,
        modified_files={"src/backend/api/patients.py": clean_code},
        run_tests=False,
    )

    assert verdict.status == "PASS"
    assert verdict.total_violations == 0
    feedback = engine.format_feedback(verdict)
    assert "[VALIDACIÓN EXITOSA - PASS]" in feedback


def test_validation_engine_fail_scenario_generates_actionable_feedback():
    spec = TaskSpec(
        task_id="EXP-02",
        goal="Validación con violación CWE-532",
        allowed_paths=["src/backend/api/patients.py"],
        test_targets=["tests/demo/test_patients.py"],
    )
    engine = ValidationEngine()

    leaking_code = (
        "def log_patient_access(rut: str):\n"
        "    logger.info(f'Acceso concedido a RUT {rut}')\n"
        "    return True\n"
    )

    verdict = engine.validate_change(
        task_spec=spec,
        modified_files={"src/backend/api/patients.py": leaking_code},
        run_tests=False,
    )

    assert verdict.status == "FAIL"
    assert verdict.total_violations == 1
    assert verdict.findings[0].policy_id == "privacy.cwe_532"

    feedback = engine.format_feedback(verdict)
    assert "[VALIDACIÓN RECHAZADA - FAIL]" in feedback
    assert "privacy.cwe_532" in feedback
    assert "Directiva de Mitigación" in feedback
    assert "Acceso concedido a RUT {rut}" in feedback
