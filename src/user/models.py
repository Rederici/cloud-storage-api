from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from persistance.sqlalchemy.models import Base, IdMixin


class User(IdMixin, Base):
    __tablename__ = 'user'

    username: Mapped[str] = mapped_column(String(24), unique=True)
    password_hash: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
