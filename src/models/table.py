from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_model import Base
from core.constants import TABLE_DESCRIPTION_MAX_LEN

if TYPE_CHECKING:
    from models.booking import BookingTableSlot
    from models.cafe import Cafe


class CafeTable(Base):
    """Физический столик внутри кафе."""

    __tablename__ = 'tables'
    __table_args__ = (CheckConstraint('seat_number > 0', name='ck_table_seat_number_positive'),)

    cafe_id: Mapped[int] = mapped_column(Integer, ForeignKey('cafes.id', ondelete='RESTRICT'), nullable=False)
    description: Mapped[str | None] = mapped_column(String(TABLE_DESCRIPTION_MAX_LEN), nullable=True)
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)

    cafe: Mapped['Cafe'] = relationship(back_populates='tables')
    booking_slots: Mapped[list['BookingTableSlot']] = relationship(back_populates='table')
