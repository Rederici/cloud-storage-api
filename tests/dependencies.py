from collections.abc import AsyncGenerator

from dishka import Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from src.core import InfrastructureProvider


class TestInfrastructureProvider(InfrastructureProvider):
    @provide(scope=Scope.SESSION)
    async def async_connection(self, engine: AsyncEngine) -> AsyncGenerator[AsyncConnection]:
        async with engine.connect() as connection:
            trans = await connection.begin()
            try:
                yield connection
            finally:
                await trans.rollback()

    @provide(scope=Scope.SESSION, override=True)
    async def async_session_maker(self, connection: AsyncConnection) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
