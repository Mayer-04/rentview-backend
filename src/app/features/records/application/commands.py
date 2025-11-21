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