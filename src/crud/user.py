"""CRUD пользователей."""

from typing import List

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import CRUDBase
from models.user import User, UserRole


class CRUDUser(CRUDBase[User]):
    """CRUD для пользователей."""

    async def get_user_by_login(
        self,
        session: AsyncSession,
        login: str,
    ) -> User | None:
        """Получает пользователя по email или phone."""
        query = select(User).where(
            or_(
                User.email == login,
                User.phone == login,
            ),
        )

        result = await session.execute(query)

        return result.scalar_one_or_none()

    async def get_managers_by_ids(
        self,
        session: AsyncSession,
        manager_ids: List[int],
    ) -> List[User]:
        """Получает менеджеров по списку ID."""
        query = select(self.model).where(
            self.model.id.in_(manager_ids),
            self.model.role == UserRole.MANAGER,
        )

        result = await session.execute(query)

        return result.scalars().all()

    async def user_exists(
        self,
        session: AsyncSession,
        email: str | None = None,
        phone: str | None = None,
        exclude_user_id: int | None = None,
    ) -> bool:
        """Проверяет существование пользователя."""
        conditions = []

        if email:
            conditions.append(User.email == email)

        if phone:
            conditions.append(User.phone == phone)

        if not conditions:
            return False

        query = (
            select(func.count())
            .select_from(User)
            .where(or_(*conditions))
        )

        if exclude_user_id is not None:
            query = query.where(
                User.id != exclude_user_id,
            )

        result = await session.execute(query)

        return bool(result.scalar())


user_crud = CRUDUser(User)
