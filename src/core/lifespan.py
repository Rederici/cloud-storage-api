from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dishka import AsyncContainer, Scope
from fastapi import FastAPI

from src.storage import StorageService
from src.storage.service import StorageInitializer


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    container: AsyncContainer = app.state.dishka_container
    storage_service = await container.get(StorageInitializer)
    await storage_service.init_bucket()

    yield
