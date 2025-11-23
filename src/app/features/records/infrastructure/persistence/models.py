from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RecordModel(Base):
    __tablename__ = "records"
    __table_args__ = (
        CheckConstraint("monthly_rent > 0", name="ck_records_monthly_rent_positive"),
        CheckConstraint(
            "housing_type IN ('apartamento','casa','comercial')",
            name="ck_records_housing_type_allowed",
        ),
    )
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    housing_type: Mapped[str] = mapped_column(String(20), nullable=False)
    monthly_rent: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    images: Mapped[list[RecordImageModel]] = relationship(
        "RecordImageModel",
        back_populates="record",
        cascade="all, delete-orphan",
    )


class RecordImageModel(Base):
    __tablename__ = "record_images"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    record_id: Mapped[int] = mapped_column(
        ForeignKey("records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    record: Mapped[RecordModel] = relationship("RecordModel", back_populates="images")
