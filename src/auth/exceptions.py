from starlette import status

from src.core import AppError


class AuthError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED


class InvalidTokenError(AuthError):
    message = "Invalid or expired token"


class InvalidCredentialsError(AuthError):
    message = "Invalid credentials"
