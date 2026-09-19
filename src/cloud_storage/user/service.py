from cloud_storage.security import hash_password

from .exceptions import UserAlreadyExists, UserNotFound
from .interface import IUserRepository
from .models import User


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
