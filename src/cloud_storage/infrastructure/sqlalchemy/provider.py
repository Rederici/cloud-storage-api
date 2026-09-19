from collections.abc import AsyncGenerator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from cloud_storage.config import Config


class SQLAlchemyProvider(Provider):
    @provide(scope=Scope.APP)
    async def async_engine(self, config: Config) -> AsyncGenerator[AsyncEngine]:
        engine = create_async_engine(config.postgres.get_dsn(sync=False))
        try:
            yield engine
        finally:
            await engine.dispose()

    @provide(scope=Scope.APP)
    def async_session_maker(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(bind=engine)

    @provide(scope=Scope.REQUEST)
    async def async_session(self, session_maker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession]:
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
