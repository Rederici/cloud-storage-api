from collections.abc import AsyncGenerator

from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from src.config import Config


class RedisProvider(Provider):
    @provide(scope=Scope.APP)
    async def async_redis_client(self, config: Config) -> AsyncGenerator[Redis]:
        client = Redis.from_url(config.redis.get_dsn())
        try:
            yield client
        finally:
            await client.aclose()
