from cloud_storage.exceptions import AppError


class AuthError(AppError):
    pass


class InvalidTokenError(AuthError):
    message = "Invalid or expired token"


class InvalidCredentialsError(AuthError):
    message = "Invalid credentials"


class AccountAlreadyExists(AuthError):
    message = "User already exists"


class AccountNotFound(AuthError):
    message = "User not found"
