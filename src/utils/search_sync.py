import logging

from src.config import settings
from src.db import sessionmaker
from src.utils.db_tools import DBManager
from src.utils.es_manager import ESManager

logger = logging.getLogger("src.utils.search_sync")


async def sync_news_documents(
    documents: list[dict],
    *,
    refresh: bool = False,
) -> bool:
    if not ESManager.is_enabled() or not documents:
        return False

    try:
        async with ESManager(
            index_name=settings.ES_INDEX_NAME
        ) as es:
            await es.add(data=documents, refresh=refresh)
    except Exception as exc:
        ESManager.disable_runtime()
        logger.warning(
            "Search sync failed, PostgreSQL fallback remains active: %s",
            exc,
        )
        return False

    return True


async def rebuild_search_index(
    *,
    reset_index: bool = False,
) -> bool:
    if not ESManager.is_enabled():
        return False

    try:
        async with DBManager(session_factory=sessionmaker) as db:
            news_rows = await db.news.get_all()
        documents = [
            row.model_dump(mode="json") for row in news_rows
        ]

        async with ESManager(
            index_name=settings.ES_INDEX_NAME
        ) as es:
            if reset_index:
                await es.recreate_index()
            await es.add(data=documents, refresh=True)
    except Exception as exc:
        ESManager.disable_runtime()
        logger.warning(
            "Search bootstrap failed, PostgreSQL fallback remains active: %s",
            exc,
        )
        return False

    logger.info(
        "Search index synchronized with %d news items.",
        len(documents),
    )
    return True
