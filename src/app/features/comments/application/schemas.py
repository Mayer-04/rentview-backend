from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.shared.infrastructure.pagination import PaginationMeta

CommentBody = Annotated[
    str, StringConstraints(min_length=1, max_length=2000, strip_whitespace=True)
]


class CreateCommentRequest(BaseModel):
    body: CommentBody

    model_config = ConfigDict(extra="forbid")


class UpdateCommentRequest(BaseModel):
    body: CommentBody

    model_config = ConfigDict(extra="forbid")


class CommentResponse(BaseModel):
    id: int
    review_id: int
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SaveRecordRequest(BaseModel):
    record_id: int = Field(gt=0)

    model_config = ConfigDict(extra="forbid")


class SavedRecordResponse(BaseModel):
    id: int
    record_id: int
    saved_at: datetime
    already_saved: bool = False

    model_config = ConfigDict(from_attributes=True)


class PaginatedCommentsResponse(BaseModel):
    items: list[CommentResponse]
    meta: PaginationMeta

    model_config = ConfigDict(populate_by_name=True)


class PaginatedSavedRecordsResponse(BaseModel):
    items: list[SavedRecordResponse]
    meta: PaginationMeta

    model_config = ConfigDict(populate_by_name=True)
