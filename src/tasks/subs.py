import asyncio
import logging

from src.config import settings
from src.db import sessionmaker_null_pool
from src.schemas.news import NewsDTO
from src.schemas.subscriptions import (
    SubscriptionUpdateDTO,
    SubscriptionWithUserDTO,
)
from src.tasks.app import celery_app
from src.tasks.publisher import RMQPublisher
from src.utils.db_tools import DBManager

logger = logging.getLogger("src.tasks.subs")


@celery_app.task(name="check_subs")
def check_subs() -> None:
    if not settings.ENABLE_SUBS_CHECK:
        logger.info(
            "Subscriptions check disabled. Skipping task."
        )
        return
    asyncio.run(collect_and_publish_news())


async def collect_and_publish_news():
    with RMQPublisher() as publisher:
        async with DBManager(
            session_factory=sessionmaker_null_pool
        ) as db:
            logger.info("Started checking subscriptions...")
            subs: list[
                SubscriptionWithUserDTO
            ] = await db.subs.get_all_with_user()

            total_published = 0

            for sub in subs:
                news_to_send: list[NewsDTO] = (
                    await db.news.get_recent(
                        channel_id=sub.channel_id,
                        gt=sub.last_news_id,
                    )
                )

                logger.info(
                    "Got %s recent news for subscription id=%s (user=%s, channel=%s)",
                    len(news_to_send),
                    sub.id,
                    sub.user.telegram_id,
                    sub.channel_id,
                )

                if news_to_send:
                    messages = [
                        {
                            "subscription_id": sub.id,
                            "telegram_id": sub.user.telegram_id,
                            "news": news_item.model_dump(
                                mode="json"
                            ),
                            "channel_id": sub.channel_id,
                        }
                        for news_item in news_to_send
                    ]
                    total_published += publisher.publish_many(
                        messages
                    )

                    await db.subs.edit(
                        data=SubscriptionUpdateDTO(
                            last_news_id=news_to_send[-1].id
                        ),  # type: ignore
                        id=sub.id,
                    )
                    await db.commit()
                    logger.info(
                        "Published %s news to queue for subscription id=%s",
                        len(news_to_send),
                        sub.id,
                    )

            logger.info(
                "Finished checking subscriptions. Total published: %s",
                total_published,
            )
