import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, ClassVar, Self

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


@dataclass(frozen=True, slots=True)
class ResourcePath:
    value: str

    separator: ClassVar[str] = "/"

    def __post_init__(self) -> None:
        self._validate(self.value)

    def _spawn(self, value: str) -> Self:
        return type(self)(value=value)

    @classmethod
    def _validate(cls, value) -> None:
        if not isinstance(value, str):
            raise TypeError("Path must be a string")

        if not value:
            raise ValueError("Path must not be empty")

        if not value.startswith(cls.separator):
            raise ValueError(f"Resource path must start with '{cls.separator}'")

        if value == cls.separator:
            return

        if "\\" in value:
            raise ValueError("Backslash is not allowed")

        if cls.separator * 2 in value:
            raise ValueError("Empty path segments are not allowed")

        parts = value.strip(cls.separator).split(cls.separator)
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError("Invalid path segment")

    @property
    def is_root(self) -> bool:
        return self.value == self.separator

    @property
    def is_directory(self) -> bool:
        return self.value.endswith(self.separator)

    @property
    def is_file(self) -> bool:
        return not self.is_directory

    @property
    def name(self) -> str:
        if self.is_root:
            return ""

        return self.value.removesuffix(
            self.separator,
        ).rsplit(
            self.separator,
            maxsplit=1,
        )[-1]

    @property
    def parent(self) -> Self:
        if self.is_root:
            return self

        raw = self.value.removesuffix(self.separator)
        parent_value, _, _ = raw.rpartition(self.separator)

        if not parent_value:
            return self._spawn(self.separator)

        return self._spawn(f"{parent_value}{self.separator}")

    def __truediv__(
        self,
        other: str | ResourcePath,
    ) -> Self:
        if self.is_file:
            raise ValueError("Children can only be added to a directory")

        if isinstance(other, ResourcePath):
            other_value = other.value.lstrip(self.separator)
        elif isinstance(other, str):
            other_value = other.lstrip(self.separator)
        else:
            return NotImplemented

        if not other_value:
            return self

        return self._spawn(f"{self.value}{other_value}")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.value!r})"

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        def validate(value: object) -> ResourcePath:
            if isinstance(value, cls):
                return value

            if not isinstance(value, str):
                raise ValueError("Resource path must be a string")

            return cls(value)

        return core_schema.no_info_plain_validator_function(
            validate,
            json_schema_input_schema=core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda value: value.value,
                return_schema=core_schema.str_schema(),
                when_used="always",
            ),
        )


@dataclass(frozen=True, slots=True)
class UserSpacePath(ResourcePath):
    user_id: int

    def __post_init__(self) -> None:
        super().__post_init__()

        if self.user_id <= 0:
            raise ValueError("user_id must be greater than zero")

    @classmethod
    def from_storage_key(cls, storage_key: str) -> Self:
        if not isinstance(storage_key, str):
            raise TypeError("Storage key must be a string")

        m = re.fullmatch(
            rf"^user-(?P<user_id>[1-9]\d*)-files"
            rf"(?P<path>{re.escape(cls.separator)}.*)?$",
            storage_key,
        )

        if not m:
            raise ValueError("Invalid user space path")

        return cls(
            value=m["path"] or cls.separator,
            user_id=int(m["user_id"]),
        )

    def _spawn(self, value: str) -> Self:
        return type(self)(
            value=value,
            user_id=self.user_id,
        )

    @property
    def public_path(self) -> ResourcePath:
        return ResourcePath(self.value)

    @property
    def user_root(self) -> str:
        return f"user-{self.user_id}-files{self.separator}"

    @property
    def storage_key(self) -> str:
        if self.is_root:
            return self.user_root

        return f"{self.user_root}{self.value.lstrip('/')}"


class ResourceType(StrEnum):
    FILE = "file"
    DIRECTORY = "directory"


@dataclass(frozen=True, slots=True)
class StoredResource:
    path: ResourcePath
    size: int
    type: ResourceType
