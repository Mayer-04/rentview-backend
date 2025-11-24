import pytest

from app.features.reviews.application.mappers import to_review_dto
from app.features.reviews.domain.review import Review


def test_to_review_dto_requires_persisted_values() -> None:
    transient_review = Review(
        record_id=1,
        email="user@example.com",
        body="texto",
        rating=4,
    )

    with pytest.raises(ValueError):
        to_review_dto(transient_review)
