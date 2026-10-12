"""Роуты пользователей."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.user import user_crud
from models.user import User, UserRole
from schemas.user import (
    AdminUserUpdateSchema,
    UserCreateSchema,
    UserResponseSchema,
    UserUpdateSchema,
)
from services.user import (
    create_user_service,
    deactivate_user_service,
    update_user_service,
)

from core.db import get_session
from core.exceptions import UserAlreadyExistsError, UserNotFoundError
from core.security import (
    get_current_admin,
    get_current_manager,
    get_current_user,
    get_current_user_optional,
)

router = APIRouter(
    prefix='/users',
    tags=['Users'],
)


@router.get(
    path='/me',
    response_model=UserResponseSchema,
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponseSchema:
    """Получение текущего пользователя."""
    return current_user


@router.patch(
    path='/me',
    response_model=UserResponseSchema,
)
async def update_me(
    user_data: UserUpdateSchema,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserResponseSchema:
    """Обновление текущего пользователя."""
    try:
        return await update_user_service(
            session=session,
            user_id=current_user.id,
            user_data=user_data,
        )

    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )

    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.post(
    path='/',
    response_model=UserResponseSchema,
)
async def create_user(
    user_data: UserCreateSchema,
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(
        get_current_user_optional,
    ),
) -> UserResponseSchema:
    """Создание пользователя."""
    if (
        current_user is not None
        and current_user.role == UserRole.USER
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied',
        )

    try:
        return await create_user_service(
            session=session,
            user_data=user_data,
        )

    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.get(
    path='/',
    response_model=list[UserResponseSchema],
)
async def get_users(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_manager),
) -> list[UserResponseSchema]:
    """Получение списка пользователей."""
    return await user_crud.get_all(
        session=session,
    )


@router.get(
    path='/{user_id}',
    response_model=UserResponseSchema,
)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_manager),
) -> UserResponseSchema:
    """Получение пользователя по ID."""
    user = await user_crud.get_by_id(
        session=session,
        obj_id=user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )

    return user


@router.patch(
    path='/{user_id}',
    response_model=UserResponseSchema,
)
async def update_user(
    user_id: int,
    user_data: AdminUserUpdateSchema,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_manager),
) -> UserResponseSchema:
    """Обновление пользователя."""
    target_user = await user_crud.get_by_id(
        session=session,
        obj_id=user_id,
    )

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )

    if (
        current_user.role == UserRole.MANAGER
        and target_user.role == UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Managers cannot edit admins',
        )

    try:
        return await update_user_service(
            session=session,
            user_id=user_id,
            user_data=user_data,
        )

    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )

    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )


@router.delete(
    path='/{user_id}',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Response:
    """Удаление пользователя."""
    try:
        await deactivate_user_service(
            session=session,
            user_id=user_id,
        )

    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
