from __future__ import annotations

import uuid

from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.associations import cafe_actions

from core.base_model import Base
from core.constants import ACTION_DESCRIPTION_MAX_LEN


class Action(Base):
    """Акция, предлагаемая одним или несколькими кафе."""

    description: Mapped[str] = mapped_column(String(ACTION_DESCRIPTION_MAX_LEN), nullable=False, unique=True)
    photo_id: Mapped[uuid.UUID | None] = mapped_column(UUID, nullable=True)

    cafes: Mapped[list['Cafe']] = relationship(
        secondary=cafe_actions,
        back_populates='actions',
    )
