"""Add brand assets tables for US-013.

Revision ID: 002
Revises: 001
Create Date: 2026-01-21

Tables:
- brand_assets: Brand asset storage with visual features
- brand_asset_ingestion_jobs: Bulk ingestion job tracking
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create brand asset tables."""
    # Brand Assets table
    op.create_table(
        "brand_assets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("approval_status", sa.String(50), server_default="pending"),
        sa.Column("campaign", sa.String(255)),
        sa.Column("season", sa.String(100)),
        sa.Column("photographer", sa.String(255)),
        sa.Column("location", sa.String(255)),
        sa.Column("shoot_date", sa.TIMESTAMP(timezone=True)),
        sa.Column("tags", postgresql.ARRAY(sa.Text())),
        sa.Column("notes", sa.Text()),
        sa.Column("r2_key", sa.String(500)),
        sa.Column("file_size_bytes", sa.Integer(), server_default="0"),
        sa.Column("width", sa.Integer()),
        sa.Column("height", sa.Integer()),
        sa.Column("mime_type", sa.String(100)),
        sa.Column(
            "visual_features",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("quality_score", sa.DECIMAL(3, 2), server_default="0.0"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
    )

    # Create indexes
    op.create_index("ix_brand_assets_category", "brand_assets", ["category"])
    op.create_index("ix_brand_assets_approval_status", "brand_assets", ["approval_status"])
    op.create_index("ix_brand_assets_campaign", "brand_assets", ["campaign"])
    op.create_index("ix_brand_assets_r2_key", "brand_assets", ["r2_key"])

    # Brand Asset Ingestion Jobs table
    op.create_table(
        "brand_asset_ingestion_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("total", sa.Integer(), server_default="0"),
        sa.Column("processed", sa.Integer(), server_default="0"),
        sa.Column("succeeded", sa.Integer(), server_default="0"),
        sa.Column("failed", sa.Integer(), server_default="0"),
        sa.Column(
            "results",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
    )

    # Create index for job status
    op.create_index(
        "ix_brand_asset_ingestion_jobs_status",
        "brand_asset_ingestion_jobs",
        ["status"],
    )

    # Create updated_at trigger for brand_assets
    op.execute("""
        CREATE OR REPLACE TRIGGER update_brand_assets_updated_at
            BEFORE UPDATE ON brand_assets
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop brand asset tables."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_brand_assets_updated_at ON brand_assets;")

    # Drop indexes
    op.drop_index("ix_brand_asset_ingestion_jobs_status")
    op.drop_index("ix_brand_assets_r2_key")
    op.drop_index("ix_brand_assets_campaign")
    op.drop_index("ix_brand_assets_approval_status")
    op.drop_index("ix_brand_assets_category")

    # Drop tables
    op.drop_table("brand_asset_ingestion_jobs")
    op.drop_table("brand_assets")
