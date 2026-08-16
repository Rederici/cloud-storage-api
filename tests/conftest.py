import secrets
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config as AlembicConfig
from asgi_lifespan import LifespanManager
from dishka import AsyncContainer, Scope
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from testcontainers.minio import MinioContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from src.auth.schemas import CredentialsRequest
from src.bootstrap import create_app, create_container
from src.core.config import Config, Env, MinioConfig, PostgresConfig, RedisConfig
from tests.dependencies import TestInfrastructureProvider


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer]:
    with PostgresContainer() as container:
        yield container


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer]:
    with RedisContainer() as container:
        yield container


@pytest.fixture(scope="session")
def minio_container() -> Generator[MinioContainer]:
    with MinioContainer() as container:
        yield container


@pytest.fixture(scope="session")
def config(
    postgres_container: PostgresContainer,
    redis_container: RedisContainer,
    minio_container: MinioContainer,
) -> Config:
    return Config(
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


@pytest.fixture(scope="session", autouse=True)
def apply_migrations(config: Config) -> None:
    alembic_cfg = AlembicConfig("alembic.ini")
    alembic_cfg.attributes["sqlalchemy_url"] = config.postgres.get_dsn(sync=True)
    command.upgrade(alembic_cfg, "head")


@pytest_asyncio.fixture(scope="session")
async def di_container(config: Config) -> AsyncGenerator[AsyncContainer]:
    container = create_container(
        TestInfrastructureProvider(),
        context={Config: config},
    )
    yield container
    await container.close()


@pytest_asyncio.fixture
async def app(config: Config, di_container: AsyncContainer) -> AsyncGenerator[FastAPI]:
    async with di_container(scope=Scope.SESSION) as session_container:
        yield create_app(
            container=session_container,
            config=config,
        )


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with (
        LifespanManager(app),
        AsyncClient(
            transport=ASGITransport(
                app=app,
                raise_app_exceptions=True,
            ),
            base_url="http://test",
        ) as client,
    ):
        yield client


@pytest.fixture
def user() -> CredentialsRequest:
    return CredentialsRequest(
        username=f"user_{secrets.token_hex(4)}",
        password=f"{secrets.token_hex(6)}_@2Aa{secrets.token_hex(6).upper()}",
    )


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient, user: CredentialsRequest) -> CredentialsRequest:
    resp = await client.post("/api/v1/auth/sign-up", json=user.model_dump())
    assert resp.status_code == 201
    return user
