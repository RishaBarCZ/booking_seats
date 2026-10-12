from dataclasses import dataclass

from fastapi import HTTPException, status


@dataclass()
class BookingAccessScope:
    """Ограничение доступа к бронированиям на уровне SQL-запроса."""

    cafe_id: int | None = None
    user_id: int | None = None

    def ensure_cafe_allowed(self, cafe_id: int) -> None:
        """Проверить, что кафе входит в область доступа."""
        if self.cafe_id is None:
            return
        if cafe_id == self.cafe_id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Вы не имеете доступа к этому кафе.',
        )


@dataclass
class BookingAccessFilters:
    """Фильтры для списка бронирований с учётом прав пользователя."""

    cafe_id: int | None
    user_id: int | None
    show_active: bool | None
