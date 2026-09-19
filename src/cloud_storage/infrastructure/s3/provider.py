from collections.abc import AsyncGenerator

import aioboto3
from dishka import Provider, Scope, provide

from cloud_storage.config import Config
from cloud_storage.types_stubs import S3Client


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
            endpoint_url=config.rustfs.url,
            aws_access_key_id=config.rustfs.access_key,
            aws_secret_access_key=config.rustfs.secret_key,
        ) as client:
            yield client
