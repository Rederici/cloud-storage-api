from dishka import Provider, Scope, provide
from types_aiobotocore_s3.client import S3Client

from src.core import Config
from src.storage.interface import IStorageRepository

from .repository import StorageRepository
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
            bucket_name=config.minio.bucket,
        )

    @provide(scope=Scope.REQUEST)
    def service(self, storage_repo: IStorageRepository) -> StorageService:
        return StorageService(storage_repo=storage_repo)

    @provide(scope=Scope.APP)
    def initializer(self, s3_client: S3Client, config: Config) -> StorageInitializer:
        return StorageInitializer(s3_client=s3_client, bucket_name=config.minio.bucket)
