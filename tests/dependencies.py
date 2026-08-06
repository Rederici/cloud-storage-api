import os
from collections.abc import AsyncGenerator, Generator

from alembic import command
from alembic.config import Config as AlembicConfig
from dishka import Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from src.core import Config, InfrastructureProvider
from src.core.config import Env, MinioConfig, PostgresConfig, RedisConfig
from testcontainers.minio import MinioContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


class TestInfrastructureProvider(InfrastructureProvider):
    @provide(scope=Scope.APP)
    def postgres_container(self) -> Generator[PostgresContainer]:
        with PostgresContainer() as container:
            yield container

    @provide(scope=Scope.APP)
    def redis_container(self) -> Generator[RedisContainer]:
        with RedisContainer() as container:
            yield container

    @provide(scope=Scope.APP)
    def minio_container(self) -> Generator[MinioContainer]:
        with MinioContainer() as container:
            yield container

    @provide(scope=Scope.APP, override=True)
    def config(
        self,
        postgres_container: PostgresContainer,
        redis_container: RedisContainer,
        minio_container: MinioContainer,
    ) -> Config:
        config = Config(
            postgres=PostgresConfig(
                host=postgres_container.get_container_host_ip(),
                port=postgres_container.get_exposed_port(5432),
                username=postgres_container.username,
                password=postgres_container.password,
                database=postgres_container.dbname,
            ),
            redis=RedisConfig(
                host=redis_container.get_container_host_ip(),
                port=redis_container.get_exposed_port(6379),
                database=0,
            ),
            minio=MinioConfig(
                host=minio_container.get_container_host_ip(),
                port=minio_container.get_exposed_port(9000),
                access_key_id=minio_container.access_key,
                secret_access_key=minio_container.secret_key,
                bucket="test-bucket",
                ssl=False,
            ),
            env=Env.DEV,
        )

        self.migrate(config.postgres.get_dsn(sync=True))

        return config

    @staticmethod
    def migrate(dsn: str):
        os.environ["ALEMBIC_DATABASE_URL"] = dsn
        alembic_cfg = AlembicConfig("alembic.ini")
        command.upgrade(alembic_cfg, "head")

    @provide(scope=Scope.SESSION)
    async def async_connection(self, engine: AsyncEngine) -> AsyncGenerator[AsyncConnection]:
        async with engine.connect() as connection:
            trans = await connection.begin()
            try:
                yield connection
            finally:
                await trans.rollback()

    @provide(scope=Scope.SESSION, override=True)
    async def async_session_maker(self, connection: AsyncConnection) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
