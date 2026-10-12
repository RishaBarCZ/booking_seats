from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict

from schemas.cafe import CafeShortInfo
from schemas.mixins import OptionalTimeSlotIntervalValidator, TimeSlotIntervalValidator


class BaseTimeSlot(BaseModel):
    """Базовая модель схемы стола."""

    description: Optional[str] = None


class TimeSlotCreate(BaseTimeSlot, TimeSlotIntervalValidator):
    """Схема для создания временного слота."""

    start_time: time
    end_time: time


class TimeSlotUpdate(BaseTimeSlot, OptionalTimeSlotIntervalValidator):
    """Схема для обновления временного слота."""

    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_active: Optional[bool] = None


class TimeSlotShortInfo(BaseModel):
    """Краткая информация о временном слоте."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    start_time: time
    end_time: time
    description: Optional[str] = None


class TimeSlotInfo(TimeSlotShortInfo):
    """Полная информация о временном слоте."""

    cafe: CafeShortInfo
    is_active: bool
    created_at: datetime
    updated_at: datetime
