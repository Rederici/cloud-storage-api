from src.auth.exceptions import AuthError
from src.exceptions import AppError
from src.storage.exceptions import (
    ContentSizeExceeded,
    FileTooLarge,
    InvalidFileName,
    InvalidPath,
    ParentDirectoryDoesNotExist,
    ResourceCreationConflict,
    ResourceNotFound,
    TooManyFiles,
)
from src.user.exceptions import UserAlreadyExists, UserNotFound

mapping: dict[type[AppError], int] = {
    UserAlreadyExists: 409,
    UserNotFound: 404,
    ContentSizeExceeded: 413,
    TooManyFiles: 413,
    ResourceCreationConflict: 409,
    ParentDirectoryDoesNotExist: 404,
    ResourceNotFound: 404,
    InvalidFileName: 400,
    FileTooLarge: 413,
    InvalidPath: 400,
    AuthError: 401,
}
