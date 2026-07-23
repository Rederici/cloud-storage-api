from uuid import uuid4

from httpx import AsyncClient, Response

DIRECTORY_URL = "/api/v1/directory"


async def create_directory(
    client: AsyncClient,
    path: str,
) -> Response:
    return await client.post(DIRECTORY_URL, params={"path": path})


def unique_name(prefix: str = "directory") -> str:
    return f"{prefix}-{uuid4().hex}"
