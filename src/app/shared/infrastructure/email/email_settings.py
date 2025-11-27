from enum import Enum

from pydantic import AliasChoices, EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmailProvider(str, Enum):
    SMTP = "smtp"
    RESEND = "resend"


class EmailSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.prod"),
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        case_sensitive=False,
    )

    enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("EMAIL_ENABLED", "EMAIL__ENABLED"),
    )
    provider: EmailProvider = Field(
        default=EmailProvider.SMTP,
        validation_alias=AliasChoices("EMAIL_PROVIDER", "EMAIL__PROVIDER"),
    )
    from_email: EmailStr | None = Field(
        default=None,
        validation_alias=AliasChoices("EMAIL_FROM", "SMTP_FROM", "EMAIL__FROM"),
    )
    reply_to: EmailStr | None = Field(
        default=None,
        validation_alias=AliasChoices("EMAIL_REPLY_TO", "EMAIL__REPLY_TO"),
    )
    smtp_host: str = Field(
        default="smtp.gmail.com",
        validation_alias=AliasChoices("SMTP_HOST", "EMAIL_SMTP_HOST", "SMTP__HOST"),
    )
    smtp_port: int = Field(
        default=587,
        ge=1,
        le=65535,
        validation_alias=AliasChoices("SMTP_PORT", "EMAIL_SMTP_PORT", "SMTP__PORT"),
    )
    smtp_username: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SMTP_USERNAME", "EMAIL_SMTP_USERNAME", "SMTP__USERNAME"
        ),
    )
    smtp_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SMTP_PASSWORD", "EMAIL_SMTP_PASSWORD", "SMTP__PASSWORD"
        ),
    )
    smtp_use_tls: bool = Field(
        default=True,
        validation_alias=AliasChoices(
            "SMTP_USE_TLS", "EMAIL_SMTP_USE_TLS", "SMTP__USE_TLS"
        ),
    )
    smtp_use_ssl: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "SMTP_USE_SSL", "EMAIL_SMTP_USE_SSL", "SMTP__USE_SSL"
        ),
    )
    smtp_timeout: float = Field(
        default=30.0,
        ge=1,
        validation_alias=AliasChoices(
            "SMTP_TIMEOUT", "EMAIL_SMTP_TIMEOUT", "SMTP__TIMEOUT"
        ),
    )
