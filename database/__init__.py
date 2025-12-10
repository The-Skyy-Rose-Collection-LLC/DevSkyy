"""
Database Module
===============

Async SQLAlchemy with connection pooling.

Usage:
    from database import db_manager, get_db, UserRepository
    
    # Initialize on startup
    await db_manager.initialize()
    
    # Use in FastAPI
    @router.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db)):
        repo = UserRepository(db)
        return await repo.get_all()
"""

from database.db import (
    # Manager
    db_manager,
    DatabaseManager,
    DatabaseConfig,
    get_db,
    
    # Models
    Base,
    User,
    Product,
    Order,
    OrderItem,
    AuditLog,
    AgentTask,
    
    # Repositories
    BaseRepository,
    UserRepository,
    ProductRepository,
    OrderRepository,
    AuditLogRepository,
)

__all__ = [
    "db_manager",
    "DatabaseManager",
    "DatabaseConfig",
    "get_db",
    "Base",
    "User",
    "Product",
    "Order",
    "OrderItem",
    "AuditLog",
    "AgentTask",
    "BaseRepository",
    "UserRepository",
    "ProductRepository",
    "OrderRepository",
    "AuditLogRepository",
]
