from datetime import timedelta
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    PyprojectTomlConfigSettingsSource,
    SettingsConfigDict,
)


class PostgresConfig(BaseModel):
    model_config = ConfigDict(
        validate_by_alias=True,
        validate_by_name=True,
        populate_by_name=True,
    )

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="postgres", alias="name")
    username: str = Field(default="postgres", alias="user")
    password: str = Field(default="postgres", alias="pass")

    def get_dsn(self, sync: bool = False) -> str:
        engine = "psycopg" if sync else "asyncpg"
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


class CorsConfig(BaseModel):
    allow_origins: list[str] = Field(default_factory=lambda: ["http://127.0.0.1:5173", "http://localhost:5173"])
    allow_credentials: bool = True
    allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    allow_headers: list[str] = Field(default_factory=lambda: ["*"])


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
    cors: CorsConfig = Field(default_factory=CorsConfig)
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
            init_settings,
            env_settings,
            dotenv_settings,
            PyprojectTomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )
