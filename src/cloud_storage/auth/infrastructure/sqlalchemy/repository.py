from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from cloud_storage.auth.entities import Credentials, Principal
from cloud_storage.auth.exceptions import AccountAlreadyExists

from .models import Account as AccountORM


class SQLAlchemyAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, username: str, password_hash: str) -> Principal:
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
        return self._to_domain_principal(account)

    async def find_by_id(self, id: int) -> Principal | None:
        query = select(AccountORM).where(AccountORM.id == id)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return self._to_domain_principal(row) if row is not None else None

    async def find_by_username(self, username: str) -> Principal | None:
        query = select(AccountORM).where(AccountORM.username == username)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        return self._to_domain_principal(row) if row is not None else None

    async def find_credentials_by_username(self, username: str) -> Credentials | None:
        query = select(AccountORM).where(AccountORM.username == username)
        result = await self._session.execute(query)
        row = result.scalar_one_or_none()
        if row is None:
            return None

        return Credentials(
            account=self._to_domain_principal(row),
            password_hash=row.password_hash,
        )

    @staticmethod
    def _to_domain_principal(account: AccountORM) -> Principal:
        return Principal(
            id=account.id,
            username=account.username,
        )
