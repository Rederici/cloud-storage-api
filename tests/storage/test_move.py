import pytest
from httpx import AsyncClient

from cloud_storage.auth.schemas import CredentialsRequest
from tests.storage.helpers import (
    TestUpload,
    create_directory,
    move_resource,
    upload_resources,
)


@pytest.mark.asyncio
async def test_move_file(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    upload = TestUpload(filename="file.txt", content=b"hello")
    await upload_resources(client, [upload])
    await create_directory(client, "/folder/")

    response = await move_resource(
        client,
        source="/file.txt",
        destination="/folder/file.txt",
    )

    assert response.status_code == 200
    assert response.json() == {
        "path": "/folder/",
        "name": "file.txt",
        "size": len(upload.content),
        "type": "file",
    }


@pytest.mark.asyncio
async def test_rename_file(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    upload = TestUpload(filename="old.txt", content=b"hello")
    await upload_resources(client, [upload])

    response = await move_resource(
        client,
        source="/old.txt",
        destination="/new.txt",
    )

    assert response.status_code == 200
    assert response.json() == {
        "path": "/",
        "name": "new.txt",
        "size": len(upload.content),
        "type": "file",
    }


@pytest.mark.asyncio
async def test_move_and_rename_file(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    upload = TestUpload(filename="old.txt", content=b"hello")
    await upload_resources(client, [upload])
    await create_directory(client, "/folder/")

    response = await move_resource(
        client,
        source="/old.txt",
        destination="/folder/new.txt",
    )

    assert response.status_code == 200
    assert response.json() == {
        "path": "/folder/",
        "name": "new.txt",
        "size": len(upload.content),
        "type": "file",
    }


@pytest.mark.asyncio
async def test_move_directory(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    await create_directory(client, "/source/")
    await upload_resources(
        client,
        [TestUpload(filename="file.txt", content=b"hello")],
        path="/source/",
    )

    response = await move_resource(
        client,
        source="/source/",
        destination="/destination/",
    )

    assert response.status_code == 200
    assert response.json() == {
        "path": "/",
        "size": 0,
        "name": "destination",
        "type": "directory",
    }


@pytest.mark.asyncio
async def test_move_missing_resource(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    response = await move_resource(
        client,
        source="/missing.txt",
        destination="/new.txt",
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_move_to_existing_file(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    await upload_resources(
        client,
        [
            TestUpload(filename="source.txt", content=b"source"),
            TestUpload(filename="destination.txt", content=b"destination"),
        ],
    )

    response = await move_resource(
        client,
        source="/source.txt",
        destination="/destination.txt",
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_move_to_existing_directory(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    await create_directory(client, "/source/")
    await create_directory(client, "/destination/")

    response = await move_resource(
        client,
        source="/source/",
        destination="/destination/",
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_move_directory_into_itself(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    await create_directory(client, "/source/")

    response = await move_resource(
        client,
        source="/source/",
        destination="/source/nested/",
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_move_directory_into_nested_path(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    await create_directory(client, "/source/")

    response = await move_resource(
        client,
        source="/source/",
        destination="/source/a/b/c/",
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_move_file_to_child_path(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    await upload_resources(
        client,
        [TestUpload(filename="file.txt", content=b"hello")],
    )

    response = await move_resource(
        client,
        source="/file.txt",
        destination="/file.txt/child.txt",
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_move_to_path_with_file_parent(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    await upload_resources(
        client,
        [
            TestUpload(filename="parent.txt", content=b"parent"),
            TestUpload(filename="source.txt", content=b"source"),
        ],
    )

    response = await move_resource(
        client,
        source="/source.txt",
        destination="/parent.txt/child.txt",
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_move_file_to_directory_path(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    await upload_resources(
        client,
        [TestUpload(filename="file.txt", content=b"hello")],
    )
    await create_directory(client, "/folder/")

    response = await move_resource(
        client,
        source="/file.txt",
        destination="/folder/",
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_move_directory_to_file_path(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    await create_directory(client, "/source/")
    await upload_resources(
        client,
        [TestUpload(filename="file.txt", content=b"hello")],
    )

    response = await move_resource(
        client,
        source="/source/",
        destination="/file.txt",
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_move_root(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    response = await move_resource(
        client,
        source="/",
        destination="/new/",
    )

    assert response.status_code == 400
