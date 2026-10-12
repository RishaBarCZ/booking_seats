from fastapi import APIRouter

from api.v1.auth import router as auth_router
from api.v1.booking import router as booking_router
from api.v1.cafes import router as cafes_router
from api.v1.media import router as media_router
from api.v1.tables import router as tables_router
from api.v1.time_slots import router as time_slots_router
from api.v1.users import router as users_router

router = APIRouter(prefix='/api/v1')

# Sub-routers are added here as features are implemented:
# from api.v1.dishes import router as dishes_router
# from api.v1.actions import router as actions_router


router.include_router(auth_router)
router.include_router(users_router)

router.include_router(cafes_router)
router.include_router(tables_router)
router.include_router(time_slots_router)
# router.include_router(dishes_router)
# router.include_router(actions_router)
router.include_router(media_router)
router.include_router(booking_router, prefix='/booking', tags=['Booking'])
