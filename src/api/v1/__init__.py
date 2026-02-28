from fastapi import APIRouter

from src.api.v1.news import router as news_router
from src.api.v1.channels import router as channels_router
from src.api.v1.auth import router as auth_router
from src.api.v1.subscriptions import router as subscriptions_router
from src.api.v1.samples import router as samples_router
from src.api.v1.ml import router as ml_router

router = APIRouter(prefix="/v1")
router.include_router(news_router)
router.include_router(channels_router)
router.include_router(auth_router)
router.include_router(subscriptions_router)
router.include_router(samples_router)
router.include_router(ml_router)
__all__ = ["router"]
