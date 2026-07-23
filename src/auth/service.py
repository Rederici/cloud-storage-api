import secrets

from src.core import Config
from src.core.security import DUMMY_HASH, verify_password
from src.storage import StorageService
from src.user.service import UserService

from .exceptions import InvalidCredentialsError
from .interface import ISessionRepository
from .schemas import AuthorizedDTO, TokenPayload


class SessionService:
    def __init__(self, config: Config, session_repo: ISessionRepository) -> None:
        self._session_repo = session_repo
        self._config = config

    @staticmethod
    def generate_token() -> str:
        return secrets.token_hex(32)

    async def touch(self, token: str) -> None:
        await self._session_repo.touch(token, self._config.session_ttl)

    async def create_session(self, user_id: int) -> str:
        token = self.generate_token()
        await self._session_repo.create(user_id=user_id, token=token, ttl=self._config.session_ttl)
        return token

    async def find_by_token(self, token: str) -> TokenPayload | None:
        return await self._session_repo.get(token)

    async def delete_session(self, token: str) -> None:
        await self._session_repo.delete(token)


class AuthService:
    def __init__(
        self, session_service: SessionService, user_service: UserService, storage_service: StorageService
    ) -> None:
        self._session_service = session_service
        self._user_service = user_service
        self._storage_service = storage_service

    async def register(self, username: str, password: str) -> AuthorizedDTO:
        user = await self._user_service.create(username, password)
        token = await self._session_service.create_session(user.id)
        await self._storage_service.init_root(user.id)
        return AuthorizedDTO(username=username, token=token)

    async def login(self, username: str, password: str) -> AuthorizedDTO:
        user = await self._user_service.find_by_username(username)
        hashed = user.password_hash if user else DUMMY_HASH
        if not verify_password(password, hashed) or not user:
            raise InvalidCredentialsError()
        session = await self._session_service.create_session(user.id)
        return AuthorizedDTO(username=username, token=session)

    async def logout(self, token: str) -> None:
        await self._session_service.delete_session(token)
