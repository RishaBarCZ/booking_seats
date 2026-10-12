from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.table import table_crud
from models.table import CafeTable


async def get_table_or_404(
    db: AsyncSession,
    table_id: int,
    cafe_id: int,
    show_active: Optional[bool] = None,
) -> CafeTable:
    """Получает стол по ID или возвращает 404 если не найден."""
    table = await table_crud.get_table_by_id(
        db,
        table_id,
        cafe_id,
        show_active=show_active,
    )
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Стол не найден',
        )
    return table
