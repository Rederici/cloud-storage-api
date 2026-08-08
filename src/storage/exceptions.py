from starlette import status

from src.core import AppError

from .types import ResourcePath


class StorageError(AppError):
    pass


class ContentSizeExceeded(Exception):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    message = "Body is too large"


class TooManyFiles(AppError):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    message = "Too many files"


class ResourceCreationConflict(StorageError):
    status_code = status.HTTP_409_CONFLICT
    message = "Resource '{resource}' creation conflict"

    def __init__(self, resource: str | ResourcePath):
        super().__init__(resource=resource)
        self.resource = resource


class ParentDirectoryDoesNotExist(ResourceCreationConflict):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Parent directory '{resource}' does not exist"


class ResourceNotFound(ResourceCreationConflict):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Resource '{resource}' not found"


class ResourceAlreadyExists(ResourceCreationConflict):
    message = "Resource '{resource}' already exists"


class InvalidFileName(ResourceCreationConflict):
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Invalid file name '{resource}'"


class FileTooLarge(StorageError):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    message = "File size is too large"


class InvalidPath(StorageError):
    status_code = status.HTTP_400_BAD_REQUEST
