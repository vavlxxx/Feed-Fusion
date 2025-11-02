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

from src.db import engine, sessionmaker
from src.api import router as main_router
from src.utils.exceptions import UserExistsError
from src.utils.redis_manager import redis_manager
from src.utils.logging import configurate_logging, get_logger
from src.api.docs import router as docs_router
from src.utils.db_tools import DBHealthChecker, DBManager
from src.config import settings
from src.bot.bot import bot
from src.schemas.auth import UserRegisterDTO
from src.services.auth import AuthService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger = get_logger("src")

    await DBHealthChecker(engine=engine).check()

    await redis_manager.connect()
    logger.info("Successfully connected to Redis!")

    FastAPICache.init(RedisBackend(redis_manager._redis), prefix="fastapi-cache")
    logger.info("FastAPI Cache has been initialized!")

    async with DBManager(session_factory=sessionmaker) as db:
        try:
            await AuthService(db).register_user(
                register_data=UserRegisterDTO(
                    username=settings.ADMIN_USERNAME,
                    password=settings.ADMIN_PASSWORD,
                ),
                is_admin=True,
            )
            await db.commit()
            logger.info("Successfully created admin user!")
        except UserExistsError:
            logger.info("Admin user already exists, skipping...")

    if settings.MODE == "TEST":
        await bot.send_message(
            chat_id=settings.TELEGRAM_ADMIN_CONTACT,
            text="🚀 Feed Fusion app has been started!",
        )
        logger.info("Sent message to admin Telegram Chat...")

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
