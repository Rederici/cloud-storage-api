from dataclasses import dataclass

from httpx import AsyncClient, Response

DIRECTORY_URL = "/api/v1/directory"


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
    return await client.post(DIRECTORY_URL, params={"path": path})


async def upload_resources(
    client: AsyncClient,
    uploads: list[TestUpload],
    *,
    path: str = "/",
) -> Response:
    params = {}

    if path is not None:
        params["path"] = path

    return await client.post(
        "/api/v1/resources",
        params=params,
        files=[upload.as_multipart() for upload in uploads],
    )


async def delete_resource(
    client: AsyncClient,
    *,
    path: str,
):
    return await client.delete(
        "/api/v1/resources",
        params={"path": path},
    )
