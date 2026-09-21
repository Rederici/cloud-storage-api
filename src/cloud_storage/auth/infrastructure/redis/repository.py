import json
from datetime import datetime, timedelta

from redis.asyncio import Redis

from cloud_storage.auth.entities import Session


class RedisSessionRepository:
    def __init__(self, redis_client: Redis, ttl: timedelta) -> None:
        self._redis = redis_client
        self._ttl = ttl

    async def save(self, session: Session) -> None:
        await self._redis.set(
            self._session_key(session.token),
            self._serialize(session),
            ex=self._ttl,
        )

    async def get(self, token: str) -> Session | None:
        raw = await self._redis.get(self._session_key(token))
        if raw is None:
            return None

        return self._deserialize(token, raw)

    async def delete(self, token: str) -> None:
        await self._redis.delete(self._session_key(token))

    @staticmethod
    def _session_key(token: str) -> str:
        return f"session:{token}"

    @staticmethod
    def _serialize(session: Session) -> str:
        return json.dumps(
            {
                "account_id": session.account_id,
                "created_at": session.created_at.isoformat(),
                "last_access": session.last_access.isoformat(),
            }
        )

    @staticmethod
    def _deserialize(token: str, raw: bytes | str) -> Session:
        payload = json.loads(raw)
        return Session(
            token=token,
            account_id=payload["account_id"],
            created_at=datetime.fromisoformat(payload["created_at"]),
            last_access=datetime.fromisoformat(payload["last_access"]),
        )
