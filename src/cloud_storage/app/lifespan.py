from contextlib import asynccontextmanager
from types import TracebackType

from fastapi import FastAPI

from cloud_storage.config import Config
from cloud_storage.storage.service import StorageInitializer


class Lifespan:
    def __init__(self, config: Config, storage_initializer: StorageInitializer):
        self._config: Config = config
        self._storage_initializer: StorageInitializer = storage_initializer

    async def __aenter__(self):
        await self.startup()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ):
        await self.shutdown()

    async def startup(self):
        await self._storage_initializer.init_bucket()

    async def shutdown(self):
        pass

    @staticmethod
    @asynccontextmanager
    async def context(app: FastAPI):
        container = app.state.dishka_container
        assert container is not None

        config = await container.get(Config)
        storage_service = await container.get(StorageInitializer)
        async with Lifespan(config=config, storage_initializer=storage_service):
            yield
