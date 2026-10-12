from __future__ import annotations

from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_model import Base
from core.constants import TIME_SLOT_DESCRIPTION_MAX_LEN

if TYPE_CHECKING:
    from models.booking import BookingTableSlot, Cafe


class TimeSlot(Base):
    """Временной слот для бронирования, определённый для кафе."""

    __tablename__ = 'time_slots'
    __table_args__ = (CheckConstraint('start_time < end_time', name='ck_time_slot_start_before_end'),)

    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey('cafes.id', ondelete='RESTRICT'), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    description: Mapped[str | None] = mapped_column(String(TIME_SLOT_DESCRIPTION_MAX_LEN), nullable=True)

    booking_slots: Mapped[list['BookingTableSlot']] = relationship(back_populates='slot')
    cafe: Mapped['Cafe'] = relationship(back_populates='time_slots')
