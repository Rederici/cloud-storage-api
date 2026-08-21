from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import Depends, Query, UploadFile
from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    PlainSerializer,
    ValidateAs,
    WithJsonSchema,
    WrapValidator,
)
from pydantic_core.core_schema import ValidatorFunctionWrapHandler

from src.storage.types import StoredResource

from .types import ResourcePath, ResourceType


def validate_resource_path(
    value: Any,
    handler: ValidatorFunctionWrapHandler,
) -> ResourcePath:
    if isinstance(value, ResourcePath):
        return value

    if not isinstance(value, str):
        raise ValueError("Resource path must be a string")

    value = value.strip()

    if not value.startswith("/"):
        value = f"/{value}"

    return ResourcePath(value)


def validate_path_as(type: Literal["file", "directory", "any"] = "any"):
    def validator(path: ResourcePath) -> ResourcePath:
        if type == "any":
            return path

        if path.is_file and type == "directory":
            raise ValueError("Path must point to a directory")

        if path.is_directory and type == "file":
            raise ValueError("Path must point to a file")

        return path

    return validator


type _AnyPath = Annotated[
    ResourcePath,
    WrapValidator(
        validate_resource_path,
        json_schema_input_type=str | None,
    ),
    PlainSerializer(
        lambda path: path.value,
        return_type=str,
    ),
    WithJsonSchema({"type": "string"}),
]

type AnyPath = Annotated[
    _AnyPath,
    AfterValidator(validate_path_as("any")),
]

type FilePath = Annotated[
    _AnyPath,
    AfterValidator(validate_path_as("file")),
]

type DirPath = Annotated[
    _AnyPath,
    AfterValidator(validate_path_as("directory")),
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
