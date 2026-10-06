"""FCM push-notification device tokens (Phase 6 early warning).

Mirrors the `device_tokens` table (migration 0005). Mobile clients register
their Firebase Cloud Messaging token here so the alert engine can push
warnings and risk-change notifications to at-risk users.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fcm_token: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    platform: Mapped[str] = mapped_column(String(20), nullable=False, default="android")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="device_tokens")
