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
    PaginatedCommentsResponse,
    PaginatedSavedRecordsResponse,
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
    InvalidPaginationError,
    RecordNotFoundError,
    ReviewNotFoundError,
)
from app.features.comments.infrastructure.repository import (
    SqlAlchemyCommentsRepository,
    SqlAlchemySavedRecordsRepository,
)
from app.shared.domain.pagination import PageOutOfRangeError
from app.shared.infrastructure.database import get_db
from app.shared.infrastructure.pagination import PaginationMeta


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


@comments_router.get("", response_model=PaginatedCommentsResponse)
def list_comments(
    review_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: CommentsService = Depends(get_comments_service),
) -> PaginatedCommentsResponse:
    try:
        result = service.list_comments(
            review_id=review_id,
            page=page,
            page_size=page_size,
        )
    except PageOutOfRangeError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidPaginationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    comments = [CommentResponse.model_validate(comment) for comment in result.items]
    return PaginatedCommentsResponse(
        items=comments,
        meta=PaginationMeta(
            page=result.page,
            page_size=result.page_size,
            total=result.total,
            total_pages=result.total_pages,
        ),
    )


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
    validated = SavedRecordResponse.model_validate(saved_record)
    return validated.model_copy(update={"already_saved": not created})


@saved_records_router.get("", response_model=PaginatedSavedRecordsResponse)
def list_saved_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    service: SavedRecordsService = Depends(get_saved_records_service),
) -> PaginatedSavedRecordsResponse:
    try:
        result = service.list_saved(page=page, page_size=page_size)
    except PageOutOfRangeError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidPaginationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    saved_records = [
        SavedRecordResponse.model_validate(saved_record) for saved_record in result.items
    ]
    return PaginatedSavedRecordsResponse(
        items=saved_records,
        meta=PaginationMeta(
            page=result.page,
            page_size=result.page_size,
            total=result.total,
            total_pages=result.total_pages,
        ),
    )


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
