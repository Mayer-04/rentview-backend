from unittest.mock import Mock

import pytest

from app.features.reviews.application.services import ReviewService
from app.features.reviews.domain.exceptions import ReviewNotFoundError


def test_get_review_not_found() -> None:
    repository = Mock()
    repository.get.return_value = None
    service = ReviewService(repository)

    with pytest.raises(ReviewNotFoundError):
        service.get_review(123)
