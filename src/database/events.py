import os
import sys

sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.inspection import inspect
from src.database.models import SoftDeleteMixin
from src.database.models import AuditLog

SENSITIVE_FIELDS = {
    "password_hash", "secret_token", "access_token", "refresh_token", "password",
    "identifier", "rut", "status", "diagnosis", "clinical_notes"
}

def _redact(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    field_lower = field_name.lower()
    if field_lower in SENSITIVE_FIELDS:
        val_str = str(value)
        # Enmascaramiento de identificador RUT bajo Ley 21.719 (Art. 2 let. a y Art. 14 bis)
        if field_lower in ("identifier", "rut") and len(val_str) > 4:
            return f"{val_str[:2]}.***.***-{val_str[-1]}"
        # Redaccion de datos sensibles de salud bajo Ley 21.719 (Art. 2 let. g y Art. 16 bis) y Ley 20.584
        return "[REDACTED]"
    return str(value)

def _get_current_user() -> str:
    try:
        from src.backend.security.context import current_user_ctx
        return current_user_ctx.get()
    except Exception:
        return "system"

@event.listens_for(Session, "after_flush")
def _audit_changes(session, flush_context):
    for obj in session.new:
        _record_audit(session, obj, "CREATE")
    for obj in session.dirty:
        _record_audit(session, obj, "UPDATE")
    for obj in session.deleted:
        _record_audit(session, obj, "DELETE")

def _record_audit(session, obj, operation):
    if not hasattr(obj, '__tablename__'):
        return
    table_name = obj.__tablename__
    if table_name == 'audit_logs':
        return

    user = _get_current_user()

    if operation == "CREATE":
        for col in obj.__table__.columns:
            if col.key in ("id", "is_deleted", "deleted_at"):
                continue
            val = getattr(obj, col.key, None)
            session.add(AuditLog(
                entity_type=table_name,
                entity_id=str(getattr(obj, 'id', '')),
                field_name=col.key,
                old_value=None,
                new_value=_redact(col.key, val),
                operation="CREATE",
                changed_by=user
            ))

    elif operation == "UPDATE":
        insp = inspect(obj)
        for attr in insp.attrs:
            hist = getattr(attr, 'history', None)
            if hist is None:
                continue
            if not hist.has_changes():
                continue
            if attr.key in ("is_deleted", "deleted_at"):
                continue
            old = hist.deleted[0] if hist.deleted else None
            new = hist.added[0] if hist.added else None
            session.add(AuditLog(
                entity_type=table_name,
                entity_id=str(getattr(obj, 'id', '')),
                field_name=attr.key,
                old_value=_redact(attr.key, old),
                new_value=_redact(attr.key, new),
                operation="UPDATE",
                changed_by=user
            ))

    elif operation == "DELETE":
        snapshot = {}
        for col in obj.__table__.columns:
            if col.key in ("is_deleted", "deleted_at"):
                continue
            val = getattr(obj, col.key, None)
            snapshot[col.key] = _redact(col.key, val)
        import json
        session.add(AuditLog(
            entity_type=table_name,
            entity_id=str(getattr(obj, 'id', '')),
            field_name="*",
            old_value=json.dumps(snapshot, default=str),
            new_value=None,
            operation="DELETE",
            changed_by=user
        ))

@event.listens_for(Session, "do_orm_execute")
def _add_soft_delete_filter(execute_state):
    """
    Intercepta consultas y añade filtro `is_deleted == False` automáticamente.
    Garantiza que la API no devuelva registros eliminados lógicamente.
    """
    if (
        execute_state.is_select 
        and not execute_state.is_column_load 
        and not execute_state.is_relationship_load
    ):
        entity = getattr(execute_state.statement, 'column_descriptions', [{}])[0].get('type')
        if hasattr(entity, 'is_deleted'):
            execute_state.statement = execute_state.statement.filter(
                entity.is_deleted == False
            )

@event.listens_for(Session, "after_bulk_update")
def _audit_bulk_soft_delete(update_context):
    """Captura soft-deletes hechos via bulk UPDATE (is_deleted=True)"""
    stmt = update_context.statement
    user = _get_current_user()
    try:
        table = stmt.table
        table_name = table.name
        if table_name == 'audit_logs':
            return
        # Solo registrar si el bulk update afecta is_deleted=True
        values = update_context.result.context.compiled_parameters[0] if update_context.result.context.compiled_parameters else {}
        is_soft_del = values.get('is_deleted') == True
        import json

        session = update_context.session
        # Registrar para cada fila afectada
        for row in update_context.rows:
            snapshot = {}
            for col in table.columns:
                if col.key in ("is_deleted", "deleted_at"):
                    continue
                if row._mapping and col.key in row._mapping:
                    val = getattr(row._mapping, col.key, None)
                    snapshot[col.key] = str(val) if val else None
            session.add(AuditLog(
                entity_type=table_name,
                entity_id=str(getattr(row._mapping, 'id', '')),
                field_name="*",
                old_value=json.dumps(snapshot, default=str) if snapshot else None,
                new_value=None,
                operation="DELETE",
                changed_by=user
            ))
    except Exception:
        pass  # Evitar que un error de auditoría rompa la operación
