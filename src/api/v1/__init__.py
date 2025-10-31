from fastapi import APIRouter

from src.api.v1.news import router as news_router
from src.api.v1.channels import router as channels_router

router = APIRouter(prefix="/v1")
router.include_router(news_router)
router.include_router(channels_router)

__all__ = ["router"]
