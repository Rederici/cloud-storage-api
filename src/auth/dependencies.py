from typing import Annotated

from dishka import FromDishka, Provider, Scope, provide
from dishka.integrations.fastapi import inject
from fastapi import Depends
from redis.asyncio import Redis

from security import security
from src.config import Config
from src.storage import StorageService
from src.user import UserService
from src.user.models import User

from .exceptions import InvalidTokenError
from .repository import SessionRepository
from .service import AuthService, SessionService


class AuthProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def repository(self, redis: Redis) -> SessionRepository:
        return SessionRepository(redis_client=redis)

    @provide(scope=Scope.REQUEST)
    def session_service(self, config: Config, session_repo: SessionRepository) -> SessionService:
        return SessionService(config, session_repo)

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
