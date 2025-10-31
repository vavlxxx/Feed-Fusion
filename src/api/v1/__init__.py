from fastapi import APIRouter

from src.api.v1.news import router as news_router

router = APIRouter(prefix="/v1")
router.include_router(news_router)

__all__ = ["router"]
