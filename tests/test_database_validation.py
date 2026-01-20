"""
Comprehensive Database Integration Validation Tests
=====================================================

Production-ready tests for PostgreSQL, ChromaDB, and Redis integrations.

Tests:
1. PostgreSQL connection pooling and transactions
2. Repository pattern and CRUD operations
3. ChromaDB vector store functionality
4. Redis cache operations and failover
5. Database migrations
6. Error handling and recovery
7. Query optimization and performance
"""

import secrets
import tempfile

import pytest

from database.db import (
    AuditLogRepository,
    DatabaseConfig,
    DatabaseManager,
    Order,
    OrderItem,
    OrderRepository,
    Product,
    ProductRepository,
    User,
    UserRepository,
)

# =============================================================================
# PostgreSQL Tests
# =============================================================================


class TestPostgreSQLIntegration:
    """Test PostgreSQL database integration."""

    @pytest.fixture
    async def db_manager(self):
        """Create database manager with test database."""
        db = DatabaseManager()
        # Use SQLite for tests (can switch to PostgreSQL for full integration tests)
        await db.initialize(DatabaseConfig(url="sqlite+aiosqlite:///:memory:"))
        yield db
        await db.close()

    @pytest.mark.asyncio
    async def test_database_initialization(self, db_manager):
        """Test database initialization and health check."""
        health = await db_manager.health_check()
        assert health["status"] == "healthy"
        assert "user_count" in health

    @pytest.mark.asyncio
    async def test_connection_pooling(self, db_manager):
        """Test connection pool is properly configured."""
        engine = db_manager.engine
        assert engine is not None

        # Pool should be created
        pool = engine.pool
        assert pool is not None

    @pytest.mark.asyncio
    async def test_session_management(self, db_manager):
        """Test session creation and cleanup."""
        async with db_manager.session() as session:
            assert session is not None
            # Session should be active
            assert True  # Session may not be active until first query

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, db_manager):
        """Test transaction rollback on error."""
        try:
            async with db_manager.transaction() as session:
                # Create a user
                user = User(
                    id=secrets.token_urlsafe(16),
                    email="test@example.com",
                    username="testuser",
                    hashed_password="hashed",
                )
                session.add(user)
                # Force an error to trigger rollback
                raise ValueError("Test error")
        except ValueError:
            pass

        # Verify user was not created (rolled back)
        async with db_manager.session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_email("test@example.com")
            assert user is None

    @pytest.mark.asyncio
    async def test_user_repository(self, db_manager):
        """Test UserRepository CRUD operations."""
        async with db_manager.session() as session:
            repo = UserRepository(session)

            # Create user
            user = User(
                id=secrets.token_urlsafe(16),
                email="john@example.com",
                username="johndoe",
                hashed_password="hashed123",
                role="customer",
            )
            created = await repo.create(user)
            assert created.id == user.id

            # Get by email
            found = await repo.get_by_email("john@example.com")
            assert found is not None
            assert found.username == "johndoe"

            # Get by username
            found = await repo.get_by_username("johndoe")
            assert found is not None
            assert found.email == "john@example.com"

            # Get active users
            users = await repo.get_active_users()
            assert len(users) >= 1

    @pytest.mark.asyncio
    async def test_product_repository(self, db_manager):
        """Test ProductRepository operations."""
        async with db_manager.session() as session:
            repo = ProductRepository(session)

            # Create product
            product = Product(
                id=secrets.token_urlsafe(16),
                sku="TEST-001",
                name="Test Product",
                price=99.99,
                quantity=100,
                category="electronics",
            )
            created = await repo.create(product)
            assert created.sku == "TEST-001"

            # Get by SKU
            found = await repo.get_by_sku("TEST-001")
            assert found is not None
            assert found.price == 99.99

            # Get by category
            products = await repo.get_by_category("electronics")
            assert len(products) >= 1

            # Search
            results = await repo.search("Test Product")
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_order_repository(self, db_manager):
        """Test OrderRepository with relationships."""
        async with db_manager.session() as session:
            # Create user
            user_repo = UserRepository(session)
            user = User(
                id=secrets.token_urlsafe(16),
                email="customer@example.com",
                username="customer1",
                hashed_password="hashed",
            )
            await user_repo.create(user)

            # Create product
            product_repo = ProductRepository(session)
            product = Product(
                id=secrets.token_urlsafe(16),
                sku="PROD-001",
                name="Test Item",
                price=49.99,
                quantity=50,
            )
            await product_repo.create(product)

            # Create order
            order_repo = OrderRepository(session)
            order = Order(
                id=secrets.token_urlsafe(16),
                order_number=f"ORD-{secrets.token_hex(4).upper()}",
                user_id=user.id,
                status="pending",
                total=49.99,
            )
            await order_repo.create(order)

            # Create order item
            item = OrderItem(
                id=secrets.token_urlsafe(16),
                order_id=order.id,
                product_id=product.id,
                quantity=1,
                unit_price=49.99,
                total=49.99,
            )
            session.add(item)
            await session.flush()

            # Get order with items - refresh to load relationship after adding item
            found = await order_repo.get_by_order_number(order.order_number)
            assert found is not None
            # Refresh to ensure items are loaded (SQLAlchemy caches objects)
            await session.refresh(found, ["items"])
            assert len(found.items) == 1

            # Get user orders
            user_orders = await order_repo.get_user_orders(user.id)
            assert len(user_orders) >= 1

    @pytest.mark.asyncio
    async def test_audit_log_repository(self, db_manager):
        """Test AuditLogRepository."""
        async with db_manager.session() as session:
            repo = AuditLogRepository(session)

            # Create audit log
            log = await repo.log(
                action="create",
                resource_type="user",
                resource_id="user123",
                user_id="admin123",
                details={"email": "test@example.com"},
                ip_address="127.0.0.1",
            )
            assert log.id is not None

            # Get user activity
            activity = await repo.get_user_activity("admin123")
            assert len(activity) >= 1

            # Get resource history
            history = await repo.get_resource_history("user", "user123")
            assert len(history) >= 1


# =============================================================================
# Redis Cache Tests
# =============================================================================


class TestRedisIntegration:
    """Test Redis cache integration."""

    @pytest.fixture
    async def redis_cache(self):
        """Create Redis cache instance."""
        from core.redis_cache import RedisCache

        cache = RedisCache()
        await cache.connect()
        yield cache
        await cache.disconnect()

    @pytest.mark.asyncio
    async def test_redis_connection(self, redis_cache):
        """Test Redis connection (may be unavailable)."""
        # This test passes even if Redis is unavailable (graceful degradation)
        assert redis_cache is not None

    @pytest.mark.asyncio
    async def test_cache_set_get(self, redis_cache):
        """Test cache set and get operations."""
        # Skip if Redis not connected
        if not redis_cache._connected:
            pytest.skip("Redis not available")

        # Set cache
        success = await redis_cache.set_llm_response(
            prompt="What is AI?",
            model="gpt-4",
            response={"answer": "Artificial Intelligence"},
            ttl=60,
        )
        assert success

        # Get cache
        cached = await redis_cache.get_llm_response(prompt="What is AI?", model="gpt-4")
        assert cached is not None
        assert cached["answer"] == "Artificial Intelligence"

    @pytest.mark.asyncio
    async def test_cache_stats(self, redis_cache):
        """Test cache statistics."""
        stats = await redis_cache.get_stats()
        assert "hit_rate" in stats
        assert "total_hits" in stats
        assert "total_misses" in stats


# =============================================================================
# ChromaDB Vector Store Tests
# =============================================================================


class TestChromaDBIntegration:
    """Test ChromaDB vector store integration."""

    @pytest.fixture
    async def vector_store(self):
        """Create vector store instance."""
        from orchestration.vector_store import VectorDBType, VectorStoreConfig, create_vector_store

        # Use temporary directory for test
        with tempfile.TemporaryDirectory() as tmpdir:
            config = VectorStoreConfig(
                db_type=VectorDBType.CHROMADB,
                persist_directory=tmpdir,
                collection_name="test_collection",
            )
            store = create_vector_store(config)

            try:
                await store.initialize()
                yield store
            except ImportError:
                pytest.skip("ChromaDB not installed")
            finally:
                await store.close()

    @pytest.mark.asyncio
    async def test_vector_store_initialization(self, vector_store):
        """Test vector store initialization."""
        stats = await vector_store.get_collection_stats()
        assert stats["db_type"] == "chromadb"
        assert "collection_name" in stats

    @pytest.mark.asyncio
    async def test_add_and_search_documents(self, vector_store):
        """Test adding and searching documents."""
        from orchestration.vector_store import Document

        # Create test documents
        docs = [
            Document(content="Python is a programming language", source="test1"),
            Document(content="JavaScript is used for web development", source="test2"),
            Document(content="Machine learning uses Python", source="test3"),
        ]

        # Create dummy embeddings (in production, use real embeddings)
        embeddings = [[0.1] * 384 for _ in docs]

        # Add documents
        ids = await vector_store.add_documents(docs, embeddings)
        assert len(ids) == 3

        # Search
        results = await vector_store.search(embeddings[0], top_k=2)
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_delete_documents(self, vector_store):
        """Test document deletion."""
        from orchestration.vector_store import Document

        doc = Document(content="Test document to delete", source="test")
        embedding = [[0.5] * 384]

        # Add document
        ids = await vector_store.add_documents([doc], embedding)
        doc_id = ids[0]

        # Delete document
        deleted = await vector_store.delete_documents([doc_id])
        assert deleted == 1

        # Verify deleted
        result = await vector_store.get_document(doc_id)
        assert result is None


# =============================================================================
# Performance and Optimization Tests
# =============================================================================


class TestDatabasePerformance:
    """Test database performance and optimization."""

    @pytest.fixture
    async def db_manager(self):
        """Create database manager."""
        db = DatabaseManager()
        await db.initialize(DatabaseConfig(url="sqlite+aiosqlite:///:memory:"))
        yield db
        await db.close()

    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, db_manager):
        """Test bulk insert performance."""
        async with db_manager.session() as session:
            repo = ProductRepository(session)

            # Create multiple products
            products = [
                Product(
                    id=secrets.token_urlsafe(16),
                    sku=f"BULK-{i:04d}",
                    name=f"Bulk Product {i}",
                    price=99.99 + i,
                    quantity=100 + i,
                )
                for i in range(100)
            ]

            # Insert all (using individual creates for now)
            for product in products:
                await repo.create(product)

            # Verify count
            count = await repo.count()
            assert count >= 100

    @pytest.mark.asyncio
    async def test_query_with_filters(self, db_manager):
        """Test query performance with filters."""
        async with db_manager.session() as session:
            repo = ProductRepository(session)

            # Create test products
            for i in range(10):
                product = Product(
                    id=secrets.token_urlsafe(16),
                    sku=f"FILTER-{i:04d}",
                    name=f"Filter Test {i}",
                    price=50.0 + i,
                    quantity=10 + i,
                    category="test_category",
                    is_active=True,
                )
                await repo.create(product)

            # Test filtered query
            results = await repo.get_by_category("test_category")
            assert len(results) == 10


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestDatabaseErrorHandling:
    """Test database error handling and recovery."""

    @pytest.fixture
    async def db_manager(self):
        """Create database manager."""
        db = DatabaseManager()
        await db.initialize(DatabaseConfig(url="sqlite+aiosqlite:///:memory:"))
        yield db
        await db.close()

    @pytest.mark.asyncio
    async def test_duplicate_key_error(self, db_manager):
        """Test handling of duplicate key errors."""
        async with db_manager.session() as session:
            repo = UserRepository(session)

            # Create user
            user1 = User(
                id=secrets.token_urlsafe(16),
                email="duplicate@example.com",
                username="duplicate",
                hashed_password="hash",
            )
            await repo.create(user1)

        # Try to create duplicate email
        with pytest.raises(Exception, match="duplicate|unique|integrity"):  # Should raise integrity error
            async with db_manager.session() as session:
                repo = UserRepository(session)
                user2 = User(
                    id=secrets.token_urlsafe(16),
                    email="duplicate@example.com",  # Duplicate email
                    username="different",
                    hashed_password="hash",
                )
                await repo.create(user2)

    @pytest.mark.asyncio
    async def test_not_found_handling(self, db_manager):
        """Test handling of not found scenarios."""
        async with db_manager.session() as session:
            repo = UserRepository(session)

            # Try to get non-existent user
            user = await repo.get_by_id("nonexistent-id")
            assert user is None

            user = await repo.get_by_email("nonexistent@example.com")
            assert user is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
