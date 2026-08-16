from dishka import AsyncContainer, Provider, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import APIRouter, FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.auth import AuthProvider, AuthRouter
from src.core import AppError, Config, lifespan
from src.core.exception_handler import app_error_handler
from src.storage import StorageProvider
from src.storage.routes import directory_router as DirectoryRouter
from src.storage.routes import resource_router as ResourceRouter
from src.user import UserProvider
from src.user.routes import router as UserRouter


def setup_routes(app: FastAPI):
    api = APIRouter()
    app.include_router(api, prefix="/api/v1")

    api.include_router(AuthRouter, prefix="/auth", tags=["Auth"])
    api.include_router(UserRouter, prefix="/users", tags=["User"])
    api.include_router(ResourceRouter, prefix="/resources", tags=["Resource"])
    api.include_router(DirectoryRouter, prefix="/directory", tags=["Directory"])


def setup_exceptions_handler(app: FastAPI) -> None:
    # noinspection bad-argument-type
    app.add_exception_handler(
        AppError,
        app_error_handler,  # pyright: ignore[reportArgumentType]
    )


def setup_middlewares(app: FastAPI, config: Config) -> None:
    # noinspection bad-argument-type
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allow_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
    )


def create_app(
    *,
    config: Config,
    container: AsyncContainer,
) -> FastAPI:
    app = FastAPI(
        title="Cloud Storage API",
        lifespan=lifespan,
    )

    setup_middlewares(app, config)
    setup_routes(app)
    setup_exceptions_handler(app)
    setup_dishka(container, app)

    return app


def create_container(infrastructure_provider: Provider, *, context: dict | None) -> AsyncContainer:
    return make_async_container(
        infrastructure_provider,
        UserProvider(),
        StorageProvider(),
        AuthProvider(),
        context=context,
    )
