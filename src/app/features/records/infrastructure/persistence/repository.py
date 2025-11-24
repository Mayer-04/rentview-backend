from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.features.records.domain import exceptions
from app.features.records.domain.models import HousingType, Record, RecordImage
from app.features.records.domain.repository import RecordRepository
from app.features.records.infrastructure.persistence.models import RecordImageModel, RecordModel
from app.features.reviews.infrastructure.models import ReviewModel


class SQLAlchemyRecordRepository(RecordRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, record: Record) -> Record:
        record_model = RecordModel(
            address=record.address,
            country=record.country,
            city=record.city,
            housing_type=record.housing_type.value,
            monthly_rent=record.monthly_rent,
        )

        if record.images:
            record_model.images = [
                RecordImageModel(image_url=image.image_url) for image in record.images
            ]

        with self._session.begin():
            self._session.add(record_model)

        self._session.refresh(record_model)
        return self._to_domain(record_model)

    def get(self, record_id: int) -> Record | None:
        stmt = (
            select(RecordModel)
            .options(selectinload(RecordModel.images))
            .where(RecordModel.id == record_id)
        )
        record_model = self._session.scalar(stmt)
        if record_model is None:
            return None
        stats = self._load_review_stats([record_id])
        return self._to_domain(record_model, stats)

    def delete(self, record_id: int) -> None:
        record_model = self._session.get(RecordModel, record_id)
        if record_model is None:
            return

        self._session.delete(record_model)
        self._session.commit()

    def list(self, limit: int = 20, offset: int = 0) -> tuple[list[Record], int]:
        stmt = (
            select(RecordModel)
            .options(selectinload(RecordModel.images))
            .order_by(RecordModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        records = self._session.scalars(stmt).all()
        stats = self._load_review_stats([record.id for record in records])

        total_stmt = select(func.count()).select_from(RecordModel)
        total = self._session.scalar(total_stmt) or 0

        return [self._to_domain(record_model, stats) for record_model in records], int(total)

    def update(self, record: Record, *, replace_images: bool) -> Record:
        record_model = self._session.get(RecordModel, record.id)
        if record_model is None:
            raise exceptions.RecordNotFoundError(f"Record {record.id} does not exist")

        record_model.address = record.address
        record_model.country = record.country
        record_model.city = record.city
        record_model.housing_type = record.housing_type.value
        record_model.monthly_rent = record.monthly_rent

        if replace_images:
            record_model.images.clear()
            for image in record.images:
                record_model.images.append(RecordImageModel(image_url=image.image_url))

        self._session.commit()
        self._session.refresh(record_model)
        stats = self._load_review_stats([record_model.id])
        return self._to_domain(record_model, stats)

    def _load_review_stats(self, record_ids: list[int]) -> dict[int, tuple[int, float | None]]:
        if not record_ids:
            return {}

        stmt = (
            select(
                ReviewModel.record_id,
                func.count(ReviewModel.id).label("reviews_count"),
                func.avg(ReviewModel.rating).label("average_rating"),
            )
            .where(ReviewModel.record_id.in_(record_ids))
            .group_by(ReviewModel.record_id)
        )
        results = self._session.execute(stmt).all()
        stats: dict[int, tuple[int, float | None]] = {}
        for row in results:
            stats[int(row.record_id)] = (
                int(row.reviews_count),
                float(row.average_rating) if row.average_rating is not None else None,
            )
        return stats

    def _to_domain(
        self, record_model: RecordModel, stats: dict[int, tuple[int, float | None]] | None = None
    ) -> Record:
        images = [
            RecordImage(
                id=image.id,
                image_url=image.image_url,
                created_at=image.created_at,
            )
            for image in record_model.images or []
        ]

        reviews_count = 0
        average_rating: float | None = None
        if stats and record_model.id is not None:
            record_stats = stats.get(record_model.id)
            if record_stats is not None:
                reviews_count, average_rating = record_stats

        return Record(
            id=record_model.id,
            address=record_model.address,
            country=record_model.country,
            city=record_model.city,
            housing_type=HousingType(record_model.housing_type),
            monthly_rent=record_model.monthly_rent,
            reviews_count=reviews_count,
            average_rating=average_rating,
            images=images,
            created_at=record_model.created_at,
            updated_at=record_model.updated_at,
        )
