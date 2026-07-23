import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi.security import APIKeyCookie

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


DUMMY_HASH = _hasher.hash(secrets.token_hex(32))


def verify_password(password: str, password_hash: str) -> bool:
    try:
        _hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False

security = APIKeyCookie(name="sessionId")
