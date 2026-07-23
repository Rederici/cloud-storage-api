from collections.abc import AsyncGenerator

import aioboto3
from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from types_aiobotocore_s3.client import S3Client

from .config import Config


class InfrastructureProvider(Provider):
    @provide(scope=Scope.APP)
    def config(self) -> Config:
        return Config()

    @provide(scope=Scope.APP)
    async def async_redis_client(self, config: Config) -> AsyncGenerator[Redis]:
        client = Redis.from_url(config.redis.get_dsn())
        try:
            yield client
        finally:
            await client.aclose()

    @provide(scope=Scope.APP)
    def s3_session(self) -> aioboto3.Session:
        return aioboto3.Session()

    @provide(scope=Scope.APP)
    async def s3_client(self, config: Config, session: aioboto3.Session) -> AsyncGenerator[S3Client]:
        async with session.client(
            "s3",
            endpoint_url=config.minio.url,
            aws_access_key_id=config.minio.access_key_id,
            aws_secret_access_key=config.minio.secret_access_key,
        ) as client:
            yield client

    @provide(scope=Scope.APP)
    async def async_engine(self, config: Config) -> AsyncGenerator[AsyncEngine]:
        engine = create_async_engine(config.postgres.get_dsn(sync=False))
        try:
            yield engine
        finally:
            await engine.dispose()

    @provide(scope=Scope.APP)
    def async_session_maker(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(bind=engine)

    @provide(scope=Scope.REQUEST)
    async def async_session(self, session_maker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession]:
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
