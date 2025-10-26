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
(logging.basicConfig( if logging else None)
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = (logging.getLogger( if logging else None)__name__)

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
        print("🧪 DevSkyy SQLite Test Suite")
        print("=" * 60)
        
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
            ("Data Integrity", self.test_data_integrity)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Testing: {test_name}")
            try:
                success = await test_func()
                self.test_results[test_name] = success
                status = "✅ PASS" if success else "❌ FAIL"
                print(f"   {status}")
            except Exception as e:
                self.test_results[test_name] = False
                print(f"   ❌ FAIL - {e}")
                (logger.error( if logger else None)f"Test {test_name} failed: {e}")
        
        return self.test_results
    
    async def test_database_config(self) -> bool:
        """Test database configuration."""
        try:
            # Check database URL
            if not DATABASE_URL:
                return False
            
            # Verify SQLite configuration
            if "sqlite" not in DATABASE_URL:
                print(f"   ⚠️  Not using SQLite: {DB_PROVIDER}")
                return True  # Not a failure, just different config
            
            # Check if database file exists or can be created
            if "sqlite" in DATABASE_URL:
                db_path = Path("./devskyy.db")
                if not (db_path.exists( if db_path else None)):
                    print(f"   ℹ️  Database file will be created: {db_path}")
            
            print(f"   ✓ Database Provider: {DB_PROVIDER}")
            print(f"   ✓ Database URL: {DATABASE_URL}")
            return True
            
        except Exception as e:
            print(f"   ❌ Configuration error: {e}")
            return False
    
    async def test_database_connection(self) -> bool:
        """Test database connection."""
        try:
            # Test connection through db_manager
            health = await (db_manager.health_check( if db_manager else None))
            
            if (health.get( if health else None)"status") != "healthy":
                print(f"   ❌ Health check failed: {health}")
                return False
            
            # Test direct connection
            async with AsyncSessionLocal() as session:
                result = await (session.execute( if session else None)text("SELECT 1"))
                value = (result.scalar( if result else None))
                if value != 1:
                    return False
            
            print(f"   ✓ Connection healthy: {(health.get( if health else None)'type')}")
            return True
            
        except Exception as e:
            print(f"   ❌ Connection error: {e}")
            return False
    
    async def test_table_creation(self) -> bool:
        """Test table creation and schema."""
        try:
            # Initialize database (create tables)
            await init_db()
            
            # Verify tables exist
            async with AsyncSessionLocal() as session:
                if "sqlite" in DATABASE_URL:
                    result = await (session.execute( if session else None)
                        text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    )
                    tables = [row[0] for row in (result.fetchall( if result else None))]
                else:
                    result = await (session.execute( if session else None)
                        text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                    )
                    tables = [row[0] for row in (result.fetchall( if result else None))]
            
            expected_tables = ["users", "products", "customers", "orders", "agent_logs", "brand_assets", "campaigns"]
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                print(f"   ❌ Missing tables: {missing_tables}")
                return False
            
            print(f"   ✓ Created {len(tables)} tables: {', '.join(sorted(tables))}")
            return True
            
        except Exception as e:
            print(f"   ❌ Table creation error: {e}")
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
                    hashed_password="hashed_password"
                )
                (session.add( if session else None)user)
                await (session.commit( if session else None))
                await (session.refresh( if session else None)user)
                
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
                    colors=["red", "blue"]
                )
                (session.add( if session else None)product)
                await (session.commit( if session else None))
                await (session.refresh( if session else None)product)
                
                if not product.id:
                    return False
                
                self.test_data_ids["product_id"] = product.id
                
                print(f"   ✓ Created user (ID: {user.id}) and product (ID: {product.id})")
                return True
                
        except Exception as e:
            print(f"   ❌ Model operation error: {e}")
            return False
    
    async def test_crud_operations(self) -> bool:
        """Test CRUD (Create, Read, Update, Delete) operations."""
        try:
            async with AsyncSessionLocal() as session:
                # CREATE - Already done in previous test
                user_id = self.(test_data_ids.get( if test_data_ids else None)"user_id")
                if not user_id:
                    return False
                
                # READ
                result = await (session.execute( if session else None)select(User).where(User.id == user_id))
                user = (result.scalar_one_or_none( if result else None))
                if not user or user.email != "test@example.com":
                    return False
                
                # UPDATE
                user.full_name = "Updated Test User"
                await (session.commit( if session else None))
                await (session.refresh( if session else None)user)
                
                if user.full_name != "Updated Test User":
                    return False
                
                # DELETE (we'll keep the data for other tests)
                # await (session.delete( if session else None)user)
                # await (session.commit( if session else None))
                
                print(f"   ✓ CRUD operations successful")
                return True
                
        except Exception as e:
            print(f"   ❌ CRUD operation error: {e}")
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
                        stock_quantity=i
                    )
                    (products.append( if products else None)product)
                
                (session.add_all( if session else None)products)
                await (session.commit( if session else None))
                
                # Test query performance
                start_time = (time.time( if time else None))
                
                # Query all products
                result = await (session.execute( if session else None)select(Product).where(Product.category == "Performance"))
                perf_products = (result.scalars( if result else None)).all()
                
                query_time = (time.time( if time else None)) - start_time
                
                if len(perf_products) != 100:
                    return False
                
                # Performance should be reasonable (< 1 second for 100 records)
                if query_time > 1.0:
                    print(f"   ⚠️  Query took {query_time:.3f}s (may be slow)")
                
                print(f"   ✓ Queried {len(perf_products)} records in {query_time:.3f}s")
                return True
                
        except Exception as e:
            print(f"   ❌ Performance test error: {e}")
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
                        hashed_password="password"
                    )
                    (session.add( if session else None)user)
                    
                    # This should succeed
                    await (session.flush( if session else None))
                    
                    # Now try to add a duplicate email (should fail)
                    duplicate_user = User(
                        email="transaction@test.com",  # Duplicate email
                        username="duplicate",
                        full_name="Duplicate",
                        hashed_password="password"
                    )
                    (session.add( if session else None)duplicate_user)
                    
                    # This should fail due to unique constraint
                    await (session.commit( if session else None))
                    
                    # If we get here, the test failed (should have raised an exception)
                    return False
                    
                except Exception:
                    # Expected to fail - rollback should work
                    await (session.rollback( if session else None))
                    
                    # Verify the first user was not committed
                    result = await (session.execute( if session else None)
                        select(User).where(User.email == "transaction@test.com")
                    )
                    user = (result.scalar_one_or_none( if result else None))
                    
                    # User should not exist due to rollback
                    if user is not None:
                        return False
                    
                    print(f"   ✓ Transaction rollback successful")
                    return True
                    
        except Exception as e:
            print(f"   ❌ Transaction test error: {e}")
            return False
    
    async def test_health_checks(self) -> bool:
        """Test health check functionality."""
        try:
            # Test db_manager health check
            health = await (db_manager.health_check( if db_manager else None))
            
            required_fields = ["status", "connected", "type"]
            for field in required_fields:
                if field not in health:
                    return False
            
            if health["status"] != "healthy":
                return False
            
            if not health["connected"]:
                return False
            
            print(f"   ✓ Health check passed: {health}")
            return True
            
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False
    
    async def test_concurrent_operations(self) -> bool:
        """Test concurrent database operations."""
        try:
            async def create_agent_log(agent_name: str, action: str):
                async with AsyncSessionLocal() as session:
                    log = AgentLog(
                        agent_name=agent_name,
                        action=action,
                        status="success",
                        execution_time_ms=100.0
                    )
                    (session.add( if session else None)log)
                    await (session.commit( if session else None))
                    return log.id
            
            # Run multiple concurrent operations
            tasks = [
                create_agent_log(f"Agent_{i}", f"action_{i}")
                for i in range(10)
            ]
            
            results = await (asyncio.gather( if asyncio else None)*tasks, return_exceptions=True)
            
            # Check that all operations succeeded
            successful_ops = [r for r in results if isinstance(r, int)]
            
            if len(successful_ops) != 10:
                return False
            
            print(f"   ✓ {len(successful_ops)} concurrent operations successful")
            return True
            
        except Exception as e:
            print(f"   ❌ Concurrent operations error: {e}")
            return False
    
    async def test_data_integrity(self) -> bool:
        """Test data integrity and constraints."""
        try:
            async with AsyncSessionLocal() as session:
                # Test JSON field storage and retrieval
                brand_asset = BrandAsset(
                    asset_type="color_palette",
                    name="Primary Colors",
                    data={
                        "primary": "#FF6B6B",
                        "secondary": "#4ECDC4",
                        "accent": "#45B7D1"
                    },
                    asset_metadata={
                        "created_by": "AI Designer",
                        "version": "1.0"
                    }
                )
                (session.add( if session else None)brand_asset)
                await (session.commit( if session else None))
                await (session.refresh( if session else None)brand_asset)
                
                # Verify JSON data integrity
                if brand_asset.data["primary"] != "#FF6B6B":
                    return False
                
                if brand_asset.asset_metadata["version"] != "1.0":
                    return False
                
                # Test timestamp fields
                if not brand_asset.created_at:
                    return False
                
                print(f"   ✓ Data integrity verified (JSON, timestamps)")
                return True
                
        except Exception as e:
            print(f"   ❌ Data integrity error: {e}")
            return False
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 SQLite Test Summary")
        print("=" * 60)
        
        passed = sum(1 for result in self.(test_results.values( if test_results else None)) if result)
        total = len(self.test_results)
        
        print(f"Tests Passed: {passed}/{total}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        for test_name, result in self.(test_results.items( if test_results else None)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status} - {test_name}")
        
        print("\n🎯 SQLite Setup Status:")
        if passed == total:
            print("✅ SQLITE SETUP COMPLETE")
            print("   All tests passed. Database is ready for production.")
        else:
            print("❌ SQLITE SETUP ISSUES")
            print("   Some tests failed. Review errors before deployment.")
            
            failed_tests = [name for name, result in self.(test_results.items( if test_results else None)) if not result]
            print(f"   Failed tests: {', '.join(failed_tests)}")

async def main():
    """Main test function."""
    print("🚀 DevSkyy SQLite Setup Test Suite")
    print("Testing database configuration and operations...")
    
    test_suite = SQLiteTestSuite()
    results = await (test_suite.run_all_tests( if test_suite else None))
    (test_suite.print_summary( if test_suite else None))
    
    # Exit with appropriate code
    passed = sum(1 for result in (results.values( if results else None)) if result)
    total = len(results)
    
    if passed == total:
        print("\n🎉 All SQLite tests passed! Database setup is complete.")
        (sys.exit( if sys else None)0)
    else:
        print("\n💥 Some SQLite tests failed! Review errors before proceeding.")
        (sys.exit( if sys else None)1)

if __name__ == "__main__":
    (asyncio.run( if asyncio else None)main())
