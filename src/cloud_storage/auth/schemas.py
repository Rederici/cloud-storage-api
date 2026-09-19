from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CredentialsRequest(BaseModel):
    username: str = Field(min_length=6, max_length=24, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not cls.has_lower(value):
            raise ValueError("Password must contain at least one lowercase letter.")

        if not cls.has_upper(value):
            raise ValueError("Password must contain at least one uppercase letter.")

        if not cls.has_digit(value):
            raise ValueError("Password must contain at least one digit.")

        if not cls.has_special(value):
            raise ValueError("Password must contain at least one special character.")

        return value

    @staticmethod
    def has_upper(s: str) -> bool:
        return any(ch.isupper() for ch in s)

    @staticmethod
    def has_lower(s: str) -> bool:
        return any(ch.islower() for ch in s)

    @staticmethod
    def has_digit(s: str) -> bool:
        return any(ch.isdigit() for ch in s)

    @staticmethod
    def has_special(s: str) -> bool:
        return any(not ch.isalnum() for ch in s)


class TokenPayload(BaseModel):
    user_id: int
    created_at: datetime
    last_access: datetime


class AuthorizedDTO(BaseModel):
    username: str
    token: str


class UserResponse(BaseModel):
    username: str
