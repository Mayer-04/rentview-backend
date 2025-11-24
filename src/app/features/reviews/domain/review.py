from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ReviewImage:
    """Image attached to a review."""

    image_url: str
    review_id: int | None = None
    id: int | None = None
    created_at: datetime | None = None


@dataclass(slots=True)
class Review:
    """Pure domain entity representing a housing review."""

    record_id: int
    email: str
    body: str
    rating: int
    images: list[ReviewImage] = field(default_factory=list)
    id: int | None = None
    title: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
