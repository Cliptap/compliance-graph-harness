from __future__ import annotations
from typing import TypeVar, Generic, Type, Optional, Sequence, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone

T = TypeVar("T", bound=Any)

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: str) -> Optional[T]:
        stmt = select(self.model).where(
            getattr(self.model, "id") == id,
            getattr(self.model, "is_deleted") == False
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self) -> Sequence[T]:
        if hasattr(self.model, "is_deleted"):
            stmt = select(self.model).where(self.model.is_deleted == False)
        else:
            stmt = select(self.model)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj_in: dict) -> T:
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        await self.session.commit()
        await self.session.refresh(db_obj)
        return db_obj

    async def soft_delete(self, id: str) -> bool:
        stmt = (
            update(self.model)
            .where(getattr(self.model, "id") == id)
            .values(is_deleted=True, deleted_at=datetime.now(timezone.utc))
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return getattr(result, "rowcount", 0) > 0
