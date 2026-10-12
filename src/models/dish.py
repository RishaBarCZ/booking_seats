from __future__ import annotations

import uuid

from sqlalchemy import UUID, CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.associations import cafe_dishes

from core.base_model import Base
from core.constants import DISH_DESCRIPTION_MAX_LEN, DISH_NAME_MAX_LEN, DISH_PRICE_PRECISION, DISH_PRICE_SCALE


class Dish(Base):
    """Пункт меню, предлагаемый одним или несколькими кафе."""

    __tablename__ = 'dishes'
    __table_args__ = (CheckConstraint('price >= 0', name='ck_dish_price_non_negative'),)

    name: Mapped[str] = mapped_column(String(DISH_NAME_MAX_LEN), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(DISH_DESCRIPTION_MAX_LEN), nullable=True)
    photo_id: Mapped[uuid.UUID | None] = mapped_column(UUID, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(DISH_PRICE_PRECISION, DISH_PRICE_SCALE), nullable=False)

    cafes: Mapped[list['Cafe']] = relationship(
        secondary=cafe_dishes,
        back_populates='dishes',
    )
