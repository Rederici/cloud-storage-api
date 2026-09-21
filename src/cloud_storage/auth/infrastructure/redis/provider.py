from dishka import Provider, Scope, provide
from redis.asyncio import Redis

from cloud_storage.auth.ports import SessionRepository
from cloud_storage.config import Config

from .repository import RedisSessionRepository


class RedisSessionRepositoryProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def repository(self, redis: Redis, config: Config) -> SessionRepository:
        return RedisSessionRepository(
            redis_client=redis,
            ttl=config.app.session.ttl,
        )
