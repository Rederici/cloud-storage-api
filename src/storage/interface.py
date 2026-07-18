from typing import Protocol

from .types import UserSpacePath


class IStorageRepository(Protocol):
    async def create_directory(self, path: UserSpacePath) -> None: ...
    async def exists(self, path: UserSpacePath) -> bool: ...
