import asyncio
import hashlib
import logging

from src.utils.db_tools import DBManager
from src.tasks.app import celery_app
from src.schemas.news import AddNewsDTO, ParsedNewsDTO
from src.db import sessionmaker_null_pool


logger = logging.getLogger("src.tasks.processor")


@celery_app.task(name="process_news_item", bind=True, max_retries=3)
def process_news(self, news_items: list[ParsedNewsDTO]) -> None:
    asyncio.run(save_news(self, news_items))


async def save_news(self, news_items: list[ParsedNewsDTO]):
    logger.info("Started saving news into DB...")
    async with DBManager(session_factory=sessionmaker_null_pool) as db:
        for news_item in news_items:
            content_hash: str = hashlib.sha256(news_item["link"].encode()).hexdigest()
            data = AddNewsDTO(**news_item, content_hash=content_hash)
            try:
                await db.news.add(data)
                await db.commit()
                logger.info("Saved into DB: %s", news_item["title"][:50])
            except Exception as exc:
                logger.info("Error during processing news item: %s", exc)
                raise self.retry(exc=exc, countdown=60 * (2**self.request.retries))
