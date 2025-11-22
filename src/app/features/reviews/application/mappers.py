from app.features.reviews.application.dtos import CreateReviewDTO, ReviewDTO
from app.features.reviews.domain.review import Review


def to_review_entity(dto: CreateReviewDTO) -> Review:
    """Build a domain Review from a creation DTO."""
    return Review(
        record_id=dto.record_id,
        title=(dto.title.strip() if dto.title is not None else None),
        body=dto.body.strip(),
        rating=dto.rating,
    )


def to_review_dto(review: Review) -> ReviewDTO:
    """Map a domain Review into an application DTO."""
    if review.id is None or review.created_at is None or review.updated_at is None:
        raise ValueError("Review must be persisted before mapping to DTO")
    return ReviewDTO(
        id=review.id,
        record_id=review.record_id,
        title=review.title,
        body=review.body,
        rating=review.rating,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )
