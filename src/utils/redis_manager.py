import pickle
from typing import Any

from redis.asyncio import Redis

from src.config import settings


class RedisManager:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    async def connect(self) -> Redis:
        self._redis = Redis(host=self.host, port=self.port)
        await self._redis.ping()  # type: ignore
        return self._redis

    async def set(self, key: Any, value: Any, ex: int | None = 120):
        b_key, b_value = pickle.dumps(key), pickle.dumps(value)
        await self._redis.set(name=b_key, value=b_value, ex=ex)

    async def get(self, key: Any):
        b_key = pickle.dumps(key)
        b_value = await self._redis.get(name=b_key)
        return pickle.loads(b_value)

    async def close(self):
        if self._redis:
            await self._redis.close()


redis_manager = RedisManager(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
)
