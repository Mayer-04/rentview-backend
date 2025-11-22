from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.features.comments.application.services import CommentsRepository, SavedRecordsRepository
from app.features.comments.domain.exceptions import (
    CommentNotFoundError,
    RecordNotFoundError,
    ReviewNotFoundError,
)
from app.features.comments.domain.models import Comment, SavedRecord


def _is_foreign_key_violation(exc: IntegrityError) -> bool:
    sqlstate = getattr(getattr(exc, "orig", None), "sqlstate", None)
    return sqlstate == "23503"


class SqlAlchemyCommentsRepository(CommentsRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, review_id: int, body: str) -> Comment:
        stmt = text(
            """
            INSERT INTO comments (review_id, body)
            VALUES (:review_id, :body)
            RETURNING id, review_id, body, created_at, updated_at
            """
        )
        try:
            result = self._session.execute(stmt, {"review_id": review_id, "body": body})
            row = result.mappings().one()
            self._session.commit()
            return Comment(**row)
        except IntegrityError as exc:
            self._session.rollback()
            if _is_foreign_key_violation(exc):
                raise ReviewNotFoundError(f"Review {review_id} not found") from exc
            raise

    def list(self, review_id: int, limit: int, offset: int) -> list[Comment]:
        stmt = text(
            """
            SELECT id, review_id, body, created_at, updated_at
            FROM comments
            WHERE review_id = :review_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
        )
        result = self._session.execute(
            stmt, {"review_id": review_id, "limit": limit, "offset": offset}
        )
        return [Comment(**row) for row in result.mappings().all()]

    def update(self, comment_id: int, review_id: int, body: str) -> Comment:
        stmt = text(
            """
            UPDATE comments
            SET body = :body, updated_at = CURRENT_TIMESTAMP
            WHERE id = :comment_id AND review_id = :review_id
            RETURNING id, review_id, body, created_at, updated_at
            """
        )
        result = self._session.execute(
            stmt, {"body": body, "comment_id": comment_id, "review_id": review_id}
        )
        row = result.mappings().first()
        if row is None:
            self._session.rollback()
            raise CommentNotFoundError(f"Comment {comment_id} not found for review {review_id}")

        self._session.commit()
        return Comment(**row)

    def delete(self, comment_id: int, review_id: int) -> bool:
        stmt = text(
            """
            DELETE FROM comments
            WHERE id = :comment_id AND review_id = :review_id
            RETURNING id
            """
        )
        result = self._session.execute(
            stmt, {"comment_id": comment_id, "review_id": review_id}
        )
        self._session.commit()
        return result.first() is not None


class SqlAlchemySavedRecordsRepository(SavedRecordsRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, record_id: int) -> tuple[SavedRecord, bool]:
        insert_stmt = text(
            """
            INSERT INTO saved_records (record_id)
            VALUES (:record_id)
            ON CONFLICT (record_id) DO NOTHING
            RETURNING id, record_id, saved_at
            """
        )
        try:
            result = self._session.execute(insert_stmt, {"record_id": record_id})
            row = result.mappings().first()
            created = row is not None

            if not created:
                existing_stmt = text(
                    "SELECT id, record_id, saved_at FROM saved_records WHERE record_id = :record_id"
                )
                row = (
                    self._session.execute(existing_stmt, {"record_id": record_id}).mappings().one()
                )

            self._session.commit()
            return SavedRecord(**row), created
        except IntegrityError as exc:
            self._session.rollback()
            if _is_foreign_key_violation(exc):
                raise RecordNotFoundError(f"Record {record_id} not found") from exc
            raise

    def list(self, limit: int, offset: int) -> list[SavedRecord]:
        stmt = text(
            """
            SELECT id, record_id, saved_at
            FROM saved_records
            ORDER BY saved_at DESC
            LIMIT :limit OFFSET :offset
            """
        )
        result = self._session.execute(stmt, {"limit": limit, "offset": offset})
        return [SavedRecord(**row) for row in result.mappings().all()]

    def delete(self, record_id: int) -> bool:
        stmt = text("DELETE FROM saved_records WHERE record_id = :record_id RETURNING id")
        result = self._session.execute(stmt, {"record_id": record_id})
        self._session.commit()
        return result.first() is not None
