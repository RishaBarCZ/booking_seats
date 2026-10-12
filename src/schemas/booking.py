from __future__ import annotations

from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from models.booking import BookingStatus
from schemas import BaseSchema, CafeShortInfo, InfoSchema, TableShortInfo, TimeSlotShortInfo, UserShortInfo

PositiveId = Annotated[int, Field(gt=0)]
PositiveGuestNumber = Annotated[int, Field(gt=0)]
RequiredBookingTableSlots = Annotated[
    list['BookingTableSlot'],
    Field(
        min_length=1,
        description='Пары table_id, дата и slot_id',
    ),
]
OptionalBookingTableSlots = Annotated[
    list['BookingTableSlot'] | None,
    Field(min_length=1),
]


class BookingTableSlotsValidationMixin:
    """Общие проверки поля tables_slots."""

    @staticmethod
    def _validate_tables_slots(
        tables_slots: RequiredBookingTableSlots | None,
        booking_date: date | None,
    ) -> None:
        """Проверить уникальность пар столиков и слотов на дату."""
        if tables_slots is None:
            return

        pairs = {(item.table_id, booking_date, item.slot_id) for item in tables_slots}
        if len(pairs) != len(tables_slots):
            raise ValueError(
                'Повторяющиеся пары table_id, date и slot_id недопустимы.',
            )

        slot_ids = {item.slot_id for item in tables_slots}
        if len(slot_ids) != len(tables_slots):
            raise ValueError(
                'Одно бронирование не может содержать разные столы для одного и того же slot_id.',
            )

    @staticmethod
    def _validate_booking_date_not_past(booking_date: date | None) -> None:
        """Проверить, что booking_date не раньше сегодняшней даты.

        Используется в схемах создания и обновления бронирования.
        """
        if booking_date is None:
            return
        if booking_date < date.today():
            raise ValueError('Дата бронирования не может быть раньше сегодняшней.')


class NotNullIfProvidedMixin:
    """Проверка, что переданные поля не равны null."""

    @staticmethod
    def _validate_not_null_if_provided(
        instance: BaseModel,
        field_names: set[str],
    ) -> None:
        """Проверить, что переданные поля не равны null."""
        for field_name in field_names:
            if field_name in instance.model_fields_set and getattr(instance, field_name) is None:
                raise ValueError(f'Поле {field_name} не может быть null.')


class BookingTableSlot(BaseSchema):
    """Пара столика и временного слота на дату."""

    table_id: PositiveId
    slot_id: PositiveId


class BookingTableSlotShortInfo(BaseSchema):
    """Краткая информация о столике и временном слоте бронирования."""

    table: TableShortInfo | None = None
    slot: TimeSlotShortInfo | None = None


class BookingCreate(BaseSchema, BookingTableSlotsValidationMixin):
    """Данные для создания бронирования."""

    cafe_id: PositiveId
    tables_slots: RequiredBookingTableSlots
    guest_number: PositiveGuestNumber
    note: str = ''
    booking_date: date

    @model_validator(mode='after')
    def validate_booking_create(self) -> BookingCreate:
        """Проверить данные нового бронирования."""
        self._validate_tables_slots(self.tables_slots, self.booking_date)
        self._validate_booking_date_not_past(self.booking_date)
        return self


class BookingUpdate(
    BaseSchema,
    BookingTableSlotsValidationMixin,
    NotNullIfProvidedMixin,
):
    """Данные для обновления бронирования."""

    tables_slots: OptionalBookingTableSlots = None
    guest_number: PositiveGuestNumber | None = None
    note: str | None = None
    status: BookingStatus | None = None
    booking_date: date | None = None
    is_active: bool | None = None

    @model_validator(mode='after')
    def validate_booking_update(self) -> BookingUpdate:
        """Проверить данные обновления бронирования."""
        self._validate_not_null_if_provided(
            self,
            {
                'tables_slots',
                'guest_number',
                'note',
                'status',
                'booking_date',
                'is_active',
            },
        )
        self._validate_tables_slots(self.tables_slots, self.booking_date)
        self._validate_booking_date_not_past(self.booking_date)
        return self


class BookingInfo(InfoSchema):
    """Информация о бронировании для ответа API."""

    user: UserShortInfo | None = None
    cafe: CafeShortInfo | None = None
    tables_slots: list[BookingTableSlotShortInfo] = Field(default_factory=list)
    guest_number: int | None = None
    note: str = ''
    status: BookingStatus | None = None
    booking_date: date | None = None


__all__ = [
    'BookingCreate',
    'BookingInfo',
    'BookingStatus',
    'BookingTableSlot',
    'BookingTableSlotShortInfo',
    'BookingUpdate',
]
