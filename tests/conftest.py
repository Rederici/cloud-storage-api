import secrets
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from dishka import AsyncContainer, Scope
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from src.auth.schemas import CredentialsRequest
from src.main import create_app, create_container
from tests.dependencies import TestInfrastructureProvider


@pytest_asyncio.fixture(scope="session")
async def di_container() -> AsyncGenerator[AsyncContainer]:
    container = create_container(TestInfrastructureProvider())
    yield container
    await container.close()


@pytest_asyncio.fixture
async def test_container(di_container: AsyncContainer) -> AsyncGenerator[AsyncContainer]:
    async with di_container(scope=Scope.SESSION) as session_container:
        yield session_container


@pytest_asyncio.fixture
async def app(test_container: AsyncContainer) -> FastAPI:
    return create_app(test_container)


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
