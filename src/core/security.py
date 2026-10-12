"""Модуль безопасности."""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import user_crud
from models.user import ADMIN_ROLES, STAFF_ROLES, User

from core.db import get_session
from core.settings import settings

logger = logging.getLogger(__name__)

password_hasher = PasswordHash.recommended()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='/api/v1/auth/login',
)

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl='/api/v1/auth/login',
    auto_error=False,
)


def hash_password(password: str) -> str:
    """Хеширует пароль."""
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Проверяет пароль."""
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """Создает JWT token."""
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes,
    )

    to_encode.update({'exp': expire})

    try:
        return jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    except JWTError:
        logger.error('Failed to create access token', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Token creation failed',
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Получает текущего пользователя."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get('sub')

        if user_id is None:
            raise credentials_exception

    except JWTError:
        logger.warning('Invalid token', exc_info=True)
        raise credentials_exception

    user = await user_crud.get_by_id(
        session=session,
        obj_id=int(user_id),
    )

    if user is None:
        raise credentials_exception

    return user


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    """Получает текущего пользователя, если он авторизован."""
    if token is None:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get('sub')

        if user_id is None:
            return None

    except JWTError:
        return None

    return await user_crud.get_by_id(
        session=session,
        obj_id=int(user_id),
    )


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверка ADMIN."""
    if current_user.role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied',
        )

    return current_user


async def get_current_manager(
    cafe_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Проверка MANAGER."""
    if current_user.role in ADMIN_ROLES:
        return current_user
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied',
        )
    if not cafe_id:
        return current_user

    result = await db.execute(
        select(User).where(
            User.cafe_id == cafe_id,
        ),
    )
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Вы не имеете доступа к этому кафе',
        )

    return current_user
