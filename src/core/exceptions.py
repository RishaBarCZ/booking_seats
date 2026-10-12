"""Кастомные исключения."""

from http import HTTPStatus

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class UserAlreadyExistsError(Exception):
    """Пользователь уже существует."""


class UserNotFoundError(Exception):
    """Пользователь не найден."""


def create_error_response(
    status_code: int,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Создает кастомное сообщение об ошибке."""
    return JSONResponse(
        status_code=status_code,
        content={
            'code': status_code,
            'message': message,
        },
        headers=headers,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Обрабатывает стандартные HTTP исключения и возвращает кастомный ответ."""
    if isinstance(exc.detail, str):
        message = exc.detail
    else:
        message = HTTPStatus(exc.status_code).phrase

    return create_error_response(
        status_code=exc.status_code,
        message=message,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Обрабатывает исключения валидации и возвращает кастомный ответ."""
    errors = exc.errors()

    if errors:
        field = '.'.join(str(loc) for loc in errors[0]['loc'])
        message = f"Ошибка валидации данных в поле '{field}': {errors[0]['msg']}"
    else:
        message = 'Ошибка валидации данных'

    return create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message=message,
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Обрабатывает все необработанные исключения и возвращает кастомный ответ."""
    return create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message='Внутренняя ошибка сервера.',
    )


def register_error_handlers(app: FastAPI) -> None:
    """Регистрирует все обработчики ошибок в приложении FastAPI.

    Args:
        app: FastAPI приложение

    """
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
