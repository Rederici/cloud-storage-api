from botocore.client import ClientError
from types_aiobotocore_s3.client import S3Client

from .exceptions import ParentDirectoryDoesNotExist, ResourceAlreadyExists
from .interface import IStorageRepository
from .types import ResourcePath, StoredResource, UserSpacePath


class StorageService:
    def __init__(self, storage_repo: IStorageRepository):
        self._storage_repo = storage_repo

    async def init_root(self, user_id: int) -> None:
        root = UserSpacePath(value="/", user_id=user_id)
        if not await self._storage_repo.exists(root):
            await self._storage_repo.create_directory(root)

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

        if await self._storage_repo.exists(user_path):
            raise ResourceAlreadyExists(resource=path)

        await self._storage_repo.create_directory(user_path)

    async def list_directory(
        self,
        path: ResourcePath,
        *,
        user_id: int,
    ) -> list[StoredResource]:
        items = await self._storage_repo.list_directory(UserSpacePath(value=str(path), user_id=user_id))
        if not items:
            raise ParentDirectoryDoesNotExist(resource=path)

        return [i for i in items if i.path != path]

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


class StorageInitializer:
    def __init__(self, s3_client: S3Client, bucket_name: str):
        self._s3 = s3_client
        self._bucket_name = bucket_name

    async def init_bucket(self) -> None:
        try:
            await self._s3.create_bucket(Bucket=self._bucket_name)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") not in (
                "BucketAlreadyOwnedByYou",
                "BucketAlreadyExists",
            ):
                raise
