from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import APIRouter, FastAPI

from src.auth import AuthProvider, AuthRouter
from src.core import AppError, InfrastructureProvider, lifespan
from src.core.exception_handler import app_error_handler
from src.user import UserProvider
from src.user.routes import router as UserRouter


def setup_routes(app: FastAPI):
    api = APIRouter()
    app.include_router(api, prefix="/api/v1")

    api.include_router(AuthRouter, prefix="/auth", tags=["Auth"])
    api.include_router(UserRouter, prefix="/users", tags=["User"])
    # api.include_router(ResourceRouter, prefix="/resource", tags=["Resource"])


def setup_exceptions_handler(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)  # pyrefly: ignore [bad-argument-type]


def create_app(container: AsyncContainer) -> FastAPI:
    app = FastAPI(
        title="Cloud Storage API",
        lifespan=lifespan,
    )

    setup_routes(app)
    setup_exceptions_handler(app)
    setup_dishka(container, app)

    return app


app = create_app(
    make_async_container(
        InfrastructureProvider(),
        UserProvider(),
        AuthProvider(),
    )
)
