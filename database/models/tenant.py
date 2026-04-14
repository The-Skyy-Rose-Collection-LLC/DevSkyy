"""
Tenant Model
============

Multi-tenancy support for the DevSkyy platform.
Each tenant is an organisation (team / company) with its own plan and settings.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class Tenant(Base):
    """
    Top-level tenancy record.

    A Tenant groups users under a shared subscription plan.
    Settings are persisted as a JSON blob for schema-free extensibility.
    """

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    tier: Mapped[str] = mapped_column(String(50), default="free", index=True)
    settings: Mapped[str] = mapped_column(Text, default="{}")  # JSON blob
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def get_settings(self) -> dict:
        """Deserialize the JSON settings blob."""
        try:
            return json.loads(self.settings or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_settings(self, data: dict) -> None:
        """Serialize and store settings."""
        self.settings = json.dumps(data)

    def __repr__(self) -> str:
        return f"<Tenant id={self.id!r} slug={self.slug!r} tier={self.tier!r}>"
