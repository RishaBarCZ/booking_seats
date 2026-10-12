import logging

from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import user_crud
from models.user import User
from schemas.user import (
    UserCreateSchema,
    UserUpdateSchema,
)

from core.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from core.security import hash_password

logger = logging.getLogger(__name__)


async def create_user_service(
    session: AsyncSession,
    user_data: UserCreateSchema,
) -> User:
    """Создает пользователя."""
    if await user_crud.user_exists(
        session=session,
        email=user_data.email,
        phone=user_data.phone,
    ):
        raise UserAlreadyExistsError(
            'User already exists',
        )

    created_user = await user_crud.create(
        session=session,
        data={
            'username': user_data.username,
            'email': user_data.email,
            'phone': user_data.phone,
            'password_hash': hash_password(
                user_data.password,
            ),
        },
    )

    await session.commit()

    logger.info(
        'User created: %s',
        created_user.username,
    )

    return created_user


async def update_user_service(
    session: AsyncSession,
    user_id: int,
    user_data: UserUpdateSchema,
) -> User:
    """Обновляет пользователя."""
    user = await user_crud.get_by_id(
        session=session,
        obj_id=user_id,
    )

    if user is None:
        raise UserNotFoundError(
            'User not found',
        )

    if await user_crud.user_exists(
        session=session,
        email=user_data.email,
        phone=user_data.phone,
        exclude_user_id=user.id,
    ):
        raise UserAlreadyExistsError(
            'User already exists',
        )

    update_data = user_data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    # Если обновляется пароль — сохраняем только его хэш
    if 'password' in update_data:
        update_data['password_hash'] = hash_password(
            update_data.pop('password'),
        )

    updated_user = await user_crud.update(
        session=session,
        obj=user,
        data=update_data,
    )

    await session.commit()

    logger.info(
        'User updated: %s',
        updated_user.username,
    )

    return updated_user


async def deactivate_user_service(
    session: AsyncSession,
    user_id: int,
) -> User:
    """Деактивирует пользователя."""
    user = await user_crud.get_by_id(
        session=session,
        obj_id=user_id,
    )

    if user is None:
        raise UserNotFoundError(
            'User not found',
        )

    deactivated_user = await user_crud.deactivate(
        session=session,
        obj=user,
    )

    await session.commit()

    logger.info(
        'User deactivated: %s',
        deactivated_user.username,
    )

    return deactivated_user
