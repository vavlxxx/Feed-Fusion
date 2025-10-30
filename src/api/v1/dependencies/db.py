from typing import Annotated, Any, AsyncGenerator

from fastapi import Depends

from src.db import sessionmaker, sessionmaker_null_pool
from utils.db_tools import DBManager


async def get_db() -> AsyncGenerator[DBManager, Any]:
    async with DBManager(session_factory=sessionmaker) as db:
        yield db


async def get_db_with_null_pool() -> AsyncGenerator[DBManager, None]:
    async with DBManager(session_factory=sessionmaker_null_pool) as db:
        yield db


DBDep = Annotated[DBManager, Depends(get_db)]
