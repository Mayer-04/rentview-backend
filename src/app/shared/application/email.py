from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(slots=True)
class EmailMessage:
    """Small value object representing an outbound email."""

    to: Sequence[str] | str
    subject: str
    body: str
    html_body: str | None = None
    reply_to: str | None = None
    from_email: str | None = None


class EmailSender(Protocol):
    """Abstraction to deliver emails without tying features to a provider."""

    def send(self, message: EmailMessage) -> None: ...


class EmailDeliveryError(Exception):
    """Raised when an email cannot be delivered."""

