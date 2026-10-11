import pytest
from fastapi import status
from httpx import AsyncClient

from tests.conftest import UserCredentials
from tests.storage.helpers import (
    TestUpload,
    delete_resource,
    upload_resources,
)


@pytest.mark.asyncio
async def test_delete_existing_file(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    upload = TestUpload(
        filename="file-to-delete.txt",
        content=b"file content",
        content_type="text/plain",
    )

    upload_response = await upload_resources(
        client,
        [upload],
    )

    assert upload_response.status_code == status.HTTP_201_CREATED

    delete_response = await delete_resource(
        client,
        path="/file-to-delete.txt",
    )

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert delete_response.content == b""

    repeated_delete_response = await delete_resource(
        client,
        path="/file-to-delete.txt",
    )

    assert repeated_delete_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_missing_file(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    response = await delete_resource(
        client,
        path="/missing-file.txt",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_existing_directory_recursively(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    uploads = [
        TestUpload(
            filename="directory-to-delete/root.txt",
            content=b"root content",
            content_type="text/plain",
        ),
        TestUpload(
            filename="directory-to-delete/nested/first.txt",
            content=b"first content",
            content_type="text/plain",
        ),
        TestUpload(
            filename="directory-to-delete/nested/deep/second.txt",
            content=b"second content",
            content_type="text/plain",
        ),
    ]

    upload_response = await upload_resources(client, uploads)
    assert upload_response.status_code == status.HTTP_201_CREATED

    delete_response = await delete_resource(client, path="/directory-to-delete/")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert delete_response.content == b""

    deleted_paths = [
        "/directory-to-delete/",
        "/directory-to-delete/root.txt",
        "/directory-to-delete/nested/first.txt",
        "/directory-to-delete/nested/deep/second.txt",
    ]

    for path in deleted_paths:
        repeated_file_delete = await delete_resource(client, path=path)
        assert repeated_file_delete.status_code == status.HTTP_404_NOT_FOUND, path


@pytest.mark.asyncio
async def test_delete_missing_directory(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    response = await delete_resource(
        client,
        path="/missing-directory/",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "path",
    [
        "/folder//file.txt",
        "/folder/../file.txt",
        "/folder/./file.txt",
        r"/folder\file.txt",
    ],
)
@pytest.mark.asyncio
async def test_delete_with_invalid_path(
    client: AsyncClient,
    registered_user: UserCredentials,
    path: str,
) -> None:
    response = await delete_resource(
        client,
        path=path,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
