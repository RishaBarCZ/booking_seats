from datetime import time
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud.base import CRUDBase
from models.time_slot import TimeSlot


class CRUDTimeSlot(CRUDBase[TimeSlot]):
    """CRUD операции для модели TimeSlot."""

    async def get_time_slots(
        self,
        session: AsyncSession,
        cafe_id: int,
        show_active: Optional[bool] = None,
    ) -> List[TimeSlot]:
        """Получает список временных слотов в кафе с фильтрацией по активности."""
        query = select(self.model).where(self.model.cafe_id == cafe_id)
        query = query.options(selectinload(self.model.cafe))

        if show_active is not None:
            query = query.where(self.model.is_active.is_(show_active))

        result = await session.execute(query)
        return result.scalars().all()

    async def get_time_slot_by_id(
        self,
        session: AsyncSession,
        slot_id: int,
        cafe_id: int,
        show_active: Optional[bool] = None,
    ) -> Optional[TimeSlot]:
        """Получает один временной слот по ID."""
        query = (
            select(self.model)
            .where(
                self.model.id == slot_id,
                self.model.cafe_id == cafe_id,
            )
            .options(selectinload(self.model.cafe))
        )
        if show_active is not None:
            query = query.where(self.model.is_active.is_(show_active))

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def create_time_slot(
        self,
        session: AsyncSession,
        data: dict,
    ) -> TimeSlot:
        """Создает временной слот в кафе."""
        time_slot = await self.create(session, data)
        await session.refresh(time_slot, attribute_names=['cafe'])
        return time_slot

    async def update_time_slot(
        self,
        session: AsyncSession,
        slot_id: int,
        data: dict,
    ) -> Optional[TimeSlot]:
        """Обновляет временной слот."""
        time_slot = await self.get_by_id(session, slot_id)
        if not time_slot:
            return None
        time_slot = await self.update(session, time_slot, data)
        if time_slot:
            await session.refresh(time_slot, attribute_names=['cafe'])
        return time_slot

    async def check_overlap(
        self,
        session: AsyncSession,
        cafe_id: int,
        start_time: time,
        end_time: time,
        exclude_slot_id: Optional[int] = None,
    ) -> bool:
        """Проверяет, пересекается ли временной слот с существующими."""
        query = select(self.model).where(
            self.model.cafe_id == cafe_id,
            self.model.is_active.is_(True),
            self.model.start_time < end_time,
            self.model.end_time > start_time,
        )

        if exclude_slot_id is not None:
            query = query.where(self.model.id != exclude_slot_id)

        result = await session.execute(query)
        return result.first() is not None


time_slot_crud = CRUDTimeSlot(TimeSlot)
