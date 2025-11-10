import asyncio
import hashlib
import logging

from src.utils.db_tools import DBManager
from src.tasks.app import celery_app
from src.schemas.news import AddNewsDTO, ParsedNewsDTO
from src.db import sessionmaker_null_pool
from src.utils.es_manager import ESManager
from src.config import settings


logger = logging.getLogger("src.tasks.processor")


@celery_app.task(name="process_news_item", bind=True, max_retries=3)
def process_news(self, news_items: list[dict]) -> None:
    logger.info("Started saving news into DB...")
    if not news_items:
        return
    news_items = [ParsedNewsDTO(**item) for item in news_items]
    asyncio.run(save_news(self, news_items))


async def save_news(self, news_items: list[ParsedNewsDTO]):
    news_with_hashes = [
        (item, hashlib.sha256(item.link.encode()).hexdigest()) for item in news_items
    ]
    all_hashes = [content_hash for _, content_hash in news_with_hashes]

    async with DBManager(session_factory=sessionmaker_null_pool) as db:
        existing_hashes = await db.news.get_hashes_by_hashes(all_hashes)
        unique_items = [
            (item, content_hash)
            for item, content_hash in news_with_hashes
            if content_hash not in existing_hashes
        ]
        logger.info(
            "Filtered news: %d new, %d duplicates",
            len(unique_items),
            len(existing_hashes),
        )
        if not unique_items:
            logger.info("No news to save, skipping...")
            return

        data = []
        for news_item, content_hash in unique_items:
            data.append(AddNewsDTO(**news_item.model_dump(), content_hash=content_hash))

        try:
            inserted_ids = await db.news.add_bulk_upsert(data)
            await db.commit()
            logger.info("Saved into DB: %s items", len(inserted_ids))
        except Exception as exc:
            retry_countdown = 60 * (2**self.request.retries)
            logger.info(
                "Error during processing news item: %s, retrying from %s sec...",
                exc,
                retry_countdown,
            )
            await db.rollback()
            raise self.retry(exc=exc, countdown=retry_countdown)

        logger.info("Started indexing news in Elasticsearch...")
        async with ESManager(index_name=settings.ES_INDEX_NAME) as es:
            data_dict: list[dict] = [obj.model_dump() for obj in data]
            await es.add(data=data_dict)
