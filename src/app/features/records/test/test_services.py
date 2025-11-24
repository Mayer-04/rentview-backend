from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.features.records.application.commands import CreateRecordCommand, UpdateRecordCommand
from app.features.records.application.services import RecordService
from app.features.records.domain import exceptions
from app.features.records.domain.models import HousingType, Record, RecordImage


def _sample_record() -> Record:
    return Record(
        id=1,
        address="Old Address",
        country="CO",
        city="Bogota",
        housing_type=HousingType.APARTAMENTO,
        monthly_rent=Decimal("950.00"),
        images=[RecordImage(id=10, image_url="https://img.com/old.png")],
    )


def test_create_record_persists_normalized_data() -> None:
    repository = MagicMock()
    repository.create.side_effect = lambda record: replace(record, id=42)
    service = RecordService(repository)
    command = CreateRecordCommand(
        address=" 123 Main St ",
        country=" Colombia ",
        city=" Bogota ",
        housing_type="CASA",
        monthly_rent=Decimal("1200"),
        image_urls=[" https://img.com/photo.PNG?size=large "],
    )

    created = service.create_record(command)

    repository.create.assert_called_once()
    persisted = repository.create.call_args[0][0]
    assert persisted.address == "123 Main St"
    assert persisted.country == "Colombia"
    assert persisted.city == "Bogota"
    assert persisted.housing_type is HousingType.CASA
    assert persisted.monthly_rent == Decimal("1200")
    assert [image.image_url for image in persisted.images] == [
        "https://img.com/photo.PNG?size=large"
    ]
    assert created.id == 42
    assert created.housing_type is HousingType.CASA


def test_create_record_rejects_invalid_inputs() -> None:
    service = RecordService(MagicMock())

    with pytest.raises(exceptions.InvalidMonthlyRentError):
        service.create_record(
            CreateRecordCommand(
                address="A",
                country="B",
                city="C",
                housing_type=HousingType.CASA,
                monthly_rent=Decimal("0"),
            )
        )

    with pytest.raises(exceptions.MissingRequiredFieldError):
        service.create_record(
            CreateRecordCommand(
                address="   ",
                country="B",
                city="C",
                housing_type="casa",
                monthly_rent=Decimal("1"),
            )
        )

    with pytest.raises(exceptions.MissingRequiredFieldError):
        service.create_record(
            CreateRecordCommand(
                address="A",
                country="B",
                city="C",
                housing_type="penthouse",
                monthly_rent=Decimal("1"),
            )
        )

    with pytest.raises(exceptions.InvalidImageFormatError):
        service.create_record(
            CreateRecordCommand(
                address="A",
                country="B",
                city="C",
                housing_type=HousingType.CASA,
                monthly_rent=Decimal("1"),
                image_urls=["http://img.com/photo.gif"],
            )
        )


def test_get_record_returns_when_found() -> None:
    repository = MagicMock()
    existing = _sample_record()
    repository.get.return_value = existing
    service = RecordService(repository)

    result = service.get_record(7)

    repository.get.assert_called_once_with(7)
    assert result is existing


def test_get_record_raises_when_missing() -> None:
    repository = MagicMock()
    repository.get.return_value = None
    service = RecordService(repository)

    with pytest.raises(exceptions.RecordNotFoundError):
        service.get_record(99)


def test_delete_record_checks_existence() -> None:
    repository = MagicMock()
    repository.get.return_value = _sample_record()
    service = RecordService(repository)

    service.delete_record(5)

    repository.delete.assert_called_once_with(5)

    repository.get.return_value = None
    with pytest.raises(exceptions.RecordNotFoundError):
        service.delete_record(5)
    repository.delete.assert_called_once_with(5)


def test_update_record_replaces_fields_and_images() -> None:
    repository = MagicMock()
    existing = _sample_record()
    repository.get.return_value = existing
    repository.update.side_effect = lambda record, replace_images: Record(**record.__dict__)
    service = RecordService(repository)
    command = UpdateRecordCommand(
        address=" New Address ",
        country=" Peru ",
        city=" Lima ",
        housing_type="comercial",
        monthly_rent=Decimal("1500"),
        image_urls=[" new.jpg ", "two.png#hash"],
    )

    updated = service.update_record(1, command)

    repository.update.assert_called_once()
    persisted = repository.update.call_args[0][0]
    assert persisted.id == existing.id
    assert persisted.address == "New Address"
    assert persisted.country == "Peru"
    assert persisted.city == "Lima"
    assert persisted.housing_type is HousingType.COMERCIAL
    assert persisted.monthly_rent == Decimal("1500")
    assert [image.image_url for image in persisted.images] == [
        "new.jpg",
        "two.png#hash",
    ]
    assert repository.update.call_args.kwargs["replace_images"] is True
    assert updated.housing_type is HousingType.COMERCIAL


def test_update_record_keeps_existing_fields_when_missing_in_command() -> None:
    repository = MagicMock()
    existing = _sample_record()
    repository.get.return_value = existing
    repository.update.side_effect = lambda record, replace_images: record
    service = RecordService(repository)
    command = UpdateRecordCommand(address=None, country=None, city=None, image_urls=None)

    updated = service.update_record(existing.id, command)

    assert repository.update.call_args.kwargs["replace_images"] is False
    persisted = repository.update.call_args[0][0]
    assert persisted.address == existing.address
    assert persisted.country == existing.country
    assert persisted.city == existing.city
    assert persisted.housing_type is existing.housing_type
    assert persisted.images is existing.images
    assert updated is persisted


def test_update_record_validations_and_not_found() -> None:
    repository = MagicMock()
    repository.get.return_value = _sample_record()
    service = RecordService(repository)

    with pytest.raises(exceptions.InvalidMonthlyRentError):
        service.update_record(
            1, UpdateRecordCommand(monthly_rent=Decimal("-1"), housing_type="casa")
        )

    with pytest.raises(exceptions.MissingRequiredFieldError):
        service.update_record(
            1,
            UpdateRecordCommand(
                city="   ",
                housing_type="casa",
                monthly_rent=Decimal("10"),
            ),
        )

    repository.get.return_value = None
    with pytest.raises(exceptions.RecordNotFoundError):
        service.update_record(99, UpdateRecordCommand(housing_type="casa"))


def test_list_records_validates_pagination() -> None:
    repository = MagicMock()
    repository.list.return_value = [_sample_record()]
    service = RecordService(repository)

    records = service.list_records(limit=10, offset=5)

    repository.list.assert_called_once_with(limit=10, offset=5)
    assert records == repository.list.return_value

    with pytest.raises(exceptions.MissingRequiredFieldError):
        service.list_records(limit=0)

    with pytest.raises(exceptions.MissingRequiredFieldError):
        service.list_records(limit=5, offset=-1)
