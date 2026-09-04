from src.exceptions import AppError


class UserError(AppError):
    pass


class UserAlreadyExists(UserError):
    message = "User already exists"


class UserNotFound(UserError):
    message = "User not found"
