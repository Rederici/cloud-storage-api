from starlette import status

from src.core import AppError

from .types import ResourcePath


class StorageError(AppError):
    pass


class ResourceCreationConflict(StorageError):
    status_code = status.HTTP_409_CONFLICT
    message = "Resource '{resource}' creation conflict"

    def __init__(self, resource: str | ResourcePath):
        super().__init__(resource=resource)
        self.resource = resource


class ParentDirectoryDoesNotExist(ResourceCreationConflict):
    status_code = status.HTTP_404_NOT_FOUND
    message = "Parent directory '{resource}' does not exist"


class ResourceAlreadyExists(ResourceCreationConflict):
    message = "Resource '{resource}' already exists"
