from unittest.mock import Mock

import pytest

from app.features.reviews.application.dtos import UpdateReviewDTO
from app.features.reviews.application.services import ReviewService
from app.features.reviews.domain.exceptions import EmptyReviewUpdateError


def test_update_review_applies_changes_and_saves(make_review) -> None:
    repository = Mock()
    existing = make_review(
        id=10,
        title="Viejo",
        email="old@example.com",
        body="Texto viejo",
        rating=2,
    )
    repository.get.return_value = existing
    updated = make_review(
        id=10,
        title="Nuevo",
        email="nuevo@example.com",
        body="Texto nuevo",
        rating=5,
    )
    repository.save.return_value = updated
    service = ReviewService(repository)

    dto = UpdateReviewDTO(
        review_id=10,
        title=" Nuevo ",
        email=" nuevo@example.com ",
        body=" Texto nuevo ",
        rating=5,
    )

    result = service.update_review(dto)

    assert result is updated
    repository.get.assert_called_once_with(10)
    repository.save.assert_called_once()
    saved_review = repository.save.call_args.args[0]
    assert saved_review.title == "Nuevo"
    assert saved_review.email == "nuevo@example.com"
    assert saved_review.body == "Texto nuevo"
    assert saved_review.rating == 5


def test_update_review_requires_at_least_one_field() -> None:
    repository = Mock()
    service = ReviewService(repository)

    with pytest.raises(EmptyReviewUpdateError):
        service.update_review(UpdateReviewDTO(review_id=1))

    repository.get.assert_not_called()
