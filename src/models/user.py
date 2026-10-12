from __future__ import annotations

import enum

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.base_model import Base
from core.constants import (
    USER_EMAIL_MAX_LEN,
    USER_PASSWORD_HASH_MAX_LEN,
    USER_PHONE_MAX_LEN,
    USER_TG_ID_MAX_LEN,
    USER_USERNAME_MAX_LEN,
)


class UserRole(str, enum.Enum):
    """Роли, определяющие права доступа пользователя."""

    ADMIN = 'ADMIN'
    MANAGER = 'MANAGER'
    USER = 'USER'


ADMIN_ROLES = (UserRole.ADMIN,)
STAFF_ROLES = (UserRole.ADMIN, UserRole.MANAGER)


class User(Base):
    """Пользователь приложения с ролевым управлением доступом."""

    __table_args__ = (
        CheckConstraint('email IS NOT NULL OR phone IS NOT NULL', name='ck_user_email_or_phone'),
        CheckConstraint(r"email IS NULL OR email ~ '^[^@]+@[^@]+\.[^@]+$'", name='ck_user_email_format'),
        CheckConstraint(
            r"phone IS NULL OR phone ~ '^\+?[0-9][0-9 \-\(\)]{5,}$'",
            name='ck_user_phone_format',
        ),
    )

    username: Mapped[str] = mapped_column(String(USER_USERNAME_MAX_LEN), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(USER_EMAIL_MAX_LEN), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(USER_PHONE_MAX_LEN), unique=True, nullable=True)
    tg_id: Mapped[str | None] = mapped_column(String(USER_TG_ID_MAX_LEN), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(USER_PASSWORD_HASH_MAX_LEN), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    cafe_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('cafes.id', ondelete='SET NULL'),
        nullable=True,
    )

    bookings: Mapped[list['Booking']] = relationship(back_populates='user')
