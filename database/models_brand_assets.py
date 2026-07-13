# database/models_brand_assets.py
"""SQLAlchemy models backing the brand-assets store (US-013).

Registered on database.db.Base so DatabaseManager.initialize()'s
create_all() creates these tables on startup — the same runtime mechanism
every other table in database/db.py relies on. Alembic tracks a separate
schema for this domain via agents/models.py (see database/CLAUDE.md); that
migration is not run at deploy, so this Base is what actually persists data.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class BrandAssetRecord(Base):
    """Persisted row for api.v1.brand_assets.BrandAsset."""

    __tablename__ = "brand_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    url: Mapped[str] = mapped_column(String(2048))
    category: Mapped[str] = mapped_column(String(50), index=True)
    approval_status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    visual_features_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    r2_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    __table_args__ = (Index("ix_brand_assets_category_status", "category", "approval_status"),)


class IngestionJobRecord(Base):
    """Persisted row for api.v1.brand_assets.BulkIngestionJob."""

    __tablename__ = "brand_asset_ingestion_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    succeeded: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    results_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
