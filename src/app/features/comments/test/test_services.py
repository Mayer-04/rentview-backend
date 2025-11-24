from datetime import datetime

import pytest

from app.features.comments.application.services import (
    CommentsRepository,
    CommentsService,
    SavedRecordsRepository,
    SavedRecordsService,
)
from app.features.comments.domain.exceptions import InvalidPaginationError
from app.features.comments.domain.models import Comment, SavedRecord
from app.shared.domain.pagination import PageOutOfRangeError


class StubCommentsRepository(CommentsRepository):
    def __init__(self, items: list[Comment] | None = None, total: int = 0) -> None:
        self.created: list[tuple[int, str]] = []
        self.updated: list[tuple[int, int, str]] = []
        self.deleted: list[tuple[int, int]] = []
        self.list_called_with: list[dict[str, int]] = []
        self.create_return: Comment | None = None
        self.update_return: Comment | None = None
        self.delete_return: bool = True
        self.list_items = items or []
        self.list_total = total

    def create(self, review_id: int, body: str) -> Comment:
        self.created.append((review_id, body))
        return self.create_return or self.list_items[0]

    def list(self, review_id: int, limit: int, offset: int) -> tuple[list[Comment], int]:
        self.list_called_with.append({"review_id": review_id, "limit": limit, "offset": offset})
        return self.list_items, self.list_total

    def update(self, comment_id: int, review_id: int, body: str) -> Comment:
        self.updated.append((comment_id, review_id, body))
        return self.update_return or self.list_items[0]

    def delete(self, comment_id: int, review_id: int) -> bool:
        self.deleted.append((comment_id, review_id))
        return self.delete_return


class StubSavedRecordsRepository(SavedRecordsRepository):
    def __init__(self, items: list[SavedRecord] | None = None, total: int = 0) -> None:
        self.saved: list[int] = []
        self.list_called_with: list[dict[str, int]] = []
        self.delete_called_with: list[int] = []
        self.save_return: tuple[SavedRecord, bool] | None = None
        self.list_items = items or []
        self.list_total = total
        self.delete_return: bool = True

    def save(self, record_id: int) -> tuple[SavedRecord, bool]:
        self.saved.append(record_id)
        return self.save_return or (self.list_items[0], True)

    def list(self, limit: int, offset: int) -> tuple[list[SavedRecord], int]:
        self.list_called_with.append({"limit": limit, "offset": offset})
        return self.list_items, self.list_total

    def delete(self, record_id: int) -> bool:
        self.delete_called_with.append(record_id)
        return self.delete_return


def _sample_comment(idx: int = 1, review_id: int = 10) -> Comment:
    return Comment(
        id=idx,
        review_id=review_id,
        body=f"comment {idx}",
        created_at=datetime(2024, 1, idx),
        updated_at=datetime(2024, 1, idx, 12),
    )


def _sample_saved_record(idx: int = 1) -> SavedRecord:
    return SavedRecord(id=idx, record_id=idx * 100, saved_at=datetime(2024, 1, idx))


def test_create_comment_delegates_to_repository() -> None:
    comment = _sample_comment()
    repo = StubCommentsRepository(items=[comment])
    service = CommentsService(repo)

    result = service.create_comment(review_id=comment.review_id, body=comment.body)

    assert result == comment
    assert repo.created == [(comment.review_id, comment.body)]


def test_update_comment_delegates_to_repository() -> None:
    comment = _sample_comment()
    repo = StubCommentsRepository(items=[comment])
    service = CommentsService(repo)

    result = service.update_comment(
        comment_id=comment.id, review_id=comment.review_id, body="updated"
    )

    assert result == comment
    assert repo.updated == [(comment.id, comment.review_id, "updated")]


def test_delete_comment_delegates_to_repository() -> None:
    repo = StubCommentsRepository(items=[_sample_comment()])
    service = CommentsService(repo)

    removed = service.delete_comment(comment_id=1, review_id=2)

    assert removed is True
    assert repo.deleted == [(1, 2)]


def test_list_comments_returns_paginated_result_and_calculates_offset() -> None:
    items = [_sample_comment(idx=1), _sample_comment(idx=2)]
    repo = StubCommentsRepository(items=items, total=5)
    service = CommentsService(repo)

    result = service.list_comments(review_id=10, page=2, page_size=2)

    assert result.items == items
    assert result.total == 5
    assert result.page == 2
    assert result.page_size == 2
    assert result.total_pages == 3
    assert repo.list_called_with == [{"review_id": 10, "limit": 2, "offset": 2}]


@pytest.mark.parametrize("page", [0, -1])
def test_list_comments_rejects_invalid_page(page: int) -> None:
    service = CommentsService(StubCommentsRepository())

    with pytest.raises(InvalidPaginationError, match="page must be at least 1"):
        service.list_comments(review_id=1, page=page, page_size=10)


@pytest.mark.parametrize("page_size", [0, -5, 101])
def test_list_comments_rejects_invalid_page_size(page_size: int) -> None:
    service = CommentsService(StubCommentsRepository())

    with pytest.raises(InvalidPaginationError, match="page_size must be between 1 and 100"):
        service.list_comments(review_id=1, page=1, page_size=page_size)


def test_list_comments_raises_when_no_results_for_requested_page() -> None:
    service = CommentsService(StubCommentsRepository(items=[], total=0))

    with pytest.raises(
        PageOutOfRangeError, match="No hay comentarios disponibles para la página solicitada"
    ):
        service.list_comments(review_id=1, page=2, page_size=10)


def test_list_comments_raises_when_page_exceeds_total_pages() -> None:
    repo = StubCommentsRepository(items=[_sample_comment()], total=3)
    service = CommentsService(repo)

    with pytest.raises(
        PageOutOfRangeError,
        match="La página solicitada 5 excede el total de páginas 3",
    ):
        service.list_comments(review_id=1, page=5, page_size=1)


def test_save_record_delegates_to_repository() -> None:
    saved_record = _sample_saved_record()
    repo = StubSavedRecordsRepository(items=[saved_record])
    service = SavedRecordsService(repo)

    result, created = service.save_record(record_id=saved_record.record_id)

    assert result == saved_record
    assert created is True
    assert repo.saved == [saved_record.record_id]


def test_remove_saved_record_delegates_to_repository() -> None:
    repo = StubSavedRecordsRepository(items=[_sample_saved_record()])
    service = SavedRecordsService(repo)

    removed = service.remove_saved_record(record_id=123)

    assert removed is True
    assert repo.delete_called_with == [123]


def test_list_saved_returns_paginated_result_and_calculates_offset() -> None:
    saved_records = [_sample_saved_record(idx=1), _sample_saved_record(idx=2)]
    repo = StubSavedRecordsRepository(items=saved_records, total=4)
    service = SavedRecordsService(repo)

    result = service.list_saved(page=2, page_size=2)

    assert result.items == saved_records
    assert result.total == 4
    assert result.page == 2
    assert result.page_size == 2
    assert result.total_pages == 2
    assert repo.list_called_with == [{"limit": 2, "offset": 2}]


@pytest.mark.parametrize("page", [0, -3])
def test_list_saved_rejects_invalid_page(page: int) -> None:
    service = SavedRecordsService(StubSavedRecordsRepository())

    with pytest.raises(InvalidPaginationError, match="page must be at least 1"):
        service.list_saved(page=page, page_size=10)


@pytest.mark.parametrize("page_size", [0, -1, 201])
def test_list_saved_rejects_invalid_page_size(page_size: int) -> None:
    service = SavedRecordsService(StubSavedRecordsRepository())

    with pytest.raises(InvalidPaginationError, match="page_size must be between 1 and 200"):
        service.list_saved(page=1, page_size=page_size)


def test_list_saved_raises_when_no_results_for_requested_page() -> None:
    service = SavedRecordsService(StubSavedRecordsRepository(items=[], total=0))

    with pytest.raises(
        PageOutOfRangeError, match="No hay registros guardados para la página solicitada"
    ):
        service.list_saved(page=2, page_size=10)


def test_list_saved_raises_when_page_exceeds_total_pages() -> None:
    repo = StubSavedRecordsRepository(items=[_sample_saved_record()], total=2)
    service = SavedRecordsService(repo)

    with pytest.raises(
        PageOutOfRangeError,
        match="La página solicitada 3 excede el total de páginas 2",
    ):
        service.list_saved(page=3, page_size=1)
