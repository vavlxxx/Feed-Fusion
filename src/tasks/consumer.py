import json
import logging
import asyncio
import random
import sys

from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from pika import BlockingConnection
from pika.spec import BasicProperties, Basic
from pika.channel import Channel
from pika.adapters import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel

from src.schemas.news import NewsDTO
from src.bot.bot import bot
from src.config import settings
from src.utils.texts import format_message
from src.utils.rmq_manager import RMQManager

logger = logging.getLogger("src.tasks.telegram_consumer")


class RMQTelegramNewsConsumer(RMQManager):
    def __init__(self):
        super().__init__()
        self.loop = None

    def start(self):
        logger.info("Starting Telegram News Consumer...")

        try:
            self.loop = asyncio.new_event_loop()
            self.connection: BlockingConnection = self.get_connection()
            self.channel: BlockingChannel = self.connection.channel()
            self.channel.basic_qos(prefetch_count=1)

            self.channel.queue_declare(
                queue=settings.TELEGRAM_NEWS_QUEUE,
                durable=True,
            )
            self.channel.basic_consume(
                queue=settings.TELEGRAM_NEWS_QUEUE,
                on_message_callback=self.consume,
                auto_ack=False,
            )

            self.is_running = True
            logger.info("Consumer started. Waiting for messages...")
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
            self.stop()
        except Exception as e:
            logger.error("Consumer error: %s", e)
            self.stop()
            raise

    def stop(self):
        logger.info("Stopping consumer...")

        if self.channel and self.channel.is_open:
            self.channel.stop_consuming()

        if self.connection and not self.connection.is_closed:
            self.connection.close()

        if self.loop and not self.loop.is_closed():
            self.loop.close()

        logger.info("Consumer stopped")

    def consume(
        self,
        channel: Channel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ):
        delivery_tag = method.delivery_tag

        try:
            message = json.loads(body.decode("utf-8"))
            subscription_id = message["subscription_id"]
            telegram_id = message["telegram_id"]
            news_data = message["news"]
            channel_id = message["channel_id"]

            if isinstance(news_data.get("published"), str):
                news_data["published"] = self._parse_datetime(news_data["published"])
            if isinstance(news_data.get("created_at"), str):
                news_data["created_at"] = self._parse_datetime(news_data["created_at"])
            if isinstance(news_data.get("updated_at"), str):
                news_data["updated_at"] = self._parse_datetime(news_data["updated_at"])

            news = NewsDTO.model_validate(news_data)

            logger.info(
                "Processing message: subscription_id=%s, news_id=%s, telegram_id=%s",
                subscription_id,
                news.id,
                telegram_id,
            )

            success = self.loop.run_until_complete(
                self.send_news_to_telegram(telegram_id, news)
            )
            if success:
                channel.basic_ack(delivery_tag=delivery_tag)
                logger.info(
                    "Message ACKed: news_id=%s, subscription_id=%s",
                    news.id,
                    subscription_id,
                )
            else:
                channel.basic_nack(delivery_tag=delivery_tag, requeue=True)
                logger.warning(
                    "Message NACKed (requeued): news_id=%s, subscription_id=%s",
                    news.id,
                    subscription_id,
                )

        except json.JSONDecodeError as e:
            logger.error("Failed to parse message JSON: %s", e)
            channel.basic_nack(delivery_tag=delivery_tag, requeue=False)

        except Exception as e:
            logger.error("Error processing message: %s", e, exc_info=True)
            channel.basic_nack(delivery_tag=delivery_tag, requeue=True)

    @staticmethod
    def _parse_datetime(date_str: str) -> datetime:
        if not date_str:
            return datetime.now()

        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        logger.warning("Could not parse datetime: %s", date_str)
        return datetime.now()

    async def send_news_to_telegram(self, telegram_id: str, news: NewsDTO) -> bool:
        try:
            message = format_message(
                news.title,
                news.published,
                news.summary,
                news.link,
                news.source,
            )

            if news.image:
                await bot.send_photo(
                    chat_id=telegram_id,
                    photo=news.image,
                    caption=message,
                )
            else:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=message,
                )

            logger.info("Successfully sent news_id=%s to chat=%s", news.id, telegram_id)

            await asyncio.sleep(random.uniform(0.5, 1.5))
            return True

        except Exception as exc:
            logger.error(
                "Failed to send news_id=%s to chat=%s: %s",
                news.id,
                telegram_id,
                exc,
            )
            return False


if __name__ == "__main__":
    RMQTelegramNewsConsumer().start()
