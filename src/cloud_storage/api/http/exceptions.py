from cloud_storage.auth.exceptions import AccountAlreadyExists, AccountNotFound, AuthError
from cloud_storage.exceptions import AppError
from cloud_storage.storage.exceptions import (
    ContentSizeExceeded,
    FileTooLarge,
    InvalidFileName,
    InvalidPath,
    ParentDirectoryDoesNotExist,
    ResourceCreationConflict,
    ResourceNotFound,
    TooManyFiles,
)

mapping: dict[type[AppError], int] = {
    AccountAlreadyExists: 409,
    AccountNotFound: 404,
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
