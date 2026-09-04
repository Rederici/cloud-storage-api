from collections.abc import AsyncGenerator

import aioboto3
from dishka import Provider, Scope, provide
from types_aiobotocore_s3.client import S3Client

from src.config import Config


class BotoProvider(Provider):
    @provide(scope=Scope.APP)
    def s3_session(self) -> aioboto3.Session:
        return aioboto3.Session()

    @provide(scope=Scope.APP)
    async def s3_client(
        self,
        config: Config,
        session: aioboto3.Session,
    ) -> AsyncGenerator[S3Client]:
        async with session.client(  # pyright: ignore[reportGeneralTypeIssues]
            "s3",
            endpoint_url=config.minio.url,
            aws_access_key_id=config.minio.access_key_id,
            aws_secret_access_key=config.minio.secret_access_key,
        ) as client:
            yield client
