from dishka import Provider, Scope, provide

from cloud_storage.storage import StorageService

from .ports import AccountRepository, SessionRepository
from .service import AuthService


class AuthProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def service(
        self,
        account_repo: AccountRepository,
        session_repo: SessionRepository,
        storage_service: StorageService,
    ) -> AuthService:
        return AuthService(
            account_repo=account_repo,
            session_repo=session_repo,
            storage_service=storage_service,
        )
