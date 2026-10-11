from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True, slots=True)
class UploadResource:
    filename: str
    file: BinaryIO
    content_type: str | None
    size: int | None
