from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies.booking import (
    BookingAccessFiltersDep,
    BookingAccessScopeDep,
    CurrentUserDep,
)
from crud.booking import booking_crud
from schemas.booking import BookingCreate, BookingInfo, BookingUpdate
from schemas.error import CustomError
from tasks.reminders import schedule_booking_reminder

from core.db import get_session

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_session)]
IdDep = Annotated[int, Path(gt=0)]


@router.get('', response_model=list[BookingInfo])
async def get_all_bookings(
    access_filters: BookingAccessFiltersDep,
    session: SessionDep,
) -> list[BookingInfo]:
    """Получить список бронирований с учётом прав доступа."""
    bookings = await booking_crud.get_all_with_relations(
        session,
        show_active=access_filters.show_active,
        cafe_id=access_filters.cafe_id,
        user_id=access_filters.user_id,
    )
    return [BookingInfo.model_validate(booking) for booking in bookings]


@router.post(
    '',
    response_model=BookingInfo,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    booking_in: BookingCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
    scope: BookingAccessScopeDep,
) -> BookingInfo:
    """Создать новое бронирование."""
    booking = await booking_crud.create(
        session,
        user_id=current_user.id,
        data=booking_in,
    )
    schedule_booking_reminder(booking)

    return BookingInfo.model_validate(booking)


@router.get(
    '/{booking_id}',
    response_model=BookingInfo,
    status_code=status.HTTP_200_OK,
)
async def get_booking_by_id(
    booking_id: IdDep,
    session: SessionDep,
    scope: BookingAccessScopeDep,
) -> BookingInfo:
    """Получить бронирование по идентификатору."""
    booking = await booking_crud.get_with_relations_by_scope(session, obj_id=booking_id, scope=scope)
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Бронирование не найдено.',
        )
    return BookingInfo.model_validate(booking)


@router.patch('/{booking_id}', response_model=BookingInfo)
async def update_booking(
    booking_id: IdDep,
    booking_in: BookingUpdate,
    session: SessionDep,
    scope: BookingAccessScopeDep,
) -> BookingInfo:
    """Обновить бронирование по идентификатору."""
    updated_booking = await booking_crud.update(
        session,
        obj_id=booking_id,
        data=booking_in,
        scope=scope,
    )
    if updated_booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=CustomError(message='Бронирование не найдено.', code=404).model_dump(),
        )

    schedule_booking_reminder(updated_booking)

    return BookingInfo.model_validate(updated_booking)


@router.delete('/{booking_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    booking_id: IdDep,
    session: SessionDep,
    scope: BookingAccessScopeDep,
) -> None:
    """Удалить бронирование по идентификатору."""
    deleted_booking = await booking_crud.remove(
        session,
        obj_id=booking_id,
        scope=scope,
    )

    if deleted_booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Бронирование не найдено.',
        )
