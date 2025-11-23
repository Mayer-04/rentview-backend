from collections.abc import Sequence

from psycopg.errors import ForeignKeyViolation
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.features.reviews.domain.exceptions import (
    RecordNotFoundError,
    ReviewDeletionError,
    ReviewNotFoundError,
    ReviewPersistenceError,
)
from app.features.reviews.domain.repository import ReviewRepository
from app.features.reviews.domain.review import Review
from app.features.reviews.infrastructure.mappers import review_model_to_domain
from app.features.reviews.infrastructure.models import ReviewImageModel, ReviewModel


class SqlAlchemyReviewRepository(ReviewRepository):
    """SQLAlchemy-backed repository for reviews."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def record_exists(self, record_id: int) -> bool:
        stmt = text("SELECT 1 FROM records WHERE id = :record_id LIMIT 1")
        try:
            result = self.session.execute(stmt, {"record_id": record_id})
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as exc:  # pragma: no cover - DB failure
            self.session.rollback()
            raise ReviewPersistenceError("Error verificando la existencia del record") from exc

    def create(self, review: Review) -> Review:
        model = ReviewModel(
            record_id=review.record_id,
            title=review.title,
            email=review.email,
            body=review.body,
            rating=review.rating,
        )
        if review.images:
            model.images = [
                ReviewImageModel(image_url=image.image_url.strip()) for image in review.images
            ]
        self.session.add(model)
        try:
            self.session.commit()
            self.session.refresh(model)
            return review_model_to_domain(model)
        except IntegrityError as exc:
            self.session.rollback()
            self._handle_integrity_error(exc, record_id=review.record_id)
            raise ReviewPersistenceError("Error al crear la reseña") from exc
        except SQLAlchemyError as exc:  # pragma: no cover - DB failure
            self.session.rollback()
            raise ReviewPersistenceError("Error al crear la reseña") from exc

    def list_by_record(
        self, *, record_id: int, limit: int, offset: int
    ) -> tuple[Sequence[Review], int]:
        stmt = (
            select(ReviewModel)
            .options(selectinload(ReviewModel.images))
            .where(ReviewModel.record_id == record_id)
            .order_by(ReviewModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        try:
            models = self.session.scalars(stmt).all()

            total_stmt = select(func.count()).select_from(
                select(ReviewModel.id).where(ReviewModel.record_id == record_id).subquery()
            )
            total = self.session.scalar(total_stmt) or 0

            return [review_model_to_domain(model) for model in models], int(total)
        except SQLAlchemyError as exc:  # pragma: no cover - DB failure
            self.session.rollback()
            raise ReviewPersistenceError("Error al listar reseñas") from exc

    def get(self, review_id: int) -> Review | None:
        try:
            model = self.session.get(
                ReviewModel,
                review_id,
                options=(selectinload(ReviewModel.images),),
            )
            return review_model_to_domain(model) if model else None
        except SQLAlchemyError as exc:  # pragma: no cover - DB failure
            self.session.rollback()
            raise ReviewPersistenceError("Error al obtener la reseña") from exc

    def save(self, review: Review) -> Review:
        model = self.session.get(ReviewModel, review.id)
        if model is None:
            raise ReviewNotFoundError(f"Review {review.id} was not found")

        model.title = review.title
        model.email = review.email
        model.body = review.body
        model.rating = review.rating

        try:
            self.session.commit()
            self.session.refresh(model)
            return review_model_to_domain(model)
        except SQLAlchemyError as exc:  # pragma: no cover - DB failure
            self.session.rollback()
            raise ReviewPersistenceError("Error al actualizar la reseña") from exc

    def delete(self, review_id: int) -> None:
        try:
            model = self.session.get(ReviewModel, review_id)
            if model is None:
                raise ReviewNotFoundError(f"Review {review_id} was not found")
            self.session.delete(model)
            self.session.commit()
        except ReviewNotFoundError:
            raise
        except SQLAlchemyError as exc:  # pragma: no cover - DB failure
            self.session.rollback()
            raise ReviewDeletionError("Error al eliminar la reseña") from exc

    @staticmethod
    def _handle_integrity_error(exc: IntegrityError, *, record_id: int) -> None:
        if (
            isinstance(exc.orig, ForeignKeyViolation)
            or getattr(exc.orig, "pgcode", None) == "23503"
        ):
            raise RecordNotFoundError(f"Record {record_id} does not exist") from exc
