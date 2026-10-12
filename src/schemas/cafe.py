from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.mixins import ManagersValidationMixin, OptionalManagersValidationMixin
from schemas.user import UserShortInfo

from core.constants import CAFE_ADDRESS_MAX_LEN, CAFE_NAME_MAX_LEN, CAFE_PHONE_MAX_LEN


class CafeBase(BaseModel):
    """Базовая модель схемы Cafe."""

    name: str = Field(..., max_length=CAFE_NAME_MAX_LEN)
    address: str = Field(..., max_length=CAFE_ADDRESS_MAX_LEN)
    phone: str = Field(
        ...,
        max_length=CAFE_PHONE_MAX_LEN,
        pattern=r'^\+?[0-9][0-9 \-\(\)]{5,}$',
    )
    description: Optional[str] = None
    photo_id: Optional[UUID] = None


class CafeCreate(CafeBase, ManagersValidationMixin):
    """Схема для создания кафе."""

    managers_id: List[int] = Field(..., description='Список id менеджеров')


class CafeUpdate(CafeBase, OptionalManagersValidationMixin):
    """Схема для обновления кафе."""

    name: Optional[str] = Field(default=None, max_length=CAFE_NAME_MAX_LEN)
    address: Optional[str] = Field(default=None, max_length=CAFE_ADDRESS_MAX_LEN)
    phone: Optional[str] = Field(
        default=None,
        max_length=CAFE_PHONE_MAX_LEN,
        pattern=r'^\+?[0-9][0-9 \-\(\)]{5,}$',
    )
    description: Optional[str] = None
    photo_id: Optional[UUID] = None
    managers_id: Optional[List[int]] = None
    is_active: Optional[bool] = None


class CafeShortInfo(CafeBase):
    """Краткая информация о кафе."""

    model_config = ConfigDict(from_attributes=True)

    id: int


class CafeInfo(CafeShortInfo):
    """Полная информация о кафе."""

    managers: List[UserShortInfo] = []
    is_active: bool
    created_at: datetime
    updated_at: datetime
