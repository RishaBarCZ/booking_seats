from typing import Annotated

from fastapi import Depends, HTTPException, Query, status

from models.user import ADMIN_ROLES, STAFF_ROLES, User
from services.booking import BookingAccessFilters, BookingAccessScope

from core.security import get_current_user

CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_booking_access_scope(current_user: CurrentUserDep) -> BookingAccessScope:
    """Получить область доступа пользователя к бронированиям."""
    if current_user.role in ADMIN_ROLES:
        return BookingAccessScope()

    if current_user.role in STAFF_ROLES:
        if current_user.cafe_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Менеджер не привязан к кафе.',
            )
        return BookingAccessScope(cafe_id=current_user.cafe_id)

    return BookingAccessScope(user_id=current_user.id)


async def get_booking_access_filters(
    current_user: CurrentUserDep,
    show_active: Annotated[bool | None, Query(description='Только активные бронирования')] = None,
    cafe_id: Annotated[int | None, Query(gt=0)] = None,
    user_id: Annotated[int | None, Query(gt=0)] = None,
) -> BookingAccessFilters:
    """Получить фильтры списка бронирований с учётом прав доступа."""
    scope = get_booking_access_scope(current_user)

    if current_user.role in ADMIN_ROLES:
        return BookingAccessFilters(
            show_active=show_active,
            cafe_id=cafe_id,
            user_id=user_id,
        )

    if current_user.role in STAFF_ROLES:
        if cafe_id is not None and cafe_id != scope.cafe_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Вы не имеете доступа к этому кафе.',
            )
        return BookingAccessFilters(
            cafe_id=scope.cafe_id,
            user_id=user_id,
            show_active=True if show_active is None else show_active,
        )

    # Обычный пользователь:
    # - user_id из query игнорируется;
    # - show_active из query игнорируется;
    # - cafe_id можно оставить, чтобы пользователь мог смотреть свои брони
    #   в конкретном кафе.
    return BookingAccessFilters(
        cafe_id=cafe_id,
        user_id=scope.user_id,
        show_active=True,
    )


BookingAccessScopeDep = Annotated[
    BookingAccessScope,
    Depends(get_booking_access_scope),
]

BookingAccessFiltersDep = Annotated[
    BookingAccessFilters,
    Depends(get_booking_access_filters),
]
