from app.shared.domain.pagination import PageOutOfRangeError as SharedPageOutOfRangeError


class RecordError(Exception):
    """Base domain exception for record use cases."""


class RecordNotFoundError(RecordError):
    """Raised when attempting to access a missing record."""


class MissingRequiredFieldError(RecordError):
    """Raised when mandatory fields like address, country or city are empty."""


class InvalidImageFormatError(RecordError):
    """Raised when an image URL does not match allowed formats."""


class InvalidMonthlyRentError(RecordError):
    """Raised when monthly rent is not a positive amount."""


class PageOutOfRangeError(SharedPageOutOfRangeError, RecordError):
    """Raised when the requested page is beyond available results."""