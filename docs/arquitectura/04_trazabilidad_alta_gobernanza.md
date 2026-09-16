# Documento de Arquitectura — Iteración 4: Trazabilidad Alta Gobernanza

> **PRD de referencia:** `docs/prd/04_trazabilidad_alta_gobernanza_prd.md`
> **Fecha:** 2026-06-11
> **Gobernanza:** Alta

## 1. Patrón Arquitectónico

**Decisión:** Monolito modular (mantener existente).

**Justificación:** El sistema ya está desplegado como monolito modular (Vue 3 + FastAPI + PostgreSQL en Docker Compose). La extensión de trazabilidad agrega un módulo `audit` sin cambiar la arquitectura base. Migrar a microservicios para una feature de auditoría sería sobre-ingeniería (YAGNI).

## 2. Componentes del Sistema

| Capa | Responsabilidad | Existente | Nuevo (Iteración 4) |
|------|----------------|-----------|---------------------|
| **Presentación** | Vue 3 + Vite + TailwindCSS | Vistas: pacientes, médicos, citas | Vista de auditoría (`/audit`) — solo admin |
| **Aplicación** | Lógica de negocio | `patient_service`, `doctor_appointment_service`, `user_service` | `audit_service` — consulta historial, borrado de logs |
| **Dominio** | Entidades y reglas | `Patient`, `Practitioner`, `Appointment` + `SoftDeleteMixin` | `AuditLog`: entity_type, entity_id, field_name, old_value, new_value, operation, changed_by, changed_at |
| **Infraestructura** | Persistencia y eventos | PostgreSQL + SQLAlchemy 2.0 + `events.py` (soft-delete) | Extender `events.py` con listeners `after_insert`, `after_update`, `after_delete` que capturan cambios por campo |

## 3. Comunicación

- **Frontend ↔ Backend:** REST API con JWT (existente, sin cambios).
- **Auditoría:** El backend registra automáticamente cambios en `audit_logs` vía SQLAlchemy event listeners. El frontend solo consulta el historial vía `GET /audit`. No hay escritura manual de auditoría desde el frontend.

## 4. Estructura de Directorios

**Decisión:** Mantener organización por tipo técnico (estructura actual).

```
src/
├── backend/
│   ├── api/
│   │   └── audit.py              ← GET /audit, DELETE /audit (solo admin)
│   ├── services/
│   │   └── audit_service.py      ← consulta historial, borrado con "delete"
│   ├── schemas/
│   │   └── audit.py              ← AuditLogRead, AuditLogDelete
│   └── security/
│       └── dependencies.py       ← extender con scope "audit:read", "audit:delete"
├── database/
│   ├── models.py                 ← agregar modelo AuditLog
│   ├── events.py                 ← extender: listeners after_insert/update/delete
│   └── repository.py             ← extender con AuditRepository (si es necesario)
└── frontend/
    └── src/components/
        └── AuditView.vue         ← vista de auditoría (solo admin)
```

## 5. Stack Tecnológico

Sin cambios respecto a la iteración 3:

| Componente | Tecnología |
|-----------|-----------|
| Frontend | Vue 3 + Vite + Tailwind CSS |
| Backend | FastAPI + Pydantic 2.x |
| Base de datos | PostgreSQL |
| ORM | SQLAlchemy 2.0 (async) |
| Auth | OAuth2 + JWT + `SecurityScopes` (RBAC) |
| Infraestructura | Docker + Docker Compose (3 servicios: db, api, frontend) |
| Testing | Pytest con TDD estricto |

## 6. Estrategia de Manejo de Errores

**Decisión:** Fail Fast.

**Regla:** Si el registro de auditoría falla (ej: error de BD al insertar en `audit_logs`), la operación CRUD original también falla. El dato no se persiste sin trazabilidad.

**Implementación:** Los listeners de SQLAlchemy se ejecutan en la misma transacción que la operación CRUD. Si el listener lanza excepción, el `COMMIT` falla y se hace `ROLLBACK` completo.

**Campos sensibles:** `password_hash`, `secret_token` y similares se registran como `[REDACTED]` en `audit_logs`.

## 7. Seguridad — Gobernanza Alta

| Requisito | Implementación |
|-----------|---------------|
| Solo admin consulta auditoría | `GET /audit` protegido con `SecurityScopes("audit:read")` — solo rol `admin` |
| Solo admin borra logs | `DELETE /audit` protegido con `SecurityScopes("audit:delete")` — requiere body `{"confirm": "delete"}` |
| Trazabilidad automática | Listeners SQLAlchemy en `after_insert`, `after_update`, `after_delete` — sin endpoints públicos de escritura |
| Registro de actor | `changed_by` se obtiene del `request.state.user` (JWT) — propagado al listener vía contexto |
| Campos sensibles | `password_hash`, tokens, secrets → almacenados como `[REDACTED]` |
| Soft-delete | Mantenido (`SoftDeleteMixin`). DELETE genera registro con `operation = "DELETE"`, `old_value` = snapshot de la fila eliminada |

## 8. Modelo de Datos — `audit_logs`

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,      -- 'patient', 'practitioner', 'appointment'
    entity_id UUID NOT NULL,               -- ID del registro modificado
    field_name VARCHAR(100) NOT NULL,      -- nombre del campo modificado
    old_value TEXT,                        -- valor anterior (NULL en CREATE)
    new_value TEXT,                        -- valor nuevo (NULL en DELETE)
    operation VARCHAR(10) NOT NULL,        -- 'CREATE', 'UPDATE', 'DELETE'
    changed_by VARCHAR(100) NOT NULL,      -- username o ID del actor
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_changed_by ON audit_logs(changed_by);
CREATE INDEX idx_audit_changed_at ON audit_logs(changed_at DESC);
```

## 9. Diagrama de Flujo — Registro de Auditoría

```
Usuario autenticado
       │
       ▼
PATCH /api/v1/patients/{id}  ──► FastAPI Router
       │                            │
       │                      (verify JWT + scope)
       │                            │
       ▼                            ▼
patient_service.update()  ──►  SQLAlchemy Session
       │                            │
       │                      (flush - detecta cambios)
       │                            │
       ▼                            ▼
session.commit()  ──────────►  after_update listener (events.py)
                                     │
                               Itera columnas modificadas
                                     │
                               INSERT INTO audit_logs
                               (entity_type, entity_id,
                                field_name, old_value,
                                new_value, operation='UPDATE',
                                changed_by, changed_at)
                                     │
                               Si falla → ROLLBACK completo
                               Si OK → COMMIT
```
