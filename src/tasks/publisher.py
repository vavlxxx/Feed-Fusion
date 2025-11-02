import json
import logging
import pika

from pika import BlockingConnection
from pika.adapters.blocking_connection import BlockingChannel

from src.schemas.base import DateTimeEncoder
from src.config import settings
from src.utils.rmq_manager import RMQManager

logger = logging.getLogger("src.tasks.rabbitmq.publisher")


class RMQPublisher(RMQManager):
    def publish(self, message: dict):
        connection = None
        try:
            self.connection: BlockingConnection = self.get_connection()
            self.channel: BlockingChannel = self.connection.channel()

            self.channel.queue_declare(queue=settings.TELEGRAM_NEWS_QUEUE, durable=True)
            self.channel.basic_publish(
                exchange="",
                routing_key=settings.TELEGRAM_NEWS_QUEUE,
                body=json.dumps(message, cls=DateTimeEncoder, ensure_ascii=False),
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
        finally:
            if connection and not connection.is_closed:
                connection.close()
