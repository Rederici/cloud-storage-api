import re
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import BinaryIO

from botocore.exceptions import ClientError
from starlette import status

from cloud_storage.storage.exceptions import (
    InvalidPath,
    ParentDirectoryDoesNotExist,
    ResourceAlreadyExists,
    ResourceCreationConflict,
    ResourceNotFound,
    StorageError,
)
from cloud_storage.storage.types import ResourceType, StoredResource, UserSpacePath
from cloud_storage.types_stubs import (
    CommonPrefixTypeDef,
    ListObjectsV2RequestPaginateTypeDef,
    ObjectTypeDef,
    S3Client,
)

STORAGE_SEPARATOR = "/"
STORAGE_TO_PATH_PATTERN = re.compile(
    rf"^user-(?P<user_id>[1-9]\d*)-files"
    rf"(?P<path>{re.escape(STORAGE_SEPARATOR)}.*)?$"
)


def get_user_root(user_id: int) -> str:
    return f"user-{user_id}-files{STORAGE_SEPARATOR}"


def storage_key(path: UserSpacePath) -> str:
    root = get_user_root(path.user_id)
    if path.is_root:
        return root
    return f"{root}{path.value.lstrip('/')}"


def from_storage_key(key: str) -> UserSpacePath:
    if not (m := re.fullmatch(STORAGE_TO_PATH_PATTERN, key)):
        raise ValueError("Invalid user space path")

    return UserSpacePath(
        value=m["path"] or STORAGE_SEPARATOR,
        user_id=int(m["user_id"]),
    )


class S3StorageRepository:
    def __init__(self, s3_client: S3Client, bucket_name: str, chunk_size: int):
        self._bucket_name = bucket_name
        self._chunk_size = chunk_size
        self._s3 = s3_client

    async def get(self, path: UserSpacePath) -> StoredResource:
        if path.is_root:
            return StoredResource(path=path.public_path, size=0, type=ResourceType.DIRECTORY)

        try:
            response = await self._s3.head_object(
                Bucket=self._bucket_name,
                Key=storage_key(path),
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")

            if error_code in {"NoSuchKey", "404", "NotFound"}:
                raise ResourceNotFound(resource=path.public_path) from None
            raise

        content_type = response["ContentType"]

        if content_type == "application/x-directory":
            return StoredResource(
                path=path.public_path,
                size=0,
                type=ResourceType.DIRECTORY,
            )

        return StoredResource(
            path=path.public_path,
            size=response["ContentLength"] or 0,
            type=ResourceType.FILE,
        )

    async def move(
        self,
        source: UserSpacePath,
        destination: UserSpacePath,
    ) -> StoredResource:
        if source.is_root:
            raise InvalidPath(path=source.public_path)

        if not await self.exists(source):
            raise ResourceNotFound(resource=source.public_path)

        if await self.exists(destination):
            raise ResourceAlreadyExists(resource=destination.public_path)

        if source.is_directory and destination.public_path.value.startswith(source.public_path.value):
            raise InvalidPath(path=destination.public_path)

        if source.is_file:
            await self._s3.copy_object(
                Bucket=self._bucket_name,
                Key=storage_key(destination),
                CopySource={
                    "Bucket": self._bucket_name,
                    "Key": storage_key(source),
                },
            )
            await self._delete_object(source)

            return await self.get(destination)

        await self.create_directory(
            path=destination,
            parents=True,
        )

        async for item in await self.list_directory(source, recursive=True):
            relative_path = item.path.value.removeprefix(
                source.public_path.value,
            )

            destination_path = UserSpacePath(
                value=str(destination.public_path / relative_path),
                user_id=source.user_id,
            )

            item_source = UserSpacePath(
                value=str(item.path),
                user_id=source.user_id,
            )

            if item.type == ResourceType.FILE:
                await self._s3.copy_object(
                    Bucket=self._bucket_name,
                    Key=storage_key(destination_path),
                    CopySource={
                        "Bucket": self._bucket_name,
                        "Key": storage_key(item_source),
                    },
                )
            else:
                await self.create_directory(
                    path=destination_path,
                    parents=True,
                )

        await self._delete_recursive(source)

        return await self.get(destination)

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
                Key=storage_key(path),
                ContentType="application/x-directory",
                IfNoneMatch="*",
            )
        except ClientError as e:
            status_code = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            error_code = e.response.get("Error", {}).get("Code")

            if status_code == status.HTTP_412_PRECONDITION_FAILED or error_code == "PreconditionFailed":
                raise ResourceAlreadyExists(str(path)) from None

            if status_code == status.HTTP_409_CONFLICT or error_code == "ConditionalRequestConflict":
                raise ResourceCreationConflict(str(path)) from None

            raise StorageError() from None

    async def _delete_object(self, path: UserSpacePath) -> None:
        await self._s3.delete_object(Bucket=self._bucket_name, Key=storage_key(path))

    async def delete(self, path: UserSpacePath):
        if path.is_root:
            raise InvalidPath(path=path.public_path)

        if not await self.exists(path):
            raise ResourceNotFound(resource=path.public_path)

        if path.is_directory:
            await self._delete_recursive(path)

        await self._s3.delete_object(
            Bucket=self._bucket_name,
            Key=storage_key(path),
        )

    async def _delete_recursive(self, path: UserSpacePath):
        async for item in await self.list_directory(path, recursive=True):
            await self._delete_object(
                UserSpacePath(
                    value=str(item.path),
                    user_id=path.user_id,
                )
            )
        await self._delete_object(path)

    async def get_content(self, path: UserSpacePath) -> AsyncIterator[bytes]:
        try:
            response = await self._s3.get_object(
                Bucket=self._bucket_name,
                Key=storage_key(path),
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")

            if error_code == "NoSuchKey":
                raise ResourceNotFound(resource=path.public_path) from None
            raise

        body = response["Body"]

        async def stream() -> AsyncIterator[bytes]:
            try:
                while chunk := await body.read(self._chunk_size):
                    yield chunk
            finally:
                body.close()

        return stream()

    async def list_directory(self, path: UserSpacePath, *, recursive: bool = False) -> AsyncIterator[StoredResource]:
        paginator = self._s3.get_paginator("list_objects_v2")

        params: ListObjectsV2RequestPaginateTypeDef = {
            "Bucket": self._bucket_name,
            "Prefix": storage_key(path),
            "PaginationConfig": {
                "PageSize": 1000,
            },
        }

        if not recursive:
            params["Delimiter"] = "/"

        async def iterator() -> AsyncIterator[StoredResource]:
            is_first_page = True
            async for page in paginator.paginate(**params):
                items = page.get("Contents", [])
                if is_first_page and not items and not path.is_root:
                    raise ParentDirectoryDoesNotExist(resource=path)

                if is_first_page:
                    is_first_page = False

                for prefix in page.get("CommonPrefixes", []):
                    yield self._map_s3_prefix(prefix)

                for item in items:
                    if item.get("Key") == storage_key(path):
                        continue

                    yield self._map_s3_object(item)

        return iterator()

    async def exists(self, path: UserSpacePath) -> bool:
        try:
            await self.get(path)
            return True
        except ResourceNotFound:
            return False

    async def search(self, query: str, *, user_id: int) -> AsyncIterator[StoredResource]:
        user_path = UserSpacePath(value="/", user_id=user_id)

        async def iterator() -> AsyncIterator[StoredResource]:
            async for i in await self.list_directory(user_path, recursive=True):
                if query in str(i.path):
                    yield i

        return iterator()

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
                Key=storage_key(path),
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
        path = from_storage_key(key)
        return StoredResource(
            path=path.public_path,
            size=item.get("Size", 0),
            type=ResourceType.DIRECTORY if str(path).endswith("/") else ResourceType.FILE,
        )

    @staticmethod
    def _map_s3_prefix(item: CommonPrefixTypeDef) -> StoredResource:
        key = item.get("Prefix")
        assert key is not None
        path = from_storage_key(key)
        return StoredResource(
            path=path.public_path,
            size=0,
            type=ResourceType.DIRECTORY,
        )
