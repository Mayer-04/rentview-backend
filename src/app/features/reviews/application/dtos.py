from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class CreateReviewDTO:
    record_id: int
    title: str | None
    email: str
    body: str
    rating: int
    images: list[str] = field(default_factory=list)


@dataclass(slots=True)
class UpdateReviewDTO:
    review_id: int
    title: str | None = None
    email: str | None = None
    body: str | None = None
    rating: int | None = None
    images: list[str] | None = None


@dataclass(slots=True)
class ListReviewsQuery:
    record_id: int
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


@dataclass(slots=True)
class ReviewDTO:
    id: int
    record_id: int
    title: str | None
    email: str
    body: str
    rating: int
    images: list["ReviewImageDTO"]
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class ReviewImageDTO:
    id: int
    review_id: int
    image_url: str
    created_at: datetime
