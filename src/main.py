import sys
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator

sys.path.append(str(Path(__file__).parent.parent))

import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.db import engine
from src.api import router as main_router
from src.utils.logging import configurate_logging, get_logger
from src.api.docs import router as docs_router
from src.utils.db_tools import DBHealthChecker
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configurate_logging()
    logger = get_logger("src")

    await DBHealthChecker(engine=engine).check()

    logger.info("All checks passed!")
    yield
    logger.info("Shutting down...")


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
