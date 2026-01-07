"""SQLAlchemy ORM models for DevSkyy.

Production-grade database models matching the schema defined in
alembic/versions/001_baseline_schema.py.

All models use:
- UUID primary keys with automatic generation
- Proper indexing for query performance
- JSONB for flexible metadata storage
- Timezone-aware timestamps
- Explicit type hints and validation
"""

from sqlalchemy import (
    DECIMAL,
    TIMESTAMP,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Create declarative base
Base = declarative_base()


class User(Base):
    """User model for authentication and authorization.

    Attributes:
        id: Primary key UUID
        email: Unique email address
        username: Unique username
        password_hash: Bcrypt/Argon2 hashed password
        full_name: User's full name
        role: User role (customer, admin, agent, etc.)
        is_active: Account active status
        is_verified: Email verification status
        created_at: Account creation timestamp
        updated_at: Last update timestamp (auto-updated via trigger)
        last_login: Last successful login timestamp
        extra_data: Flexible JSONB field (maps to 'metadata' column in DB)
    """
    __tablename__ = "users"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), server_default="customer", index=True)
    is_active = Column(Boolean, server_default="true")
    is_verified = Column(Boolean, server_default="false")
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    last_login = Column(TIMESTAMP(timezone=True))
    extra_data = Column("metadata", JSONB, server_default=text("'{}'::jsonb"))

    # Relationships
    orders = relationship("Order", back_populates="user")
    tool_executions = relationship("ToolExecution", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class Product(Base):
    """Product model for e-commerce catalog.

    Attributes:
        id: Primary key UUID
        sku: Unique stock keeping unit
        name: Product name/title
        description: Full product description
        category: Product category
        price: Current price (DECIMAL for precision)
        inventory_quantity: Current stock level
        status: Product status (draft, published, archived)
        tags: Array of tag strings for search/filtering
        created_at: Product creation timestamp
        updated_at: Last update timestamp (auto-updated via trigger)
        extra_data: Flexible JSONB field (maps to 'metadata' column, variants/specs)
    """
    __tablename__ = "products"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    price = Column(DECIMAL(10, 2), nullable=False)
    inventory_quantity = Column(Integer, server_default="0")
    status = Column(String(50), server_default="draft", index=True)
    tags = Column(ARRAY(Text))
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    extra_data = Column("metadata", JSONB, server_default=text("'{}'::jsonb"))

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, sku={self.sku}, name={self.name})>"


class Order(Base):
    """Order model for e-commerce transactions.

    Attributes:
        id: Primary key UUID
        order_number: Unique human-readable order number
        user_id: Foreign key to users table (nullable for guest orders)
        status: Order status (pending, processing, completed, cancelled)
        total_price: Final total including taxes/shipping
        subtotal: Subtotal before taxes/shipping
        created_at: Order creation timestamp
        updated_at: Last update timestamp (auto-updated via trigger)
        extra_data: Flexible JSONB field (maps to 'metadata' column, items/shipping/payment)
    """
    __tablename__ = "orders"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    order_number = Column(String(50), unique=True, nullable=False)
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    status = Column(String(50), server_default="pending", index=True)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    extra_data = Column("metadata", JSONB, server_default=text("'{}'::jsonb"))

    # Relationships
    user = relationship("User", back_populates="orders")

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number={self.order_number}, status={self.status})>"


class LLMRoundTableResult(Base):
    """LLM Round Table competition results.

    Stores results from multi-LLM competitions where multiple providers
    compete on the same prompt and the best response is selected via
    A/B testing or statistical evaluation.

    Attributes:
        id: Primary key UUID
        result_id: Unique result identifier
        prompt: Original prompt sent to LLMs
        task_category: Task category (reasoning, creative, qa, etc.)
        winner_provider: Winning LLM provider name
        winner_response: Winning LLM response
        participants: JSONB array of all participant results
        created_at: Competition timestamp
        extra_data: Flexible JSONB field (maps to 'metadata' column, scores/metrics/config)
    """
    __tablename__ = "llm_round_table_results"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    result_id = Column(String(100), unique=True, nullable=False)
    prompt = Column(Text, nullable=False)
    task_category = Column(String(100), index=True)
    winner_provider = Column(String(50))
    winner_response = Column(Text)
    participants = Column(JSONB, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    extra_data = Column("metadata", JSONB, server_default=text("'{}'::jsonb"))

    def __repr__(self) -> str:
        return f"<LLMRoundTableResult(id={self.id}, winner={self.winner_provider}, category={self.task_category})>"


class AgentExecution(Base):
    """Agent execution audit log.

    Tracks all SuperAgent executions for monitoring, debugging,
    and analytics.

    Attributes:
        id: Primary key UUID
        execution_id: Unique execution identifier
        agent_name: Name of the agent (Commerce, Creative, etc.)
        prompt: User prompt/task
        status: Execution status (running, completed, failed)
        result: JSONB execution result
        tokens_used: Total tokens consumed
        duration_ms: Execution duration in milliseconds
        created_at: Execution start timestamp
        extra_data: Flexible JSONB field (maps to 'metadata' column, plan/tools/etc.)
    """
    __tablename__ = "agent_executions"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    execution_id = Column(String(100), unique=True, nullable=False)
    agent_name = Column(String(100), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    status = Column(String(50), server_default="running", index=True)
    result = Column(JSONB)
    tokens_used = Column(Integer)
    duration_ms = Column(Integer)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    extra_data = Column("metadata", JSONB, server_default=text("'{}'::jsonb"))

    def __repr__(self) -> str:
        return f"<AgentExecution(id={self.id}, agent={self.agent_name}, status={self.status})>"


class ToolExecution(Base):
    """Tool execution audit trail.

    Comprehensive audit log for all tool executions in the system.
    Supports zero-trust security, debugging, and compliance.

    Attributes:
        id: Primary key UUID
        correlation_id: Correlation ID for distributed tracing
        tool_name: Name of the executed tool
        agent_id: ID of the agent that invoked the tool
        user_id: Foreign key to users table (nullable)
        inputs: JSONB tool input parameters
        output: JSONB tool execution result
        status: Execution status (success, failed, timeout)
        duration_ms: Execution duration in milliseconds
        error_message: Error message if status is failed
        created_at: Execution timestamp
        extra_data: Flexible JSONB field (maps to 'metadata' column, permissions/context)
    """
    __tablename__ = "tool_executions"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    correlation_id = Column(String(64), nullable=False, index=True)
    tool_name = Column(String(128), nullable=False, index=True)
    agent_id = Column(String(100))
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    inputs = Column(JSONB, nullable=False)
    output = Column(JSONB)
    status = Column(String(50), nullable=False, index=True)
    duration_ms = Column(Integer)
    error_message = Column(Text)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    extra_data = Column("metadata", JSONB, server_default=text("'{}'::jsonb"))

    # Relationships
    user = relationship("User", back_populates="tool_executions")

    def __repr__(self) -> str:
        return f"<ToolExecution(id={self.id}, tool={self.tool_name}, status={self.status})>"


class RAGDocument(Base):
    """RAG document storage for knowledge base.

    Stores document chunks for Retrieval-Augmented Generation (RAG).
    Works in conjunction with vector databases for semantic search.

    Attributes:
        id: Primary key UUID
        document_id: Unique document identifier
        source_path: Original file path or URL
        content: Document content/chunk
        content_hash: SHA-256 hash for deduplication
        chunk_index: Index of this chunk (0-based)
        total_chunks: Total number of chunks for this document
        embedding_model: Model used for embeddings
        extra_data: Flexible JSONB field (maps to 'metadata' column, author/date/tags)
        created_at: Document ingestion timestamp
        updated_at: Last update timestamp (auto-updated via trigger)
    """
    __tablename__ = "rag_documents"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
    )
    document_id = Column(String(100), unique=True, nullable=False)
    source_path = Column(String(500), index=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    chunk_index = Column(Integer)
    total_chunks = Column(Integer)
    embedding_model = Column(String(100))
    extra_data = Column("metadata", JSONB, server_default=text("'{}'::jsonb"))
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    def __repr__(self) -> str:
        return f"<RAGDocument(id={self.id}, document_id={self.document_id}, chunk={self.chunk_index}/{self.total_chunks})>"
