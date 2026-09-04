from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from starlette import status

from api.http.schemas import ErrorResponse
from src.auth.dependencies import CurrentUser
from src.user.schemas import UserResponse

UserRouter = APIRouter(route_class=DishkaRoute, prefix="/users", tags=["User"])


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
