from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Comment:
    id: int
    review_id: int
    body: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class SavedRecord:
    id: int
    record_id: int
    saved_at: datetime
