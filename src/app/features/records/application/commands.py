from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.features.records.domain.models import HousingType


@dataclass
class CreateRecordCommand:
    address: str
    country: str
    city: str
    housing_type: HousingType
    monthly_rent: Decimal
    image_urls: list[str] = field(default_factory=list)


@dataclass
class UpdateRecordCommand:
    address: str | None = None
    country: str | None = None
    city: str | None = None
    housing_type: HousingType | str | None = None
    monthly_rent: Decimal | None = None
    image_urls: list[str] | None = None