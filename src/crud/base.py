from typing import Any, Generic, TypeVar

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.base_model import Base

ModelType = TypeVar('ModelType', bound=Base)


class CRUDBase(Generic[ModelType]):
    """Универсальные асинхронные CRUD-операции для любой SQLAlchemy-модели."""

    def __init__(self, model: type[ModelType]) -> None:
        """Привязывает класс SQLAlchemy-модели к данному CRUD-экземпляру."""
        self.model = model

    def _model_attrs(self) -> set[str]:
        return set(inspect(self.model).mapper.column_attrs.keys())

    async def get_by_id(self, session: AsyncSession, obj_id: Any) -> ModelType | None:
        """Получает одну запись по первичному ключу."""
        return await session.get(self.model, obj_id)

    async def get_all(self, session: AsyncSession, **filters: Any) -> list[ModelType]:
        """Получает все записи с опциональной фильтрацией по именованным аргументам."""
        model_attrs = self._model_attrs()
        stmt = select(self.model)
        for attr, value in filters.items():
            if attr not in model_attrs:
                raise AttributeError(f"'{self.model.__name__}' has no column '{attr}'")
            stmt = stmt.where(getattr(self.model, attr) == value)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def create(self, session: AsyncSession, data: dict[str, Any]) -> ModelType:
        """Сохраняет новую запись и возвращает обновлённый экземпляр."""
        model_attrs = self._model_attrs()
        invalid = set(data) - model_attrs
        if invalid:
            raise AttributeError(f"'{self.model.__name__}' has no columns: {invalid}")
        obj = self.model(**data)
        session.add(obj)
        await session.flush()
        await session.refresh(obj)
        return obj

    async def update(self, session: AsyncSession, obj: ModelType, data: dict[str, Any]) -> ModelType:
        """Применяет частичные обновления к объекту и возвращает обновлённый экземпляр."""
        model_attrs = self._model_attrs()
        for key, value in data.items():
            if key not in model_attrs:
                raise AttributeError(f"'{self.model.__name__}' has no column '{key}'")
            setattr(obj, key, value)
        await session.flush()
        await session.refresh(obj)
        return obj

    async def deactivate(self, session: AsyncSession, obj: ModelType) -> ModelType:
        """Деактивирует запись, помечая её неактивной."""
        obj.is_active = False
        await session.flush()
        await session.refresh(obj)
        return obj
