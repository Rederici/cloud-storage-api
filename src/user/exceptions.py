from starlette import status

from src.core import AppError


class UserError(AppError):
    pass


class UserAlreadyExists(UserError):
    status_code = status.HTTP_409_CONFLICT
    message = "User already exists"


class UserNotFound(UserError):
    status_code = status.HTTP_404_NOT_FOUND
    message = "User not found"
