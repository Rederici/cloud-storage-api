import pytest
from httpx import AsyncClient

from src.auth.schemas import CredentialsRequest
from tests.helpers import get_response_error
from tests.storage.helpers import create_directory, unique_name


async def test_create_directory_in_root(
    client: AsyncClient,
    registered_user: CredentialsRequest,
) -> None:
    path = f"/{unique_name()}/"

    response = await create_directory(client, path)

    assert response.status_code == 201, get_response_error(response=response)


async def test_create_nested_directories_sequentially(
    client: AsyncClient,
    registered_user: CredentialsRequest,
) -> None:
    parent = unique_name("parent")
    child = unique_name("child")
    nested = unique_name("nested")

    parent_response = await create_directory(client, f"/{parent}/")
    child_response = await create_directory(client, f"/{parent}/{child}/")
    nested_response = await create_directory(client, f"/{parent}/{child}/{nested}/")

    assert parent_response.status_code == 201, get_response_error(response=parent_response)
    assert child_response.status_code == 201, get_response_error(response=child_response)
    assert nested_response.status_code == 201, get_response_error(response=nested_response)


async def test_cannot_create_directory_when_parent_does_not_exist(
    client: AsyncClient,
    registered_user: CredentialsRequest,
) -> None:
    missing_parent = unique_name("missing-parent")
    child = unique_name("child")

    response = await create_directory(
        client,
        f"/{missing_parent}/{child}/",
    )

    assert response.status_code == 404, get_response_error(response=response)


async def test_cannot_create_existing_directory(
    client: AsyncClient,
    registered_user: CredentialsRequest,
) -> None:
    path = f"/{unique_name()}/"

    first_response = await create_directory(client, path)
    second_response = await create_directory(client, path)

    assert first_response.status_code == 201, first_response.json().get("message", "No error message")
    assert second_response.status_code == 409, second_response.json().get("message", "No error message")


@pytest.mark.parametrize(
    "path",
    [
        "directory/",
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
        "without-leading-slash",
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

    assert response.status_code == 422, get_response_error(response=response)
