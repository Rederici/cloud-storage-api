from pathlib import Path
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, Field

from src.storage.types import StoredResource

from .types import ResourcePath, ResourceType

ResourceSize = Annotated[int, Field(ge=0)]

ResourceName = Annotated[Path, Field(pattern=r"^(?:[^/]+/)+$")]


def ensure_file(path: ResourcePath) -> ResourcePath:
    if path.is_directory:
        raise ValueError("Path must point to a file")

    return path


def ensure_directory(path: ResourcePath) -> ResourcePath:
    if not path.is_directory:
        raise ValueError("Path must point to a directory")

    return path


FileResourcePath = Annotated[
    ResourcePath,
    AfterValidator(ensure_file),
]

DirectoryResourcePath = Annotated[
    ResourcePath,
    AfterValidator(ensure_directory),
]


class PathRequest(BaseModel):
    path: ResourcePath


class FileRequest(BaseModel):
    path: FileResourcePath


class DirectoryRequest(BaseModel):
    path: DirectoryResourcePath


class ResourceResponse(BaseModel):
    path: str
    name: str
    size: ResourceSize
    type: ResourceType

    @classmethod
    def from_domain(cls, resource: StoredResource) -> ResourceResponse:
        return ResourceResponse(
            path=str(resource.path.parent),
            name=resource.path.name,
            size=resource.size,
            type=resource.type,
        )


ResourcesResponse = list[ResourceResponse]


class DirectoryResponse(BaseModel):
    path: ResourcePath
    name: str
    type: ResourceType = ResourceType.DIRECTORY
