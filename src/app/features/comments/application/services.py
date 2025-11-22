from typing import Protocol

from app.features.comments.domain.models import Comment, SavedRecord


class CommentsRepository(Protocol):
    def create(self, review_id: int, body: str) -> Comment: ...

    def list(self, review_id: int, limit: int, offset: int) -> list[Comment]: ...

    def update(self, comment_id: int, review_id: int, body: str) -> Comment: ...

    def delete(self, comment_id: int, review_id: int) -> bool: ...


class SavedRecordsRepository(Protocol):
    def save(self, record_id: int) -> tuple[SavedRecord, bool]: ...

    def list(self, limit: int, offset: int) -> list[SavedRecord]: ...

    def delete(self, record_id: int) -> bool: ...


class CommentsService:
    def __init__(self, repository: CommentsRepository) -> None:
        self._repository = repository

    def create_comment(self, review_id: int, body: str) -> Comment:
        return self._repository.create(review_id=review_id, body=body)

    def list_comments(self, review_id: int, limit: int, offset: int) -> list[Comment]:
        return self._repository.list(review_id=review_id, limit=limit, offset=offset)

    def update_comment(self, comment_id: int, review_id: int, body: str) -> Comment:
        return self._repository.update(comment_id=comment_id, review_id=review_id, body=body)

    def delete_comment(self, comment_id: int, review_id: int) -> bool:
        return self._repository.delete(comment_id=comment_id, review_id=review_id)


class SavedRecordsService:
    def __init__(self, repository: SavedRecordsRepository) -> None:
        self._repository = repository

    def save_record(self, record_id: int) -> tuple[SavedRecord, bool]:
        return self._repository.save(record_id=record_id)

    def list_saved(self, limit: int, offset: int) -> list[SavedRecord]:
        return self._repository.list(limit=limit, offset=offset)

    def remove_saved_record(self, record_id: int) -> bool:
        return self._repository.delete(record_id=record_id)
