from crud.base import CRUDBase
from models.media import Media


class CRUDMedia(CRUDBase[Media]):
    """CRUD для модели Media."""


media_crud = CRUDMedia(Media)
