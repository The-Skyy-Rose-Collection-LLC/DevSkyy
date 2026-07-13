# database/models_competitors.py
"""SQLAlchemy models backing the competitor-analysis store (US-034).

Registered on database.db.Base — see database/models_brand_assets.py for
the runtime-vs-Alembic rationale (create_all() at startup is what actually
persists data; no separate Alembic migration exists for this domain).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class CompetitorRecord(Base):
    """Persisted row for services.competitive.schemas.Competitor."""

    __tablename__ = "competitors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50), default="direct", index=True)
    price_positioning: Mapped[str] = mapped_column(String(50), default="premium", index=True)
    website: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class CompetitorAssetRecord(Base):
    """Persisted row for services.competitive.schemas.CompetitorAsset."""

    __tablename__ = "competitor_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    competitor_id: Mapped[str] = mapped_column(String(36), ForeignKey("competitors.id"), index=True)
    url: Mapped[str] = mapped_column(String(2048))
    product_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    estimated_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    extracted_attributes_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    manual_tags_json: Mapped[str] = mapped_column(Text, default="[]")
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    __table_args__ = (Index("ix_competitor_assets_competitor", "competitor_id"),)
