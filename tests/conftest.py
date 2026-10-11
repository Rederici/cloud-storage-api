import secrets
import time
import urllib
import urllib.error
import urllib.request
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config as AlembicConfig
from asgi_lifespan import LifespanManager
from dishka import Scope
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from testcontainers.core.container import DockerContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from cloud_storage.app.bootstrap import Bootstrap
from cloud_storage.auth.http.schemas import CredentialsRequest
from cloud_storage.config.models import Config, Env, PostgresConfig, RedisConfig, RustfsConfig
from tests.context import SIGN_UP
from tests.dependencies import TestPostgresProvider


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer]:
    with PostgresContainer() as container:
        yield container


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer]:
    with RedisContainer() as container:
        yield container


@pytest.fixture(scope="session")
def rustfs_container() -> Generator[DockerContainer]:
    def _wait_for_rustfs(host: str, port: int, timeout: float = 30.0) -> None:
        deadline = time.monotonic() + timeout
        url = f"http://{host}:{port}/"
        while time.monotonic() < deadline:
            try:
                urllib.request.urlopen(url, timeout=1)
                return
            except urllib.error.HTTPError:
                return
            except urllib.error.URLError, ConnectionError, OSError:
                time.sleep(0.5)
        raise TimeoutError(f"RustFS not ready at {url} after {timeout}s")

    with (
        DockerContainer("rustfs/rustfs:latest")
        .with_env("RUSTFS_ACCESS_KEY", "rustfs")
        .with_env("RUSTFS_SECRET_KEY", "rustfs")
        .with_env("RUSTFS_VOLUMES", "/data")
        .with_exposed_ports(9000) as container
    ):
        _wait_for_rustfs(container.get_container_host_ip(), container.get_exposed_port(9000))
        yield container


@pytest.fixture(scope="session")
def config(
    postgres_container: PostgresContainer,
    redis_container: RedisContainer,
    rustfs_container: DockerContainer,
) -> Config:
    return Config(
        postgres=PostgresConfig(
            host=postgres_container.get_container_host_ip(),
            port=postgres_container.get_exposed_port(5432),
            username=postgres_container.username,
            password=SecretStr(postgres_container.password),
            database=postgres_container.dbname,
        ),
        redis=RedisConfig(
            host=redis_container.get_container_host_ip(),
            port=redis_container.get_exposed_port(6379),
            database=0,
        ),
        rustfs=RustfsConfig(
            host=rustfs_container.get_container_host_ip(),
            port=rustfs_container.get_exposed_port(9000),
            bucket="test-bucket",
            access_key=SecretStr("rustfs"),
            secret_key=SecretStr("rustfs"),
            ssl=False,
        ),
        env=Env.DEV,
    )


@pytest.fixture(scope="session", autouse=True)
def apply_migrations(config: Config) -> None:
    alembic_cfg = AlembicConfig("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", config.postgres.get_dsn(sync=True))
    command.upgrade(alembic_cfg, "head")


@pytest_asyncio.fixture(scope="session")
async def bootstrap(config: Config) -> AsyncGenerator[Bootstrap]:
    bootstrap = Bootstrap(TestPostgresProvider(), config=config)
    yield bootstrap
    await bootstrap.container.close()


@pytest_asyncio.fixture
async def app(bootstrap: Bootstrap) -> AsyncGenerator[FastAPI]:
    async with bootstrap.container(scope=Scope.SESSION) as session_container:
        yield bootstrap.create_app(container=session_container)


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with (
        LifespanManager(app),
        AsyncClient(
            transport=ASGITransport(
                app=app,
                raise_app_exceptions=True,
            ),
            base_url="http://x.test",
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
    resp = await client.post(SIGN_UP, json=user.model_dump())
    assert resp.status_code == 201
    return user
