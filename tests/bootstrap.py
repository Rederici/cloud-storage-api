from dishka import Provider

from src.app.bootstrap import Bootstrap
from src.config import ConfigProvider
from src.persistance import BotoProvider, RedisProvider

from .dependencies import TestPostgresProvider


class TestBootStrap(Bootstrap):
    @property
    def infrastructure_providers(self) -> list[Provider]:
        return [
            ConfigProvider(),
            BotoProvider(),
            RedisProvider(),
            TestPostgresProvider(),
        ]
