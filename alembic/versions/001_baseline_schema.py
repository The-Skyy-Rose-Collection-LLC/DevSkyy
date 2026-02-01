"""baseline schema

Revision ID: 001
Revises:
Create Date: 2026-01-05

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create baseline schema for DevSkyy."""

    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # Users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("role", sa.String(50), server_default="customer"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("is_verified", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("last_login", sa.TIMESTAMP(timezone=True)),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])

    # Products table
    op.create_table(
        "products",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("sku", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(100)),
        sa.Column("price", sa.DECIMAL(10, 2), nullable=False),
        sa.Column("inventory_quantity", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("tags", postgresql.ARRAY(sa.Text())),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_products_sku", "products", ["sku"])
    op.create_index("idx_products_status", "products", ["status"])

    # Orders table
    op.create_table(
        "orders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("order_number", sa.String(50), unique=True, nullable=False),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("total_price", sa.DECIMAL(10, 2), nullable=False),
        sa.Column("subtotal", sa.DECIMAL(10, 2), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_orders_user_id", "orders", ["user_id"])
    op.create_index("idx_orders_status", "orders", ["status"])

    # LLM Round Table Results
    op.create_table(
        "llm_round_table_results",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("result_id", sa.String(100), unique=True, nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("task_category", sa.String(100)),
        sa.Column("winner_provider", sa.String(50)),
        sa.Column("winner_response", sa.Text()),
        sa.Column("participants", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_llm_results_category", "llm_round_table_results", ["task_category"])

    # Agent Execution Logs
    op.create_table(
        "agent_executions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("execution_id", sa.String(100), unique=True, nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), server_default="running"),
        sa.Column("result", postgresql.JSONB()),
        sa.Column("tokens_used", sa.Integer()),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_agent_executions_agent", "agent_executions", ["agent_name"])
    op.create_index("idx_agent_executions_status", "agent_executions", ["status"])

    # NEW: Tool Executions (audit trail)
    op.create_table(
        "tool_executions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("tool_name", sa.String(128), nullable=False),
        sa.Column("agent_id", sa.String(100)),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.Column("inputs", postgresql.JSONB(), nullable=False),
        sa.Column("output", postgresql.JSONB()),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("error_message", sa.Text()),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
    )
    op.create_index("idx_tool_executions_correlation", "tool_executions", ["correlation_id"])
    op.create_index("idx_tool_executions_tool", "tool_executions", ["tool_name"])
    op.create_index("idx_tool_executions_status", "tool_executions", ["status"])

    # NEW: RAG Documents (knowledge base)
    op.create_table(
        "rag_documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("document_id", sa.String(100), unique=True, nullable=False),
        sa.Column("source_path", sa.String(500)),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("chunk_index", sa.Integer()),
        sa.Column("total_chunks", sa.Integer()),
        sa.Column("embedding_model", sa.String(100)),
        sa.Column("metadata", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )
    op.create_index("idx_rag_documents_hash", "rag_documents", ["content_hash"])
    op.create_index("idx_rag_documents_source", "rag_documents", ["source_path"])

    # Create auto-update trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Apply triggers
    op.execute(
        "CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
    )
    op.execute(
        "CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
    )
    op.execute(
        "CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
    )
    op.execute(
        "CREATE TRIGGER update_rag_documents_updated_at BEFORE UPDATE ON rag_documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("rag_documents")
    op.drop_table("tool_executions")
    op.drop_table("agent_executions")
    op.drop_table("llm_round_table_results")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("users")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")
    op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
