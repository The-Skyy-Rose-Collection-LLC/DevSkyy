"""Add R2 storage keys to model3d_generations.

Revision ID: 005
Revises: 004
Create Date: 2026-07-22

Adds model_r2_key / rendered_preview_r2_key so generated GLBs and Tripo's
rendered preview images can be served via presigned R2 URLs instead of a
FastAPI byte-streaming route reading local disk (single-host-disk risk).
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add R2 key columns to model3d_generations."""
    op.add_column(
        "model3d_generations",
        sa.Column("model_r2_key", sa.String(1000), nullable=True),
    )
    op.add_column(
        "model3d_generations",
        sa.Column("rendered_preview_r2_key", sa.String(1000), nullable=True),
    )


def downgrade() -> None:
    """Remove R2 key columns from model3d_generations."""
    op.drop_column("model3d_generations", "rendered_preview_r2_key")
    op.drop_column("model3d_generations", "model_r2_key")
