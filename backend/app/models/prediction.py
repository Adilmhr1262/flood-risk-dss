"""Persisted machine learning-based risk assessment results.

Mirrors the `predictions` table in database/schema.sql. main_factors and
recommendations are stored as native TEXT[] arrays; input_features keeps the
feature vector as JSONB.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    geographic_id: Mapped[UUID] = mapped_column(
        ForeignKey("geographic_data.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)  # LOW / MEDIUM / HIGH
    input_features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    main_factors: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    recommendations: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    geographic: Mapped["GeographicData"] = relationship(back_populates="predictions")
    creator: Mapped["User | None"] = relationship(back_populates="predictions")
