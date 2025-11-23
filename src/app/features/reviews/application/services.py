from __future__ import annotations

import re

from app.features.reviews.application.dtos import CreateReviewDTO, ListReviewsQuery, UpdateReviewDTO
from app.features.reviews.application.mappers import to_review_entity
from app.features.reviews.domain.exceptions import (
    EmptyReviewUpdateError,
    InvalidPaginationError,
    InvalidReviewBodyError,
    InvalidReviewEmailError,
    InvalidReviewRatingError,
    RecordNotFoundError,
    ReviewNotFoundError,
    ReviewPersistenceError,
)
from app.features.reviews.domain.repository import ReviewRepository
from app.features.reviews.domain.review import Review
from app.shared.domain.pagination import PageOutOfRangeError, PaginatedResult


class ReviewService:
    """Application service orchestrating review operations."""

    def __init__(self, repository: ReviewRepository) -> None:
        self.repository = repository

    def create_review(self, dto: CreateReviewDTO) -> Review:
        self._validate_email(dto.email)
        self._validate_body(dto.body)
        self._validate_rating(dto.rating)

        if not self.repository.record_exists(dto.record_id):
            raise RecordNotFoundError(f"Record {dto.record_id} does not exist")

        review = to_review_entity(dto)
        return self.repository.create(review)

    def list_reviews(self, query: ListReviewsQuery) -> PaginatedResult[Review]:
        if not self.repository.record_exists(query.record_id):
            raise RecordNotFoundError(f"Record {query.record_id} does not exist")

        if query.page < 1:
            raise InvalidPaginationError("page must be at least 1")
        if query.page_size <= 0 or query.page_size > 100:
            raise InvalidPaginationError("page_size must be between 1 and 100")

        reviews, total = self.repository.list_by_record(
            record_id=query.record_id,
            limit=query.page_size,
            offset=query.offset,
        )
        total_pages = (total + query.page_size - 1) // query.page_size if total > 0 else 0
        if total == 0 and query.page > 1:
            raise PageOutOfRangeError("No hay reseñas disponibles para la página solicitada")
        if total_pages > 0 and query.page > total_pages:
            raise PageOutOfRangeError(
                f"La página solicitada {query.page} excede el total de páginas {total_pages}"
            )

        return PaginatedResult(
            items=list(reviews),
            total=total,
            page=query.page,
            page_size=query.page_size,
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
        if dto.email is not None:
            self._validate_email(dto.email)

        review = self.repository.get(dto.review_id)
        if review is None:
            raise ReviewNotFoundError(f"Review {dto.review_id} was not found")

        if dto.title is not None:
            review.title = dto.title.strip() if dto.title is not None else None
        if dto.email is not None:
            review.email = dto.email.strip()
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

    @staticmethod
    def _validate_email(email: str) -> None:
        normalized = email.strip()
        if len(normalized) > 320:
            raise InvalidReviewEmailError("El correo electrónico excede la longitud máxima permitida")
        # RFC 5322-like pattern without allowing spaces or uncommon symbols.
        email_pattern = re.compile(
            r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$",
            re.IGNORECASE,
        )
        if not normalized or not email_pattern.fullmatch(normalized):
            raise InvalidReviewEmailError("El correo electrónico no es válido")
