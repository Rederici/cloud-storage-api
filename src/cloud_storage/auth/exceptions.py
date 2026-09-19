from cloud_storage.exceptions import AppError


class AuthError(AppError):
    pass


class InvalidTokenError(AuthError):
    message = "Invalid or expired token"


class InvalidCredentialsError(AuthError):
    message = "Invalid credentials"


class UserError(AppError):
    pass


class UserAlreadyExists(UserError):
    message = "User already exists"


class UserNotFound(UserError):
    message = "User not found"
