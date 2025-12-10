"""
Database Module
===============

Production-ready database layer with:
- Async SQLAlchemy 2.0 with connection pooling
- Repository pattern for data access
- Transaction management
- Query optimization

Dependencies:
- sqlalchemy==2.0.23 (PyPI verified)
- asyncpg==0.29.0 (PyPI verified)
- aiosqlite==0.19.0 (PyPI verified)
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, TypeVar, Generic, Type
from contextlib import asynccontextmanager
import json

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Index, event, select, update, delete, func
)
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncSession, AsyncEngine, async_sessionmaker
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, selectinload
)
from sqlalchemy.pool import QueuePool, NullPool
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class DatabaseConfig(BaseModel):
    """Database configuration"""
    url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./devskyy.db")
    pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    pool_timeout: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    pool_recycle: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"


# =============================================================================
# Base Model
# =============================================================================

class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


# =============================================================================
# Models
# =============================================================================

class User(Base, TimestampMixin):
    """User model"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    orders: Mapped[List["Order"]] = relationship(back_populates="user", lazy="selectin")
    
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
    )


class Product(Base, TimestampMixin):
    """Product model"""
    __tablename__ = "products"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    compare_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    collection: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    variants_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    images_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    seo_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="product")
    
    __table_args__ = (
        Index("ix_products_category_active", "category", "is_active"),
        Index("ix_products_collection", "collection"),
    )


class Order(Base, TimestampMixin):
    """Order model"""
    __tablename__ = "orders"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    subtotal: Mapped[float] = mapped_column(Float, default=0.0)
    tax: Mapped[float] = mapped_column(Float, default=0.0)
    shipping: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    shipping_address_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    billing_address_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(back_populates="order", lazy="selectin")
    
    __table_args__ = (
        Index("ix_orders_user_status", "user_id", "status"),
        Index("ix_orders_created", "created_at"),
    )


class OrderItem(Base):
    """Order item model"""
    __tablename__ = "order_items"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("orders.id"), index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    variant_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")


class AuditLog(Base):
    """Audit log for tracking changes"""
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    resource_type: Mapped[str] = mapped_column(String(50), index=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    __table_args__ = (
        Index("ix_audit_timestamp_action", "timestamp", "action"),
    )


class AgentTask(Base, TimestampMixin):
    """Agent task tracking"""
    __tablename__ = "agent_tasks"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(100), index=True)
    action: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    parameters_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index("ix_agent_tasks_status_created", "status", "created_at"),
    )


# =============================================================================
# Database Manager
# =============================================================================

class DatabaseManager:
    """
    Async database manager with connection pooling
    
    Features:
    - Connection pooling (QueuePool for PostgreSQL)
    - Async session management
    - Automatic reconnection
    - Query logging
    """
    
    _instance: Optional["DatabaseManager"] = None
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self, config: Optional[DatabaseConfig] = None):
        """Initialize database connection"""
        if self._engine is not None:
            return
        
        config = config or DatabaseConfig()
        
        # Determine pool class based on database type
        is_sqlite = "sqlite" in config.url
        pool_class = NullPool if is_sqlite else QueuePool
        
        # Create engine with connection pooling
        engine_kwargs = {
            "echo": config.echo,
            "poolclass": pool_class,
        }
        
        if not is_sqlite:
            engine_kwargs.update({
                "pool_size": config.pool_size,
                "max_overflow": config.max_overflow,
                "pool_timeout": config.pool_timeout,
                "pool_recycle": config.pool_recycle,
                "pool_pre_ping": True,  # Verify connections before use
            })
        
        self._engine = create_async_engine(config.url, **engine_kwargs)
        
        # Create session factory
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        
        # Create tables
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info(f"Database initialized: {config.url.split('@')[-1] if '@' in config.url else config.url}")
    
    async def close(self):
        """Close database connection"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connection closed")
    
    @asynccontextmanager
    async def session(self):
        """Get database session with automatic cleanup"""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
    
    @asynccontextmanager
    async def transaction(self):
        """Execute within a transaction"""
        async with self.session() as session:
            async with session.begin():
                yield session
    
    @property
    def engine(self) -> AsyncEngine:
        """Get database engine"""
        if not self._engine:
            raise RuntimeError("Database not initialized")
        return self._engine
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            async with self.session() as session:
                result = await session.execute(select(func.count()).select_from(User))
                user_count = result.scalar()
            
            pool = self._engine.pool
            return {
                "status": "healthy",
                "pool_size": getattr(pool, "size", lambda: 0)() if hasattr(pool, "size") else 0,
                "checked_in": getattr(pool, "checkedin", lambda: 0)() if hasattr(pool, "checkedin") else 0,
                "checked_out": getattr(pool, "checkedout", lambda: 0)() if hasattr(pool, "checkedout") else 0,
                "user_count": user_count
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# =============================================================================
# Repository Pattern
# =============================================================================

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations
    
    Usage:
        repo = UserRepository(session)
        user = await repo.get_by_id("user_123")
    """
    
    model: Type[T]
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID"""
        return await self.session.get(self.model, id)
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get all entities with pagination"""
        query = select(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(self, entity: T) -> T:
        """Create new entity"""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, entity: T) -> T:
        """Update existing entity"""
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete(self, id: str) -> bool:
        """Delete entity by ID"""
        entity = await self.get_by_id(id)
        if entity:
            await self.session.delete(entity)
            return True
        return False
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities"""
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar() or 0


class UserRepository(BaseRepository[User]):
    """User repository"""
    model = User
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users"""
        query = (
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class ProductRepository(BaseRepository[Product]):
    """Product repository"""
    model = Product
    
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        query = select(Product).where(Product.sku == sku)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """Get products by category"""
        query = (
            select(Product)
            .where(Product.category == category, Product.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_collection(self, collection: str) -> List[Product]:
        """Get products by collection"""
        query = (
            select(Product)
            .where(Product.collection == collection, Product.is_active == True)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def search(self, query_str: str, limit: int = 20) -> List[Product]:
        """Search products by name"""
        query = (
            select(Product)
            .where(
                Product.name.ilike(f"%{query_str}%"),
                Product.is_active == True
            )
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_low_stock(self, threshold: int = 10) -> List[Product]:
        """Get products with low stock"""
        query = (
            select(Product)
            .where(Product.quantity <= threshold, Product.is_active == True)
            .order_by(Product.quantity)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class OrderRepository(BaseRepository[Order]):
    """Order repository"""
    model = Order
    
    async def get_by_order_number(self, order_number: str) -> Optional[Order]:
        """Get order by order number"""
        query = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.order_number == order_number)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_orders(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Order]:
        """Get orders for user"""
        query = (
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """Get orders by status"""
        query = (
            select(Order)
            .where(Order.status == status)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_revenue_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue summary"""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = (
            select(
                func.count(Order.id).label("order_count"),
                func.sum(Order.total).label("total_revenue"),
                func.avg(Order.total).label("avg_order_value")
            )
            .where(Order.created_at >= cutoff, Order.status != "cancelled")
        )
        result = await self.session.execute(query)
        row = result.one()
        
        return {
            "order_count": row.order_count or 0,
            "total_revenue": float(row.total_revenue or 0),
            "avg_order_value": float(row.avg_order_value or 0),
            "period_days": days
        }


class AuditLogRepository(BaseRepository[AuditLog]):
    """Audit log repository"""
    model = AuditLog
    
    async def log(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Create audit log entry"""
        import secrets
        
        log = AuditLog(
            id=secrets.token_urlsafe(16),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details_json=json.dumps(details) if details else None,
            ip_address=ip_address
        )
        return await self.create(log)
    
    async def get_user_activity(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get user activity"""
        query = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_resource_history(
        self,
        resource_type: str,
        resource_id: str
    ) -> List[AuditLog]:
        """Get resource change history"""
        query = (
            select(AuditLog)
            .where(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id
            )
            .order_by(AuditLog.timestamp.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


# =============================================================================
# Dependency Injection
# =============================================================================

db_manager = DatabaseManager()


async def get_db() -> AsyncSession:
    """FastAPI dependency for database session"""
    async with db_manager.session() as session:
        yield session


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Manager
    "db_manager",
    "DatabaseManager",
    "DatabaseConfig",
    "get_db",
    
    # Models
    "Base",
    "User",
    "Product",
    "Order",
    "OrderItem",
    "AuditLog",
    "AgentTask",
    
    # Repositories
    "BaseRepository",
    "UserRepository",
    "ProductRepository",
    "OrderRepository",
    "AuditLogRepository",
]
