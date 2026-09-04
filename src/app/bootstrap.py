from functools import cached_property

from dishka import AsyncContainer, Provider, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.http import ErrorResponse, error_handler
from src.auth import AuthProvider, AuthRouter
from src.config import Config, ConfigProvider
from src.config.models import Env
from src.exceptions import AppError
from src.persistance import SQLAlchemyProvider, RedisProvider, BotoProvider
from src.storage import StorageProvider
from src.storage.routes import DirectoryRouter, ResourceRouter
from src.user import UserProvider
from src.user.routes import UserRouter

from .lifespan import Lifespan


class Bootstrap:
    def __init__(self, *providers: Provider, config: Config | None = None):
        self._config: Config | None = config
        self._override_providers = providers

    def create_app(self, container: AsyncContainer | None = None) -> FastAPI:
        app = self.app()
        setup_dishka(
            app=app,
            container=container or self.container,
        )
        return app

    @property
    def config(self) -> Config:
        if self._config is None:
            self._config = Config()
        return self._config

    @property
    def api_routers(self) -> list[APIRouter]:
        return [
            AuthRouter,
            UserRouter,
            ResourceRouter,
            DirectoryRouter,
        ]

    @property
    def domain_providers(self) -> list[Provider]:
        return [
            UserProvider(),
            StorageProvider(),
            AuthProvider(),
        ]

    @property
    def infrastructure_providers(self) -> list[Provider]:
        return [
            ConfigProvider(),
            BotoProvider(),
            RedisProvider(),
            SQLAlchemyProvider(),
        ]

    @cached_property
    def container(self) -> AsyncContainer:
        return make_async_container(
            *self.infrastructure_providers,
            *self.domain_providers,
            *self._override_providers,
            context={Config: self.config},
        )

    def app(self) -> FastAPI:
        app = FastAPI(
            title="Cloud Storage",
            lifespan=Lifespan.context,
            debug=self.config.env != Env.PROD,
            exception_handlers={
                AppError: error_handler,
            },
            responses={
                500: {"model": ErrorResponse, "description": "Internal Server Error"},
            },
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors.allow_origins,
            allow_credentials=self.config.cors.allow_credentials,
            allow_methods=self.config.cors.allow_methods,
            allow_headers=self.config.cors.allow_headers,
        )

        api = APIRouter()
        for router in self.api_routers:
            api.include_router(router)

        app.include_router(api, prefix="/api/v1")
        return app
