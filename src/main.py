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
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend

from src.api import router as main_router
from src.api.docs import router as docs_router
from src.bot.bot import bot
from src.config import settings
from src.db import engine, sessionmaker
from src.ml.io_utils import load_samples_from_csv
from src.ml.service import NewsClassifierService
from src.schemas.auth import UserRegisterDTO
from src.services.auth import AuthService
from src.tasks.ml import retrain_model
from src.utils.db_tools import DBHealthChecker, DBManager
from src.utils.exceptions import UserExistsError
from src.utils.log_config import configurate_logging, get_logger
from src.utils.redis_manager import redis_manager
from src.utils.search_sync import rebuild_search_index


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    logger = get_logger("src")

    if settings.USE_REDIS_CACHE:
        try:
            await redis_manager.connect()
            logger.info("Successfully connected to Redis!")
            FastAPICache.init(
                RedisBackend(redis_manager.redis),
                prefix="fastapi-cache",
            )
            logger.info("FastAPI Cache has been initialized!")
        except Exception as exc:
            FastAPICache.init(
                InMemoryBackend(), prefix="fastapi-cache"
            )
            logger.warning(
                "Redis unavailable, using in-memory cache: %s",
                exc,
            )
    else:
        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
        logger.info(
            "Redis cache disabled: using in-memory cache backend."
        )

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

        if settings.ENABLE_ML_AUTOCATEGORIZATION:
            model_exists = NewsClassifierService.model_exists()
            if not model_exists:
                logger.info("Classificator model is not exists...")
                existing_samples = await db.denorm_news.get_all()
                if not existing_samples:
                    logger.info(
                        "Training dataset is empty, loading bootstrap dataset..."
                    )
                    samples = load_samples_from_csv(
                        settings.TRAIN_DATASET_LOCATION
                    )
                    await db.denorm_news.add_bulk(samples)
                    await db.commit()
                    logger.info(
                        "Successfully uploaded bootstrap dataset..."
                    )
                else:
                    logger.info(
                        "Training samples already exist, skipping bootstrap import."
                    )

                logger.info("Initiating ML model retraining...")
                retrain_model.delay()  # pyright: ignore

    if settings.USE_ELASTICSEARCH:
        synced = await rebuild_search_index(
            reset_index=settings.ES_RESET_INDEX
        )
        if synced:
            logger.info("Elasticsearch is ready for search.")
        else:
            logger.warning(
                "Elasticsearch unavailable, using PostgreSQL fallback for news queries."
            )
    else:
        logger.info(
            "Elasticsearch disabled: using PostgreSQL fallback for news queries."
        )

    if settings.MODE == "PROD":
        await bot.send_message(
            chat_id=settings.TELEGRAM_ADMIN_CONTACT,
            text="🚀 Feed Fusion app has been started!",
        )
        logger.info("Sent message to admin Telegram Chat...")

    logger.info("All checks passed!")
    yield

    if settings.USE_REDIS_CACHE:
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

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


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
