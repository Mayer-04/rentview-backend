from enum import Enum
from functools import lru_cache

from pydantic import (
    AliasChoices,
    AnyHttpUrl,
    BaseModel,
    Field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class AppSettings(BaseModel):
    name: str = Field(default="Arrendamos")
    version: str = Field(default="0.1.0")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080, ge=1, le=65535)
    reload: bool = Field(default=False)
    workers: int | None = Field(default=None, ge=1)
    openapi_url: str | None = Field(default="/openapi.json")
    api_prefix: str = Field(default="/api/v1")


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.prod"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "POSTGRES_URL"),
    )
    pool_size: int = Field(
        default=10,
        ge=1,
        validation_alias=AliasChoices("DATABASE_POOL_SIZE", "DATABASE__POOL_SIZE"),
    )
    max_overflow: int = Field(
        default=20,
        ge=0,
        validation_alias=AliasChoices("DATABASE_MAX_OVERFLOW", "DATABASE__MAX_OVERFLOW"),
    )
    pool_min_size: int | None = Field(
        default=None,
        ge=1,
        validation_alias=AliasChoices(
            "DATABASE_POOL_MIN_SIZE",
            "POSTGRES_POOL_MIN_SIZE",
        ),
    )
    pool_max_size: int | None = Field(
        default=None,
        ge=1,
        validation_alias=AliasChoices(
            "DATABASE_POOL_MAX_SIZE",
            "POSTGRES_POOL_MAX_SIZE",
        ),
    )
    pool_timeout: float = Field(
        default=30.0,
        ge=0,
        validation_alias=AliasChoices(
            "DATABASE_POOL_TIMEOUT",
            "POSTGRES_POOL_TIMEOUT",
        ),
    )
    echo: bool = Field(
        default=False,
        validation_alias=AliasChoices("DATABASE_ECHO", "DATABASE__ECHO"),
    )


class CorsSettings(BaseModel):
    allow_origins: list[AnyHttpUrl] = Field(default_factory=list)
    allow_credentials: bool = Field(default=False)
    allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    allow_headers: list[str] = Field(default_factory=lambda: ["*"])


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.prod"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Environment = Field(
        default=Environment.LOCAL,
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )
    debug: bool = Field(default=False, validation_alias=AliasChoices("APP_DEBUG", "DEBUG"))

    log_level: str = Field(default="info")
    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    cors: CorsSettings = Field(default_factory=CorsSettings)

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        return self.environment is Environment.TEST


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
