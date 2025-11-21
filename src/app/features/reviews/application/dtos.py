from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class CreateReviewDTO:
    record_id: int
    title: str | None
    body: str
    rating: int


@dataclass(slots=True)
class UpdateReviewDTO:
    review_id: int
    title: str | None = None
    body: str | None = None
    rating: int | None = None


@dataclass(slots=True)
class ListReviewsQuery:
    record_id: int
    limit: int
    offset: int


@dataclass(slots=True)
class ReviewDTO:
    id: int
    record_id: int
    title: str | None
    body: str
    rating: int
    created_at: datetime
    updated_at: datetime
