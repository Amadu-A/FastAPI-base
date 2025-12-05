# base_app/api/api_v1/__init__.py
from fastapi import APIRouter

from base_app.core.config import settings
from .users import router as users_router


router = APIRouter(
    prefix=settings.api.v1.prefix,
)
router.include_router(
    users_router,
    prefix=settings.api.v1.users,
)
