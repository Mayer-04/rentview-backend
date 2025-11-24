from app.features.reviews.application.dtos import CreateReviewDTO, ReviewDTO, ReviewImageDTO
from app.features.reviews.domain.review import Review, ReviewImage


def to_review_entity(dto: CreateReviewDTO) -> Review:
    """Build a domain Review from a creation DTO."""
    return Review(
        record_id=dto.record_id,
        title=(dto.title.strip() if dto.title is not None else None),
        email=dto.email.strip(),
        body=dto.body.strip(),
        rating=dto.rating,
        images=[ReviewImage(image_url=image.strip()) for image in dto.images],
    )


def to_review_dto(review: Review) -> ReviewDTO:
    """Map a domain Review into an application DTO."""
    if review.id is None or review.created_at is None or review.updated_at is None:
        raise ValueError("Review must be persisted before mapping to DTO")
    return ReviewDTO(
        id=review.id,
        record_id=review.record_id,
        title=review.title,
        email=review.email,
        body=review.body,
        rating=review.rating,
        images=[
            ReviewImageDTO(
                id=image.id if image.id is not None else 0,
                review_id=image.review_id if image.review_id is not None else review.id,
                image_url=image.image_url,
                created_at=image.created_at if image.created_at is not None else review.created_at,
            )
            for image in review.images
        ],
        created_at=review.created_at,
        updated_at=review.updated_at,
    )
