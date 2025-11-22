from fastapi import APIRouter, status

from app.features.records.infrastructure.fastapi.controller import (
    create_record,
    delete_record,
    get_record,
    list_records,
    update_record,
)
from app.features.records.infrastructure.fastapi.schemas import RecordResponse

records_router = APIRouter(prefix="/records", tags=["records"])

records_router.post(
    "",
    response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
)(create_record)

records_router.get(
    "",
    response_model=list[RecordResponse],
)(list_records)

records_router.get(
    "/{record_id}",
    response_model=RecordResponse,
)(get_record)

records_router.put(
    "/{record_id}",
    response_model=RecordResponse,
)(update_record)

records_router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)(delete_record)

records_router.put(
    "/{record_id}",
    response_model=RecordResponse,
)(update_record)
