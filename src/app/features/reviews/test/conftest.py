import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pytest

# Allow imports from the src/ layout when running pytest from the repo root.
ROOT_DIR = Path(__file__).resolve().parents[4]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.features.reviews.domain.review import Review


@pytest.fixture
def make_review() -> Callable[..., Review]:
    def _make(**overrides: object) -> Review:
        base = {
            "id": 1,
            "record_id": 1,
            "title": "Título",
            "email": "user@example.com",
            "body": "Buen lugar",
            "rating": 4,
            "images": [],
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        base.update(overrides)
        return Review(**base)  # type: ignore[arg-type]

    return _make
