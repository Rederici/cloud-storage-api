from collections.abc import AsyncGenerator

from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from src.config import Config


class RedisProvider(Provider):
    @provide(scope=Scope.APP)
    async def async_redis_client(self, config: Config) -> AsyncGenerator[Redis]:
        client = Redis(
            host=config.redis.host,
            port=config.redis.port,
            username=config.redis.username,
            password=config.redis.password.get_secret_value() if config.redis.password else None,
            db=config.redis.database,
        )
        try:
            yield client
        finally:
            await client.aclose()
