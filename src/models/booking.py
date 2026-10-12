from __future__ import annotations

import enum
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from models.cafe import Cafe
    from models.table import CafeTable
    from models.time_slot import TimeSlot
    from models.user import User

from core.base_model import Base
from core.constants import BOOKING_NOTE_MAX_LEN


class BookingStatus(str, enum.Enum):
    """Статусы жизненного цикла бронирования."""

    BOOKING = 'BOOKING'
    CANCELED = 'CANCELED'
    ACTIVE = 'ACTIVE'
    COMPLETED = 'COMPLETED'


class Booking(Base):
    """Бронирование пользователя в кафе на дату и один или несколько слотов."""

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
    )
    cafe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('cafes.id', ondelete='RESTRICT'),
        nullable=False,
    )
    guest_number: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str] = mapped_column(
        String(BOOKING_NOTE_MAX_LEN),
        nullable=False,
        default='',
        server_default='',
    )
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus),
        nullable=False,
        default=BookingStatus.BOOKING,
        server_default=BookingStatus.BOOKING.value,
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        CheckConstraint(
            'guest_number > 0',
            name='ck_bookings_guest_number_positive',
        ),
    )

    user: Mapped['User'] = relationship(back_populates='bookings')
    cafe: Mapped['Cafe'] = relationship(back_populates='bookings')
    tables_slots: Mapped[list['BookingTableSlot']] = relationship(
        cascade='all, delete-orphan',
    )


class BookingTableSlot(Base):
    """Связь бронирования с конкретным столиком и временным слотом."""

    __tablename__ = 'booking_table_slots'

    booking_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('bookings.id', ondelete='CASCADE'),
        nullable=False,
    )
    booking_date: Mapped[date] = mapped_column(Date, nullable=False)
    table_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('tables.id', ondelete='RESTRICT'),
        nullable=False,
    )
    slot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('time_slots.id', ondelete='RESTRICT'),
        nullable=False,
    )

    __table_args__ = (
        Index(
            'ix_unique_booking_table_slot_date',
            'table_id',
            'slot_id',
            'booking_date',
            unique=True,
            postgresql_where=Column('is_active'),
        ),
    )

    table: Mapped['CafeTable'] = relationship(back_populates='booking_slots')
    slot: Mapped['TimeSlot'] = relationship(back_populates='booking_slots')
