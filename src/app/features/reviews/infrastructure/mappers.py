from __future__ import annotations

from app.features.reviews.domain.review import Review
from app.features.reviews.infrastructure.models import ReviewModel


def review_model_to_domain(model: ReviewModel) -> Review:
    """Map a persistence ReviewModel to the domain Review entity."""
    return Review(
        id=model.id,
        record_id=model.record_id,
        title=model.title,
        body=model.body,
        rating=model.rating,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
