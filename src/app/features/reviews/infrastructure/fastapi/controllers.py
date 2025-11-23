from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from app.features.reviews.application.dtos import CreateReviewDTO, ListReviewsQuery, UpdateReviewDTO
from app.features.reviews.application.mappers import to_review_dto
from app.features.reviews.application.services import ReviewService
from app.features.reviews.domain.exceptions import (
    EmptyReviewUpdateError,
    InvalidPaginationError,
    InvalidReviewBodyError,
    InvalidReviewRatingError,
    RecordNotFoundError,
    ReviewNotFoundError,
    ReviewPersistenceError,
)
from app.features.reviews.infrastructure.repository import SqlAlchemyReviewRepository
from app.shared.domain.pagination import PageOutOfRangeError
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.pagination import PaginationMeta


def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    repository = SqlAlchemyReviewRepository(db)
    return ReviewService(repository)


class ReviewResponse(BaseModel):
    id: int
    record_id: int
    title: str | None
    body: str
    rating: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedReviewsResponse(BaseModel):
    items: list[ReviewResponse]
    meta: PaginationMeta

    model_config = ConfigDict(populate_by_name=True)


class ReviewCreateRequest(BaseModel):
    record_id: int = Field(gt=0)
    title: str | None = Field(default=None, max_length=120)
    body: str = Field(min_length=1, max_length=10_000)
    rating: int = Field(ge=1, le=5)

    @field_validator("body")
    @classmethod
    def ensure_body_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El texto de la reseña no puede estar vacío")
        return value.strip()

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class ReviewUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    body: str | None = Field(default=None, max_length=10_000)
    rating: int | None = Field(default=None, ge=1, le=5)

    @model_validator(mode="after")
    def ensure_at_least_one_field(self) -> ReviewUpdateRequest:
        if self.title is None and self.body is None and self.rating is None:
            raise ValueError("Proporciona al menos un campo para actualizar")
        return self

    @field_validator("body")
    @classmethod
    def ensure_body_not_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("El texto de la reseña no puede estar vacío")
        return value.strip()

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


def create_review(
    payload: ReviewCreateRequest, service: ReviewService = Depends(get_review_service)
) -> ReviewResponse:
    try:
        dto = CreateReviewDTO(
            record_id=payload.record_id,
            title=payload.title,
            body=payload.body,
            rating=payload.rating,
        )
        review = service.create_review(dto)
    except RecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="record no encontrado",
        ) from None
    except (InvalidReviewBodyError, InvalidReviewRatingError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None
    except ReviewPersistenceError as exc:  # pragma: no cover - DB failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo crear la reseña",
        ) from exc
    return ReviewResponse.model_validate(to_review_dto(review))


def list_reviews_for_record(
    record_id: int,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    service: ReviewService = Depends(get_review_service),
) -> PaginatedReviewsResponse:
    try:
        query = ListReviewsQuery(record_id=record_id, page=page, page_size=page_size)
        result = service.list_reviews(query)
    except RecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="record no encontrado",
        ) from None
    except PageOutOfRangeError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidPaginationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ReviewPersistenceError as exc:  # pragma: no cover - DB failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudieron listar las reseñas",
        ) from exc
    return PaginatedReviewsResponse(
        items=[ReviewResponse.model_validate(to_review_dto(review)) for review in result.items],
        meta=PaginationMeta(
            page=result.page,
            page_size=result.page_size,
            total=result.total,
            total_pages=result.total_pages,
        ),
    )


def get_review(
    review_id: int, service: ReviewService = Depends(get_review_service)
) -> ReviewResponse:
    try:
        review = service.get_review(review_id)
    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="reseña no encontrada",
        ) from None
    except ReviewPersistenceError as exc:  # pragma: no cover - DB failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo obtener la reseña",
        ) from exc
    return ReviewResponse.model_validate(to_review_dto(review))


def update_review(
    review_id: int,
    payload: ReviewUpdateRequest,
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    try:
        dto = UpdateReviewDTO(
            review_id=review_id,
            title=payload.title,
            body=payload.body,
            rating=payload.rating,
        )
        review = service.update_review(dto)
    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="reseña no encontrada",
        ) from None
    except (InvalidReviewBodyError, InvalidReviewRatingError, EmptyReviewUpdateError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None
    except ReviewPersistenceError as exc:  # pragma: no cover - DB failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo actualizar la reseña",
        ) from exc
    return ReviewResponse.model_validate(to_review_dto(review))


def delete_review(review_id: int, service: ReviewService = Depends(get_review_service)) -> None:
    try:
        service.delete_review(review_id)
    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="reseña no encontrada",
        ) from None
    except ReviewPersistenceError as exc:  # pragma: no cover - DB failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo eliminar la reseña",
        ) from exc
