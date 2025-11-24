from __future__ import annotations

from typing import Protocol

from app.features.records.domain.models import Record


class RecordRepository(Protocol):
    def create(self, record: Record) -> Record: ...

    def get(self, record_id: int) -> Record | None: ...

    def delete(self, record_id: int) -> None: ...

    def list(self, limit: int = 20, offset: int = 0) -> tuple[list[Record], int]: ...

    def update(self, record: Record, *, replace_images: bool) -> Record: ...
