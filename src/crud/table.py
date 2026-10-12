from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud.base import CRUDBase
from models.table import CafeTable


class CRUDTable(CRUDBase[CafeTable]):
    """CRUD операции для модели Table с контролем доступа по ролям."""

    async def get_tables(
        self,
        session: AsyncSession,
        cafe_id: int,
        show_active: Optional[bool] = None,
    ) -> list[CafeTable]:
        """Получает список столов в кафе в зависимости от роли пользователя."""
        query = select(self.model).where(self.model.cafe_id == cafe_id)
        query = query.options(selectinload(self.model.cafe))
        if show_active is not None:
            query = query.where(self.model.is_active.is_(show_active))

        result = await session.execute(query)
        return result.scalars().all()

    async def get_table_by_id(
        self,
        session: AsyncSession,
        table_id: int,
        cafe_id: int,
        show_active: Optional[bool] = None,
    ) -> Optional[CafeTable]:
        """Получает один стол по ID."""
        query = (
            select(self.model)
            .where(
                self.model.id == table_id,
                self.model.cafe_id == cafe_id,
            )
            .options(selectinload(self.model.cafe))
        )

        if show_active is not None:
            query = query.where(self.model.is_active.is_(show_active))

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create_table(
        self,
        session: AsyncSession,
        data: dict,
    ) -> CafeTable:
        """Создает стол в кафе."""
        table = await self.create(session, data)
        await session.refresh(table, attribute_names=['cafe'])
        return table

    async def update_table(
        self,
        session: AsyncSession,
        table_id: int,
        data: dict,
    ) -> Optional[CafeTable]:
        """Обновляет стол."""
        table = await self.get_by_id(session, table_id)
        if not table:
            return None
        table = await self.update(session, table, data)
        if table:
            await session.refresh(table, attribute_names=['cafe'])
        return table


table_crud = CRUDTable(CafeTable)
