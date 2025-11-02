import asyncio
import logging
import feedparser
from datetime import datetime, timezone, timedelta

from src.schemas.news import ParsedNewsDTO
from src.tasks.app import celery_app
from src.tasks.processor import process_news
from src.utils.db_tools import DBManager
from src.db import sessionmaker_null_pool
from src.config import settings

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
    text = (raw.strip() if raw else "") or settings.EMPTY_TEXT
    return text


async def parse_rss_feeds():
    logging.info("Started parsing...")
    async with DBManager(session_factory=sessionmaker_null_pool) as db:
        channels = await db.channels.get_all()

    for channel in channels:
        logger.info("Feed %s", channel.link)
        feed = feedparser.parse(channel.link)
        source_name = feed.feed.get("title", settings.EMPTY_TEXT)
        logger.info("Source: %s", source_name)
        logger.info("News quantity: %s", len(feed.entries))

        result = []
        for idx, entry in enumerate(feed.entries, 1):
            published: datetime = parse_date(entry.get("published"))
            link: str = parse_text(entry, "link")
            title: str = parse_text(entry, "title")
            if published < datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
                hours=settings.PREFERED_HOURS_PERIOD
            ):
                logger.info("#%s News (%s) too old, skipping...", idx, link)
                continue

            result.append(
                ParsedNewsDTO(
                    image=get_image_from_links(entry.get("links", [])),
                    title=title,
                    link=link,
                    summary=parse_text(entry, "summary"),
                    source=source_name,
                    published=published,
                    channel_id=channel.id,
                )
            )
            logging.info(f"#%s Sent to queue: %s", idx, title)

        if result:
            process_news.delay([obj.model_dump() for obj in result])
