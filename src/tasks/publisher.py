import json
import logging

import pika
from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel

from src.config import settings
from src.schemas.base import DateTimeEncoder
from src.utils.rmq_manager import RMQManager

logger = logging.getLogger("src.tasks.rabbitmq.publisher")


class RMQPublisher(RMQManager):
    def __init__(self):
        super().__init__()
        self._queue_declared = False
        self.connection: BlockingConnection | None = None  # pyright: ignore
        self.channel: BlockingConnection | None = None  # pyright: ignore

    def connect(self) -> None:
        if self.connection and not self.connection.is_closed:
            return
        self.connection = self.get_connection()
        self.channel = self.connection.channel()
        self._queue_declared = False

    def close(self) -> None:
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        self.connection: BlockingConnection | None = None  # pyright: ignore
        self.channel: BlockingConnection | None = None  # pyright: ignore
        self._queue_declared = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _ensure_queue(self) -> None:
        if self._queue_declared:
            return
        if not self.channel:
            raise RuntimeError(
                "RabbitMQ channel is not initialized."
            )
        self.channel.queue_declare(
            queue=settings.TELEGRAM_NEWS_QUEUE, durable=True
        )
        self._queue_declared = True

    def publish(self, message: dict):
        try:
            self.connect()
            self.connection: BlockingConnection
            self.channel: BlockingChannel
            self._ensure_queue()
            self.channel.basic_publish(
                exchange="",
                routing_key=settings.TELEGRAM_NEWS_QUEUE,
                body=json.dumps(
                    message, cls=DateTimeEncoder, ensure_ascii=False
                ),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )

            logger.debug(
                "Published news to queue: subscription_id=%s, news_id=%s",
                message.get("subscription_id"),
                message.get("news", {}).get("id"),
            )

        except Exception as exc:
            logger.error("Error publishing to queue: %s", exc)
            raise

    def publish_many(self, messages: list[dict]) -> int:
        if not messages:
            return 0

        published = 0
        for message in messages:
            self.publish(message)
            published += 1
        return published
