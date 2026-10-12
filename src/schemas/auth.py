"""Схемы авторизации."""

from pydantic import BaseModel


class TokenSchema(BaseModel):
    """JWT токен."""

    access_token: str
    token_type: str = 'bearer'
