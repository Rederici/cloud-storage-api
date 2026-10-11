from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from cloud_storage.infrastructure.sqlalchemy.models import Base, IdMixin


class Account(IdMixin, Base):
    __tablename__ = "account"

    username: Mapped[str] = mapped_column(String(24), unique=True)
    password_hash: Mapped[str] = mapped_column(String)
