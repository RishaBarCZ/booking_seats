"""Базовые схемы проекта.

Структура наследования по документации:

BaseSchema
├── IdShortInfoSchema
│   ├── UserShortInfo
│   ├── CafeShortInfo
│   ├── TableShortInfo
│   └── TimeSlotShortInfo
├── InfoSchema
│   ├── ActionInfo
│   ├── BookingInfo
│   ├── CafeInfo
│   ├── DishInfo
│   ├── TableInfo
│   ├── TimeSlotInfo
│   └── UserInfo
├── BookingTableSlotShortInfo
└── MediaInfo
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Базовая схема с поддержкой ORM-объектов SQLAlchemy."""

    model_config = ConfigDict(from_attributes=True, extra='forbid')


class IdShortInfoSchema(BaseSchema):
    """Базовая схема для кратких представлений с полем id."""

    id: int


class InfoSchema(BaseSchema):
    """Базовая схема для полных представлений с аудит-полями."""

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


__all__ = ['BaseSchema', 'IdShortInfoSchema', 'InfoSchema']
