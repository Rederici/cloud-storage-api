from dishka import Provider, Scope, provide

from .ports import AccountRepository, PasswordHasher, SessionRepository
from .service import AuthService


class AuthProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def service(
        self,
        account_repo: AccountRepository,
        session_repo: SessionRepository,
        password_hasher: PasswordHasher,
    ) -> AuthService:
        return AuthService(
            account_repo=account_repo,
            session_repo=session_repo,
            password_hasher=password_hasher,
        )
