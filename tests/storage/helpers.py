from dataclasses import dataclass

from httpx import AsyncClient, Response

from tests.context import DIRECTORY, DOWNLOAD, MOVE, RESOURCES, SEARCH


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
        DIRECTORY,
        params={"path": path},
    )


async def upload_resources(
    client: AsyncClient,
    uploads: list[TestUpload],
    *,
    path: str = "/",
) -> Response:
    return await client.post(
        RESOURCES,
        params={"path": path},
        files=[upload.as_multipart() for upload in uploads],
    )


async def delete_resource(
    client: AsyncClient,
    *,
    path: str,
):
    return await client.delete(
        RESOURCES,
        params={"path": path},
    )


async def move_resource(
    client: AsyncClient,
    *,
    source: str,
    destination: str,
):
    return await client.post(
        MOVE,
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
        DOWNLOAD,
        params={"path": path},
    )


async def search_resources(
    client: AsyncClient,
    *,
    query: str,
):
    return await client.get(
        SEARCH,
        params={"query": query},
    )
