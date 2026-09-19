from typing import Annotated

from dishka import FromDishka, Provider, Scope, provide
from dishka.integrations.fastapi import inject
from fastapi import Depends
from redis.asyncio import Redis

from cloud_storage.config import Config
from cloud_storage.security import security
from cloud_storage.storage import StorageService
from cloud_storage.user import UserService
from cloud_storage.user.models import User

from .exceptions import InvalidTokenError
from .repository import SessionRepository
from .service import AuthService, SessionService


class AuthProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def repository(self, redis: Redis) -> SessionRepository:
        return SessionRepository(redis_client=redis)

    @provide(scope=Scope.REQUEST)
    def session_service(self, config: Config, session_repo: SessionRepository) -> SessionService:
        return SessionService(session_repo, config.app.session.ttl)

    @provide(scope=Scope.REQUEST)
    def auth_service(
        self,
        session_service: SessionService,
        user_service: UserService,
        storage_service: StorageService,
    ) -> AuthService:
        return AuthService(
            session_service=session_service,
            user_service=user_service,
            storage_service=storage_service,
        )


def get_token(credentials: Annotated[str, Depends(security)]) -> str | None:
    return credentials


SessionToken = Annotated[str, Depends(get_token)]


@inject
async def get_current_user(
    token: SessionToken, user_service: FromDishka[UserService], session_service: FromDishka[SessionService]
) -> User:
    session = await session_service.find_by_token(token)
    if session is None:
        raise InvalidTokenError()

    await session_service.touch(token)

    return await user_service.get_by_id(session.user_id)


CurrentUser = Annotated[User, Depends(get_current_user)]
