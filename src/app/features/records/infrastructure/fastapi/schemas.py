from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

from app.features.records.domain.models import HousingType, Record


class CreateRecordRequest(BaseModel):
    address: Annotated[str, Field(..., min_length=1, description="Dirección de la vivienda")]
    country: Annotated[
        str, Field(..., min_length=1, description="País donde se encuentra la vivienda")
    ]
    city: Annotated[
        str, Field(..., min_length=1, description="Ciudad donde se encuentra la vivienda")
    ]
    housing_type: HousingType = Field(..., description="Tipo de vivienda")
    monthly_rent: Annotated[
        Decimal,
        Field(..., gt=0, max_digits=12, decimal_places=2, description="Canon mensual"),
    ]
    images: list[str] = Field(default_factory=list, description="URLs de imágenes opcionales")

    @field_validator("housing_type", mode="before")
    @classmethod
    def normalize_housing_type(cls, value: HousingType | str) -> HousingType:
        if isinstance(value, HousingType):
            return value
        normalized = str(value).strip().lower()
        return HousingType(normalized)

    @field_validator("images", mode="before")
    @classmethod
    def default_images(cls, value: list[str] | None) -> list[str]:
        return value or []

class UpdateRecordRequest(BaseModel):
    address: Annotated[str | None, Field(default=None, min_length=1)]
    country: Annotated[str | None, Field(default=None, min_length=1)]
    city: Annotated[str | None, Field(default=None, min_length=1)]
    housing_type: HousingType | None = Field(default=None)
    monthly_rent: Annotated[
        Decimal | None,
        Field(default=None, gt=0, max_digits=12, decimal_places=2),
    ]
    images: list[str] | None = Field(default=None, description="URLs de imágenes opcionales")

    @field_validator("housing_type", mode="before")
    @classmethod
    def normalize_housing_type(cls, value: HousingType | str | None) -> HousingType | None:
        if value is None:
            return None
        if isinstance(value, HousingType):
            return value
        normalized = str(value).strip().lower()
        return HousingType(normalized)

    @field_validator("images", mode="before")
    @classmethod
    def default_images(cls, value: list[str] | None) -> list[str] | None:
        return value if value is not None else None

    @model_validator(mode="after")
    def ensure_at_least_one_field(self) -> UpdateRecordRequest:
        if (
            self.address is None
            and self.country is None
            and self.city is None
            and self.housing_type is None
            and self.monthly_rent is None
            and self.images is None
        ):
            raise ValueError("Proporciona al menos un campo para actualizar")
        return self


class UpdateRecordRequest(BaseModel):
    address: Annotated[str | None, Field(None, min_length=1, description="Dirección de la vivienda")]
    country: Annotated[
        str | None, Field(None, min_length=1, description="País donde se encuentra la vivienda")
    ]
    city: Annotated[
        str | None, Field(None, min_length=1, description="Ciudad donde se encuentra la vivienda")
    ]
    housing_type: HousingType | None = Field(None, description="Tipo de vivienda")
    monthly_rent: Annotated[
        Decimal | None,
        Field(None, gt=0, max_digits=12, decimal_places=2, description="Canon mensual"),
    ]
    images: list[str] | None = Field(
        default=None,
        description="URLs de imágenes; omite para mantenerlas, envía lista vacía para limpiar",
    )

    @field_validator("housing_type", mode="before")
    @classmethod
    def normalize_housing_type(cls, value: HousingType | str | None) -> HousingType | None:
        if value is None or isinstance(value, HousingType):
            return value
        normalized = str(value).strip().lower()
        return HousingType(normalized)


class RecordImageResponse(BaseModel):
    id: int
    image_url: str
    created_at: datetime | None = None


class RecordResponse(BaseModel):
    id: int
    address: str
    country: str
    city: str
    housing_type: HousingType
    monthly_rent: Decimal
    images: list[RecordImageResponse]
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_domain(cls, record: Record) -> RecordResponse:
        return cls(
            id=record.id,
            address=record.address,
            country=record.country,
            city=record.city,
            housing_type=record.housing_type,
            monthly_rent=record.monthly_rent,
            images=[
                RecordImageResponse(
                    id=image.id,
                    image_url=image.image_url,
                    created_at=image.created_at,
                )
                for image in record.images
            ],
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
