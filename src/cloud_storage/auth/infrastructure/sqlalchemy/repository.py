from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cloud_storage.auth.entities import Account
from cloud_storage.auth.exceptions import AccountAlreadyExists

from .models import Account as AccountORM


class SQLAlchemyAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, username: str, password_hash: str) -> Account:
        account = AccountORM(username=username, password_hash=password_hash)
        self._session.add(account)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            if getattr(e.orig, "sqlstate", None) == "23505":
                raise AccountAlreadyExists() from None
            raise

        await self._session.refresh(account)
        return self._to_domain(account)

    async def find_by_id(self, id: int) -> Account | None:
        query = select(AccountORM).where(AccountORM.id == id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row is not None else None

    async def find_by_username(self, username: str) -> Account | None:
        query = select(AccountORM).where(AccountORM.username == username)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row is not None else None

    @staticmethod
    def _to_domain(account: AccountORM) -> Account:
        return Account(
            id=account.id,
            username=account.username,
            password_hash=account.password_hash,
            is_active=account.is_active,
        )
