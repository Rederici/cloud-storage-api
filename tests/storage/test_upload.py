import pytest
from fastapi import status
from httpx import AsyncClient

from tests.conftest import UserCredentials
from tests.context import RESOURCES
from tests.storage.helpers import TestUpload, upload_resources


@pytest.mark.asyncio
async def test_upload_file_to_root(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    upload = TestUpload(
        filename="file.txt",
        content=b"file content",
        content_type="text/plain",
    )
    response = await upload_resources(client, [upload])

    assert response.status_code == status.HTTP_201_CREATED, response.json()
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == [
        {
            "path": "/",
            "name": "file.txt",
            "size": len(upload.content),
            "type": "file",
        },
    ]


@pytest.mark.asyncio
async def test_upload_file_to_existing_directory(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    seed = TestUpload(
        filename="documents/seed.txt",
        content=b"seed",
        content_type="text/plain",
    )

    seed_response = await upload_resources(client, [seed], path="/")

    assert seed_response.status_code == status.HTTP_201_CREATED

    upload = TestUpload(
        filename="file.txt",
        content=b"file content",
        content_type="text/plain",
    )

    response = await upload_resources(
        client,
        [upload],
        path="/documents/",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == [
        {
            "path": "/documents/",
            "name": "file.txt",
            "size": len(upload.content),
            "type": "file",
        },
    ]


@pytest.mark.asyncio
async def test_upload_file_with_nested_filename(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    upload = TestUpload(
        filename="documents/reports/2026/report.txt",
        content=b"report content",
        content_type="text/plain",
    )

    response = await upload_resources(
        client,
        [upload],
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == [
        {
            "path": "/documents/reports/2026/",
            "name": "report.txt",
            "size": len(upload.content),
            "type": "file",
        },
    ]


@pytest.mark.asyncio
async def test_upload_multiple_files(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    uploads = [
        TestUpload(
            filename="first.txt",
            content=b"first content",
            content_type="text/plain",
        ),
        TestUpload(
            filename="second.txt",
            content=b"second content",
            content_type="text/plain",
        ),
        TestUpload(
            filename="third.bin",
            content=b"\x00\x01\x02\xff",
        ),
    ]

    response = await upload_resources(
        client,
        uploads,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == [
        {
            "path": "/",
            "name": "first.txt",
            "size": len(uploads[0].content),
            "type": "file",
        },
        {
            "path": "/",
            "name": "second.txt",
            "size": len(uploads[1].content),
            "type": "file",
        },
        {
            "path": "/",
            "name": "third.bin",
            "size": len(uploads[2].content),
            "type": "file",
        },
    ]


@pytest.mark.asyncio
async def test_upload_directory_tree(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    uploads = [
        TestUpload(
            filename="documents/readme.txt",
            content=b"readme",
            content_type="text/plain",
        ),
        TestUpload(
            filename="documents/images/first.png",
            content=b"first image",
            content_type="image/png",
        ),
        TestUpload(
            filename="documents/images/nested/second.png",
            content=b"second image",
            content_type="image/png",
        ),
        TestUpload(
            filename="documents/reports/2026/report.pdf",
            content=b"%PDF-1.7 test",
            content_type="application/pdf",
        ),
    ]

    response = await upload_resources(
        client,
        uploads,
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == [
        {
            "path": "/documents/",
            "name": "readme.txt",
            "size": len(uploads[0].content),
            "type": "file",
        },
        {
            "path": "/documents/images/",
            "name": "first.png",
            "size": len(uploads[1].content),
            "type": "file",
        },
        {
            "path": "/documents/images/nested/",
            "name": "second.png",
            "size": len(uploads[2].content),
            "type": "file",
        },
        {
            "path": "/documents/reports/2026/",
            "name": "report.pdf",
            "size": len(uploads[3].content),
            "type": "file",
        },
    ]


@pytest.mark.asyncio
async def test_upload_empty_file(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    upload = TestUpload(
        filename="empty.txt",
        content=b"",
        content_type="text/plain",
    )

    response = await upload_resources(
        client,
        [upload],
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == [
        {
            "path": "/",
            "name": "empty.txt",
            "size": 0,
            "type": "file",
        },
    ]


@pytest.mark.asyncio
async def test_upload_preserves_input_order(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    uploads = [
        TestUpload(
            filename="third.txt",
            content=b"third",
        ),
        TestUpload(
            filename="first.txt",
            content=b"first",
        ),
        TestUpload(
            filename="nested/second.txt",
            content=b"second",
        ),
    ]

    response = await upload_resources(
        client,
        uploads,
    )

    assert response.status_code == status.HTTP_201_CREATED

    resources = response.json()

    assert [(resource["path"], resource["name"]) for resource in resources] == [
        ("/", "third.txt"),
        ("/", "first.txt"),
        ("/nested/", "second.txt"),
    ]


@pytest.mark.asyncio
async def test_upload_existing_file_returns_conflict(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    original = TestUpload(
        filename="file.txt",
        content=b"original content",
        content_type="text/plain",
    )

    first_response = await upload_resources(client, [original])
    assert first_response.status_code == status.HTTP_201_CREATED

    replacement = TestUpload(
        filename="file.txt",
        content=b"replacement content",
        content_type="text/plain",
    )

    second_response = await upload_resources(client, [replacement])
    assert second_response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_upload_is_atomic_when_file_exists(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    existing = TestUpload(filename="existing.txt", content=b"existing content")
    initial_response = await upload_resources(client, [existing])
    assert initial_response.status_code == status.HTTP_201_CREATED

    new_file = TestUpload(filename="new.txt", content=b"new content")
    conflicting_file = TestUpload(filename="existing.txt", content=b"replacement content")

    conflict_response = await upload_resources(client, [new_file, conflicting_file])
    assert conflict_response.status_code == status.HTTP_409_CONFLICT

    # If the request was atomic, new.txt  haven't been loaded,
    # so the separate load should complete successfully.
    retry_response = await upload_resources(client, [new_file])
    assert retry_response.status_code == status.HTTP_201_CREATED


@pytest.mark.asyncio
async def test_upload_duplicate_filenames_returns_conflict(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    uploads = [
        TestUpload(
            filename="duplicate.txt",
            content=b"first content",
        ),
        TestUpload(
            filename="duplicate.txt",
            content=b"second content",
        ),
    ]

    response = await upload_resources(client, uploads)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_to_missing_parent_returns_not_found(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    upload = TestUpload(filename="file.txt", content=b"content")
    response = await upload_resources(client, [upload], path="/missing/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "path",
    [
        "/missing-trailing-slash",
        "/folder//nested/",
        "/folder/../nested/",
        "/folder/./nested/",
        r"/folder\other/",
    ],
)
@pytest.mark.asyncio
async def test_upload_with_invalid_parent_path_returns_unprocessable_entity(
    client: AsyncClient,
    registered_user: UserCredentials,
    path: str,
) -> None:
    upload = TestUpload(filename="file.txt", content=b"content")
    response = await upload_resources(client, [upload], path=path)
    assert response.status_code == 400


@pytest.mark.parametrize(
    "filename",
    [
        "../file.txt",
        "folder/../../file.txt",
        "folder/./file.txt",
        "folder//file.txt",
        r"folder\file.txt",
        "/absolute/file.txt",
        "",
    ],
)
@pytest.mark.asyncio
async def test_upload_with_invalid_filename_returns_unprocessable_entity(
    client: AsyncClient,
    registered_user: UserCredentials,
    filename: str,
) -> None:
    upload = TestUpload(filename=filename, content=b"content")
    response = await upload_resources(client, [upload])
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_without_files_returns_unprocessable_entity(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    response = await client.post(RESOURCES)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_with_wrong_multipart_field_returns_unprocessable_entity(
    client: AsyncClient,
    registered_user: UserCredentials,
) -> None:
    response = await client.post(
        RESOURCES,
        files=[
            (
                "file",
                (
                    "file.txt",
                    b"content",
                    "text/plain",
                ),
            ),
        ],
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_without_authentication_returns_unauthorized(
    client: AsyncClient,
) -> None:
    upload = TestUpload(filename="file.txt", content=b"content")
    response = await upload_resources(client, [upload])
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
