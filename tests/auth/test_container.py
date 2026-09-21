from dishka import Scope

from cloud_storage.app.bootstrap import Bootstrap
from cloud_storage.auth.infrastructure.redis.repository import RedisSessionRepository
from cloud_storage.auth.infrastructure.sqlalchemy.repository import SQLAlchemyAccountRepository
from cloud_storage.auth.ports import AccountRepository, SessionRepository
from cloud_storage.auth.service import AuthService


async def test_auth_graph_resolves_from_container(bootstrap: Bootstrap) -> None:
    async with (
        bootstrap.container(scope=Scope.SESSION) as session_container,
        session_container(scope=Scope.REQUEST) as request_container,
    ):
        auth_service = await request_container.get(AuthService)
        account_repo = await request_container.get(AccountRepository)
        session_repo = await request_container.get(SessionRepository)

    assert isinstance(auth_service, AuthService)
    assert isinstance(account_repo, SQLAlchemyAccountRepository)
    assert isinstance(session_repo, RedisSessionRepository)
