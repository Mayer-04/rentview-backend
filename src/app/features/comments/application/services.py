from typing import Protocol

from app.features.comments.domain.exceptions import InvalidPaginationError
from app.features.comments.domain.models import Comment, SavedRecord
from app.shared.domain.pagination import PageOutOfRangeError, PaginatedResult


class CommentsRepository(Protocol):
    def create(self, review_id: int, body: str) -> Comment: ...

    def list(self, review_id: int, limit: int, offset: int) -> tuple[list[Comment], int]: ...

    def update(self, comment_id: int, review_id: int, body: str) -> Comment: ...

    def delete(self, comment_id: int, review_id: int) -> bool: ...


class SavedRecordsRepository(Protocol):
    def save(self, record_id: int) -> tuple[SavedRecord, bool]: ...

    def list(self, limit: int, offset: int) -> tuple[list[SavedRecord], int]: ...

    def delete(self, record_id: int) -> bool: ...


class CommentsService:
    def __init__(self, repository: CommentsRepository) -> None:
        self._repository = repository

    def create_comment(self, review_id: int, body: str) -> Comment:
        return self._repository.create(review_id=review_id, body=body)

    def list_comments(
        self, review_id: int, *, page: int = 1, page_size: int = 20
    ) -> PaginatedResult[Comment]:
        if page < 1:
            raise InvalidPaginationError("page must be at least 1")
        if page_size <= 0 or page_size > 100:
            raise InvalidPaginationError("page_size must be between 1 and 100")

        offset = (page - 1) * page_size
        items, total = self._repository.list(review_id=review_id, limit=page_size, offset=offset)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        if total == 0 and page > 1:
            raise PageOutOfRangeError("No hay comentarios disponibles para la página solicitada")
        if total_pages > 0 and page > total_pages:
            raise PageOutOfRangeError(
                f"La página solicitada {page} excede el total de páginas {total_pages}"
            )

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def update_comment(self, comment_id: int, review_id: int, body: str) -> Comment:
        return self._repository.update(comment_id=comment_id, review_id=review_id, body=body)

    def delete_comment(self, comment_id: int, review_id: int) -> bool:
        return self._repository.delete(comment_id=comment_id, review_id=review_id)


class SavedRecordsService:
    def __init__(self, repository: SavedRecordsRepository) -> None:
        self._repository = repository

    def save_record(self, record_id: int) -> tuple[SavedRecord, bool]:
        return self._repository.save(record_id=record_id)

    def list_saved(self, *, page: int = 1, page_size: int = 50) -> PaginatedResult[SavedRecord]:
        if page < 1:
            raise InvalidPaginationError("page must be at least 1")
        if page_size <= 0 or page_size > 200:
            raise InvalidPaginationError("page_size must be between 1 and 200")

        offset = (page - 1) * page_size
        items, total = self._repository.list(limit=page_size, offset=offset)

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        if total == 0 and page > 1:
            raise PageOutOfRangeError("No hay registros guardados para la página solicitada")
        if total_pages > 0 and page > total_pages:
            raise PageOutOfRangeError(
                f"La página solicitada {page} excede el total de páginas {total_pages}"
            )

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def remove_saved_record(self, record_id: int) -> bool:
        return self._repository.delete(record_id=record_id)
