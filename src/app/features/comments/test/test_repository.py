from datetime import datetime
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.features.comments.domain.exceptions import (
    CommentNotFoundError,
    RecordNotFoundError,
    ReviewNotFoundError,
)
from app.features.comments.domain.models import Comment, SavedRecord
from app.features.comments.infrastructure.repository import (
    SqlAlchemyCommentsRepository,
    SqlAlchemySavedRecordsRepository,
)


class FakeMappings:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def one(self) -> dict:
        return self._rows[0]

    def first(self) -> dict | None:
        return self._rows[0] if self._rows else None

    def all(self) -> list[dict]:
        return list(self._rows)


class FakeResult:
    def __init__(self, rows: list[dict] | None = None, scalar_value: int | None = None) -> None:
        self._rows = rows or []
        self._scalar = scalar_value

    def mappings(self) -> FakeMappings:
        return FakeMappings(self._rows)

    def scalar(self) -> int | None:
        return self._scalar

    def first(self) -> dict | None:
        return self._rows[0] if self._rows else None


class FakeSession:
    def __init__(self, executes: list[object]) -> None:
        self._executes = list(executes)
        self.executed_params: list[dict] = []
        self.commit_calls = 0
        self.rollback_calls = 0

    def execute(self, stmt, params=None):  # type: ignore[override]
        self.executed_params.append(params or {})
        if not self._executes:
            raise AssertionError("No more fake results configured")
        action = self._executes.pop(0)
        if isinstance(action, Exception):
            raise action
        return action

    def commit(self) -> None:
        self.commit_calls += 1

    def rollback(self) -> None:
        self.rollback_calls += 1


def _comment_row(idx: int = 1, review_id: int = 10) -> dict:
    return {
        "id": idx,
        "review_id": review_id,
        "body": f"body {idx}",
        "created_at": datetime(2024, 1, idx),
        "updated_at": datetime(2024, 1, idx, 12),
    }


def _saved_record_row(idx: int = 1) -> dict:
    return {"id": idx, "record_id": idx * 100, "saved_at": datetime(2024, 1, idx)}


def _integrity_error(sqlstate: str | None) -> IntegrityError:
    return IntegrityError("stmt", {}, SimpleNamespace(sqlstate=sqlstate))


def test_create_comment_persists_and_commits_transaction() -> None:
    row = _comment_row(review_id=5)
    session = FakeSession([FakeResult(rows=[row])])
    repository = SqlAlchemyCommentsRepository(session)

    result = repository.create(review_id=5, body=row["body"])

    assert result == Comment(**row)
    assert session.commit_calls == 1
    assert session.rollback_calls == 0
    assert session.executed_params[0] == {"review_id": 5, "body": row["body"]}


def test_create_comment_raises_review_not_found_on_foreign_key_violation() -> None:
    session = FakeSession([_integrity_error("23503")])
    repository = SqlAlchemyCommentsRepository(session)

    with pytest.raises(ReviewNotFoundError):
        repository.create(review_id=99, body="missing")

    assert session.commit_calls == 0
    assert session.rollback_calls == 1


def test_create_comment_propagates_unexpected_integrity_error() -> None:
    session = FakeSession([_integrity_error("other")])
    repository = SqlAlchemyCommentsRepository(session)

    with pytest.raises(IntegrityError):
        repository.create(review_id=1, body="boom")

    assert session.commit_calls == 0
    assert session.rollback_calls == 1


def test_list_comments_returns_items_and_total() -> None:
    rows = [_comment_row(idx=1), _comment_row(idx=2)]
    session = FakeSession([FakeResult(rows=rows), FakeResult(scalar_value=5)])
    repository = SqlAlchemyCommentsRepository(session)

    items, total = repository.list(review_id=7, limit=2, offset=4)

    assert items == [Comment(**row) for row in rows]
    assert total == 5
    assert session.executed_params[0] == {"review_id": 7, "limit": 2, "offset": 4}
    assert session.executed_params[1] == {"review_id": 7}


def test_update_comment_updates_and_returns_entity() -> None:
    row = _comment_row(idx=3, review_id=8)
    session = FakeSession([FakeResult(rows=[row])])
    repository = SqlAlchemyCommentsRepository(session)

    result = repository.update(comment_id=3, review_id=8, body="updated body")

    assert result == Comment(**row)
    assert session.commit_calls == 1
    assert session.executed_params[0] == {"body": "updated body", "comment_id": 3, "review_id": 8}


def test_update_comment_raises_when_not_found() -> None:
    session = FakeSession([FakeResult(rows=[])])
    repository = SqlAlchemyCommentsRepository(session)

    with pytest.raises(CommentNotFoundError):
        repository.update(comment_id=1, review_id=2, body="nope")

    assert session.commit_calls == 0
    assert session.rollback_calls == 1


def test_delete_comment_returns_true_when_removed() -> None:
    session = FakeSession([FakeResult(rows=[{"id": 1}])])
    repository = SqlAlchemyCommentsRepository(session)

    removed = repository.delete(comment_id=1, review_id=2)

    assert removed is True
    assert session.commit_calls == 1
    assert session.executed_params[0] == {"comment_id": 1, "review_id": 2}


def test_delete_comment_returns_false_when_missing() -> None:
    session = FakeSession([FakeResult(rows=[])])
    repository = SqlAlchemyCommentsRepository(session)

    removed = repository.delete(comment_id=1, review_id=2)

    assert removed is False
    assert session.commit_calls == 1


def test_save_record_inserts_when_new() -> None:
    row = _saved_record_row(idx=1)
    session = FakeSession([FakeResult(rows=[row])])
    repository = SqlAlchemySavedRecordsRepository(session)

    saved_record, created = repository.save(record_id=row["record_id"])

    assert created is True
    assert saved_record == SavedRecord(**row)
    assert session.commit_calls == 1
    assert session.executed_params[0] == {"record_id": row["record_id"]}


def test_save_record_returns_existing_when_duplicate() -> None:
    row = _saved_record_row(idx=2)
    session = FakeSession([FakeResult(rows=[]), FakeResult(rows=[row])])
    repository = SqlAlchemySavedRecordsRepository(session)

    saved_record, created = repository.save(record_id=row["record_id"])

    assert created is False
    assert saved_record == SavedRecord(**row)
    assert session.commit_calls == 1
    assert session.executed_params[0] == {"record_id": row["record_id"]}
    assert session.executed_params[1] == {"record_id": row["record_id"]}


def test_save_record_raises_record_not_found_on_foreign_key_violation() -> None:
    session = FakeSession([_integrity_error("23503")])
    repository = SqlAlchemySavedRecordsRepository(session)

    with pytest.raises(RecordNotFoundError):
        repository.save(record_id=123)

    assert session.commit_calls == 0
    assert session.rollback_calls == 1


def test_list_saved_records_returns_items_and_total() -> None:
    rows = [_saved_record_row(idx=1)]
    session = FakeSession([FakeResult(rows=rows), FakeResult(scalar_value=2)])
    repository = SqlAlchemySavedRecordsRepository(session)

    items, total = repository.list(limit=10, offset=5)

    assert items == [SavedRecord(**row) for row in rows]
    assert total == 2
    assert session.executed_params[0] == {"limit": 10, "offset": 5}
    assert session.executed_params[1] == {}


def test_delete_saved_record_returns_true_when_removed() -> None:
    session = FakeSession([FakeResult(rows=[{"id": 1}])])
    repository = SqlAlchemySavedRecordsRepository(session)

    removed = repository.delete(record_id=111)

    assert removed is True
    assert session.commit_calls == 1
    assert session.executed_params[0] == {"record_id": 111}


def test_delete_saved_record_returns_false_when_missing() -> None:
    session = FakeSession([FakeResult(rows=[])])
    repository = SqlAlchemySavedRecordsRepository(session)

    removed = repository.delete(record_id=111)

    assert removed is False
    assert session.commit_calls == 1
