from __future__ import annotations

from datetime import date
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import Select, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud.base import CRUDBase
from models.booking import Booking, BookingStatus, BookingTableSlot
from models.table import CafeTable
from models.time_slot import TimeSlot
from schemas.booking import BookingCreate, BookingUpdate, RequiredBookingTableSlots
from services.booking import BookingAccessScope

BLOCKING_BOOKING_STATUSES = (
    BookingStatus.BOOKING,
    BookingStatus.ACTIVE,
)


class CRUDBooking(CRUDBase[Booking]):
    """CRUD-операции для бронирований."""

    @staticmethod
    def _detail_stmt() -> Select[tuple[Booking]]:
        """Сформировать запрос с основными связями бронирования."""
        return select(Booking).options(
            selectinload(Booking.user),
            selectinload(Booking.cafe),
            selectinload(Booking.tables_slots).selectinload(BookingTableSlot.table),
            selectinload(Booking.tables_slots).selectinload(BookingTableSlot.slot),
        )

    @staticmethod
    def _apply_access_scope(
        stmt: Select[tuple[Booking]],
        scope: BookingAccessScope,
    ) -> Select[tuple[Booking]]:
        """Добавить к запросу ограничения доступа."""
        if scope.cafe_id is not None:
            stmt = stmt.where(Booking.cafe_id == scope.cafe_id)
        if scope.user_id is not None:
            stmt = stmt.where(Booking.user_id == scope.user_id)
        return stmt

    async def get_with_relations(
        self,
        session: AsyncSession,
        obj_id: int,
    ) -> Booking | None:
        """Получить бронирование с основными связями."""
        stmt = self._detail_stmt().where(Booking.id == obj_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_relations_by_scope(
        self,
        session: AsyncSession,
        *,
        obj_id: int,
        scope: BookingAccessScope,
    ) -> Booking | None:
        """Получить бронирование с учётом прав доступа."""
        stmt = self._apply_access_scope(self._detail_stmt(), scope).order_by(Booking.id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_relations(
        self,
        session: AsyncSession,
        *,
        show_active: bool | None = None,
        cafe_id: int | None = None,
        user_id: int | None = None,
    ) -> list[Booking]:
        """Получить список бронирований с основными связями."""
        stmt = self._detail_stmt().order_by(Booking.id)

        if show_active is not None:
            stmt = stmt.where(Booking.is_active.is_(show_active))
        if cafe_id is not None:
            stmt = stmt.where(Booking.cafe_id == cafe_id)
        if user_id is not None:
            stmt = stmt.where(Booking.user_id == user_id)

        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_tables_slots(
        self,
        session: AsyncSession,
        obj_id: int,
    ) -> Booking | None:
        """Получить бронирование вместе со связями столов и слотов."""
        result = await session.execute(
            select(Booking).options(selectinload(Booking.tables_slots)).where(Booking.id == obj_id),
        )
        return result.scalar_one_or_none()

    async def get_with_tables_slots_by_scope(
        self,
        session: AsyncSession,
        *,
        obj_id: int,
        scope: BookingAccessScope,
    ) -> Booking | None:
        """Получить бронирование со слотами с учётом прав доступа."""
        stmt = self._apply_access_scope(
            select(Booking).options(selectinload(Booking.tables_slots)).where(Booking.id == obj_id),
            scope,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        data: BookingCreate,
    ) -> Booking:
        """Создать бронирование после проверки конфликтов."""
        await self._validate_booking_data(
            session=session,
            user_id=user_id,
            cafe_id=data.cafe_id,
            booking_date=data.booking_date,
            tables_slots=data.tables_slots,
        )

        booking = Booking(
            user_id=user_id,
            cafe_id=data.cafe_id,
            guest_number=data.guest_number,
            note=data.note,
            booking_date=data.booking_date,
            status=BookingStatus.BOOKING,
            tables_slots=[
                BookingTableSlot(
                    table_id=item.table_id,
                    slot_id=item.slot_id,
                    booking_date=data.booking_date,
                )
                for item in data.tables_slots
            ],
        )
        session.add(booking)
        await session.flush()
        return await self.get_with_relations(session, booking.id)

    async def update(
        self,
        session: AsyncSession,
        *,
        obj_id: int,
        data: BookingUpdate,
        scope: BookingAccessScope,
    ) -> Booking | None:
        """Упрощённое обновление бронирования: собрать effective, валидировать, применить."""
        booking = await self.get_with_tables_slots_by_scope(session, obj_id=obj_id, scope=scope)
        if booking is None:
            return None

        payload = data.model_dump(exclude_unset=True)

        effective_cafe_id = payload.get('cafe_id', booking.cafe_id)
        if scope.cafe_id is not None and effective_cafe_id != scope.cafe_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Вы не имеете доступа к этому кафе.',
            )

        raw_tables_slots = payload.pop('tables_slots', None)
        effective_booking_date = payload.get('booking_date', booking.booking_date)
        effective_status = payload.get('status', booking.status)
        effective_is_active = payload.get('is_active', booking.is_active)

        normalized_incoming = None
        if raw_tables_slots is not None:
            normalized_incoming = self._normalize_tables_slots(raw_tables_slots)

        # Валидация до применения изменений
        tables_slots_for_validation = normalized_incoming or [
            {'table_id': s.table_id, 'slot_id': s.slot_id} for s in booking.tables_slots
        ]

        if self._should_validate_conflicts(effective_status, effective_is_active):
            await self._validate_booking_data(
                session=session,
                user_id=booking.user_id,
                cafe_id=effective_cafe_id,
                booking_date=effective_booking_date,
                tables_slots=tables_slots_for_validation,
                exclude_booking_id=booking.id,
            )

        # Применяем изменения к слотам
        if raw_tables_slots is None:
            if 'booking_date' in payload and effective_booking_date != booking.booking_date:
                booking.booking_date = effective_booking_date
                self._update_booking_slots_date(booking.tables_slots, effective_booking_date)
        else:
            normalized = normalized_incoming
            existing_pairs = {(s.table_id, s.slot_id) for s in booking.tables_slots}
            incoming_pairs = {(item['table_id'], item['slot_id']) for item in normalized}

            if existing_pairs == incoming_pairs:
                if effective_booking_date != booking.booking_date:
                    booking.booking_date = effective_booking_date
                    self._update_booking_slots_date(booking.tables_slots, effective_booking_date)
            else:
                to_add, to_remove_ids = self._compute_slot_diff(booking.tables_slots, incoming_pairs)
                await self._apply_slot_changes(
                    session,
                    booking,
                    to_add,
                    to_remove_ids,
                    effective_booking_date,
                )

        # Применяем остальные скалярные поля
        for key, value in payload.items():
            setattr(booking, key, value)

        await session.flush()
        return await self.get_with_relations(session, booking.id)

    async def remove(
        self,
        session: AsyncSession,
        *,
        obj_id: int,
        scope: BookingAccessScope,
    ) -> Booking | None:
        """Мягко удалить бронирование с учётом прав доступа."""
        booking = await self.get_with_tables_slots_by_scope(session, obj_id=obj_id, scope=scope)
        if booking is None:
            return None
        booking.is_active = False
        for table_slot in booking.tables_slots:
            table_slot.is_active = False
        await session.flush()
        await session.refresh(booking)
        return booking

    @staticmethod
    def _should_validate_conflicts(
        booking_status: BookingStatus,
        is_active: bool,
    ) -> bool:
        """Определить, нужно ли валидировать данные."""
        return is_active and booking_status in BLOCKING_BOOKING_STATUSES

    async def _validate_booking_data(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        cafe_id: int,
        booking_date: date,
        tables_slots: RequiredBookingTableSlots | Sequence[dict[str, int]],
        exclude_booking_id: int | None = None,
    ) -> None:
        """Запустить все бизнес-проверки для бронирования."""
        normalized_tables_slots = self._normalize_tables_slots(tables_slots)

        await self._validate_tables_and_slots_belong_to_cafe(
            session=session,
            cafe_id=cafe_id,
            tables_slots=normalized_tables_slots,
        )
        await self._validate_table_slot_is_free(
            session=session,
            cafe_id=cafe_id,
            booking_date=booking_date,
            tables_slots=normalized_tables_slots,
            exclude_booking_id=exclude_booking_id,
        )
        await self._validate_user_has_no_booking_for_same_slot(
            session=session,
            user_id=user_id,
            booking_date=booking_date,
            tables_slots=normalized_tables_slots,
            exclude_booking_id=exclude_booking_id,
        )

    @staticmethod
    def _normalize_tables_slots(
        tables_slots: RequiredBookingTableSlots | Sequence[dict[str, int]],
    ) -> list[dict[str, int]]:
        """Привести пары table_id/slot_id к единому словарному виду."""
        normalized_items: list[dict[str, int]] = []
        for item in tables_slots:
            if isinstance(item, dict):
                normalized_items.append(
                    {
                        'table_id': item['table_id'],
                        'slot_id': item['slot_id'],
                    },
                )
                continue
            normalized_items.append(
                {
                    'table_id': item.table_id,
                    'slot_id': item.slot_id,
                },
            )
        return normalized_items

    @staticmethod
    def _compute_slot_diff(
        existing_slots: list[BookingTableSlot],
        incoming_pairs: set[tuple[int, int]],
    ) -> tuple[set[tuple[int, int]], set[int]]:
        """Вычислить пары для добавления и id записей для удаления.

        Возвращает (to_add_pairs, to_remove_ids).
        """
        existing_pairs = {(s.table_id, s.slot_id) for s in existing_slots}
        to_add = incoming_pairs - existing_pairs

        # Найдём id существующих записей, которые нужно удалить
        to_remove_ids: set[int] = set()
        for s in existing_slots:
            if (s.table_id, s.slot_id) not in incoming_pairs:
                to_remove_ids.add(s.id)

        return to_add, to_remove_ids

    async def _apply_slot_changes(
        self,
        session: AsyncSession,
        booking: Booking,
        to_add: set[tuple[int, int]],
        to_remove_ids: set[int],
        booking_date: date,
    ) -> None:
        """Применить изменения коллекции `booking.tables_slots`.

        Удаляет объекты с id в `to_remove_ids` из коллекции и добавляет новые пары из `to_add`.
        """
        if to_remove_ids:
            # Удаляем объекты из коллекции по id
            booking.tables_slots[:] = [s for s in booking.tables_slots if s.id not in to_remove_ids]

        if to_add:
            for table_id, slot_id in to_add:
                booking.tables_slots.append(
                    BookingTableSlot(
                        table_id=table_id,
                        slot_id=slot_id,
                        booking_date=booking_date,
                    ),
                )

    @staticmethod
    def _update_booking_slots_date(
        table_slots: list[BookingTableSlot],
        booking_date: date,
    ) -> None:
        """Обновить дату бронирования у связанных слотов."""
        for item in table_slots:
            item.booking_date = booking_date

    async def _validate_tables_and_slots_belong_to_cafe(
        self,
        session: AsyncSession,
        *,
        cafe_id: int,
        tables_slots: list[dict[str, int]],
    ) -> None:
        """Проверить, что столы и слоты принадлежат указанному кафе."""
        table_ids = {item['table_id'] for item in tables_slots}
        slot_ids = {item['slot_id'] for item in tables_slots}

        valid_table_ids = set(
            (
                await session.execute(
                    select(CafeTable.id).where(
                        CafeTable.id.in_(table_ids),
                        CafeTable.cafe_id == cafe_id,
                    ),
                )
            )
            .scalars()
            .all(),
        )
        valid_slot_ids = set(
            (
                await session.execute(
                    select(TimeSlot.id).where(
                        TimeSlot.id.in_(slot_ids),
                        TimeSlot.cafe_id == cafe_id,
                    ),
                )
            )
            .scalars()
            .all(),
        )

        if valid_table_ids != table_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Столик не принадлежит указанному кафе.',
            )
        if valid_slot_ids != slot_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Временной слот не принадлежит указанному кафе.',
            )

    async def _validate_table_slot_is_free(
        self,
        session: AsyncSession,
        *,
        cafe_id: int,
        booking_date: date,
        tables_slots: list[dict[str, int]],
        exclude_booking_id: int | None = None,
    ) -> None:
        """Проверить, что стол не занят на эту дату и слот."""
        requested_pairs = [(item['table_id'], item['slot_id']) for item in tables_slots]

        stmt = (
            select(Booking.id)
            .join(BookingTableSlot, BookingTableSlot.booking_id == Booking.id)
            .where(
                Booking.cafe_id == cafe_id,
                BookingTableSlot.booking_date == booking_date,
                Booking.is_active.is_(True),
                Booking.status.in_(BLOCKING_BOOKING_STATUSES),
                tuple_(BookingTableSlot.table_id, BookingTableSlot.slot_id).in_(
                    requested_pairs,
                ),
            )
        )

        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)

        conflict_booking_id = await session.scalar(stmt.limit(1))
        if conflict_booking_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'На дату {booking_date} стол уже забронирован на выбранное время.',
            )

    async def _validate_user_has_no_booking_for_same_slot(
        self,
        session: AsyncSession,
        *,
        user_id: int,
        booking_date: date,
        tables_slots: list[dict[str, int]],
        exclude_booking_id: int | None = None,
    ) -> None:
        """Проверить, что у пользователя нет другой брони на тот же слот."""
        slot_ids = {item['slot_id'] for item in tables_slots}

        stmt = (
            select(Booking.id)
            .join(BookingTableSlot, BookingTableSlot.booking_id == Booking.id)
            .where(
                Booking.user_id == user_id,
                Booking.booking_date == booking_date,
                Booking.is_active.is_(True),
                Booking.status.in_(BLOCKING_BOOKING_STATUSES),
                BookingTableSlot.slot_id.in_(slot_ids),
            )
        )

        if exclude_booking_id is not None:
            stmt = stmt.where(Booking.id != exclude_booking_id)

        conflict_booking_id = await session.scalar(stmt.limit(1))
        if conflict_booking_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Пользователь уже забронировал стол на это время.',
            )


booking_crud = CRUDBooking(Booking)
