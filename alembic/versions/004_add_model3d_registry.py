"""Add 3D model generation/review registry tables.

Revision ID: 004
Revises: 003
Create Date: 2026-07-22

Tables:
- model3d_generations: One row per Tripo generation attempt (dispatch
  inputs, GLB location, automated validation outcome)
- model3d_reviews: One row per human QA review of a model3d_generations
  row, fidelity dimensions matching frontend QAReviewSchema
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the 3D model generation/review registry tables."""
    # Model3D Generations table
    op.create_table(
        "model3d_generations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("task_id", sa.String(100)),
        sa.Column("provider", sa.String(50)),
        sa.Column("format", sa.String(20)),
        sa.Column("model_path", sa.String(1000)),
        sa.Column("source_image_path", sa.String(1000)),
        sa.Column("generation_cost_credits", sa.Float()),
        sa.Column("validation_status", sa.String(50)),
        sa.Column(
            "validation_details",
            postgresql.JSONB(astext_type=sa.Text()),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for model3d_generations
    op.create_index("ix_model3d_generations_sku", "model3d_generations", ["sku"])
    op.create_index("ix_model3d_generations_task_id", "model3d_generations", ["task_id"])
    op.create_index(
        "ix_model3d_generations_validation_status", "model3d_generations", ["validation_status"]
    )

    # Model3D Reviews table
    op.create_table(
        "model3d_reviews",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "generation_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("fidelity_score", sa.Float()),
        sa.Column(
            "fidelity_breakdown",
            postgresql.JSONB(astext_type=sa.Text()),
        ),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True)),
        sa.Column("notes", sa.Text()),
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
            ["generation_id"],
            ["model3d_generations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
    )

    # Create indexes for model3d_reviews
    op.create_index("ix_model3d_reviews_generation_id", "model3d_reviews", ["generation_id"])
    op.create_index("ix_model3d_reviews_status", "model3d_reviews", ["status"])

    # Create updated_at trigger for model3d_reviews
    op.execute("""
        CREATE OR REPLACE TRIGGER update_model3d_reviews_updated_at
            BEFORE UPDATE ON model3d_reviews
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop the 3D model generation/review registry tables."""
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS update_model3d_reviews_updated_at ON model3d_reviews;")

    # Drop model3d_reviews indexes and table
    op.drop_index("ix_model3d_reviews_status")
    op.drop_index("ix_model3d_reviews_generation_id")
    op.drop_table("model3d_reviews")

    # Drop model3d_generations indexes and table
    op.drop_index("ix_model3d_generations_validation_status")
    op.drop_index("ix_model3d_generations_task_id")
    op.drop_index("ix_model3d_generations_sku")
    op.drop_table("model3d_generations")
