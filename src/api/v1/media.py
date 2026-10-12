import io
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from crud.media import media_crud
from schemas.media import MediaRead

from core.constants import (
    MEDIA_ALLOWED_CONTENT_TYPES,
    MEDIA_CHUNK_SIZE,
    MEDIA_FILENAME_MAX_LEN,
    MEDIA_MAX_SIZE_BYTES,
    MEDIA_OUTPUT_CONTENT_TYPE,
    MEDIA_OUTPUT_EXTENSION,
)
from core.db import get_session
from core.security import get_current_manager
from core.settings import settings

router = APIRouter(prefix='/media', tags=['media'])


def _storage_path_for(media_id: uuid.UUID) -> Path:
    """Возвращает путь к JPG-файлу в хранилище для заданного id."""
    return settings.media_storage_path / f'{media_id}{MEDIA_OUTPUT_EXTENSION}'


def _convert_to_jpeg(raw: bytes) -> bytes:
    """Открывает изображение и пересохраняет его в формате JPEG."""
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            if image.mode != 'RGB':
                image = image.convert('RGB')
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG')
            return buffer.getvalue()
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Не удалось обработать изображение',
        ) from exc


@router.post(
    '',
    response_model=MediaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_manager)],
)
async def upload_media(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> MediaRead:
    """Принимает изображение JPG/PNG, конвертирует в JPG и сохраняет."""
    if file.content_type not in MEDIA_ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail='Поддерживаются только изображения JPG и PNG',
        )

    too_large = HTTPException(
        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        detail='Размер изображения превышает 5 МБ',
    )

    if file.size is not None and file.size > MEDIA_MAX_SIZE_BYTES:
        raise too_large

    buffer = bytearray()
    while chunk := await file.read(MEDIA_CHUNK_SIZE):
        buffer.extend(chunk)
        if len(buffer) > MEDIA_MAX_SIZE_BYTES:
            raise too_large
    raw = bytes(buffer)

    jpeg_bytes = _convert_to_jpeg(raw)

    original_name = (file.filename or 'image')[:MEDIA_FILENAME_MAX_LEN]
    media = await media_crud.create(session, {'filename': original_name})

    settings.media_storage_path.mkdir(parents=True, exist_ok=True)
    _storage_path_for(media.id).write_bytes(jpeg_bytes)

    return MediaRead.model_validate(media)


@router.get(
    '/{media_id}',
    response_class=FileResponse,
    responses={200: {'content': {MEDIA_OUTPUT_CONTENT_TYPE: {}}}},
)
async def get_media(
    media_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Возвращает изображение в формате JPG в виде бинарных данных."""
    media = await media_crud.get_by_id(session, media_id)
    if media is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Изображение не найдено',
        )

    path = _storage_path_for(media.id)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Изображение не найдено',
        )

    return FileResponse(path, media_type=MEDIA_OUTPUT_CONTENT_TYPE)
