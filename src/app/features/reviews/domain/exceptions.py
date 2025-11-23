class RecordNotFoundError(Exception):
    """Raised when a record referenced by a review does not exist."""


class ReviewNotFoundError(Exception):
    """Raised when a requested review cannot be found."""


class InvalidReviewRatingError(ValueError):
    """Raised when the rating is outside the allowed range."""


class InvalidReviewBodyError(ValueError):
    """Raised when the review body is missing or empty."""


class EmptyReviewUpdateError(ValueError):
    """Raised when an update request does not include any fields."""


class InvalidPaginationError(ValueError):
    """Raised when pagination parameters are invalid."""


class ReviewPersistenceError(Exception):
    """Raised when a persistence operation fails unexpectedly."""


class ReviewDeletionError(ReviewPersistenceError):
    """Raised when deleting a review fails unexpectedly."""
