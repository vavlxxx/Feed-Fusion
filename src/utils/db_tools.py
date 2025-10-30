import logging
from typing import Self

from sqlalchemy import inspect, Connection
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.models.base import Base
from src.utils.exceptions import MissingTablesError


logger = logging.getLogger(__name__)


class DBManager:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self.session_factory = session_factory

    async def __aenter__(self) -> Self:
        self.session: AsyncSession = self.session_factory()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


class DBHealthChecker:

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def check(self):
        async with self.engine.begin() as conn:
            is_exists, missing = await conn.run_sync(self._check_tables_existence)
            if not is_exists:
                raise MissingTablesError(detail=missing)

    def _check_tables_existence(self, conn: Connection) -> tuple[bool, set[str]]:
        inspector = inspect(conn)
        existing_tables = set(inspector.get_table_names())
        expected_tables = set(Base.metadata.tables.keys())

        missing_tables = expected_tables - existing_tables
        extra_tables = existing_tables - expected_tables

        logger.info("Checking tables...")
        for table in expected_tables:
            if table not in existing_tables:
                logger.error("(-) Table '%s' is missing", table)
                continue
            logger.info("(+) Table '%s' is present", table)

        if extra_tables:
            logger.info("Extra tables: %s", ", ".join(map(repr, extra_tables)))

        return len(missing_tables) == 0, missing_tables
