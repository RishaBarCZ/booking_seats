"""Схемы пользователей."""

from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from models.user import UserRole

from core.constants import (
    USER_EMAIL_MAX_LEN,
    USER_PHONE_MAX_LEN,
    USER_USERNAME_MAX_LEN,
)


class UserShortInfo(BaseModel):
    """Краткая информация о пользователе."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr | None = None
    phone: str | None = None
    role: UserRole


class UserCreateSchema(BaseModel):
    """Схема создания пользователя."""

    username: str = Field(
        min_length=3,
        max_length=USER_USERNAME_MAX_LEN,
    )

    email: EmailStr | None = Field(
        default=None,
        max_length=USER_EMAIL_MAX_LEN,
    )

    phone: str | None = Field(
        default=None,
        min_length=6,
        max_length=USER_PHONE_MAX_LEN,
        pattern=r'^\+?[0-9][0-9 \-\(\)]{5,}$',
    )

    password: str = Field(
        min_length=6,
    )

    @model_validator(mode='after')
    def validate_contacts(self) -> Self:
        """Проверяет наличие email или phone."""
        if not self.email and not self.phone:
            raise ValueError(
                'Email or phone is required',
            )

        return self


class UserLoginSchema(BaseModel):
    """Схема авторизации."""

    login: str
    password: str


class UserUpdateSchema(BaseModel):
    """Схема обновления своего профиля."""

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=USER_USERNAME_MAX_LEN,
    )

    email: EmailStr | None = Field(
        default=None,
        max_length=USER_EMAIL_MAX_LEN,
    )

    phone: str | None = Field(
        default=None,
        min_length=6,
        max_length=USER_PHONE_MAX_LEN,
        pattern=r'^\+?[0-9][0-9 \-\(\)]{5,}$',
    )

    tg_id: str | None = None

    password: str | None = Field(
        default=None,
        min_length=6,
    )

    @model_validator(mode='after')
    def validate_nullable_fields(self) -> Self:
        """Проверяет, что email и phone не являются пустыми строками."""
        if self.email == '':
            raise ValueError('Email cannot be empty')

        if self.phone == '':
            raise ValueError('Phone cannot be empty')

        return self


class AdminUserUpdateSchema(UserUpdateSchema):
    """Схема обновления пользователя администратором."""

    role: UserRole | None = None


class UserResponseSchema(BaseModel):
    """Схема ответа пользователя."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr | None = None
    phone: str | None = None
    tg_id: str | None = None
    role: UserRole
    is_active: bool
