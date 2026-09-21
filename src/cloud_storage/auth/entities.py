from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, eq=False)
class Account:
    id: int
    username: str
    password_hash: str
    is_active: bool = True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Account):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(slots=True, eq=False)
class Session:
    token: str
    account_id: int
    created_at: datetime
    last_access: datetime

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Session):
            return NotImplemented

        return self.token == other.token

    def __hash__(self) -> int:
        return hash(self.token)


@dataclass(frozen=True, slots=True)
class Authorized:
    username: str
    token: str
