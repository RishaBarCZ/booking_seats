from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.table import table_crud
from models.user import User
from schemas.table import TableCreate, TableInfo, TableUpdate
from services.cafes import get_cafe_or_404, get_show_active_value
from services.tables import get_table_or_404

from core.db import get_session
from core.security import get_current_manager, get_current_user

router = APIRouter(prefix='/cafes/{cafe_id}/tables', tags=['Столы'])


@router.get('', response_model=list[TableInfo], status_code=status.HTTP_200_OK)
async def get_cafe_tables(
    cafe_id: int,
    show_active: bool = Query(True, description='Показать активные столы'),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> list[TableInfo]:
    """Получает список столов в кафе с учетом роли пользователя."""
    show_active_value = get_show_active_value(current_user, show_active)
    await get_cafe_or_404(cafe_id, db, show_active=None)
    tables = await table_crud.get_tables(db, cafe_id, show_active_value)
    return [TableInfo.model_validate(table) for table in tables]


@router.post(
    '',
    response_model=TableInfo,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_manager)],
)
async def create_table(
    cafe_id: int,
    table_data: TableCreate,
    db: AsyncSession = Depends(get_session),
) -> TableInfo:
    """Создание стола для кафе."""
    await get_cafe_or_404(cafe_id, db, show_active=None)
    table_dict = table_data.model_dump()
    table_dict['cafe_id'] = cafe_id
    table = await table_crud.create_table(db, table_dict)
    return TableInfo.model_validate(table)


@router.get('/{table_id}', response_model=TableInfo, status_code=status.HTTP_200_OK)
async def get_table_by_id(
    cafe_id: int,
    table_id: int,
    show_active: bool = Query(True, description='Показать активные столы'),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
) -> TableInfo:
    """Получает информацию о столе по ID ."""
    show_active_value = get_show_active_value(current_user, show_active)
    await get_cafe_or_404(cafe_id, db, show_active=None)
    return await get_table_or_404(db, table_id, cafe_id, show_active=show_active_value)


@router.patch(
    '/{table_id}',
    response_model=TableInfo,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_manager)],
)
async def update_table(
    cafe_id: int,
    table_id: int,
    table_data: TableUpdate,
    db: AsyncSession = Depends(get_session),
) -> TableInfo:
    """Обновляет информацию о столе."""
    await get_cafe_or_404(cafe_id, db, show_active=None)
    await get_table_or_404(db, table_id, cafe_id, show_active=None)
    update_dict = table_data.model_dump(exclude_unset=True)
    return await table_crud.update_table(db, table_id, update_dict)
