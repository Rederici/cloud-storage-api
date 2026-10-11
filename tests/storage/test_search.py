import pytest
from httpx import AsyncClient

from tests.conftest import UserCredentials
from tests.storage.helpers import SEARCH, create_directory, search_resources


@pytest.mark.asyncio
async def test_search_resources(
    client: AsyncClient,
    registered_user: UserCredentials,
):
    await create_directory(client, "/documents/")

    response = await search_resources(client, query="documents")

    assert response.status_code == 200
    assert response.json() == [
        {
            "path": "/",
            "size": 0,
            "name": "documents",
            "type": "directory",
        },
    ]


@pytest.mark.asyncio
async def test_search_resources_returns_empty_list(
    client: AsyncClient,
    registered_user: UserCredentials,
):
    response = await search_resources(client, query="not-found")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_search_resources_requires_query(
    client: AsyncClient,
    registered_user: UserCredentials,
):
    response = await client.get(SEARCH)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search_resources_rejects_empty_query(
    client: AsyncClient,
    registered_user: UserCredentials,
):
    response = await search_resources(client, query="")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_search_resources_requires_authentication(
    client: AsyncClient,
):
    response = await search_resources(client, query="documents")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_resources_url_encoded_query(
    client: AsyncClient,
    registered_user: UserCredentials,
):
    await create_directory(client, "/my documents/")

    response = await search_resources(client, query="my documents")
    assert response.status_code == 200
    assert response.json() == [
        {
            "path": "/",
            "size": 0,
            "name": "my documents",
            "type": "directory",
        },
    ]
