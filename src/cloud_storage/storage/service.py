from collections.abc import AsyncIterable, AsyncIterator
from datetime import datetime
from stat import S_IFREG

from fastapi import UploadFile
from stream_zip import ZIP_64, Method, async_stream_zip

from .exceptions import (
    InvalidFileName,
    InvalidPath,
    ParentDirectoryDoesNotExist,
    ResourceAlreadyExists,
)
from .ports import StorageRepository
from .types import DownloadResult, ResourcePath, StoredResource, UserSpacePath


class StorageService:
    def __init__(self, storage_repo: StorageRepository):
        self._storage_repo = storage_repo

    async def _ensure_parent_exists(
        self,
        path: ResourcePath,
        *,
        user_id: int,
    ) -> UserSpacePath:
        """Build a user-scoped path and ensure its parent directory exists.

        Converts the public resource path into a path scoped to the specified
        user's storage namespace. Before returning the resulting path, verifies
        that its parent directory exists in storage.

        Args:
            user_id: ID of the user who owns the storage namespace.
            path: Public path of the resource being accessed or created.

        Returns:
            The resource path scoped to the specified user's storage namespace.

        Raises:
            ParentDirectoryDoesNotExist: If the parent directory of the resource
                does not exist in the user's storage namespace.
        """
        user_path = UserSpacePath(value=str(path), user_id=user_id)
        if not await self._storage_repo.exists(user_path.parent):
            raise ParentDirectoryDoesNotExist(resource=path)
        return user_path

    async def upload_files(
        self,
        files: list[UploadFile],
        *,
        path: ResourcePath,
        user_id: int,
    ) -> None:
        user_path = UserSpacePath(value=str(path), user_id=user_id)
        if not await self._storage_repo.exists(user_path):
            raise ParentDirectoryDoesNotExist(resource=path)

        final_paths = [user_path / file.filename for file in files]
        for p in final_paths:
            if not p.is_file:
                raise InvalidFileName(resource=p)

        for file in final_paths:
            if await self._storage_repo.exists(file):
                raise ResourceAlreadyExists(resource=file.public_path)

        created_dirs = set()
        for p in final_paths:
            if p not in created_dirs:
                await self._storage_repo.create_directory(p.parent, parents=True)
                created_dirs.add(p.parent)

        for file in files:
            await self._storage_repo.upload_file(
                path=user_path / file.filename,
                file=file.file,
                content_type=file.content_type,
            )

    async def delete(
        self,
        path: ResourcePath,
        *,
        user_id: int,
    ):
        await self._storage_repo.delete(
            UserSpacePath(
                value=str(path),
                user_id=user_id,
            )
        )

    async def create_folder(
        self,
        path: ResourcePath,
        *,
        user_id: int,
    ) -> None:
        user_path = await self._ensure_parent_exists(path, user_id=user_id)

        if await self._storage_repo.exists(user_path):
            raise ResourceAlreadyExists(resource=path)

        await self._storage_repo.create_directory(user_path)

    async def list_directory(
        self,
        path: ResourcePath,
        *,
        user_id: int,
    ) -> list[StoredResource]:
        return [
            i async for i in await self._storage_repo.list_directory(UserSpacePath(value=str(path), user_id=user_id))
        ]

    async def get(
        self,
        path: ResourcePath,
        *,
        user_id: int,
    ) -> StoredResource:
        return await self._storage_repo.get(
            await self._ensure_parent_exists(
                path,
                user_id=user_id,
            )
        )

    async def download(self, path: ResourcePath, *, user_id: int) -> DownloadResult:
        user_path = await self._ensure_parent_exists(path, user_id=user_id)

        if user_path.is_file:
            return DownloadResult(
                filename=user_path.name,
                content_type="application/octet-stream",
                content=await self._storage_repo.get_content(user_path),
            )

        return DownloadResult(
            filename=f"{user_path.name}.zip",
            content_type="application/zip",
            content=async_stream_zip(await self._stream_zip(user_path)),
        )

    async def _stream_zip(self, user_path: UserSpacePath):
        async def stream() -> AsyncIterator[tuple[str, datetime, int, Method, AsyncIterable[bytes]]]:
            async for item in await self._storage_repo.list_directory(user_path, recursive=True):
                yield (
                    str(item.path).removeprefix("/"),
                    datetime.now(),
                    S_IFREG | 0o600,
                    ZIP_64,
                    await self._storage_repo.get_content(
                        UserSpacePath(
                            value=str(item.path),
                            user_id=user_path.user_id,
                        )
                    ),
                )

        return stream()

    async def move(self, source: ResourcePath, destination: ResourcePath, *, user_id: int) -> StoredResource:
        try:
            user_source = await self._ensure_parent_exists(source, user_id=user_id)
            user_dest = await self._ensure_parent_exists(destination, user_id=user_id)
        except ParentDirectoryDoesNotExist as e:
            raise InvalidPath(path=e.kwargs["resource"]) from e

        return await self._storage_repo.move(user_source, user_dest)

    async def search(self, query: str, *, user_id: int) -> list[StoredResource]:
        items = await self._storage_repo.search(query, user_id=user_id)
        return [i async for i in items]
