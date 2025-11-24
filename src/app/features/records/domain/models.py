from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TypeAlias

from app.shared.domain.pagination import PaginatedResult


class HousingType(str, Enum):
    APARTAMENTO = "apartamento"
    CASA = "casa"
    COMERCIAL = "comercial"


@dataclass
class RecordImage:
    image_url: str
    id: int | None = None
    created_at: datetime | None = None


@dataclass
class Record:
    address: str
    country: str
    city: str
    housing_type: HousingType
    monthly_rent: Decimal
    reviews_count: int = 0
    average_rating: float | None = None
    images: list[RecordImage] = field(default_factory=list)
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


PaginatedRecords: TypeAlias = PaginatedResult[Record]
