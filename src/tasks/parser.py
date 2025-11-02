import asyncio
import logging
import feedparser
from datetime import datetime, timezone

from src.schemas.news import ParsedNewsDTO
from src.tasks.app import celery_app
from src.tasks.processor import process_news
from src.utils.db_tools import DBManager
from src.db import sessionmaker_null_pool

logger = logging.getLogger("src.tasks.parser")


@celery_app.task(name="parse_rss")
def parse_rss():
    asyncio.run(parse_rss_feeds())


def get_image_from_links(links: list[dict[str, str]]):
    for link in links:
        if "image" in link.get("type", "").casefold():
            return link.get("href", None)


def parse_date(date: str) -> datetime:
    return (
        datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %z")
        .astimezone(timezone.utc)
        .replace(tzinfo=None)
    )


def parse_text(item: feedparser.FeedParserDict, key: str):
    raw = item.get(key)
    text = (raw.strip() if raw else "") or "Отсутствует"
    return text


async def parse_rss_feeds():
    logging.info("Started parsing...")
    async with DBManager(session_factory=sessionmaker_null_pool) as db:
        channels = await db.channels.get_all()

    for channel in channels:
        logger.info("Feed %s", channel.link)
        feed = feedparser.parse(channel.link)
        source_name = feed.feed.get("title", "Неизвестный источник")
        logger.info("Source: %s", source_name)
        logger.info("News quantity: %s", len(feed.entries))

        result = []
        for entry in feed.entries:
            result.append(
                ParsedNewsDTO(
                    image=get_image_from_links(entry.get("links", [])),
                    title=parse_text(entry, "title"),
                    link=parse_text(entry, "link"),
                    summary=parse_text(entry, "summary"),
                    source=source_name,
                    published=parse_date(entry.get("published")),
                    channel_id=channel.id,
                )
            )
            logging.info(f"Sent to queue: %s", entry.get("title", "Без заголовка")[:60])

        if result:
            process_news.delay([obj.model_dump() for obj in result])
