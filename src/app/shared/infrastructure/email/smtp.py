from email.message import EmailMessage as MIMEEmailMessage
import smtplib
from typing import Iterable

from app.shared.application.email import EmailDeliveryError, EmailMessage, EmailSender
from app.shared.infrastructure.logger import logger
from app.shared.infrastructure.settings import EmailSettings


class SmtpEmailSender(EmailSender):
    """SMTP implementation tuned for Gmail with STARTTLS by default."""

    def __init__(self, settings: EmailSettings) -> None:
        self._settings = settings

    def send(self, message: EmailMessage) -> None:
        if not self._settings.enabled:
            logger.info("Email sending is disabled; skipping delivery.")
            return

        recipients = self._normalize_recipients(message.to)
        if not recipients:
            raise EmailDeliveryError("No se proporcionaron destinatarios para el correo.")

        from_email = (message.from_email or self._settings.from_email or "").strip()
        if not from_email:
            raise EmailDeliveryError("Configura EMAIL_FROM para poder enviar correos.")

        subject = message.subject.strip()
        if not subject:
            raise EmailDeliveryError("El asunto del correo no puede estar vacío.")

        smtp_username = (self._settings.smtp_username or "").strip()
        smtp_password = (self._settings.smtp_password or "").strip()
        if not smtp_username or not smtp_password:
            raise EmailDeliveryError("Faltan las credenciales SMTP para enviar correos.")

        mime_message = self._build_message(
            message=message,
            recipients=recipients,
            from_email=from_email,
        )

        try:
            self._send_via_smtp(
                mime_message=mime_message,
                username=smtp_username,
                password=smtp_password,
            )
        except Exception as exc:  # pragma: no cover - network failures
            logger.exception("No se pudo enviar el correo mediante SMTP")
            raise EmailDeliveryError("No se pudo enviar el correo") from exc

    def _build_message(
        self,
        *,
        message: EmailMessage,
        recipients: list[str],
        from_email: str,
    ) -> MIMEEmailMessage:
        mime = MIMEEmailMessage()
        mime["From"] = from_email
        mime["To"] = ", ".join(recipients)
        mime["Subject"] = message.subject

        reply_to = message.reply_to or self._settings.reply_to
        if reply_to:
            mime["Reply-To"] = reply_to

        mime.set_content(message.body)
        if message.html_body:
            mime.add_alternative(message.html_body, subtype="html")

        return mime

    def _send_via_smtp(
        self,
        *,
        mime_message: MIMEEmailMessage,
        username: str,
        password: str,
    ) -> None:
        smtp_class = smtplib.SMTP_SSL if self._settings.smtp_use_ssl else smtplib.SMTP
        with smtp_class(
            host=self._settings.smtp_host,
            port=self._settings.smtp_port,
            timeout=self._settings.smtp_timeout,
        ) as client:
            client.ehlo()
            if self._settings.smtp_use_tls and not self._settings.smtp_use_ssl:
                client.starttls()
                client.ehlo()
            client.login(username, password)
            client.send_message(mime_message)

    @staticmethod
    def _normalize_recipients(recipients: Iterable[str] | str) -> list[str]:
        if isinstance(recipients, str):
            normalized = [recipients.strip()] if recipients.strip() else []
        else:
            normalized = [
                recipient.strip() for recipient in recipients if recipient and recipient.strip()
            ]
        return [recipient for recipient in normalized if recipient]
