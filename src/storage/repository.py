from collections.abc import AsyncIterator
from contextlib import suppress
from typing import BinaryIO

from botocore.exceptions import ClientError
from starlette import status
from types_aiobotocore_s3.client import S3Client
from types_aiobotocore_s3.type_defs import (
    CommonPrefixTypeDef,
    HeadObjectOutputTypeDef,
    ListObjectsV2RequestPaginateTypeDef,
    ObjectTypeDef,
)

from src.storage.constants import CHUNK_SIZE
from src.storage.exceptions import (
    ParentDirectoryDoesNotExist,
    ResourceAlreadyExists,
    ResourceCreationConflict,
    ResourceNotFound,
    StorageError,
)
from src.storage.types import ResourceType, StoredResource, UserSpacePath


class StorageRepository:
    def __init__(self, s3_client: S3Client, bucket_name: str):
        self._bucket_name = bucket_name
        self._s3 = s3_client

    async def get(self, path: UserSpacePath) -> StoredResource:
        try:
            return self._map_s3_head(
                path=path,
                item=await self._s3.head_object(
                    Bucket=self._bucket_name,
                    Key=path.storage_key,
                ),
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")

            if error_code == "404":
                raise ResourceNotFound(resource=path.public_path) from None
            raise

    async def _create_directory_recursively(self, path: UserSpacePath) -> None:
        dirs = []
        while not path.public_path.is_root:
            dirs.append(path)
            path = path.parent

        for dir in dirs[::-1]:
            with suppress(ResourceAlreadyExists, ResourceCreationConflict):
                await self.create_directory(path=dir)

    async def create_directory(self, path: UserSpacePath, *, parents: bool = False) -> None:
        if parents:
            await self._create_directory_recursively(path)
            return

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

    async def _delete_object(self, path: UserSpacePath) -> None:
        await self._s3.delete_object(Bucket=self._bucket_name, Key=path.storage_key)

    async def delete(self, path: UserSpacePath):
        if not await self.exists(path):
            raise ResourceNotFound(resource=path)

        if path.is_directory:
            await self._delete_recursive(path)

        await self._s3.delete_object(
            Bucket=self._bucket_name,
            Key=path.storage_key,
        )

    async def _delete_recursive(self, path: UserSpacePath):
        async for item in self.list_directory(path, first_level=False):
            await self._delete_object(
                UserSpacePath(
                    value=str(item.path),
                    user_id=path.user_id,
                )
            )

    async def get_content(self, path: UserSpacePath) -> AsyncIterator[bytes]:
        response = await self._s3.get_object(
            Bucket=self._bucket_name,
            Key=path.storage_key,
        )
        body = response["Body"]

        while chunk := await body.read(CHUNK_SIZE):
            yield chunk

    async def list_directory(self, path: UserSpacePath, *, first_level: bool = True) -> AsyncIterator[StoredResource]:
        paginator = self._s3.get_paginator("list_objects_v2")

        params: ListObjectsV2RequestPaginateTypeDef = {
            "Bucket": self._bucket_name,
            "Prefix": path.storage_key,
            "PaginationConfig": {
                "PageSize": 1000,
            },
        }

        if first_level:
            params["Delimiter"] = "/"

        is_first_page = True
        async for page in paginator.paginate(**params):
            items = page.get("Contents", [])
            if is_first_page and not items:
                raise ParentDirectoryDoesNotExist(resource=path)

            if is_first_page:
                is_first_page = False

            for prefix in page.get("CommonPrefixes", []):
                yield self._map_s3_prefix(prefix)

            for item in items:
                if item.get("Key") == path.storage_key:
                    continue

                yield self._map_s3_object(item)

        if is_first_page:
            raise ResourceNotFound(resource=path)

    async def exists(self, path: UserSpacePath) -> bool:
        try:
            await self.get(path)
            return True
        except ResourceNotFound:
            return False
        except ClientError:
            raise

    async def upload_file(
        self,
        file: BinaryIO,
        *,
        path: UserSpacePath,
        content_type: str | None = None,
    ) -> None:
        extra_args = {}

        if content_type is not None:
            extra_args["ContentType"] = content_type

        try:
            await self._s3.put_object(
                Bucket=self._bucket_name,
                Key=path.storage_key,
                Body=file,
                ContentType=content_type or "application/octet-stream",
                IfNoneMatch="*",
            )

        except ClientError as error:
            status_code = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            error_code = error.response.get("Error", {}).get("Code")

            if status_code == 412 or error_code == "PreconditionFailed":
                raise ResourceAlreadyExists(resource=path.public_path) from error

            raise

    @staticmethod
    def _map_s3_object(item: ObjectTypeDef) -> StoredResource:
        key = item.get("Key")
        assert key is not None
        path = UserSpacePath.from_storage_key(key)
        return StoredResource(
            path=path.public_path,
            size=item.get("Size", 0),
            type=ResourceType.FILE,
        )

    @staticmethod
    def _map_s3_head(path: UserSpacePath, item: HeadObjectOutputTypeDef) -> StoredResource:
        return StoredResource(
            path=path.public_path,
            size=item["ContentLength"],
            type=ResourceType.FILE,
        )

    @staticmethod
    def _map_s3_prefix(item: CommonPrefixTypeDef) -> StoredResource:
        key = item.get("Prefix")
        assert key is not None
        path = UserSpacePath.from_storage_key(key)
        return StoredResource(
            path=path.public_path,
            size=0,
            type=ResourceType.DIRECTORY,
        )
