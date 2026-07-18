from os import PathLike

from botocore.exceptions import ClientError
from starlette import status
from types_aiobotocore_s3.client import S3Client

from src.storage.exceptions import ResourceAlreadyExists, ResourceCreationConflict, StorageError
from src.storage.types import UserSpacePath


class StorageRepository:
    def __init__(self, s3_client: S3Client, bucket_name: str):
        self._bucket_name = bucket_name
        self._s3 = s3_client

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

    async def list(self, path: str):
        await self._s3.list_objects_v2(
            Bucket=self._bucket_name,
            Prefix=path,
            Delimiter="/",
        )

    async def get_content(self, path: PathLike): ...

    async def delete(self, path: PathLike) -> None: ...
