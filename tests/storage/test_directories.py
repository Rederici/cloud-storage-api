import pytest
from httpx import AsyncClient

from src.auth.schemas import CredentialsRequest
from tests.storage.helpers import create_directory


async def test_create_directory_in_root(
    client: AsyncClient,
    registered_user: CredentialsRequest,
) -> None:
    response = await create_directory(client, path="/directory/")
    assert response.status_code == 201


async def test_create_nested_directories_sequentially(
    client: AsyncClient,
    registered_user: CredentialsRequest,
) -> None:
    parent_response = await create_directory(client, path="/parent/")
    assert parent_response.status_code == 201

    child_response = await create_directory(client, path="/parent/child/")
    assert child_response.status_code == 201

    nested_response = await create_directory(client, path="/parent/child/nested/")
    assert nested_response.status_code == 201


async def test_cannot_create_directory_when_parent_does_not_exist(
    client: AsyncClient,
    registered_user: CredentialsRequest,
) -> None:
    response = await create_directory(client, "/missing-parent/child/")
    assert response.status_code == 404


async def test_cannot_create_existing_directory(
    client: AsyncClient,
    registered_user: CredentialsRequest,
) -> None:
    path = "/directory/"

    first_response = await create_directory(client, path)
    assert first_response.status_code == 201

    second_response = await create_directory(client, path)
    assert second_response.status_code == 409


@pytest.mark.parametrize(
    "path",
    [
        "/directory",
        "directory",
        "/parent//child/",
        "//directory/",
        "/directory//",
        "/./",
        "/../",
        "/parent/./child/",
        "/parent/../child/",
    ],
    ids=[
        "without-trailing-slash",
        "without-slashes",
        "empty-middle-level",
        "empty-first-level",
        "empty-last-level",
        "dot-level",
        "double-dot-level",
        "dot-middle-level",
        "double-dot-middle-level",
    ],
)
async def test_reject_invalid_directory_path(
    client: AsyncClient,
    registered_user: CredentialsRequest,
    path: str,
) -> None:
    response = await create_directory(client, path)
    assert response.status_code == 400
