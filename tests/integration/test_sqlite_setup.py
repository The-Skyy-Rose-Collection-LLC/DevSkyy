import asyncio
import logging
from pathlib import Path
import sys
import time

from dotenv import load_dotenv
from sqlalchemy import select, text

# Import from database.py module (not database package)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import database as db_module
AsyncSessionLocal = db_module.AsyncSessionLocal
db_manager = db_module.db_manager
init_db = db_module.init_db
DATABASE_URL = db_module.DATABASE_URL
from models_sqlalchemy import AgentLog, BrandAsset, Product, User


#!/usr/bin/env python3
"""
DevSkyy SQLite Setup Test Suite v1.0.0

Comprehensive test suite for SQLite database setup and operations.
Verifies database initialization, model operations, and performance.

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11
"""

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import database modules


class SQLiteTestSuite:
    """Comprehensive SQLite test suite."""

    def __init__(self):
        self.test_results = {}
        self.test_data_ids = {}

    async def run_all_tests(self) -> dict[str, bool]:
        """Run all SQLite tests."""

        tests = [
            ("Database Configuration", self.test_database_config),
            ("Database Connection", self.test_database_connection),
            ("Table Creation", self.test_table_creation),
            ("Model Operations", self.test_model_operations),
            ("CRUD Operations", self.test_crud_operations),
            ("Query Performance", self.test_query_performance),
            ("Transaction Handling", self.test_transaction_handling),
            ("Health Checks", self.test_health_checks),
            ("Concurrent Operations", self.test_concurrent_operations),
            ("Data Integrity", self.test_data_integrity),
        ]

        for test_name, test_func in tests:
            try:
                success = await test_func()
                self.test_results[test_name] = success
            except Exception as e:
                self.test_results[test_name] = False
                logger.error(f"Test {test_name} failed: {e}")

        return self.test_results

    async def test_database_config(self) -> bool:
        """Test database configuration."""
        try:
            # Check database URL
            if not DATABASE_URL:
                return False

            # Verify SQLite configuration
            if "sqlite" not in DATABASE_URL:
                return True  # Not a failure, just different config

            # Check if database file exists or can be created
            if "sqlite" in DATABASE_URL:
                db_path = Path("./devskyy.db")
                if not db_path.exists():
                    pass

            return True

        except Exception:
            return False

    async def test_database_connection(self) -> bool:
        """Test database connection."""
        try:
            # Test connection through db_manager
            health = await db_manager.health_check()

            if health.get("status") != "healthy":
                return False

            # Test direct connection
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                value = result.scalar()
                if value != 1:
                    return False

            return True

        except Exception:
            return False

    async def test_table_creation(self) -> bool:
        """Test table creation and schema."""
        try:
            # Initialize database (create tables)
            await init_db()

            # Verify tables exist
            async with AsyncSessionLocal() as session:
                if "sqlite" in DATABASE_URL:
                    result = await session.execute(
                        text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    )
                    tables = [row[0] for row in result.fetchall()]
                else:
                    result = await session.execute(
                        text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                    )
                    tables = [row[0] for row in result.fetchall()]

            expected_tables = ["users", "products", "customers", "orders", "agent_logs", "brand_assets", "campaigns"]
            missing_tables = [t for t in expected_tables if t not in tables]

            return not missing_tables

        except Exception:
            return False

    async def test_model_operations(self) -> bool:
        """Test basic model operations."""
        try:
            async with AsyncSessionLocal() as session:
                # Test User model
                user = User(
                    email="test@example.com",
                    username="testuser",
                    full_name="Test User",
                    hashed_password="hashed_password",
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

                if not user.id:
                    return False

                self.test_data_ids["user_id"] = user.id

                # Test Product model
                product = Product(
                    name="Test Product",
                    description="A test product",
                    sku="TEST-001",
                    category="Test",
                    price=99.99,
                    stock_quantity=10,
                    tags=["test", "product"],
                    colors=["red", "blue"],
                )
                session.add(product)
                await session.commit()
                await session.refresh(product)

                if not product.id:
                    return False

                self.test_data_ids["product_id"] = product.id

                return True

        except Exception:
            return False

    async def test_crud_operations(self) -> bool:
        """Test CRUD (Create, Read, Update, Delete) operations."""
        try:
            async with AsyncSessionLocal() as session:
                # CREATE - Already done in previous test
                user_id = self.test_data_ids.get("user_id")
                if not user_id:
                    return False

                # READ
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if not user or user.email != "test@example.com":
                    return False

                # UPDATE
                user.full_name = "Updated Test User"
                await session.commit()
                await session.refresh(user)

                if user.full_name != "Updated Test User":
                    return False

                # DELETE (we'll keep the data for other tests)
                # await session.delete(user)
                # await session.commit()

                return True

        except Exception:
            return False

    async def test_query_performance(self) -> bool:
        """Test query performance."""
        try:
            # Create multiple records for performance testing
            async with AsyncSessionLocal() as session:
                # Create 100 test products
                products = []
                for i in range(100):
                    product = Product(
                        name=f"Performance Test Product {i}",
                        sku=f"PERF-{i:03d}",
                        category="Performance",
                        price=float(i + 1),
                        stock_quantity=i,
                    )
                    products.append(product)

                session.add_all(products)
                await session.commit()

                # Test query performance
                start_time = time.time()

                # Query all products
                result = await session.execute(select(Product).where(Product.category == "Performance"))
                perf_products = result.scalars().all()

                query_time = time.time() - start_time

                if len(perf_products) != 100:
                    return False

                # Performance should be reasonable (< 1 second for 100 records)
                if query_time > 1.0:
                    pass

                return True

        except Exception:
            return False

    async def test_transaction_handling(self) -> bool:
        """Test transaction handling and rollback."""
        try:
            async with AsyncSessionLocal() as session:
                try:
                    # Start a transaction that will fail
                    user = User(
                        email="transaction@test.com",
                        username="transactionuser",
                        full_name="Transaction Test",
                        hashed_password="password",
                    )
                    session.add(user)

                    # This should succeed
                    await session.flush()

                    # Now try to add a duplicate email (should fail)
                    duplicate_user = User(
                        email="transaction@test.com",  # Duplicate email
                        username="duplicate",
                        full_name="Duplicate",
                        hashed_password="password",
                    )
                    session.add(duplicate_user)

                    # This should fail due to unique constraint
                    await session.commit()

                    # If we get here, the test failed (should have raised an exception)
                    return False

                except Exception:
                    # Expected to fail - rollback should work
                    await session.rollback()

                    # Verify the first user was not committed
                    result = await session.execute(select(User).where(User.email == "transaction@test.com"))
                    user = result.scalar_one_or_none()

                    # User should not exist due to rollback
                    return user is None

        except Exception:
            return False

    async def test_health_checks(self) -> bool:
        """Test health check functionality."""
        try:
            # Test db_manager health check
            health = await db_manager.health_check()

            required_fields = ["status", "connected", "type"]
            for field in required_fields:
                if field not in health:
                    return False

            if health["status"] != "healthy":
                return False

            return health["connected"]

        except Exception:
            return False

    async def test_concurrent_operations(self) -> bool:
        """Test concurrent database operations."""
        try:

            async def create_agent_log(agent_name: str, action: str):
                async with AsyncSessionLocal() as session:
                    log = AgentLog(agent_name=agent_name, action=action, status="success", execution_time_ms=100.0)
                    session.add(log)
                    await session.commit()
                    return log.id

            # Run multiple concurrent operations
            tasks = [create_agent_log(f"Agent_{i}", f"action_{i}") for i in range(10)]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check that all operations succeeded
            successful_ops = [r for r in results if isinstance(r, int)]

            return len(successful_ops) == 10

        except Exception:
            return False

    async def test_data_integrity(self) -> bool:
        """Test data integrity and constraints."""
        try:
            async with AsyncSessionLocal() as session:
                # Test JSON field storage and retrieval
                brand_asset = BrandAsset(
                    asset_type="color_palette",
                    name="Primary Colors",
                    data={"primary": "#FF6B6B", "secondary": "#4ECDC4", "accent": "#45B7D1"},
                    asset_metadata={"created_by": "AI Designer", "version": "1.0"},
                )
                session.add(brand_asset)
                await session.commit()
                await session.refresh(brand_asset)

                # Verify JSON data integrity
                if brand_asset.data["primary"] != "#FF6B6B":
                    return False

                if brand_asset.asset_metadata["version"] != "1.0":
                    return False

                # Test timestamp fields
                return brand_asset.created_at

        except Exception:
            return False

    def print_summary(self):
        """Print test summary."""

        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)

        for _test_name, _result in self.test_results.items():
            pass

        if passed == total:
            pass
        else:

            [name for name, result in self.test_results.items() if not result]


async def main():
    """Main test function."""

    test_suite = SQLiteTestSuite()
    results = await test_suite.run_all_tests()
    test_suite.print_summary()

    # Exit with appropriate code
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
