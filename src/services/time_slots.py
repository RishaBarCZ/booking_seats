from datetime import time
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.time_slot import time_slot_crud
from models.time_slot import TimeSlot


async def get_time_slot_or_404(
    db: AsyncSession,
    slot_id: int,
    cafe_id: int,
    show_active: Optional[bool] = None,
) -> TimeSlot:
    """Получает временной слот по ID или возвращает 404 если не найден."""
    time_slot = await time_slot_crud.get_time_slot_by_id(
        db,
        slot_id,
        cafe_id,
        show_active=show_active,
    )
    if not time_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Временной слот не найден',
        )
    return time_slot


async def validate_no_overlap(
    db: AsyncSession,
    cafe_id: int,
    start_time: time,
    end_time: time,
    exclude_slot_id: Optional[int] = None,
) -> None:
    """Проверяет отсутствие пересечения слотов."""
    if await time_slot_crud.check_overlap(
        db,
        cafe_id,
        start_time,
        end_time,
        exclude_slot_id=exclude_slot_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Временной слот пересекается с существующим',
        )
