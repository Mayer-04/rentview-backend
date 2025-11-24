from app.features.reviews.domain.review import Review, ReviewImage
from app.features.reviews.infrastructure.models import ReviewImageModel, ReviewModel


def review_model_to_domain(model: ReviewModel) -> Review:
    """Map a persistence ReviewModel to the domain Review entity."""
    return Review(
        id=model.id,
        record_id=model.record_id,
        title=model.title,
        email=model.email,
        body=model.body,
        rating=model.rating,
        images=[
            ReviewImage(
                id=image.id,
                review_id=image.review_id,
                image_url=image.image_url,
                created_at=image.created_at,
            )
            for image in model.images or []
        ],
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def review_image_model_to_domain(model: ReviewImageModel) -> ReviewImage:
    return ReviewImage(
        id=model.id,
        review_id=model.review_id,
        image_url=model.image_url,
        created_at=model.created_at,
    )
