from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.time_slot import time_slot_crud
from models.user import User
from schemas.time_slot import TimeSlotCreate, TimeSlotInfo, TimeSlotUpdate
from services.cafes import get_cafe_or_404, get_show_active_value
from services.time_slots import get_time_slot_or_404, validate_no_overlap

from core.db import get_session
from core.security import get_current_manager, get_current_user

router = APIRouter(prefix='/cafes/{cafe_id}/time_slots', tags=['Временные слоты'])


@router.get('', response_model=list[TimeSlotInfo], status_code=status.HTTP_200_OK)
async def get_cafe_time_slots(
    cafe_id: int,
    show_active: bool = Query(True, description='Показать активные временные слоты'),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[TimeSlotInfo]:
    """Получает список временных слотов в кафе."""
    show_active_value = get_show_active_value(current_user, show_active)
    await get_cafe_or_404(cafe_id, db, show_active=None)
    return await time_slot_crud.get_time_slots(db, cafe_id, show_active_value)


@router.post(
    '',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_manager)],
)
async def create_time_slot(
    cafe_id: int,
    time_slot_data: TimeSlotCreate,
    db: AsyncSession = Depends(get_session),
) -> TimeSlotInfo:
    """Создает новый временной слот в кафе."""
    await get_cafe_or_404(cafe_id, db, show_active=None)
    await validate_no_overlap(
        db,
        cafe_id,
        time_slot_data.start_time,
        time_slot_data.end_time,
    )
    time_slot_dict = time_slot_data.model_dump()
    time_slot_dict['cafe_id'] = cafe_id

    return await time_slot_crud.create_time_slot(db, time_slot_dict)


@router.get('/{slot_id}', response_model=TimeSlotInfo, status_code=status.HTTP_200_OK)
async def get_time_slot_by_id(
    cafe_id: int,
    slot_id: int,
    show_active: bool = Query(True, description='Показать активные слоты'),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> TimeSlotInfo:
    """Получает информацию о временном слоте по ID."""
    show_active_value = get_show_active_value(current_user, show_active)
    await get_cafe_or_404(cafe_id, db, show_active=None)

    return await get_time_slot_or_404(
        db,
        slot_id,
        cafe_id,
        show_active=show_active_value,
    )


@router.patch(
    '/{slot_id}',
    response_model=TimeSlotInfo,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_manager)],
)
async def update_time_slot(
    cafe_id: int,
    slot_id: int,
    time_slot_data: TimeSlotUpdate,
    db: AsyncSession = Depends(get_session),
) -> TimeSlotInfo:
    """Обновляет информацию о временном слоте."""
    await get_cafe_or_404(cafe_id, db, show_active=None)
    time_slot = await get_time_slot_or_404(db, slot_id, cafe_id, show_active=None)
    update_dict = time_slot_data.model_dump(exclude_unset=True)
    if 'start_time' in update_dict or 'end_time' in update_dict:
        new_start = update_dict.get('start_time', time_slot.start_time)
        new_end = update_dict.get('end_time', time_slot.end_time)
        await validate_no_overlap(
            db,
            cafe_id,
            new_start,
            new_end,
            exclude_slot_id=slot_id,
        )

    return await time_slot_crud.update_time_slot(db, slot_id, update_dict)
