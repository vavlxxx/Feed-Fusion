import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator


sys.path.append(str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from src.db import engine
from src.api import router as main_router
from src.utils.redis_manager import redis_manager
from src.utils.logging import configurate_logging, get_logger
from src.api.docs import router as docs_router
from src.utils.db_tools import DBHealthChecker
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger = get_logger("src")

    await DBHealthChecker(engine=engine).check()

    await redis_manager.connect()
    logger.info("Successfully connected to Redis!")

    FastAPICache.init(RedisBackend(redis_manager._redis), prefix="fastapi-cache")
    logger.info("FastAPI Cache has been initialized!")

    logger.info("All checks passed!")
    yield

    await redis_manager.close()
    logger.info("Connection to Redis has been closed")

    logger.info("Shutting down...")


configurate_logging()
app = FastAPI(
    title=settings.TITLE,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    default_response_class=ORJSONResponse,
)
app.include_router(main_router)
app.include_router(docs_router)


if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=settings.UVICORN_HOST,
        port=settings.UVICORN_PORT,
        reload=settings.UVICORN_RELOAD,
        log_config="logging_config.json",
    )
