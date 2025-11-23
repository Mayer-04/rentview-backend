from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum


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
    images: list[RecordImage] = field(default_factory=list)
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class PaginatedRecords:
    items: list[Record]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size
