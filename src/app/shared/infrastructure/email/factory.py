from __future__ import annotations

from functools import lru_cache

from app.shared.application.email import EmailSender
from app.shared.infrastructure.email.smtp import SmtpEmailSender
from app.shared.infrastructure.logger import logger
from app.shared.infrastructure.settings import EmailProvider, settings


class UnsupportedEmailProviderError(RuntimeError):
    """Raised when the configured email provider is not supported."""


@lru_cache(maxsize=1)
def get_email_sender() -> EmailSender | None:
    """Return a singleton email sender based on the current configuration."""
    email_settings = settings.email
    if not email_settings.enabled:
        logger.info("Email service disabled via EMAIL_ENABLED; notifications will be skipped.")
        return None

    if email_settings.provider is EmailProvider.SMTP:
        return SmtpEmailSender(email_settings)

    raise UnsupportedEmailProviderError(
        f"Proveedor de email no soportado: {email_settings.provider}"
    )
