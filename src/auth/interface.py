from datetime import timedelta
from typing import Protocol

from .schemas import TokenPayload


class ISessionRepository(Protocol):
    async def create(self, user_id: int, token: str, ttl: timedelta | int) -> None: ...

    async def get(self, token: str) -> TokenPayload | None: ...

    async def touch(self, token: str, ttl: timedelta | int) -> TokenPayload | None: ...

    async def delete(self, token: str) -> None: ...
