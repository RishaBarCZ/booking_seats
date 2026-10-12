import uuid

from sqlalchemy import UUID, String
from sqlalchemy.orm import Mapped, mapped_column

from core.base_model import Base
from core.constants import MEDIA_FILENAME_MAX_LEN


class Media(Base):
    """Загруженное изображение, хранимое по UUID первичному ключу."""

    __tablename__ = 'media'

    id: Mapped[uuid.UUID] = mapped_column(
        UUID, primary_key=True,
        default=uuid.uuid4,
    )
    filename: Mapped[str] = mapped_column(
        String(MEDIA_FILENAME_MAX_LEN),
        nullable=False,
    )
