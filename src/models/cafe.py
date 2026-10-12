from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UUID, CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.action import Action
from models.associations import cafe_actions, cafe_dishes
from models.dish import Dish
from models.table import CafeTable
from models.time_slot import TimeSlot
from models.user import User

from core.base_model import Base
from core.constants import (
    CAFE_ADDRESS_MAX_LEN,
    CAFE_DESCRIPTION_MAX_LEN,
    CAFE_NAME_MAX_LEN,
    CAFE_PHONE_MAX_LEN,
)

if TYPE_CHECKING:
    from models.booking import Booking
    from models.table import CafeTable


class Cafe(Base):
    """Кафе со столиками, временными слотами, блюдами и акциями."""

    __table_args__ = (
        UniqueConstraint('name', 'address', name='uq_cafe_name_address'),
        CheckConstraint(r"phone ~ '^\+?[0-9][0-9 \-\(\)]{5,}$'", name='ck_cafe_phone_format'),
    )

    name: Mapped[str] = mapped_column(String(CAFE_NAME_MAX_LEN), nullable=False)
    address: Mapped[str] = mapped_column(String(CAFE_ADDRESS_MAX_LEN), nullable=False)
    phone: Mapped[str] = mapped_column(String(CAFE_PHONE_MAX_LEN), nullable=False)
    description: Mapped[str | None] = mapped_column(String(CAFE_DESCRIPTION_MAX_LEN), nullable=True)
    photo_id: Mapped[uuid.UUID | None] = mapped_column(UUID, nullable=True)

    managers: Mapped[list['User']] = relationship()
    tables: Mapped[list['CafeTable']] = relationship(back_populates='cafe')
    time_slots: Mapped[list[TimeSlot]] = relationship()
    dishes: Mapped[list[Dish]] = relationship(
        secondary=cafe_dishes,
        back_populates='cafes',
    )
    actions: Mapped[list[Action]] = relationship(
        secondary=cafe_actions,
        back_populates='cafes',
    )
    bookings: Mapped[list['Booking']] = relationship(back_populates='cafe')
