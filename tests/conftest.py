from typing import AsyncGenerator

import pytest

from src.db import engine_null_pool
from src.api.v1.dependencies.db import get_db_with_null_pool
from src.config import settings
from utils.db_tools import DBManager
from src.models import *  # noqa: F403
from src.models.base import Base
from src.utils.db_tools import DBHealthChecker


@pytest.fixture()
async def db() -> AsyncGenerator[DBManager, None]:
    async for db in get_db_with_null_pool():
        yield db


@pytest.fixture(scope="module")
async def db_module() -> AsyncGenerator[DBManager, None]:
    async for db in get_db_with_null_pool():
        yield db


@pytest.fixture(scope="session", autouse=True)
async def check_test_mode() -> None:
    assert settings.MODE == "TEST"
    assert settings.DB_NAME == settings.TEST_DB_NAME


@pytest.fixture(scope="session", autouse=True)
async def main(check_test_mode) -> None:
    async with engine_null_pool.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    await DBHealthChecker(engine=engine_null_pool).check()
