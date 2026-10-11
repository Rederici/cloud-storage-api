from functools import cached_property
from typing import Any

from dishka import AsyncContainer, Provider, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from cloud_storage.api.http.exception_handler import base_error_handler, error_handler, validation_error_handler
from cloud_storage.api.http.schemas import ErrorResponse
from cloud_storage.auth import AuthProvider
from cloud_storage.auth.http.routes import AuthRouter, UserRouter
from cloud_storage.auth.infrastructure import (
    Argon2PasswordHasherProvider,
    RedisSessionRepositoryProvider,
    SQLAlchemyAccountRepositoryProvider,
)
from cloud_storage.config import Config, ConfigProvider
from cloud_storage.config.models import Env
from cloud_storage.exceptions import AppError
from cloud_storage.health import HealthRouter
from cloud_storage.infrastructure import BotoProvider, RedisProvider, SQLAlchemyProvider
from cloud_storage.storage import StorageProvider
from cloud_storage.storage.http.routes import DirectoryRouter, ResourceRouter
from cloud_storage.storage.infrastructure.s3 import S3StorageRepositoryProvider

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
            self._config = (cfg := Config())
            return cfg
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
            StorageProvider(),
            AuthProvider(),
        ]

    @property
    def adapter_providers(self) -> list[Provider]:
        return [
            Argon2PasswordHasherProvider(),
            S3StorageRepositoryProvider(),
            SQLAlchemyAccountRepositoryProvider(),
            RedisSessionRepositoryProvider(),
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
            *self.adapter_providers,
            *self.domain_providers,
            *self._override_providers,
            context={Config: self.config},
        )

    def app(self) -> FastAPI:
        app = FastAPI(
            title=self.config.project.display_name,
            version=self.config.project.version,
            lifespan=Lifespan.context,
            debug=self.config.env != Env.PROD,
            docs_url="/docs" if self.config.swagger_enable else None,
            redoc_url="/redoc" if self.config.swagger_enable else None,
            exception_handlers={
                AppError: error_handler,
                RequestValidationError: validation_error_handler,
                HTTPException: base_error_handler,
            },
            responses={
                400: {"model": ErrorResponse, "description": "Bad Request"},
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

        app.include_router(HealthRouter)
        app.include_router(api, prefix="/api")

        app.openapi_schema = self._custom_open_api(app)

        return app

    @staticmethod
    def _custom_open_api(app: FastAPI) -> dict[str, Any]:
        openapi_schema = app.openapi()
        for path_item in openapi_schema.get("paths", {}).values():
            for operation in path_item.values():
                if not isinstance(operation, dict):
                    continue

                responses = operation.get("responses", {})
                responses.pop("422", None)
        return openapi_schema
