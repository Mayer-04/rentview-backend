from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Review:
    """Pure domain entity representing a housing review."""

    record_id: int
    body: str
    rating: int
    id: int | None = None
    title: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(slots=True)
class ReviewImage:
    """Image attached to a review."""

    review_id: int
    image_url: str
    id: int | None = None
    created_at: datetime | None = None
