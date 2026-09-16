# Implementación Backend — Iteración 4: Trazabilidad Alta Gobernanza

> **PRD:** `docs/prd/04_trazabilidad_alta_gobernanza_prd.md`
> **Arquitectura:** `docs/arquitectura/04_trazabilidad_alta_gobernanza.md`
> **Fecha:** 2026-06-11

## 1. Lenguaje y Framework

**FastAPI + Python 3.12** (existente). Sin cambios.

## 2. ORM / Capa de Datos

**SQLAlchemy 2.0 async** (existente). Se extiende con:

- Nuevo modelo `AuditLog` en `src/database/models.py`
- Extensión de `src/database/events.py` con listeners `after_insert`, `after_update`, `after_delete`

## 3. Estructura — Archivos a Crear/Modificar

```
src/
├── backend/
│   ├── api/
│   │   └── audit.py              ← NUEVO: GET /audit, DELETE /audit
│   ├── services/
│   │   └── audit_service.py      ← NUEVO: consulta y borrado de logs
│   ├── schemas/
│   │   └── audit.py              ← NUEVO: AuditLogRead, AuditLogDelete, AuditLogQuery
│   └── security/
│       ├── auth.py               ← SIN CAMBIOS
│       └── dependencies.py       ← MODIFICAR: agregar scopes audit:read, audit:delete
├── database/
│   ├── models.py                 ← MODIFICAR: agregar modelo AuditLog
│   ├── events.py                 ← MODIFICAR: extender listeners para capturar cambios
│   └── repository.py             ← SIN CAMBIOS (AuditLog usa queries directas)
```

## 4. Manejo de Configuración

Sin cambios. Variables de entorno en `.env` (DATABASE_URL, SECRET_KEY, JWT_SECRET, etc.).

## 5. Validaciones

**Gobernanza ALTA.** Validaciones existentes se mantienen. Nuevas:

- `DELETE /audit`: validar que body contiene exactamente `{"confirm": "delete"}`
- `GET /audit`: validar parámetros de query (entity_type en lista permitida, page/limit positivos)
- Registro de auditoría: campos sensibles (`password_hash`, `secret_token`) → `[REDACTED]`

## 6. Logging

JSON estructurado (existente con `structlog` o `logging`). Sin cambios. Los logs de aplicación no deben contener valores de `audit_logs` (eso va a la BD).

## 7. Implementación — Event Listeners (pseudocódigo)

```python
# src/database/events.py — extensión

@event.listens_for(Session, "after_insert")
def audit_insert(mapper, connection, target):
    for col in target.__table__.columns:
        if col.name in ("created_at", "updated_at", "deleted_at"):
            continue
        val = getattr(target, col.name)
        if _is_sensitive(col.name):
            val = "[REDACTED]"
        connection.execute(
            audit_logs.insert().values(
                entity_type=target.__tablename__,
                entity_id=target.id,
                field_name=col.name,
                old_value=None,
                new_value=str(val) if val else None,
                operation="CREATE",
                changed_by=_get_current_user(),
                changed_at=func.now()
            )
        )

@event.listens_for(Session, "after_update")
def audit_update(mapper, connection, target):
    history = inspect(target).attrs
    for attr in history:
        if not attr.history.has_changes():
            continue
        if attr.key in ("updated_at",):
            continue
        old = _redact_if_sensitive(attr.key, attr.history.deleted[0])
        new = _redact_if_sensitive(attr.key, attr.history.added[0])
        connection.execute(
            audit_logs.insert().values(
                entity_type=target.__tablename__,
                entity_id=target.id,
                field_name=attr.key,
                old_value=str(old) if old else None,
                new_value=str(new) if new else None,
                operation="UPDATE",
                changed_by=_get_current_user(),
                changed_at=func.now()
            )
        )

@event.listens_for(Session, "after_delete")
def audit_delete(mapper, connection, target):
    snapshot = {c.name: str(getattr(target, c.name))
                for c in target.__table__.columns
                if c.name not in ("created_at", "updated_at")}
    connection.execute(
        audit_logs.insert().values(
            entity_type=target.__tablename__,
            entity_id=target.id,
            field_name="*",
            old_value=json.dumps(snapshot),
            new_value=None,
            operation="DELETE",
            changed_by=_get_current_user(),
            changed_at=func.now()
        )
    )
```

## 8. Propagación del Usuario Actual al Listener

Los listeners de SQLAlchemy no tienen acceso al request HTTP. Se requiere un mecanismo para propagar el usuario:

**Opción elegida:** `ContextVar` (nativo de Python, thread-safe para async).

```python
# src/backend/security/context.py
from contextvars import ContextVar

current_user: ContextVar[str] = ContextVar("current_user", default="system")
```

En `dependencies.py`, setear el contexto al validar el JWT:

```python
current_user.set(token_data.username)
```

En `events.py`, leer el contexto:

```python
def _get_current_user():
    return current_user.get()
```

## 9. Endpoint de Auditoría (pseudocódigo)

```python
# src/backend/api/audit.py

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

@router.get("/")
async def list_audit(
    entity_type: str | None = Query(None),
    entity_id: UUID | None = Query(None),
    changed_by: str | None = Query(None),
    operation: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Security(get_current_user, scopes=["audit:read"])
):
    return audit_service.query_logs(...)

@router.delete("/")
async def delete_audit(
    body: AuditLogDelete,
    current_user: User = Security(get_current_user, scopes=["audit:delete"])
):
    if body.confirm != "delete":
        raise HTTPException(400, "Debe confirmar con 'delete'")
    count = audit_service.delete_logs()
    return {"message": "Logs eliminados", "deleted_count": count}
```
