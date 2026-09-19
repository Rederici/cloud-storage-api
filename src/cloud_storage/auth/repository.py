from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User
from .schemas import TokenPayload


class SessionRepository:
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    @staticmethod
    def get_session_key(token: str) -> str:
        return f"session:{token}"

    async def create(self, user_id: int, token: str, ttl: timedelta | int) -> None:
        created_at = datetime.now(UTC)
        await self._redis.set(
            self.get_session_key(token),
            TokenPayload(
                user_id=user_id,
                created_at=created_at,
                last_access=created_at,
            ).model_dump_json(),
            ex=ttl,
        )

    async def get(self, token: str) -> TokenPayload | None:
        raw = await self._redis.get(self.get_session_key(token))
        if raw is None:
            return None
        return TokenPayload.model_validate_json(raw)

    async def touch(self, token: str, ttl: timedelta | int) -> TokenPayload | None:
        payload = await self.get(token)
        if payload is None:
            return None

        payload.last_access = datetime.now(UTC)
        await self._redis.set(
            self.get_session_key(token),
            payload.model_dump_json(),
            ex=ttl,
        )
        return payload

    async def delete(self, token: str) -> None:
        await self._redis.delete(self.get_session_key(token))


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, username: str, password_hash: str) -> User:
        user = User(username=username, password_hash=password_hash)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def find_by_id(self, id: int) -> User | None:
        query = select(User).where(User.id == id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def find_by_username(self, username: str) -> User | None:
        query = select(User).where(User.username == username)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
