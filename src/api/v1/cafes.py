from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.cafe import cafe_crud
from models.user import User, UserRole
from schemas.cafe import CafeCreate, CafeInfo, CafeUpdate
from services.cafes import get_cafe_or_404, get_show_active_value, validate_managers

from core.db import get_session
from core.security import get_current_admin, get_current_manager, get_current_user

router = APIRouter(prefix='/cafes', tags=['Кафе'])


@router.get('', response_model=list[CafeInfo], status_code=status.HTTP_200_OK)
async def get_all_cafes(
    show_active: bool = Query(True, description='Показать активные кафе'),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[CafeInfo]:
    """Получить список всех кафе."""
    show_active_value = get_show_active_value(current_user, show_active)
    cafes = await cafe_crud.get_cafes(session, show_active_value)
    return [CafeInfo.model_validate(cafe) for cafe in cafes]


@router.post('', response_model=CafeInfo, status_code=status.HTTP_201_CREATED)
async def create_cafe(
    cafe_data: CafeCreate,
    current_user: User = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> CafeInfo:
    """Создает новое кафе. Только для администраторов."""
    managers = await validate_managers(session, cafe_data.managers_id)
    cafe_dict = cafe_data.model_dump(exclude={'managers_id'})
    return await cafe_crud.create_cafe_with_managers(session, cafe_dict, managers)


@router.get('/{cafe_id}', response_model=CafeInfo, status_code=status.HTTP_200_OK)
async def get_cafe_by_id(
    cafe_id: int,
    show_active: bool = Query(True, description='Показать активные кафе'),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CafeInfo:
    """Получает информацию о кафе по ID."""
    show_active_value = get_show_active_value(current_user, show_active)
    cafe = await get_cafe_or_404(cafe_id, session, show_active=show_active_value)
    return CafeInfo.model_validate(cafe)


@router.patch('/{cafe_id}', response_model=CafeInfo, status_code=status.HTTP_200_OK)
async def update_cafe(
    cafe_id: int,
    cafe_data: CafeUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_manager),
) -> CafeInfo:
    """Обновляет информацию о кафе."""
    cafe = await get_cafe_or_404(cafe_id, db, show_active=None)

    if cafe_data.managers_id is not None:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Только администратор может изменять менеджеров',
            )
        managers = await validate_managers(db, cafe_data.managers_id)
        await cafe_crud.update_managers(db, cafe, managers)
    update_dict = cafe_data.model_dump(exclude={'managers_id'}, exclude_unset=True)

    if update_dict:
        updated_cafe = await cafe_crud.update_cafe(db, cafe_id, update_dict)
    else:
        updated_cafe = cafe

    return updated_cafe
