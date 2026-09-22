import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


class Argon2PasswordHasher:
    def __init__(self) -> None:
        self._hasher = PasswordHasher()
        self._dummy = self._hasher.hash(secrets.token_hex(32))

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, hashed_password: str | None) -> bool:
        try:
            self._hasher.verify(hashed_password or self._dummy, password)
            return True
        except VerifyMismatchError:
            return False
