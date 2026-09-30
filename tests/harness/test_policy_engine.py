import pytest
from src.harness.contracts import TaskSpec, Finding
from src.harness.policy_engine import (
    PolicyEngine,
    ScopePolicy,
    SensitiveLoggingPolicy,
    DomainInvariantPolicy,
    DependencyPolicy,
)

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]


def test_scope_policy_flags_unauthorized_files():
    spec = TaskSpec(
        task_id="T01",
        goal="Corregir validación de RUT",
        allowed_paths=["src/backend/api/patients.py"],
        forbidden_paths=["src/frontend/**"],
    )
    policy = ScopePolicy()

    # Archivo permitido
    findings = policy.evaluate(spec, {"src/backend/api/patients.py": "# ok code"})
    assert len(findings) == 0

    # Archivo prohibido
    findings = policy.evaluate(spec, {"src/frontend/src/App.vue": "<template></template>"})
    assert len(findings) == 1
    assert findings[0].policy_id == "scope.forbidden_path"
    assert findings[0].severity == "CRITICAL"

    # Archivo fuera de allowed_paths
    findings = policy.evaluate(spec, {"src/backend/api/appointments.py": "# unrequested"})
    assert len(findings) == 1
    assert findings[0].policy_id == "scope.unauthorized_file"
    assert findings[0].severity == "HIGH"


def test_sensitive_logging_policy_detects_cwe_532():
    spec = TaskSpec(task_id="T02", goal="Agregar auditoría")
    policy = SensitiveLoggingPolicy()

    # Caso infractor: logger.info con RUT directo sin enmascarar
    bad_code = (
        "def get_patient(rut: str):\n"
        "    logger.info(f'Consultando paciente con rut: {rut}')\n"
        "    return {'status': 'ok'}\n"
    )
    findings = policy.evaluate(spec, {"src/backend/api/patients.py": bad_code})
    assert len(findings) == 1
    assert findings[0].policy_id == "privacy.cwe_532"
    assert findings[0].line == 2
    assert "rut" in findings[0].evidence.lower()

    # Caso conforme: seudonimizado o con token mask/redact
    good_code = (
        "def get_patient(rut: str):\n"
        "    masked_rut = mask_rut(rut)\n"
        "    logger.info(f'Consultando paciente: {masked_rut}')\n"
        "    return {'status': 'ok'}\n"
    )
    findings = policy.evaluate(spec, {"src/backend/api/patients.py": good_code})
    assert len(findings) == 0


def test_domain_invariant_policy_prevents_hard_delete():
    spec = TaskSpec(task_id="T03", goal="Cancelar cita")
    policy = DomainInvariantPolicy()

    destructive_code = (
        "def cancel_appointment(db, appt_id):\n"
        "    db.session.delete(appointment)\n"
        "    db.session.commit()\n"
    )
    findings = policy.evaluate(spec, {"src/backend/services/appointment_service.py": destructive_code})
    assert len(findings) == 1
    assert findings[0].policy_id == "domain.prohibited_deletion"
    assert findings[0].line == 2


def test_dependency_policy_prevents_unauthorized_manifest_edits():
    spec = TaskSpec(
        task_id="T04",
        goal="Tarea simple",
        constraints=["no external dependencies", "sin dependencias adicionales"],
    )
    policy = DependencyPolicy()

    findings = policy.evaluate(spec, {"requirements.txt": "redis==5.0.0\n"})
    assert len(findings) == 1
    assert findings[0].policy_id == "governance.unauthorized_dependency"


def test_policy_engine_aggregates_findings():
    spec = TaskSpec(
        task_id="T05",
        goal="Flujo con múltiples infracciones",
        allowed_paths=["src/backend/api/patients.py"],
        constraints=["no external dependencies"],
    )
    engine = PolicyEngine()

    modified_files = {
        "src/backend/api/patients.py": "logger.error(f'Error en RUT {rut}')\n",
        "requirements.txt": "celery>=5.0\n",
    }
    findings = engine.evaluate_changes(spec, modified_files)
    assert len(findings) == 3
    policy_ids = {f.policy_id for f in findings}
    assert "privacy.cwe_532" in policy_ids
    assert "scope.unauthorized_file" in policy_ids
    assert "governance.unauthorized_dependency" in policy_ids
