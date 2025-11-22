from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.features.comments.application.schemas import (
    CommentResponse,
    CreateCommentRequest,
    SavedRecordResponse,
    SaveRecordRequest,
    UpdateCommentRequest,
)
from app.features.comments.application.services import (
    CommentsService,
    SavedRecordsService,
)
from app.features.comments.domain.exceptions import (
    CommentNotFoundError,
    RecordNotFoundError,
    ReviewNotFoundError,
)
from app.features.comments.infrastructure.repository import (
    SqlAlchemyCommentsRepository,
    SqlAlchemySavedRecordsRepository,
)
from app.shared.infrastructure.database import get_db


def get_comments_service(db: Session = Depends(get_db)) -> CommentsService:
    repository = SqlAlchemyCommentsRepository(db)
    return CommentsService(repository)


def get_saved_records_service(db: Session = Depends(get_db)) -> SavedRecordsService:
    repository = SqlAlchemySavedRecordsRepository(db)
    return SavedRecordsService(repository)


comments_router = APIRouter(prefix="/reviews/{review_id}/comments", tags=["comments"])
saved_records_router = APIRouter(prefix="/saved-records", tags=["saved-records"])


@comments_router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    review_id: int,
    payload: CreateCommentRequest,
    service: CommentsService = Depends(get_comments_service),
) -> CommentResponse:
    try:
        comment = service.create_comment(review_id=review_id, body=payload.body)
    except ReviewNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="review_not_found"
        ) from exc

    return CommentResponse.model_validate(comment)


@comments_router.get("", response_model=list[CommentResponse])
def list_comments(
    review_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: CommentsService = Depends(get_comments_service),
) -> list[CommentResponse]:
    comments = service.list_comments(review_id=review_id, limit=limit, offset=offset)
    return [CommentResponse.model_validate(comment) for comment in comments]


@comments_router.put(
    "/{comment_id}",
    response_model=CommentResponse,
)
def update_comment(
    review_id: int,
    comment_id: int,
    payload: UpdateCommentRequest,
    service: CommentsService = Depends(get_comments_service),
) -> CommentResponse:
    try:
        comment = service.update_comment(
            comment_id=comment_id, review_id=review_id, body=payload.body
        )
    except CommentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="comment_not_found",
        ) from exc

    return CommentResponse.model_validate(comment)


@comments_router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_comment(
    review_id: int,
    comment_id: int,
    service: CommentsService = Depends(get_comments_service),
) -> None:
    removed = service.delete_comment(comment_id=comment_id, review_id=review_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="comment_not_found",
        )


@saved_records_router.post("", response_model=SavedRecordResponse)
def save_record(
    payload: SaveRecordRequest,
    response: Response,
    service: SavedRecordsService = Depends(get_saved_records_service),
) -> SavedRecordResponse:
    try:
        saved_record, created = service.save_record(record_id=payload.record_id)
    except RecordNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="record_not_found"
        ) from exc

    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    saved_record_response = SavedRecordResponse.model_validate(saved_record)
    return saved_record_response.model_copy(update={"already_saved": not created})

@saved_records_router.get("", response_model=list[SavedRecordResponse])
def list_saved_records(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: SavedRecordsService = Depends(get_saved_records_service),
) -> list[SavedRecordResponse]:
    saved_records = service.list_saved(limit=limit, offset=offset)
    return [SavedRecordResponse.model_validate(saved_record) for saved_record in saved_records]


@saved_records_router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_saved_record(
    record_id: int,
    service: SavedRecordsService = Depends(get_saved_records_service),
) -> None:
    removed = service.remove_saved_record(record_id=record_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="saved_record_not_found",
        )
