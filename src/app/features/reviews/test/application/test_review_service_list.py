from unittest.mock import Mock

import pytest

from app.features.reviews.application.dtos import ListReviewsQuery
from app.features.reviews.application.services import ReviewService
from app.features.reviews.domain.exceptions import InvalidPaginationError
from app.shared.domain.pagination import PageOutOfRangeError


def test_list_reviews_returns_paginated_result(make_review) -> None:
    repository = Mock()
    repository.record_exists.return_value = True
    paged_review = make_review(id=2)
    repository.list_by_record.return_value = ([paged_review], 3)
    service = ReviewService(repository)

    query = ListReviewsQuery(record_id=7, page=2, page_size=2)
    result = service.list_reviews(query)

    repository.list_by_record.assert_called_once_with(record_id=7, limit=2, offset=2)
    assert result.items == [paged_review]
    assert result.total == 3
    assert result.total_pages == 2


def test_list_reviews_rejects_invalid_pagination() -> None:
    repository = Mock()
    repository.record_exists.return_value = True
    service = ReviewService(repository)

    with pytest.raises(InvalidPaginationError):
        service.list_reviews(ListReviewsQuery(record_id=1, page=0, page_size=20))

    repository.list_by_record.assert_not_called()


def test_list_reviews_raises_when_page_out_of_range() -> None:
    repository = Mock()
    repository.record_exists.return_value = True
    repository.list_by_record.return_value = ([], 0)
    service = ReviewService(repository)

    with pytest.raises(PageOutOfRangeError):
        service.list_reviews(ListReviewsQuery(record_id=1, page=2, page_size=5))
