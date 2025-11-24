from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from sqlalchemy.orm import Session

from app.features.reviews.application.dtos import CreateReviewDTO, ListReviewsQuery, UpdateReviewDTO
from app.features.reviews.application.mappers import to_review_dto
from app.features.reviews.application.services import ReviewService
from app.features.reviews.domain.exceptions import (
    EmptyReviewUpdateError,
    InvalidPaginationError,
    InvalidReviewBodyError,
    InvalidReviewEmailError,
    InvalidReviewImageError,
    InvalidReviewRatingError,
    RecordNotFoundError,
    ReviewImageNotFoundError,
    ReviewNotFoundError,
    ReviewPersistenceError,
)
from app.features.reviews.infrastructure.repository import SqlAlchemyReviewRepository
from app.shared.domain.pagination import PageOutOfRangeError
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.email.factory import get_email_sender
from app.shared.infrastructure.pagination import PaginationMeta


def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    repository = SqlAlchemyReviewRepository(db)
    email_sender = get_email_sender()
    return ReviewService(repository, email_sender=email_sender)


class ReviewImageResponse(BaseModel):
    id: int
    review_id: int
    image_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewImageCreateRequest(BaseModel):
    image_url: str = Field(..., min_length=1, description="URL de la imagen (.jpg/.png)")

    @field_validator("image_url")
    @classmethod
    def normalize_image_url(cls, value: str) -> str:
        return value.strip()


class ReviewResponse(BaseModel):
    id: int
    record_id: int
    title: str | None
    email: str
    body: str
    rating: int
    images: list["ReviewImageResponse"]
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
    email: EmailStr = Field(max_length=320)
    body: str = Field(min_length=1, max_length=10_000)
    rating: int = Field(ge=1, le=5)
    images: list[str] = Field(default_factory=list, description="URLs de imágenes opcionales")

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

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

    @field_validator("images", mode="before")
    @classmethod
    def default_images(cls, value: list[str] | None) -> list[str]:
        return value or []

    @field_validator("images")
    @classmethod
    def normalize_images(cls, value: list[str]) -> list[str]:
        if any(not isinstance(image, str) for image in value):
            raise ValueError("Las imágenes deben ser cadenas de texto")
        return [image.strip() for image in value]


class ReviewUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = Field(default=None, max_length=320)
    body: str | None = Field(default=None, max_length=10_000)
    rating: int | None = Field(default=None, ge=1, le=5)
    images: list[str] | None = Field(
        default=None,
        description="URLs de imágenes; envía lista vacía para limpiar, omite para mantener",
    )

    @model_validator(mode="after")
    def ensure_at_least_one_field(self) -> ReviewUpdateRequest:
        if (
            self.title is None
            and self.body is None
            and self.rating is None
            and self.email is None
            and self.images is None
        ):
            raise ValueError("Proporciona al menos un campo para actualizar")
        return self

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

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

    @field_validator("images", mode="before")
    @classmethod
    def normalize_images(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        if any(not isinstance(image, str) for image in value):
            raise ValueError("Las imágenes deben ser cadenas de texto")
        return [image.strip() for image in value]


def create_review(
    payload: ReviewCreateRequest, service: ReviewService = Depends(get_review_service)
) -> ReviewResponse:
    try:
        dto = CreateReviewDTO(
            record_id=payload.record_id,
            title=payload.title,
            email=str(payload.email),
            body=payload.body,
            rating=payload.rating,
            images=payload.images,
        )
        review = service.create_review(dto)
    except RecordNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="record no encontrado",
        ) from None
    except (
        InvalidReviewBodyError,
        InvalidReviewEmailError,
        InvalidReviewRatingError,
        InvalidReviewImageError,
    ) as exc:
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
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
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
            email=str(payload.email) if payload.email is not None else None,
            body=payload.body,
            rating=payload.rating,
            images=payload.images,
        )
        review = service.update_review(dto)
    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="reseña no encontrada",
        ) from None
    except (
        InvalidReviewBodyError,
        InvalidReviewEmailError,
        InvalidReviewRatingError,
        EmptyReviewUpdateError,
    ) as exc:
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


def add_review_image(
    review_id: int,
    payload: ReviewImageCreateRequest,
    service: ReviewService = Depends(get_review_service),
) -> ReviewImageResponse:
    try:
        image = service.add_review_image(review_id, payload.image_url)
    except ReviewNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="reseña no encontrada",
        ) from None
    except InvalidReviewImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from None
    except ReviewPersistenceError as exc:  # pragma: no cover - DB failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo guardar la imagen",
        ) from exc
    return ReviewImageResponse.model_validate(image)


def delete_review_image(
    review_id: int,
    image_id: int,
    service: ReviewService = Depends(get_review_service),
) -> None:
    try:
        service.delete_review_image(review_id, image_id)
    except ReviewImageNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="imagen_no_encontrada",
        ) from None
    except ReviewPersistenceError as exc:  # pragma: no cover - DB failure
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo eliminar la imagen",
        ) from exc
