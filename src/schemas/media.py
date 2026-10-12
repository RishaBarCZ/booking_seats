"""Схемы для медиа-файлов."""

import uuid

from pydantic import BaseModel, ConfigDict


class MediaRead(BaseModel):
    """Ответ при успешной загрузке изображения."""

    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
