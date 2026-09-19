import secrets
from datetime import timedelta

from cloud_storage.security import DUMMY_HASH, hash_password, verify_password
from cloud_storage.storage import StorageService

from .exceptions import InvalidCredentialsError, UserAlreadyExists, UserNotFound
from .interface import ISessionRepository, IUserRepository
from .models import User
from .schemas import AuthorizedDTO, TokenPayload


class SessionService:
    def __init__(self, session_repo: ISessionRepository, session_ttl: timedelta) -> None:
        self._session_repo = session_repo
        self._session_ttl = session_ttl

    @staticmethod
    def generate_token() -> str:
        return secrets.token_hex(32)

    async def touch(self, token: str) -> None:
        await self._session_repo.touch(token, self._session_ttl)

    async def create_session(self, user_id: int) -> str:
        token = self.generate_token()
        await self._session_repo.create(user_id=user_id, token=token, ttl=self._session_ttl)
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


class UserService:
    def __init__(self, user_repo: IUserRepository) -> None:
        self._user_repo = user_repo

    async def create(self, username: str, password: str) -> User:
        if await self._user_repo.find_by_username(username) is not None:
            raise UserAlreadyExists()

        password_hash = hash_password(password)
        user = await self._user_repo.create(username, password_hash)
        return user

    async def get_by_id(self, id: int) -> User:
        user = await self._user_repo.find_by_id(id)
        if user is None:
            raise UserNotFound()
        return user

    async def find_by_username(self, username: str) -> User | None:
        return await self._user_repo.find_by_username(username)
