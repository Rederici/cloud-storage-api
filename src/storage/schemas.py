from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query, UploadFile
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    WithJsonSchema,
)

from src.storage.types import StoredResource

from .types import ResourcePath, ResourceType


def parse_resource_path(value: object) -> ResourcePath:
    if isinstance(value, ResourcePath):
        return value

    if not isinstance(value, str):
        raise ValueError("Resource path must be a string")

    if not value.startswith("/"):
        value = f"/{value}"

    return ResourcePath(value)


def validate_file_path(path: ResourcePath) -> ResourcePath:
    if path.is_directory:
        raise ValueError("Path must point to a file")

    return path


def validate_directory_path(path: ResourcePath) -> ResourcePath:
    if path.is_file:
        raise ValueError("Path must point to a directory")

    return path


type _AnyPathValue = Annotated[
    ResourcePath,
    BeforeValidator(parse_resource_path),
    PlainSerializer(
        lambda path: path.value,
        return_type=str,
    ),
    WithJsonSchema({"type": "string"}),
]

type _FilePathValue = Annotated[
    _AnyPathValue,
    AfterValidator(validate_file_path),
]

type _DirPathValue = Annotated[
    _AnyPathValue,
    AfterValidator(validate_directory_path),
]


class _AnyPathQuery(BaseModel):
    path: _AnyPathValue = Field(default="/", validate_default=True)


class _FilePathQuery(BaseModel):
    path: _FilePathValue


class _DirPathQuery(BaseModel):
    path: _DirPathValue = Field(default="/", validate_default=True)


def get_any_path(query: Annotated[_AnyPathQuery, Query()]) -> ResourcePath:
    return query.path


def get_file_path(query: Annotated[_FilePathQuery, Query()]) -> ResourcePath:
    return query.path


def get_dir_path(query: Annotated[_DirPathQuery, Query()]) -> ResourcePath:
    return query.path


type AnyPath = Annotated[
    _AnyPathValue,
    Depends(get_any_path),
]

type FilePath = Annotated[
    _FilePathValue,
    Depends(get_file_path),
]

type DirPath = Annotated[
    _DirPathValue,
    Depends(get_dir_path),
]


class ResourceResponse(BaseModel):
    path: str
    name: str
    size: int
    type: ResourceType

    @classmethod
    def from_domain(cls, resource: StoredResource) -> ResourceResponse:
        return ResourceResponse(
            path=str(resource.path.parent),
            name=resource.path.name,
            size=resource.size,
            type=resource.type,
        )


class DirectoryResponse(BaseModel):
    path: ResourcePath
    name: str
    type: ResourceType = ResourceType.DIRECTORY


def validate_upload_filename(
    file: UploadFile,
) -> UploadFile:
    filename = file.filename

    if not filename:
        raise ValueError("Upload filename must not be empty")

    if filename.startswith("/"):
        raise ValueError("Upload filename must not be absolute path")

    try:
        path = ResourcePath(f"/{filename}")
    except (TypeError, ValueError) as e:
        raise ValueError(str(e)) from e

    if path.is_directory:
        raise ValueError("Upload filename must not be a directory")
    return file


def validate_unique_filenames(
    files: list[ValidatedUploadFile],
) -> list[UploadFile]:
    filenames: set[str] = set()

    for file in files:
        assert file.filename is not None

        if file.filename in filenames:
            raise ValueError(f"Filename is duplicated: {file.filename!r}")

        filenames.add(file.filename)

    return files


type ValidatedUploadFile = Annotated[
    UploadFile,
    AfterValidator(validate_upload_filename),
]


type ValidatedUploadFiles = Annotated[
    list[UploadFile],
    AfterValidator(validate_unique_filenames),
]
