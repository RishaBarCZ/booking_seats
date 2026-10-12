from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud.base import CRUDBase
from models.cafe import Cafe


class CRUDCafe(CRUDBase[Cafe]):
    """CRUD операции для модели Cafe с контролем доступа по ролям."""

    async def get_cafes(
        self,
        session: AsyncSession,
        show_active: Optional[bool] = None,
    ) -> list[Cafe]:
        """Получает список кафе с фильтрацией по активности."""
        query = select(self.model).options(selectinload(self.model.managers))
        if show_active is not None:
            query = query.where(self.model.is_active.is_(show_active))

        result = await session.execute(query)
        return result.scalars().all()

    async def get_cafe_by_id(
        self,
        session: AsyncSession,
        cafe_id: int,
        show_active: Optional[bool] = None,
    ) -> Optional[Cafe]:
        """Получает одно кафе по ID."""
        query = select(self.model).where(self.model.id == cafe_id)
        query = query.options(selectinload(self.model.managers))

        if show_active is not None:
            query = query.where(self.model.is_active.is_(show_active))

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create_cafe_with_managers(
        self,
        session: AsyncSession,
        data: dict,
        managers: List,
    ) -> Cafe:
        """Создает кафе с назначенными менеджерами."""
        if not managers:
            raise ValueError('Список менеджеров не может быть пустым')
        # cafe = await self.create(session, data)
        # cafe.managers.extend(managers)
        cafe = self.model(**data)
        cafe.managers = managers
        session.add(cafe)
        await session.commit()
        # await session.flush()
        await session.refresh(cafe, attribute_names=['managers'])

        return cafe

    async def update_cafe(
        self,
        session: AsyncSession,
        cafe_id: int,
        data: dict,
    ) -> Optional[Cafe]:
        """Обновляет кафе."""
        # cafe = await self.update(session, cafe_id, data)
        cafe = await self.get_by_id(session, cafe_id)
        if not cafe:
            return None
        cafe = await self.update(session, cafe, data)
        if cafe:
            await session.refresh(cafe, attribute_names=['managers'])
        return cafe

    async def update_managers(
        self,
        session: AsyncSession,
        cafe: Cafe,
        managers: List,
    ) -> Cafe:
        """Заменяет всех менеджеров кафе новым списком."""
        cafe.managers = managers
        await session.flush()
        await session.refresh(cafe, attribute_names=['managers'])
        return cafe


cafe_crud = CRUDCafe(Cafe)
