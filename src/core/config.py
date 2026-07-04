from datetime import timedelta
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


class PostgresConfig(BaseModel):
    model_config = ConfigDict(validate_by_alias=True, validate_by_name=True, populate_by_name=True)

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="postgres", alias="name")
    username: str = Field(default="postgres", alias="user")
    password: str = Field(default="postgres", alias="pass")

    def get_dsn(self, sync: bool = False) -> str:
        engine = "psycopg2" if sync else "asyncpg"
        return f"postgresql+{engine}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    database: int = Field(default=0, ge=0)

    def get_dsn(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.database}"


class MinioConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=9000)
    access_key_id: str = Field(default="minio")
    secret_access_key: str = Field(default="minio")
    ssl: bool = Field(default=True)
    bucket: str = Field(default="ResourcesBucket")

    @property
    def url(self) -> str:
        return f"{'https' if self.ssl else 'http'}://{self.host}:{self.port}"


class Env(StrEnum):
    PROD = "prod"
    DEV = "dev"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    minio: MinioConfig = Field(default_factory=MinioConfig)
    session_ttl: timedelta = Field(default=timedelta(days=7))
    env: Env = Field(default=Env.DEV)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ):
        return (
            PyprojectTomlConfigSettingsSource(settings_cls),
            env_settings,
            init_settings,
            dotenv_settings,
            file_secret_settings,
        )
