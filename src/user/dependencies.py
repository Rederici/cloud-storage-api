from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from .repository import UserRepository
from .service import UserService


class UserProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def repository(self, session: AsyncSession) -> UserRepository:
        return UserRepository(session)

    @provide(scope=Scope.REQUEST)
    async def service(self, repository: UserRepository) -> UserService:
        return UserService(repository)
