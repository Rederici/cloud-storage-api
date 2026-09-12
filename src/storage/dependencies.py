from typing import Annotated

from dishka import Provider, Scope, provide
from fastapi import Depends, File, UploadFile
from pydantic import AfterValidator
from types_aiobotocore_s3.client import S3Client

from src.config import Config
from src.storage.constants import MAX_FILES_COUNT, MAX_TOTAL_FILES_SIZE
from src.storage.exceptions import ContentSizeExceeded, TooManyFiles
from src.storage.interface import IStorageRepository

from .repository import StorageRepository
from .schemas import (
    ValidatedUploadFile,
    ValidatedUploadFiles,
    validate_unique_filenames,
)
from .service import StorageInitializer, StorageService


class StorageProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def repository(
        self,
        config: Config,
        s3_client: S3Client,
    ) -> IStorageRepository:
        return StorageRepository(
            s3_client=s3_client,
            bucket_name=config.rustfs.bucket,
        )

    @provide(scope=Scope.REQUEST)
    def service(self, storage_repo: IStorageRepository) -> StorageService:
        return StorageService(storage_repo=storage_repo)

    @provide(scope=Scope.APP)
    def initializer(self, s3_client: S3Client, config: Config) -> StorageInitializer:
        return StorageInitializer(s3_client=s3_client, bucket_name=config.rustfs.bucket)


def verify_files_size(
    max_total_files_size: int = MAX_TOTAL_FILES_SIZE,
    max_files_count: int = MAX_FILES_COUNT,
):
    def verifier(
        files: Annotated[
            list[ValidatedUploadFile],
            File(),
            AfterValidator(validate_unique_filenames),
        ],
    ) -> ValidatedUploadFiles:
        if len(files) > max_files_count:
            raise TooManyFiles()

        total_size = 0
        for file in files:
            if file.size is None:
                raise ContentSizeExceeded()

            total_size += file.size

            if total_size > max_total_files_size:
                raise ContentSizeExceeded()

        return files

    return verifier


VerifiedFiles = Annotated[list[UploadFile], Depends(verify_files_size())]
