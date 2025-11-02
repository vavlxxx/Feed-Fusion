import pika

from src.config import settings


class RMQManager:
    def __init__(self):
        self.connection = None
        self.channel = None

    def get_connection(self):
        params = pika.URLParameters(settings.rabbit_url)
        return pika.BlockingConnection(params)
