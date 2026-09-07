
from src.exceptions import AppError


class AuthError(AppError):
    pass


class InvalidTokenError(AuthError):
    message = "Invalid or expired token"


class InvalidCredentialsError(AuthError):
    message = "Invalid credentials"
