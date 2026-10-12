from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.cafe import cafe_crud
from crud.user import user_crud
from models.cafe import Cafe
from models.user import User, UserRole


def get_show_active_value(current_user: User, show_active: bool) -> bool:
    """Определяет значение show_active в зависимости от роли пользователя."""
    if current_user.role == UserRole.USER:
        return True
    return show_active


async def get_cafe_or_404(
    cafe_id: int,
    db: AsyncSession,
    show_active: Optional[bool] = None,
) -> Cafe:
    """Получает кафе по ID или возвращает 404 если не найдено."""
    cafe = await cafe_crud.get_cafe_by_id(db, cafe_id, show_active=show_active)
    if not cafe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Кафе id={cafe_id} не найдено',
        )
    return cafe


async def validate_managers(
    session: AsyncSession,
    managers_id: List[int],
) -> List[User]:
    """Проверяет существование менеджеров и возвращает их."""
    managers = await user_crud.get_managers_by_ids(session, managers_id)

    if len(managers) != len(managers_id):
        found_ids = {m.id for m in managers}
        missing_ids = set(managers_id) - found_ids
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Менеджеры с ID {list(missing_ids)} не найдены',
        )

    return managers
