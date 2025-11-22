from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.features.records.application.commands import CreateRecordCommand, UpdateRecordCommand
from app.features.records.application.services import RecordService
from app.features.records.domain import exceptions
from app.features.records.infrastructure.fastapi.schemas import (
    CreateRecordRequest,
    RecordResponse,
    UpdateRecordRequest,
)
from app.features.records.infrastructure.persistence.repository import SQLAlchemyRecordRepository
from app.shared.infrastructure.database import get_db


def _get_service(db: Session) -> RecordService:
    repository = SQLAlchemyRecordRepository(db)
    return RecordService(repository)


async def create_record(
    payload: CreateRecordRequest, db: Session = Depends(get_db)
) -> RecordResponse:
    service = _get_service(db)
    command = CreateRecordCommand(
        address=payload.address,
        country=payload.country,
        city=payload.city,
        housing_type=payload.housing_type,
        monthly_rent=payload.monthly_rent,
        image_urls=payload.images,
    )

    try:
        record = service.create_record(command)
    except exceptions.RecordError as exc:
        raise _to_http_exception(exc) from exc

    return RecordResponse.from_domain(record)


async def delete_record(record_id: int, db: Session = Depends(get_db)) -> None:
    service = _get_service(db)
    try:
        service.delete_record(record_id)
    except exceptions.RecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


async def get_record(record_id: int, db: Session = Depends(get_db)) -> RecordResponse:
    service = _get_service(db)
    try:
        record = service.get_record(record_id)
    except exceptions.RecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return RecordResponse.from_domain(record)


async def list_records(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[RecordResponse]:
    service = _get_service(db)
    try:
        records = service.list_records(limit=limit, offset=offset)
    except exceptions.RecordError as exc:
        raise _to_http_exception(exc) from exc
    return [RecordResponse.from_domain(record) for record in records]


async def update_record(
    record_id: int,
    payload: UpdateRecordRequest,
    db: Session = Depends(get_db),
) -> RecordResponse:
    service = _get_service(db)
    command = UpdateRecordCommand(
        record_id=record_id,
        address=payload.address,
        country=payload.country,
        city=payload.city,
        housing_type=payload.housing_type,
        monthly_rent=payload.monthly_rent,
        image_urls=payload.images,
    )
    try:
        record = service.update_record(command)
    except exceptions.RecordNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except exceptions.RecordError as exc:
        raise _to_http_exception(exc) from exc

    return RecordResponse.from_domain(record)


def _to_http_exception(error: exceptions.RecordError) -> HTTPException:
    if isinstance(
        error,
        (
            exceptions.MissingRequiredFieldError,
            exceptions.InvalidImageFormatError,
            exceptions.InvalidMonthlyRentError,
        ),
    ):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
