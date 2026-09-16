from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Security
from fastapi.security import SecurityScopes
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.security.dependencies import get_current_user, TokenData
from src.backend.schemas import AuditLogRead, AuditLogDelete
from src.backend.services.audit_service import query_logs, delete_all_logs
from src.database.database import get_db

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("", response_model=dict)
async def list_audit(
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    changed_by: str | None = Query(None),
    operation: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: TokenData = Security(get_current_user, scopes=["audit:read"]),
    session: AsyncSession = Depends(get_db),
):
    rows, total, pages = await query_logs(
        session,
        entity_type=entity_type,
        entity_id=entity_id,
        changed_by=changed_by,
        operation=operation,
        date_from=date_from,
        date_to=date_to,
        page=page,
        limit=limit,
    )
    return {
        "data": [AuditLogRead.model_validate(r).model_dump(mode="json") for r in rows],
        "meta": {"page": page, "limit": limit, "total": total, "pages": pages},
    }


@router.delete("", response_model=dict)
async def delete_audit(
    body: AuditLogDelete,
    current_user: TokenData = Security(get_current_user, scopes=["audit:delete"]),
    session: AsyncSession = Depends(get_db),
):
    if body.confirm != "delete":
        raise HTTPException(status_code=400, detail="Debe enviar confirm: 'delete' para eliminar los logs")
    count = await delete_all_logs(session)
    return {"message": "Logs eliminados correctamente", "deleted_count": count}
