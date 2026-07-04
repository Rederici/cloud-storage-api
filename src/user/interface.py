from typing import Protocol

from .models import User


class IUserRepository(Protocol):
    async def create(self, username: str, password_hash: str) -> User: ...

    async def find_by_id(self, id: int) -> User | None: ...

    async def find_by_username(self, username: str) -> User | None: ...
