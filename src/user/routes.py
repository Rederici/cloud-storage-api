from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
from starlette import status

from src.auth.dependencies import CurrentUser
from src.core.schemas import ErrorResponse
from src.user.schemas import UserResponse

router = APIRouter(route_class=DishkaRoute)


@router.get("/me", status_code=status.HTTP_200_OK, responses={
    200: {"model": UserResponse, "description": "The user's info"},
    401: {"model": ErrorResponse, "description": "Unauthorized"},
})
async def get_me(user: CurrentUser) -> UserResponse:
    return UserResponse(username=user.username)
