from os import PathLike

from botocore.exceptions import ClientError
from starlette import status
from types_aiobotocore_s3.client import S3Client
from types_aiobotocore_s3.type_defs import CommonPrefixTypeDef, ObjectTypeDef

from src.storage.exceptions import ResourceAlreadyExists, ResourceCreationConflict, StorageError
from src.storage.types import ResourceType, StoredResource, UserSpacePath


class StorageRepository:
    def __init__(self, s3_client: S3Client, bucket_name: str):
        self._bucket_name = bucket_name
        self._s3 = s3_client

    @staticmethod
    def _map_s3_object(item: ObjectTypeDef) -> StoredResource:
        path = UserSpacePath.from_storage_key(item["Key"])
        return StoredResource(
            path=path.public_path,
            size=item["Size"],
            type=ResourceType.FILE,
        )

    @staticmethod
    def _map_s3_prefix(item: CommonPrefixTypeDef) -> StoredResource:
        path = UserSpacePath.from_storage_key(item["Prefix"])
        return StoredResource(
            path=path.public_path,
            size=0,
            type=ResourceType.DIRECTORY,
        )

    async def create_directory(self, path: UserSpacePath) -> None:
        try:
            await self._s3.put_object(
                Bucket=self._bucket_name,
                Key=path.storage_key,
                ContentType="application/x-directory",
                IfNoneMatch="*",
            )
        except ClientError as e:
            status_code = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            error_code = e.response.get("Error", {}).get("Code")

            if status_code == status.HTTP_412_PRECONDITION_FAILED or error_code == "PreconditionFailed":
                raise ResourceAlreadyExists(path) from None

            if status_code == status.HTTP_409_CONFLICT or error_code == "ConditionalRequestConflict":
                raise ResourceCreationConflict(path) from None

            raise StorageError() from None

    async def exists(self, path: UserSpacePath) -> bool:
        try:
            await self._s3.head_object(
                Bucket=self._bucket_name,
                Key=path.storage_key,
            )
            return True
        except ClientError as e:
            return False

    async def get(self, path: str) -> None:
        try:
            info = self._s3.head_object(
                Bucket=self._bucket_name,
                Key=path,
            )
        except ClientError:
            return None

    async def list_directory(self, path: UserSpacePath) -> list[StoredResource]:
        items = await self._s3.list_objects_v2(
            Bucket=self._bucket_name,
            Prefix=path.storage_key,
            Delimiter="/",
        )

        files = [self._map_s3_object(file) for file in items.get("Contents", [])]
        dirs = [self._map_s3_prefix(dir) for dir in items.get("CommonPrefixes", [])]
        return files + dirs

    async def get_content(self, path: PathLike): ...

    async def delete(self, path: PathLike) -> None: ...
