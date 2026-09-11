import pytest_asyncio

from src.auth.schemas import CredentialsRequest


@pytest_asyncio.fixture(autouse=True)
async def registered_user(registered_user: CredentialsRequest) -> None:
    pass
