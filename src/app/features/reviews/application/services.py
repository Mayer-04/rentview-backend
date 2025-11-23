from __future__ import annotations

import logging
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
from app.shared.application.email import EmailDeliveryError, EmailMessage, EmailSender
from app.shared.domain.pagination import PageOutOfRangeError, PaginatedResult


logger = logging.getLogger(__name__)


class ReviewService:
    """Application service orchestrating review operations."""

    def __init__(self, repository: ReviewRepository, email_sender: EmailSender | None = None) -> None:
        self.repository = repository
        self.email_sender = email_sender

    def create_review(self, dto: CreateReviewDTO) -> Review:
        self._validate_email(dto.email)
        self._validate_body(dto.body)
        self._validate_rating(dto.rating)

        if not self.repository.record_exists(dto.record_id):
            raise RecordNotFoundError(f"Record {dto.record_id} does not exist")

        review = to_review_entity(dto)
        created_review = self.repository.create(review)
        self._notify_review_created(created_review)
        return created_review

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
            raise

    def _notify_review_created(self, review: Review) -> None:
        if self.email_sender is None:
            return

        title_line = review.title if review.title else "Sin título"
        subject = "¡Gracias por tu reseña en Rentview!"
        plain_body = (
            "Hola,\n\n"
            "Hemos recibido tu reseña y la estamos revisando.\n\n"
            "Resumen:\n"
            f"- Título: {title_line}\n"
            f"- Calificación: {review.rating}/5\n"
            f"- Comentario: {review.body.strip()}\n\n"
            "Gracias por compartir tu experiencia y ayudar a la comunidad.\n"
        )

        html_body = f"""
        <html>
          <body style="background:#f6f7fb;padding:24px;font-family:Helvetica,Arial,sans-serif;color:#1f2d3d;">
            <table role="presentation" width="100%%" cellspacing="0" cellpadding="0" style="max-width:640px;margin:0 auto;background:white;border-radius:12px;box-shadow:0 8px 24px rgba(31,45,61,0.08);">
              <tr>
                <td style="padding:24px 28px;">
                  <h1 style="margin:0 0 12px;font-size:22px;color:#111827;">¡Gracias por tu reseña!</h1>
                  <p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#4b5563;">
                    Hemos recibido tu reseña y la estamos revisando. Apreciamos que compartas tu experiencia.
                  </p>
                  <div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 18px;background:#f9fafb;margin-bottom:16px;">
                    <p style="margin:0 0 8px;font-weight:600;color:#111827;">Resumen</p>
                    <p style="margin:4px 0;font-size:14px;color:#374151;"><strong>Título:</strong> {title_line}</p>
                    <p style="margin:4px 0;font-size:14px;color:#374151;"><strong>Calificación:</strong> {review.rating}/5</p>
                    <p style="margin:8px 0 0;font-size:14px;color:#374151;line-height:1.5;"><strong>Comentario:</strong> {review.body.strip()}</p>
                  </div>
                  <p style="margin:0;font-size:14px;line-height:1.6;color:#4b5563;">Atentamente, el equipo de RentView</p>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """
        message = EmailMessage(
            to=review.email,
            subject=subject,
            body=plain_body,
            html_body=html_body,
        )

        try:
            self.email_sender.send(message)
        except EmailDeliveryError:
            logger.exception("Fallo el envío del correo de confirmación de reseña")

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
