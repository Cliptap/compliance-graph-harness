from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import AuditLog


async def query_logs(
    session: AsyncSession,
    entity_type: str | None = None,
    entity_id: str | None = None,
    changed_by: str | None = None,
    operation: str | None = None,
    date_from=None,
    date_to=None,
    page: int = 1,
    limit: int = 50,
):
    stmt = select(AuditLog)
    count_stmt = select(func.count(AuditLog.id))

    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
        count_stmt = count_stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
        count_stmt = count_stmt.where(AuditLog.entity_id == entity_id)
    if changed_by:
        stmt = stmt.where(AuditLog.changed_by.ilike(f"%{changed_by}%"))
        count_stmt = count_stmt.where(AuditLog.changed_by.ilike(f"%{changed_by}%"))
    if operation:
        stmt = stmt.where(AuditLog.operation == operation)
        count_stmt = count_stmt.where(AuditLog.operation == operation)
    if date_from:
        stmt = stmt.where(AuditLog.changed_at >= date_from)
        count_stmt = count_stmt.where(AuditLog.changed_at >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.changed_at <= date_to)
        count_stmt = count_stmt.where(AuditLog.changed_at <= date_to)

    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    stmt = stmt.order_by(AuditLog.changed_at.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    rows = result.scalars().all()

    pages = max(1, (total + limit - 1) // limit)
    return list(rows), total, pages


async def delete_all_logs(session: AsyncSession) -> int:
    result = await session.execute(delete(AuditLog))
    await session.commit()
    return result.rowcount
