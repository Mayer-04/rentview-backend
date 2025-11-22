from fastapi import APIRouter

from app.features.comments.infrastructure.fastapi.controller import (
    comments_router as comments_controller_router,
)
from app.features.comments.infrastructure.fastapi.controller import (
    saved_records_router,
)

comments_router = APIRouter()
comments_router.include_router(comments_controller_router)
comments_router.include_router(saved_records_router)
