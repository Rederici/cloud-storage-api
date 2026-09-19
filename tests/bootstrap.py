from dishka import Provider

from cloud_storage.app.bootstrap import Bootstrap
from cloud_storage.config import ConfigProvider
from cloud_storage.infrastructure import BotoProvider, RedisProvider
from tests.dependencies import TestPostgresProvider


class TestBootStrap(Bootstrap):
    @property
    def infrastructure_providers(self) -> list[Provider]:
        return [
            ConfigProvider(),
            BotoProvider(),
            RedisProvider(),
            TestPostgresProvider(),
        ]
