"""Add analytics tables for US-001: Analytics Database Schema.

Revision ID: 003
Revises: 002
Create Date: 2026-01-22

Tables:
- analytics_events: Raw event storage for dashboard analytics
- analytics_rollups: Pre-aggregated metrics for performance
- alert_configs: Alert rule configurations
- alert_history: Alert trigger history with acknowledgment tracking
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create analytics tables for admin dashboard."""
    # Analytics Events table - raw event storage
    op.create_table(
        "analytics_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_name", sa.String(255), nullable=False),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("session_id", sa.String(100)),
        sa.Column("correlation_id", sa.String(64)),
        sa.Column(
            "properties",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("numeric_value", sa.DECIMAL(20, 6)),
        sa.Column("string_value", sa.String(500)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("geo_country", sa.String(2)),
        sa.Column("geo_region", sa.String(100)),
        sa.Column(
            "event_timestamp",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for analytics_events
    op.create_index("ix_analytics_events_event_type", "analytics_events", ["event_type"])
    op.create_index("ix_analytics_events_event_name", "analytics_events", ["event_name"])
    op.create_index("ix_analytics_events_source", "analytics_events", ["source"])
    op.create_index("ix_analytics_events_user_id", "analytics_events", ["user_id"])
    op.create_index("ix_analytics_events_session_id", "analytics_events", ["session_id"])
    op.create_index("ix_analytics_events_correlation_id", "analytics_events", ["correlation_id"])
    op.create_index("ix_analytics_events_event_timestamp", "analytics_events", ["event_timestamp"])
    # Composite index for common query patterns
    op.create_index(
        "ix_analytics_events_type_timestamp",
        "analytics_events",
        ["event_type", "event_timestamp"],
    )

    # Analytics Rollups table - pre-aggregated metrics
    op.create_table(
        "analytics_rollups",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("metric_name", sa.String(255), nullable=False),
        sa.Column("dimension", sa.String(100), nullable=False),
        sa.Column("dimension_value", sa.String(255)),
        sa.Column(
            "granularity",
            sa.String(20),
            nullable=False,
        ),  # minute, hour, day, week, month
        sa.Column("period_start", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("period_end", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("count", sa.BigInteger(), server_default="0"),
        sa.Column("sum_value", sa.DECIMAL(20, 6)),
        sa.Column("avg_value", sa.DECIMAL(20, 6)),
        sa.Column("min_value", sa.DECIMAL(20, 6)),
        sa.Column("max_value", sa.DECIMAL(20, 6)),
        sa.Column("p50_value", sa.DECIMAL(20, 6)),
        sa.Column("p95_value", sa.DECIMAL(20, 6)),
        sa.Column("p99_value", sa.DECIMAL(20, 6)),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
        ),
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
    )

    # Create unique constraint for rollup deduplication
    op.create_unique_constraint(
        "uq_analytics_rollups_metric_dimension_period",
        "analytics_rollups",
        ["metric_name", "dimension", "dimension_value", "granularity", "period_start"],
    )

    # Create indexes for analytics_rollups
    op.create_index("ix_analytics_rollups_metric_name", "analytics_rollups", ["metric_name"])
    op.create_index("ix_analytics_rollups_dimension", "analytics_rollups", ["dimension"])
    op.create_index("ix_analytics_rollups_granularity", "analytics_rollups", ["granularity"])
    op.create_index("ix_analytics_rollups_period_start", "analytics_rollups", ["period_start"])
    # Composite index for rollup queries
    op.create_index(
        "ix_analytics_rollups_metric_granularity_period",
        "analytics_rollups",
        ["metric_name", "granularity", "period_start"],
    )

    # Alert Configs table - alert rule configurations
    op.create_table(
        "alert_configs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("metric_name", sa.String(255), nullable=False),
        sa.Column("condition_type", sa.String(50), nullable=False),  # threshold, anomaly, rate
        sa.Column(
            "condition_operator",
            sa.String(20),
            nullable=False,
        ),  # gt, lt, gte, lte, eq, neq
        sa.Column("threshold_value", sa.DECIMAL(20, 6)),
        sa.Column("threshold_unit", sa.String(50)),
        sa.Column("window_duration_seconds", sa.Integer(), server_default="300"),
        sa.Column("evaluation_interval_seconds", sa.Integer(), server_default="60"),
        sa.Column("cooldown_seconds", sa.Integer(), server_default="300"),
        sa.Column("severity", sa.String(20), server_default="warning"),  # info, warning, critical
        sa.Column("is_enabled", sa.Boolean(), server_default="true"),
        sa.Column(
            "notification_channels",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column(
            "notification_config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "filters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
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
    )

    # Create indexes for alert_configs
    op.create_index("ix_alert_configs_name", "alert_configs", ["name"])
    op.create_index("ix_alert_configs_metric_name", "alert_configs", ["metric_name"])
    op.create_index("ix_alert_configs_severity", "alert_configs", ["severity"])
    op.create_index("ix_alert_configs_is_enabled", "alert_configs", ["is_enabled"])

    # Alert History table - alert trigger history
    op.create_table(
        "alert_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "alert_config_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("alert_configs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False),  # triggered, resolved, acknowledged
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("metric_value", sa.DECIMAL(20, 6)),
        sa.Column("threshold_value", sa.DECIMAL(20, 6)),
        sa.Column(
            "context",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "triggered_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("acknowledged_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "acknowledged_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("acknowledge_note", sa.Text()),
        sa.Column(
            "notifications_sent",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes for alert_history
    op.create_index("ix_alert_history_alert_config_id", "alert_history", ["alert_config_id"])
    op.create_index("ix_alert_history_status", "alert_history", ["status"])
    op.create_index("ix_alert_history_severity", "alert_history", ["severity"])
    op.create_index("ix_alert_history_triggered_at", "alert_history", ["triggered_at"])
    # Composite index for alert queries
    op.create_index(
        "ix_alert_history_config_status_triggered",
        "alert_history",
        ["alert_config_id", "status", "triggered_at"],
    )

    # Create updated_at trigger for analytics_rollups
    op.execute("""
        CREATE OR REPLACE TRIGGER update_analytics_rollups_updated_at
            BEFORE UPDATE ON analytics_rollups
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    # Create updated_at trigger for alert_configs
    op.execute("""
        CREATE OR REPLACE TRIGGER update_alert_configs_updated_at
            BEFORE UPDATE ON alert_configs
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop analytics tables."""
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_alert_configs_updated_at ON alert_configs;")
    op.execute("DROP TRIGGER IF EXISTS update_analytics_rollups_updated_at ON analytics_rollups;")

    # Drop alert_history indexes and table
    op.drop_index("ix_alert_history_config_status_triggered")
    op.drop_index("ix_alert_history_triggered_at")
    op.drop_index("ix_alert_history_severity")
    op.drop_index("ix_alert_history_status")
    op.drop_index("ix_alert_history_alert_config_id")
    op.drop_table("alert_history")

    # Drop alert_configs indexes and table
    op.drop_index("ix_alert_configs_is_enabled")
    op.drop_index("ix_alert_configs_severity")
    op.drop_index("ix_alert_configs_metric_name")
    op.drop_index("ix_alert_configs_name")
    op.drop_table("alert_configs")

    # Drop analytics_rollups indexes and table
    op.drop_index("ix_analytics_rollups_metric_granularity_period")
    op.drop_index("ix_analytics_rollups_period_start")
    op.drop_index("ix_analytics_rollups_granularity")
    op.drop_index("ix_analytics_rollups_dimension")
    op.drop_index("ix_analytics_rollups_metric_name")
    op.drop_constraint("uq_analytics_rollups_metric_dimension_period", "analytics_rollups")
    op.drop_table("analytics_rollups")

    # Drop analytics_events indexes and table
    op.drop_index("ix_analytics_events_type_timestamp")
    op.drop_index("ix_analytics_events_event_timestamp")
    op.drop_index("ix_analytics_events_correlation_id")
    op.drop_index("ix_analytics_events_session_id")
    op.drop_index("ix_analytics_events_user_id")
    op.drop_index("ix_analytics_events_source")
    op.drop_index("ix_analytics_events_event_name")
    op.drop_index("ix_analytics_events_event_type")
    op.drop_table("analytics_events")
