import pickle
from typing import Any

from redis.asyncio import Redis

from src.config import settings


class RedisManager:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.redis_obj: Redis | None = None

    async def connect(self) -> Redis:
        self.redis_obj = Redis(host=self.host, port=self.port)
        await self.redis_obj.ping()  # type: ignore
        return self.redis_obj

    @property
    def redis(self) -> Redis:
        if not self.redis_obj:
            raise RuntimeError("Redis not connected")
        return self.redis_obj

    async def set(self, key: Any, value: Any, ex: int | None = 120):
        if not self.redis_obj:
            raise RuntimeError("Redis not connected")
        b_key, b_value = pickle.dumps(key), pickle.dumps(value)
        await self.redis_obj.set(name=b_key, value=b_value, ex=ex)

    async def get(self, key: Any):
        if not self.redis_obj:
            raise RuntimeError("Redis not connected")
        b_key = pickle.dumps(key)
        b_value = await self.redis_obj.get(name=b_key)
        return pickle.loads(b_value)

    async def close(self):
        if self.redis_obj:
            await self.redis_obj.close()


redis_manager = RedisManager(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
)
