import pika

from src.config import settings


class RMQManager:
    def __init__(self):
        self.connection = None
        self.channel = None

    def get_connection(self):
        params = pika.URLParameters(settings.rabbit_url)
        params.heartbeat = 30
        params.blocked_connection_timeout = 30
        params.socket_timeout = 10
        params.connection_attempts = 5
        params.retry_delay = 2
        return pika.BlockingConnection(params)
