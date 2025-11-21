from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.features.reviews.domain.review import Review


class ReviewRepository(Protocol):
    """Contract for persisting and retrieving reviews."""

    def record_exists(self, record_id: int) -> bool: ...

    def create(self, review: Review) -> Review: ...

    def list_by_record(self, *, record_id: int, limit: int, offset: int) -> Sequence[Review]: ...

    def get(self, review_id: int) -> Review | None: ...

    def save(self, review: Review) -> Review: ...

    def delete(self, review_id: int) -> None: ...
