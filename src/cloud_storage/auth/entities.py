from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(slots=True, eq=False)
class Principal:
    id: int
    username: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Principal):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(frozen=True, slots=True)
class Credentials:
    account: Principal
    password_hash: str


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

    def touch(self):
        self.last_access = datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class Authorized:
    username: str
    token: str
