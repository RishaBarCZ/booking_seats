"""Сервис авторизации."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import user_crud

from core.security import create_access_token, verify_password

logger = logging.getLogger(__name__)


async def authenticate_user(
    session: AsyncSession,
    login: str,
    password: str,
) -> str | None:
    """Авторизация пользователя."""
    user = await user_crud.get_user_by_login(
        session=session,
        login=login,
    )

    if user is None:
        logger.warning(
            'Login failed. User not found: %s',
            login,
        )

        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        logger.warning(
            'Login failed. Invalid password: %s',
            login,
        )

        return None

    token = create_access_token(
        data={
            'sub': str(user.id),
        },
    )

    logger.info(
        'User logged in: %s',
        user.username,
    )

    return token
