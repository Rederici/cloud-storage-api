import secrets
from datetime import UTC, datetime

from .entities import Account, Authorized, Session
from .exceptions import AccountNotFound, InvalidCredentialsError
from .ports import AccountRepository, PasswordHasher, SessionRepository


class AuthService:
    def __init__(
        self,
        account_repo: AccountRepository,
        session_repo: SessionRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._account_repo = account_repo
        self._session_repo = session_repo
        self._hasher = password_hasher

    async def register(self, username: str, password: str) -> Authorized:
        account = await self._account_repo.create(username, self._hasher.hash(password))
        token = await self._create_session(account.id)
        return Authorized(username=account.username, token=token)

    async def login(self, username: str, password: str) -> Authorized:
        account = await self._account_repo.find_by_username(username)
        password_hash = account.password_hash if account else None
        if not self._hasher.verify(password, password_hash) or not account:
            raise InvalidCredentialsError()

        token = await self._create_session(account.id)
        return Authorized(username=account.username, token=token)

    async def logout(self, token: str) -> None:
        await self._session_repo.delete(token)

    async def find_session(self, token: str) -> Session | None:
        return await self._session_repo.get(token)

    async def touch_session(self, token: str) -> None:
        session = await self._session_repo.get(token)
        if session is None:
            return

        session.last_access = datetime.now(UTC)
        await self._session_repo.save(session)

    async def get_account(self, id: int) -> Account:
        account = await self._account_repo.find_by_id(id)
        if account is None:
            raise AccountNotFound()

        return account

    async def _create_session(self, account_id: int) -> str:
        token = self._generate_token()
        now = datetime.now(UTC)
        await self._session_repo.save(
            Session(
                token=token,
                account_id=account_id,
                created_at=now,
                last_access=now,
            )
        )
        return token

    @staticmethod
    def _generate_token() -> str:
        return secrets.token_hex(32)
