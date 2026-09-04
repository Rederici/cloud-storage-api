from collections.abc import AsyncGenerator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)


class TestPostgresProvider(Provider):
    @provide(scope=Scope.SESSION, override=True)
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
