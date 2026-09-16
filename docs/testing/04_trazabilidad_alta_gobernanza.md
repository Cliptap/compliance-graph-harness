# Estrategia de Testing — Iteración 4: Trazabilidad Alta Gobernanza

> **PRD:** `docs/prd/04_trazabilidad_alta_gobernanza_prd.md`
> **Arquitectura:** `docs/arquitectura/04_trazabilidad_alta_gobernanza.md`
> **Fecha:** 2026-06-11

## 1. Nivel de Testing

**Unit tests + Integration tests** (TDD estricto). PRD 03 ya definió TDD con rojo-verde-refactor.

## 2. Framework

**Pytest** (existente) + `httpx` para tests de API + `pytest-asyncio` para async.

## 3. Cobertura Objetivo

**80%** — gobernanza alta lo exige. Enfocado en:
- Event listeners de auditoría (`events.py`)
- Endpoint de auditoría (`audit.py`)
- Servicio de auditoría (`audit_service.py`)

## 4. Base de Datos para Tests

SQLite en memoria (existente en `conftest.py`). Se agrega la tabla `audit_logs` al fixture de creación de tablas.

## 5. Tests a Implementar

### 5.1 Event Listeners (`test_audit_events.py`)

| Test | Descripción |
|------|-------------|
| `test_create_patient_generates_audit_log` | INSERT en patient → N filas en audit_logs |
| `test_update_patient_generates_audit_log` | UPDATE de email → fila en audit_logs con old/new |
| `test_update_unchanged_field_no_audit` | UPDATE sin cambios reales → sin filas extra |
| `test_delete_patient_generates_audit_log` | Soft-delete → fila en audit_logs con snapshot |
| `test_sensitive_field_is_redacted` | password_hash → `[REDACTED]` en audit_logs |
| `test_audit_log_has_correct_user` | changed_by coincide con el usuario autenticado |

### 5.2 API Endpoints (`test_audit_api.py`)

| Test | Descripción |
|------|-------------|
| `test_admin_can_list_audit_logs` | 200, data con estructura correcta |
| `test_non_admin_cannot_list_audit` | 403 |
| `test_list_audit_with_filters` | Filtro por entity_type reduce resultados |
| `test_list_audit_pagination` | page=2, limit=10 devuelve página correcta |
| `test_admin_can_delete_audit_with_confirm` | Body {"confirm":"delete"} → 200 |
| `test_admin_cannot_delete_audit_without_confirm` | Body vacío → 400 |
| `test_non_admin_cannot_delete_audit` | 403 |
| `test_unauthenticated_cannot_access_audit` | Sin token → 401 |

### 5.3 Endpoints Existentes con Auditoría

| Test | Descripción |
|------|-------------|
| `test_update_patient_triggers_audit_via_api` | PATCH /patients/{id} → verificar audit_logs |
| `test_create_appointment_triggers_audit_via_api` | POST /appointments → verificar audit_logs |

## 6. Fixtures Necesarias

```python
# conftest.py — fixtures nuevos

@pytest.fixture
def admin_token():
    """Token JWT con scopes de admin incluyendo audit:read y audit:delete"""
    return create_test_token("admin", ["audit:read", "audit:delete"])

@pytest.fixture
def recepcionista_token():
    """Token JWT sin scopes de auditoría"""
    return create_test_token("recepcionista", ["patients:read", "patients:write"])

@pytest.fixture
def sample_patient(db_session):
    """Paciente de prueba para testear eventos de auditoría"""
    patient = Patient(rut="12345678-9", nombre_completo="Test Patient", ...)
    db_session.add(patient)
    db_session.commit()
    return patient
```

## 7. Ejecución

```bash
pytest tests/unit/test_audit_events.py -v
pytest tests/unit/test_audit_api.py -v
pytest --cov=src/database/events --cov=src/backend/api/audit --cov-report=term
```

## 8. Criterios de Aceptación

- Todos los tests en verde antes de considerar el feature completo
- Cobertura ≥ 80% en módulos de auditoría
- El test de `sensitive_field_is_redacted` debe pasar (no exponer datos sensibles en logs)
- El test de `non_admin_cannot_access_audit` debe pasar (403 para roles no admin)
