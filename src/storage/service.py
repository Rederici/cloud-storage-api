from botocore.client import ClientError
from types_aiobotocore_s3.client import S3Client

from .exceptions import ParentDirectoryDoesNotExist, ResourceAlreadyExists
from .interface import IStorageRepository
from .types import ResourcePath, UserSpacePath


class StorageService:
    def __init__(self, storage_repo: IStorageRepository):
        self._storage_repo = storage_repo

    async def init_root(self, user_id: int) -> None:
        root = UserSpacePath(value="/", user_id=user_id)
        if not await self._storage_repo.exists(root):
            await self._storage_repo.create_directory(root)

    async def create_folder(self, user_id: int, path: ResourcePath) -> None:
        user_path = UserSpacePath(value=str(path), user_id=user_id)

        if not await self._storage_repo.exists(user_path.parent):
            raise ParentDirectoryDoesNotExist(resource=path)

        if await self._storage_repo.exists(user_path):
            raise ResourceAlreadyExists(resource=path)

        await self._storage_repo.create_directory(user_path)

    async def list_directory(self, user_id: int, path: ResourcePath) -> list: ...

    async def get(self) -> bytes: ...


class StorageInitializer:
    def __init__(self, s3_client: S3Client, bucket_name: str):
        self._s3 = s3_client
        self._bucket_name = bucket_name

    async def init_bucket(self) -> None:
        try:
            await self._s3.create_bucket(Bucket=self._bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] not in (
                "BucketAlreadyOwnedByYou",
                "BucketAlreadyExists",
            ):
                raise
