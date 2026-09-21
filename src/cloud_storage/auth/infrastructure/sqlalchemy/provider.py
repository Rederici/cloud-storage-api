from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from cloud_storage.auth.ports import AccountRepository

from .repository import SQLAlchemyAccountRepository


class SQLAlchemyAccountRepositoryProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def repository(self, session: AsyncSession) -> AccountRepository:
        return SQLAlchemyAccountRepository(session)
