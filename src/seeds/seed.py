import asyncio

from sqlalchemy import select

import models  # noqa: F401 — registers all ORM classes so forward refs resolve
from models.user import User, UserRole

from core.db import session_maker
from core.logger import setup_logger
from core.security import hash_password
from core.settings import settings

logger = setup_logger(__name__)


async def create_admin() -> None:
    """Создаёт администратора по умолчанию, если он ещё не существует."""
    async with session_maker() as session:
        result = await session.execute(select(User).where(User.username == settings.admin_username))
        if result.scalar_one_or_none() is not None:
            logger.info('Admin already exists, skipping.')
            return

        admin = User(
            username=settings.admin_username,
            email=settings.admin_email,
            password_hash=hash_password(settings.admin_password),
            role=UserRole.ADMIN,
        )
        session.add(admin)
        await session.commit()
        logger.info('Admin user created: %s', settings.admin_username)


async def main() -> None:
    """Запускает все операции начального заполнения данных."""
    await create_admin()
    logger.info('Seeding complete.')


if __name__ == '__main__':
    asyncio.run(main())
