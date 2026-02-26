import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import cast

import feedparser
from celery import Task
from dateutil import parser as date_parser

from src.config import settings
from src.db import sessionmaker_null_pool
from src.schemas.news import ParsedNewsDTO
from src.tasks.app import celery_app
from src.tasks.processor import process_news
from src.utils.db_tools import DBManager

logger = logging.getLogger("src.tasks.parser")


@celery_app.task(name="parse_rss")
def parse_rss():
    asyncio.run(parse_rss_feeds())


def get_image_from_links(links: list[dict[str, str]]):
    for link in links:
        if "image" in link.get("type", "").casefold():
            return link.get("href", None)


def parse_date(date: str) -> datetime | None:
    try:
        dt = date_parser.parse(date)
        # Конвертируем в UTC и удаляем tzinfo
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except (ValueError, TypeError) as e:
        logger.warning("Failed to parse date '%s': %s", date, e)
        return None


def parse_text(item: feedparser.FeedParserDict, key: str):
    raw = item.get(key)
    text = (raw.strip() if isinstance(raw, str) else "") or settings.EMPTY_TEXT
    return text


async def parse_rss_feeds():
    logging.info("Started parsing...")
    async with DBManager(session_factory=sessionmaker_null_pool) as db:
        channels = await db.channels.get_all()

    for channel in channels:
        logger.info("Feed %s", channel.link)
        feed: feedparser.FeedParserDict = feedparser.parse(channel.link)
        source_name = feed.feed.get("title", settings.EMPTY_TEXT)  # type: ignore
        logger.info("Source: %s", source_name)
        logger.info("News quantity: %s", len(feed.entries))

        result = []
        entries = feed.entries
        for idx, entry in enumerate(entries, 1):
            link: str = parse_text(entry, "link")
            title: str = parse_text(entry, "title")

            published: datetime | None = parse_date(entry.get("published"))  # type: ignore
            if not published:
                logger.error(
                    "#%s News (%s) has no published date, skipping...", idx, link
                )
                continue
            if published < datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
                hours=settings.PREFERRED_HOURS_PERIOD
            ):
                logger.debug("#%s News (%s) too old, skipping...", idx, link)
                continue

            result.append(
                ParsedNewsDTO(
                    image=get_image_from_links(entry.get("links", [])),  # type: ignore
                    title=title,
                    link=link,
                    summary=parse_text(entry, "summary"),
                    source=source_name,
                    published=published,
                    channel_id=channel.id,
                )
            )
            logging.debug("#%s Sent to queue: %s", idx, title)

        if result:
            process_news_task = cast(Task, process_news)
            process_news_task.delay([obj.model_dump() for obj in result])
