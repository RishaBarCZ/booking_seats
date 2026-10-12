from datetime import datetime, timezone

from sqlalchemy import BOOLEAN, DateTime, Integer, MetaData, func
from sqlalchemy.orm import Mapped, declarative_base, declared_attr, mapped_column

metadata = MetaData(
    naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': ('fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s'),
        'pk': 'pk_%(table_name)s',
    },
)


def get_utc_now() -> datetime:
    """Вернуть текущие дату и время в UTC."""
    return datetime.now(timezone.utc)


class PreBase:
    """Общие служебные поля и имя таблицы для всех ORM-моделей."""

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:  # noqa: N805
        """Формирует имя таблицы из имени класса в нижнем регистре во множественном числе."""
        return f'{cls.__name__.lower()}s'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    is_active: Mapped[bool] = mapped_column(BOOLEAN, default=True, server_default='true')

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_utc_now,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=get_utc_now,
        server_onupdate=func.now(),
    )


Base = declarative_base(cls=PreBase, metadata=metadata)
