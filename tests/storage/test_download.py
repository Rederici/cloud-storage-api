from io import BytesIO
from zipfile import ZipFile

import pytest
from fastapi import status
from httpx import AsyncClient

from cloud_storage.auth.http.schemas import CredentialsRequest
from tests.storage.helpers import TestUpload, download_resource, upload_resources


@pytest.mark.asyncio
async def test_download_existing_file(
    client: AsyncClient,
    registered_user: CredentialsRequest,
) -> None:
    upload = TestUpload(
        filename="file.txt",
        content=b"file content",
        content_type="text/plain",
    )

    upload_response = await upload_resources(client, [upload])
    assert upload_response.status_code == status.HTTP_201_CREATED

    response = await download_resource(client, path="/file.txt")

    assert response.status_code == status.HTTP_200_OK
    assert response.content == upload.content
    assert response.headers["content-type"] == "application/octet-stream"


@pytest.mark.asyncio
async def test_download_missing_file(
    client: AsyncClient,
    registered_user: CredentialsRequest,
) -> None:
    response = await download_resource(
        client,
        path="/missing.txt",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_download_existing_directory(
    client: AsyncClient,
    registered_user: CredentialsRequest,
):
    uploads = [
        TestUpload(
            filename="2025/photo.jpg",
            content=b"photo",
        ),
        TestUpload(
            filename="2025/trips/paris.jpg",
            content=b"paris",
        ),
        TestUpload(
            filename="2024/old.jpg",
            content=b"old",
        ),
    ]

    response = await upload_resources(client, uploads)

    assert response.status_code == status.HTTP_201_CREATED

    response = await download_resource(client, path="/2025/")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/zip"

    with ZipFile(BytesIO(response.content)) as archive:
        assert set(archive.namelist()) == {
            "2025/photo.jpg",
            "2025/trips/",
            "2025/trips/paris.jpg",
        }

        assert archive.read("2025/photo.jpg") == b"photo"
        assert archive.read("2025/trips/paris.jpg") == b"paris"
        assert "2024/old.jpg" not in archive.namelist()
