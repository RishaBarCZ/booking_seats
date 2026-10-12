from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.cafe import CafeShortInfo
from schemas.mixins import SeatNumberValidator


class BaseTable(BaseModel):
    """Модель для базовой схемы стола."""

    description: Optional[str] = None


class TableCreate(BaseTable):
    """Схема для создания стола."""

    seat_number: int = Field(..., gt=0)


class TableUpdate(BaseTable, SeatNumberValidator):
    """Схема для обновления стола."""

    seat_number: Optional[int] = Field(None)
    is_active: Optional[bool] = None


class TableShortInfo(BaseTable):
    """Краткая информация о столе."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    seat_number: int


class TableInfo(TableShortInfo):
    """Полная информация о столе."""

    cafe: CafeShortInfo
    is_active: bool
    created_at: datetime
    updated_at: datetime
