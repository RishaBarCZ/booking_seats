from datetime import time
from typing import List, Optional

from pydantic import ValidationInfo, field_validator


class ManagersValidationMixin:
    """Миксин с валидацией списка менеджеров."""

    @field_validator('managers_id')
    @classmethod
    def validate_managers_not_empty(cls, v: List[int]) -> List[int]:
        """Проверка, что список менеджеров не пустой."""
        if len(v) == 0:
            raise ValueError('Список менеджеров не может быть пустым')
        return v


class OptionalManagersValidationMixin:
    """Миксин с опциональной валидацией для обновления."""

    @field_validator('managers_id')
    @classmethod
    def validate_managers_not_empty(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        """Проверка, что список менеджеров не пустой (если передан)."""
        if v is not None and len(v) == 0:
            raise ValueError('Список менеджеров не может быть пустым')
        return v


class SeatNumberValidator:
    """Валидатор для количества посадочных мест."""

    @field_validator('seat_number')
    @classmethod
    def validate_seat_number(cls, v: Optional[int]) -> Optional[int]:
        """Валидация количества мест при обновлении."""
        if v is not None and v <= 0:
            raise ValueError('Количество посадочных мест должно быть больше 0')
        return v


class TimeSlotIntervalValidator:
    """Валидатор для временных интервалов."""

    @field_validator('end_time')
    @classmethod
    def validate_end_time_after_start(cls, v: time, info: ValidationInfo) -> time:
        """Проверяет, что end_time > start_time."""
        start_time = info.data.get('start_time')
        if start_time and v <= start_time:
            raise ValueError('Время окончания должно быть больше времени начала')
        return v


class OptionalTimeSlotIntervalValidator:
    """Валидатор для временных интервалов при обновлении."""

    @field_validator('end_time')
    @classmethod
    def validate_end_time_after_start(cls, v: Optional[time], info: ValidationInfo) -> Optional[time]:
        """Если оба поля переданы, проверяем end_time > start_time."""
        if v is not None:
            start_time = info.data.get('start_time')
            if start_time is not None and v <= start_time:
                raise ValueError('Время окончания должно быть больше времени начала')
        return v
