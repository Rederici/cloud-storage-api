from src.exceptions import AppError


class StorageError(AppError):
    pass


class ContentSizeExceeded(AppError):
    message = "Body is too large"


class TooManyFiles(AppError):
    message = "Too many files"


class ResourceCreationConflict(StorageError):
    message = "Resource '{resource}' creation conflict"


class ParentDirectoryDoesNotExist(ResourceCreationConflict):
    message = "Parent directory '{resource}' does not exist"


class ResourceNotFound(ResourceCreationConflict):
    message = "Resource '{resource}' not found"


class ResourceAlreadyExists(ResourceCreationConflict):
    message = "Resource '{resource}' already exists"


class InvalidFileName(ResourceCreationConflict):
    message = "Invalid file name '{resource}'"


class FileTooLarge(StorageError):
    message = "File size is too large"


class InvalidPath(StorageError):
    message = "Invalid path '{path}'"
