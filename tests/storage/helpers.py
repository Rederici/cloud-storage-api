from dataclasses import dataclass

from httpx import AsyncClient, Response

CONTEXT = "/api/v1"
DIRECTORY_URL = f"{CONTEXT}/directory"
RESOURCES_URL = f"{CONTEXT}/resources"
MOVE_URL = f"{RESOURCES_URL}/move"
DOWNLOAD_URL = f"{RESOURCES_URL}/download"


@dataclass(frozen=True, slots=True)
class TestUpload:
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"

    def as_multipart(self) -> tuple[str, tuple[str, bytes, str]]:
        return (
            "files",
            (
                self.filename,
                self.content,
                self.content_type,
            ),
        )


async def create_directory(
    client: AsyncClient,
    path: str,
) -> Response:
    return await client.post(
        DIRECTORY_URL,
        params={"path": path},
    )


async def upload_resources(
    client: AsyncClient,
    uploads: list[TestUpload],
    *,
    path: str = "/",
) -> Response:
    return await client.post(
        RESOURCES_URL,
        params={"path": path},
        files=[upload.as_multipart() for upload in uploads],
    )


async def delete_resource(
    client: AsyncClient,
    *,
    path: str,
):
    return await client.delete(
        RESOURCES_URL,
        params={"path": path},
    )


async def move_resource(
    client: AsyncClient,
    *,
    source: str,
    destination: str,
):
    return await client.post(
        MOVE_URL,
        params={
            "from": source,
            "to": destination,
        },
    )


async def download_resource(
    client: AsyncClient,
    *,
    path: str,
):
    return await client.get(
        DOWNLOAD_URL,
        params={"path": path},
    )
