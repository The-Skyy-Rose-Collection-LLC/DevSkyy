"""
TenantUser Model
================

Membership record linking a user to a tenant with a specific role.
Supports owner / admin / member / viewer role hierarchy within each tenant.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class TenantUser(Base):
    """
    Junction table: tenant ↔ user with role.

    A user may belong to multiple tenants with different roles.
    The (tenant_id, user_id) pair is unique — one membership record per user per tenant.
    """

    __tablename__ = "tenant_users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    role: Mapped[str] = mapped_column(
        String(50),
        default="member",
        index=True,
    )  # owner | admin | member | viewer
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),)

    def __repr__(self) -> str:
        return f"<TenantUser tenant={self.tenant_id!r} user={self.user_id!r} role={self.role!r}>"
