from dishka import Provider, Scope, provide

from cloud_storage.config import Config
from cloud_storage.storage.ports import StorageRepository
from cloud_storage.types_stubs import S3Client

from .initializer import StorageInitializer
from .repository import S3StorageRepository


class S3StorageRepositoryProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def repository(
        self,
        config: Config,
        s3_client: S3Client,
    ) -> StorageRepository:
        return S3StorageRepository(
            s3_client=s3_client,
            bucket_name=config.rustfs.bucket,
            chunk_size=config.app.files.chunk_size,
        )

    @provide(scope=Scope.APP)
    def initializer(self, s3_client: S3Client, config: Config) -> StorageInitializer:
        return StorageInitializer(s3_client=s3_client, bucket_name=config.rustfs.bucket)
