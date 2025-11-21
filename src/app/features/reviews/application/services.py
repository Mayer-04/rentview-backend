from __future__ import annotations

from collections.abc import Sequence

from app.features.reviews.application.dtos import CreateReviewDTO, ListReviewsQuery, UpdateReviewDTO
from app.features.reviews.application.mappers import to_review_entity
from app.features.reviews.domain.exceptions import (
    EmptyReviewUpdateError,
    InvalidReviewBodyError,
    InvalidReviewRatingError,
    RecordNotFoundError,
    ReviewNotFoundError,
    ReviewPersistenceError,
)
from app.features.reviews.domain.repository import ReviewRepository
from app.features.reviews.domain.review import Review


class ReviewService:
    """Application service orchestrating review operations."""

    def __init__(self, repository: ReviewRepository) -> None:
        self.repository = repository

    def create_review(self, dto: CreateReviewDTO) -> Review:
        self._validate_body(dto.body)
        self._validate_rating(dto.rating)

        if not self.repository.record_exists(dto.record_id):
            raise RecordNotFoundError(f"Record {dto.record_id} does not exist")

        review = to_review_entity(dto)
        return self.repository.create(review)

    def list_reviews(self, query: ListReviewsQuery) -> Sequence[Review]:
        if not self.repository.record_exists(query.record_id):
            raise RecordNotFoundError(f"Record {query.record_id} does not exist")

        return self.repository.list_by_record(
            record_id=query.record_id,
            limit=query.limit,
            offset=query.offset,
        )

    def get_review(self, review_id: int) -> Review:
        review = self.repository.get(review_id)
        if review is None:
            raise ReviewNotFoundError(f"Review {review_id} was not found")
        return review

    def update_review(self, dto: UpdateReviewDTO) -> Review:
        if dto.title is None and dto.body is None and dto.rating is None:
            raise EmptyReviewUpdateError("Proporciona al menos un campo para actualizar")

        if dto.body is not None:
            self._validate_body(dto.body)
        if dto.rating is not None:
            self._validate_rating(dto.rating)

        review = self.repository.get(dto.review_id)
        if review is None:
            raise ReviewNotFoundError(f"Review {dto.review_id} was not found")

        if dto.title is not None:
            review.title = dto.title.strip() if dto.title is not None else None
        if dto.body is not None:
            review.body = dto.body.strip()
        if dto.rating is not None:
            review.rating = dto.rating

        return self.repository.save(review)

    def delete_review(self, review_id: int) -> None:
        try:
            self.repository.delete(review_id)
        except ReviewNotFoundError:
            raise
        except ReviewPersistenceError:
            # Dejo pasar la excepción de persistencia sin envolver para que el controller la traduzca.
            raise

    @staticmethod
    def _validate_body(body: str) -> None:
        if not body or not body.strip():
            raise InvalidReviewBodyError("El texto de la reseña no puede estar vacío")

    @staticmethod
    def _validate_rating(rating: int) -> None:
        if rating < 1 or rating > 5:
            raise InvalidReviewRatingError("La calificación debe estar entre 1 y 5")
