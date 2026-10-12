"""Роуты авторизации."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.auth import TokenSchema
from schemas.user import UserLoginSchema
from services.auth import authenticate_user

from core.db import get_session

router = APIRouter(
    prefix='/auth',
    tags=['Auth'],
)


@router.post(
    path='/login',
    response_model=TokenSchema,
)
async def login(
    user_data: UserLoginSchema,
    session: AsyncSession = Depends(get_session),
) -> TokenSchema:
    """Авторизация пользователя."""
    token = await authenticate_user(
        session=session,
        login=user_data.login,
        password=user_data.password,
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid login or password',
        )

    return TokenSchema(
        access_token=token,
    )
