from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from app.features.records.application.commands import CreateRecordCommand, UpdateRecordCommand
from app.features.records.domain import exceptions
from app.features.records.domain.models import HousingType, PaginatedRecords, Record, RecordImage
from app.features.records.domain.repository import RecordRepository

ALLOWED_IMAGE_EXTENSIONS = (".jpg", ".png")


class RecordService:
    def __init__(self, repository: RecordRepository) -> None:
        self._repository = repository

    def create_record(self, command: CreateRecordCommand) -> Record:
        housing_type = self._normalize_housing_type(command.housing_type)
        self._validate_create_command(command, housing_type)

        record = Record(
            address=command.address.strip(),
            country=command.country.strip(),
            city=command.city.strip(),
            housing_type=housing_type,
            monthly_rent=command.monthly_rent,
            images=[RecordImage(image_url=image.strip()) for image in command.image_urls],
        )

        return self._repository.create(record)

    def delete_record(self, record_id: int) -> None:
        record = self._repository.get(record_id)
        if record is None:
            raise exceptions.RecordNotFoundError(f"Record {record_id} does not exist")

        self._repository.delete(record_id)

    def get_record(self, record_id: int) -> Record:
        record = self._repository.get(record_id)
        if record is None:
            raise exceptions.RecordNotFoundError(f"Record {record_id} does not exist")
        return record

    def update_record(self, record_id: int, command: UpdateRecordCommand) -> Record:
        existing_record = self._repository.get(record_id)
        if existing_record is None:
            raise exceptions.RecordNotFoundError(f"Record {record_id} does not exist")

        housing_type = (
            self._normalize_housing_type(command.housing_type)
            if command.housing_type is not None
            else existing_record.housing_type
        )

        address = existing_record.address if command.address is None else command.address.strip()
        country = existing_record.country if command.country is None else command.country.strip()
        city = existing_record.city if command.city is None else command.city.strip()
        monthly_rent = (
            existing_record.monthly_rent if command.monthly_rent is None else command.monthly_rent
        )

        self._validate_required_fields(
            {
                "address": address,
                "country": country,
                "city": city,
            }
        )

        if monthly_rent <= Decimal("0"):
            raise exceptions.InvalidMonthlyRentError("Monthly rent must be greater than zero")

        if not isinstance(housing_type, HousingType):
            raise exceptions.MissingRequiredFieldError("Housing type is required")

        replace_images = command.image_urls is not None
        images = existing_record.images
        if replace_images:
            self._validate_images(command.image_urls or [])
            images = [RecordImage(image_url=image.strip()) for image in command.image_urls or []]

        updated_record = Record(
            id=existing_record.id,
            address=address,
            country=country,
            city=city,
            housing_type=housing_type,
            monthly_rent=monthly_rent,
            reviews_count=existing_record.reviews_count,
            average_rating=existing_record.average_rating,
            images=images,
            created_at=existing_record.created_at,
            updated_at=existing_record.updated_at,
        )

        return self._repository.update(updated_record, replace_images=replace_images)

    def list_records(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedRecords | list[Record] | tuple[list[Record], int]:
        if limit is not None:
            if limit <= 0:
                raise exceptions.MissingRequiredFieldError("limit must be greater than zero")
            if offset < 0:
                raise exceptions.MissingRequiredFieldError("offset cannot be negative")

            return self._repository.list(limit=limit, offset=offset)

        if page < 1:
            raise exceptions.MissingRequiredFieldError("page must be at least 1")
        if page_size <= 0 or page_size > 100:
            raise exceptions.MissingRequiredFieldError("page_size must be between 1 and 100")

        offset = (page - 1) * page_size
        items, total = self._repository.list(limit=page_size, offset=offset)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        if total == 0 and page > 1:
            raise exceptions.PageOutOfRangeError("No results available for the requested page")
        if total_pages > 0 and page > total_pages:
            raise exceptions.PageOutOfRangeError(
                f"Requested page {page} exceeds total pages {total_pages}"
            )

        return PaginatedRecords(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def _validate_create_command(
        self, command: CreateRecordCommand, housing_type: HousingType
    ) -> None:
        self._validate_required_fields(
            {
                "address": command.address,
                "country": command.country,
                "city": command.city,
            }
        )

        if command.monthly_rent <= Decimal("0"):
            raise exceptions.InvalidMonthlyRentError("Monthly rent must be greater than zero")

        if not isinstance(housing_type, HousingType):
            raise exceptions.MissingRequiredFieldError("Housing type is required")

        self._validate_images(command.image_urls)

    def _normalize_housing_type(self, value: HousingType | str) -> HousingType:
        if isinstance(value, HousingType):
            return value
        normalized = str(value).strip().lower()
        try:
            return HousingType(normalized)
        except ValueError as exc:
            raise exceptions.MissingRequiredFieldError("Housing type is required") from exc

    def _validate_required_fields(self, fields: dict[str, str]) -> None:
        for field_name, value in fields.items():
            if not value or not value.strip():
                raise exceptions.MissingRequiredFieldError(f"{field_name} is required")

    def _validate_images(self, images: Iterable[str]) -> None:
        for image in images:
            normalized = image.strip().lower()
            if not normalized:
                raise exceptions.InvalidImageFormatError("Image URLs cannot be empty")
            trimmed = normalized.split("?")[0].split("#")[0]
            if not trimmed.endswith(ALLOWED_IMAGE_EXTENSIONS):
                raise exceptions.InvalidImageFormatError("Images must be in jpg or png format")
