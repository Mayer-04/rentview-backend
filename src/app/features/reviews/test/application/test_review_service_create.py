from unittest.mock import Mock

import pytest

from app.features.reviews.application.dtos import CreateReviewDTO
from app.features.reviews.application.services import ReviewService
from app.features.reviews.domain.exceptions import InvalidReviewImageError, RecordNotFoundError


def test_create_review_persists_and_notifies(make_review) -> None:
    repository = Mock()
    repository.record_exists.return_value = True
    created_review = make_review(id=42)
    repository.create.return_value = created_review
    email_sender = Mock()
    service = ReviewService(repository, email_sender=email_sender)

    dto = CreateReviewDTO(
        record_id=1,
        title="  Excelente estadía ",
        email=" user@example.com ",
        body=" Muy cómodo ",
        rating=5,
        images=[" https://cdn.example.com/photo.jpg "],
    )

    result = service.create_review(dto)

    assert result is created_review
    repository.record_exists.assert_called_once_with(1)
    repository.create.assert_called_once()
    saved_review = repository.create.call_args.args[0]
    assert saved_review.title == "Excelente estadía"
    assert saved_review.email == "user@example.com"
    assert saved_review.body == "Muy cómodo"
    assert saved_review.images[0].image_url == "https://cdn.example.com/photo.jpg"
    email_sender.send.assert_called_once()


def test_create_review_fails_when_record_missing() -> None:
    repository = Mock()
    repository.record_exists.return_value = False
    service = ReviewService(repository)

    dto = CreateReviewDTO(
        record_id=99,
        title="Sin record",
        email="user@example.com",
        body="Comentario",
        rating=3,
    )

    with pytest.raises(RecordNotFoundError):
        service.create_review(dto)

    repository.create.assert_not_called()


def test_create_review_rejects_invalid_image_extension() -> None:
    repository = Mock()
    repository.record_exists.return_value = True
    service = ReviewService(repository)

    dto = CreateReviewDTO(
        record_id=1,
        title="Depto",
        email="user@example.com",
        body="Texto",
        rating=4,
        images=["https://cdn.example.com/foto.bmp"],
    )

    with pytest.raises(InvalidReviewImageError):
        service.create_review(dto)

    repository.create.assert_not_called()
