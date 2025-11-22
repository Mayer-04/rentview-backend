class ReviewNotFoundError(Exception):
    """Raised when the referenced review does not exist."""


class RecordNotFoundError(Exception):
    """Raised when the referenced record does not exist."""


class CommentNotFoundError(Exception):
    """Raised when the referenced comment does not exist."""
