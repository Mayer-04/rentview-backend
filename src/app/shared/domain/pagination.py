from dataclasses import dataclass
from typing import Generic, TypeVar


class PageOutOfRangeError(Exception):
    """Raised when the requested page is beyond available results."""


T = TypeVar("T")


@dataclass
class PaginatedResult(Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size
