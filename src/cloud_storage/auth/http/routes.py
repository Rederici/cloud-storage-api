from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Request
from starlette import status
from starlette.responses import Response

from cloud_storage.api.http.schemas import ErrorResponse
from cloud_storage.auth.exceptions import InvalidTokenError
from cloud_storage.auth.service import AuthService
from cloud_storage.config import Config
from cloud_storage.config.models import Env

from .dependencies import CurrentUser, SessionToken
from .schemas import CredentialsRequest, UserResponse

AuthRouter = APIRouter(route_class=DishkaRoute, prefix="/auth", tags=["Auth"])
UserRouter = APIRouter(route_class=DishkaRoute, prefix="/users", tags=["User"])


def set_token(response: Response, config: Config, token: str):
    response.set_cookie(
        key=config.app.session.cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
        secure=config.env == Env.PROD,
        max_age=int(config.app.session.ttl.total_seconds()),
    )


@AuthRouter.post(
    "/sign-up",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": UserResponse, "description": "User registration successful"},
        409: {"model": ErrorResponse, "description": "User already exists"},
    },
)
async def sign_up(
    config: FromDishka[Config],
    auth_service: FromDishka[AuthService],
    credentials: CredentialsRequest,
    response: Response,
) -> UserResponse:
    authorized = await auth_service.register(credentials.username, credentials.password)
    set_token(response, config, authorized.token)
    return UserResponse(username=authorized.username)


@AuthRouter.post(
    "/sign-in",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": UserResponse, "description": "User logged in successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
)
async def sign_in(
    config: FromDishka[Config],
    auth_service: FromDishka[AuthService],
    credentials: CredentialsRequest,
    response: Response,
) -> UserResponse:
    authorized = await auth_service.login(credentials.username, credentials.password)
    set_token(response, config, authorized.token)
    return UserResponse(username=authorized.username)


@AuthRouter.post(
    "/sign-out", status_code=status.HTTP_204_NO_CONTENT, responses={204: {"description": "User logout successful"}}
)
async def sign_out(
    response: Response,
    auth_service: FromDishka[AuthService],
    token: SessionToken,
    config: FromDishka[Config],
):
    response.delete_cookie(config.app.session.cookie_name)

    if token is None:
        raise InvalidTokenError()

    await auth_service.logout(token)


@UserRouter.get(
    "/me",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": UserResponse, "description": "The user's info"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_me(user: CurrentUser) -> UserResponse:
    return UserResponse(username=user.username)
