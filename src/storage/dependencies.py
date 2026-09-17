from typing import Annotated

from dishka import FromDishka, Provider, Scope, provide
from dishka.integrations.fastapi import inject
from fastapi import Depends, File, UploadFile
from pydantic import AfterValidator

from src.config import Config
from src.storage.exceptions import ContentSizeExceeded, TooManyFiles
from src.storage.interface import IStorageRepository
from src.types_stubs import S3Client

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
            chunk_size=config.app.files.chunk_size,
        )

    @provide(scope=Scope.REQUEST)
    def service(self, storage_repo: IStorageRepository) -> StorageService:
        return StorageService(storage_repo=storage_repo)

    @provide(scope=Scope.APP)
    def initializer(self, s3_client: S3Client, config: Config) -> StorageInitializer:
        return StorageInitializer(s3_client=s3_client, bucket_name=config.rustfs.bucket)


@inject
def verify_files_size(
    config: FromDishka[Config],
    files: Annotated[
        list[ValidatedUploadFile],
        File(),
        AfterValidator(validate_unique_filenames),
    ],
) -> ValidatedUploadFiles:
    if len(files) > config.app.files.max_count:
        raise TooManyFiles()

    total_size = 0
    for file in files:
        if file.size is None:
            raise ContentSizeExceeded()

        total_size += file.size

        if total_size > config.app.files.max_total_size:
            raise ContentSizeExceeded()

    return files


VerifiedFiles = Annotated[list[UploadFile], Depends(verify_files_size)]
