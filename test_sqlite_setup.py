from datetime import datetime
from pathlib import Path
import os
import sys
import time

from models_sqlalchemy import User, Product, Customer, Order, AgentLog, BrandAsset, Campaign
from sqlalchemy import select, text, func

from database import init_db, db_manager, get_db, AsyncSessionLocal
from database_config import DATABASE_URL, DB_PROVIDER
from dotenv import load_dotenv
from typing import Dict, List, Tuple
import asyncio
import logging

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

    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all SQLite tests."""
        logger.info("🧪 DevSkyy SQLite Test Suite")
        logger.info("=" * 60)

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
            logger.info(f"\n🔍 Testing: {test_name}")
            try:
                success = await test_func()
                self.test_results[test_name] = success
                status = "✅ PASS" if success else "❌ FAIL"
                logger.info(f"   {status}")
            except Exception as e:
                self.test_results[test_name] = False
                logger.error(f"   ❌ FAIL - {e}")
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
                logger.info(f"   ⚠️  Not using SQLite: {DB_PROVIDER}")
                return True  # Not a failure, just different config

            # Check if database file exists or can be created
            if "sqlite" in DATABASE_URL:
                db_path = Path("./devskyy.db")
                if not db_path.exists():
                    logger.info(f"   ℹ️  Database file will be created: {db_path}")

            logger.info(f"   ✓ Database Provider: {DB_PROVIDER}")
            logger.info(f"   ✓ Database URL: {DATABASE_URL}")
            return True

        except Exception as e:
            logger.error(f"   ❌ Configuration error: {e}")
            return False

    async def test_database_connection(self) -> bool:
        """Test database connection."""
        try:
            # Test connection through db_manager
            health = await db_manager.health_check()

            if health.get("status") != "healthy":
                logger.error(f"   ❌ Health check failed: {health}")
                return False

            # Test direct connection
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                value = result.scalar()
                if value != 1:
                    return False

            logger.info(f"   ✓ Connection healthy: {health.get('type')}")
            return True

        except Exception as e:
            logger.error(f"   ❌ Connection error: {e}")
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

            if missing_tables:
                logger.info(f"   ❌ Missing tables: {missing_tables}")
                return False

            logger.info(f"   ✓ Created {len(tables)} tables: {', '.join(sorted(tables))}")
            return True

        except Exception as e:
            logger.error(f"   ❌ Table creation error: {e}")
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

                logger.info(f"   ✓ Created user (ID: {user.id}) and product (ID: {product.id})")
                return True

        except Exception as e:
            logger.error(f"   ❌ Model operation error: {e}")
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

                logger.info(f"   ✓ CRUD operations successful")
                return True

        except Exception as e:
            logger.error(f"   ❌ CRUD operation error: {e}")
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
                    logger.info(f"   ⚠️  Query took {query_time:.3f}s (may be slow)")

                logger.info(f"   ✓ Queried {len(perf_products)} records in {query_time:.3f}s")
                return True

        except Exception as e:
            logger.error(f"   ❌ Performance test error: {e}")
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
                    if user is not None:
                        return False

                    logger.info(f"   ✓ Transaction rollback successful")
                    return True

        except Exception as e:
            logger.error(f"   ❌ Transaction test error: {e}")
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

            if not health["connected"]:
                return False

            logger.info(f"   ✓ Health check passed: {health}")
            return True

        except Exception as e:
            logger.error(f"   ❌ Health check error: {e}")
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

            if len(successful_ops) != 10:
                return False

            logger.info(f"   ✓ {len(successful_ops)} concurrent operations successful")
            return True

        except Exception as e:
            logger.error(f"   ❌ Concurrent operations error: {e}")
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
                if not brand_asset.created_at:
                    return False

                logger.info(f"   ✓ Data integrity verified (JSON, timestamps)")
                return True

        except Exception as e:
            logger.error(f"   ❌ Data integrity error: {e}")
            return False

    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 SQLite Test Summary")
        logger.info("=" * 60)

        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)

        logger.info(f"Tests Passed: {passed}/{total}")
        logger.info(f"Success Rate: {(passed/total)*100:.1f}%")

        logger.info("\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {status} - {test_name}")

        logger.info("\n🎯 SQLite Setup Status:")
        if passed == total:
            logger.info("✅ SQLITE SETUP COMPLETE")
            logger.info("   All tests passed. Database is ready for production.")
        else:
            logger.info("❌ SQLITE SETUP ISSUES")
            logger.error("   Some tests failed. Review errors before deployment.")

            failed_tests = [name for name, result in self.test_results.items() if not result]
            logger.error(f"   Failed tests: {', '.join(failed_tests)}")


async def main():
    """Main test function."""
    logger.info("🚀 DevSkyy SQLite Setup Test Suite")
    logger.info("Testing database configuration and operations...")

    test_suite = SQLiteTestSuite()
    results = await test_suite.run_all_tests()
    test_suite.print_summary()

    # Exit with appropriate code
    passed = sum(1 for result in results.values() if result)
    total = len(results)

    if passed == total:
        logger.info("\n🎉 All SQLite tests passed! Database setup is complete.")
        sys.exit(0)
    else:
        logger.error("\n💥 Some SQLite tests failed! Review errors before proceeding.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
