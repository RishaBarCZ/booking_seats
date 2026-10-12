from pydantic import BaseModel


class CustomError(BaseModel):
    """Схема для кастомной ошибки API."""

    message: str
    code: int
