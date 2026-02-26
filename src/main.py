import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

sys.path.append(str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from src.api import router as main_router
from src.api.docs import router as docs_router
from src.bot.bot import bot
from src.config import settings
from src.db import engine, sessionmaker
from src.schemas.auth import UserRegisterDTO
from src.services.auth import AuthService
from src.utils.db_tools import DBHealthChecker, DBManager
from src.utils.es_manager import ESManager
from src.utils.exceptions import UserExistsError
from src.utils.log_config import configurate_logging, get_logger
from src.utils.redis_manager import redis_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger = get_logger("src")

    await redis_manager.connect()
    logger.info("Successfully connected to Redis!")

    FastAPICache.init(RedisBackend(redis_manager._redis), prefix="fastapi-cache")
    logger.info("FastAPI Cache has been initialized!")

    await DBHealthChecker(engine=engine).check()
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
            await db.rollback()
            logger.info("Admin user already exists, skipping...")

    async with ESManager(index_name=settings.ES_INDEX_NAME) as es:
        await es.connection_is_stable()
        logger.info("Successfully connected to Elasticsearch!")
        if settings.ES_RESET_INDEX:
            await es.delete_index(index_name=settings.ES_INDEX_NAME)
            logger.info("Deleted old index: %s", settings.ES_INDEX_NAME)

    if settings.MODE == "PROD":
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
STATIC_DIR = Path(__file__).parent / "static"
INDEX_FILE = STATIC_DIR / "index.html"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_frontend():
    return FileResponse(INDEX_FILE)


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
