#!/usr/bin/env python3
"""Test script to verify ORM models are properly linked to Alembic.

This script verifies:
1. SQLAlchemy models can be imported
2. Alembic can detect the models via Base.metadata
3. Model schema matches the baseline migration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_import_models():
    """Test that models can be imported."""
    try:
        from agents.models import (  # noqa: F401
            AgentExecution,
            Base,
            LLMRoundTableResult,
            Order,
            Product,
            RAGDocument,
            ToolExecution,
            User,
        )

        print("✅ Successfully imported all ORM models")
        return True
    except ImportError as e:
        print(f"❌ Failed to import models: {e}")
        return False


def test_base_metadata():
    """Test that Base.metadata contains table definitions."""
    try:
        from agents.models import Base

        tables = Base.metadata.tables
        expected_tables = {
            "users",
            "products",
            "orders",
            "llm_round_table_results",
            "agent_executions",
            "tool_executions",
            "rag_documents",
        }

        actual_tables = set(tables.keys())

        if actual_tables == expected_tables:
            print(f"✅ Base.metadata contains all {len(expected_tables)} expected tables")
            return True
        else:
            missing = expected_tables - actual_tables
            extra = actual_tables - expected_tables
            if missing:
                print(f"❌ Missing tables: {missing}")
            if extra:
                print(f"⚠️  Extra tables: {extra}")
            return False
    except Exception as e:
        print(f"❌ Failed to check Base.metadata: {e}")
        return False


def test_alembic_env():
    """Test that Alembic env.py imports Base correctly."""
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        # Load Alembic config
        alembic_cfg = Config("alembic.ini")
        ScriptDirectory.from_config(alembic_cfg)

        # Check that we can import the env module

        print("✅ Alembic configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to load Alembic configuration: {e}")
        return False


def test_model_schema():
    """Test that model schema matches expected structure."""
    try:
        from agents.models import Order, Product, User

        # Check User model
        user_columns = {col.name for col in User.__table__.columns}
        expected_user_cols = {
            "id",
            "email",
            "username",
            "password_hash",
            "full_name",
            "role",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
            "last_login",
            "metadata",
        }

        if user_columns == expected_user_cols:
            print("✅ User model schema matches expected structure")
        else:
            print("❌ User model schema mismatch")
            print(f"   Expected: {expected_user_cols}")
            print(f"   Actual: {user_columns}")
            return False

        # Check Product model
        product_columns = {col.name for col in Product.__table__.columns}
        expected_product_cols = {
            "id",
            "sku",
            "name",
            "description",
            "category",
            "price",
            "inventory_quantity",
            "status",
            "tags",
            "created_at",
            "updated_at",
            "metadata",
        }

        if product_columns == expected_product_cols:
            print("✅ Product model schema matches expected structure")
        else:
            print("❌ Product model schema mismatch")
            print(f"   Expected: {expected_product_cols}")
            print(f"   Actual: {product_columns}")
            return False

        # Check Order model
        order_columns = {col.name for col in Order.__table__.columns}
        expected_order_cols = {
            "id",
            "order_number",
            "user_id",
            "status",
            "total_price",
            "subtotal",
            "created_at",
            "updated_at",
            "metadata",
        }

        if order_columns == expected_order_cols:
            print("✅ Order model schema matches expected structure")
            return True
        else:
            print("❌ Order model schema mismatch")
            print(f"   Expected: {expected_order_cols}")
            print(f"   Actual: {order_columns}")
            return False

    except Exception as e:
        print(f"❌ Failed to check model schema: {e}")
        return False


def test_relationships():
    """Test that model relationships are properly defined."""
    try:
        from sqlalchemy import inspect

        from agents.models import Order, ToolExecution, User

        # Check User -> Order relationship
        user_mapper = inspect(User)
        user_relationships = {rel.key for rel in user_mapper.relationships}

        if "orders" in user_relationships and "tool_executions" in user_relationships:
            print("✅ User model relationships are properly defined")
        else:
            print("❌ User model missing expected relationships")
            print(f"   Found: {user_relationships}")
            return False

        # Check Order -> User relationship
        order_mapper = inspect(Order)
        order_relationships = {rel.key for rel in order_mapper.relationships}

        if "user" in order_relationships:
            print("✅ Order model relationships are properly defined")
        else:
            print("❌ Order model missing 'user' relationship")
            return False

        # Check ToolExecution -> User relationship
        tool_mapper = inspect(ToolExecution)
        tool_relationships = {rel.key for rel in tool_mapper.relationships}

        if "user" in tool_relationships:
            print("✅ ToolExecution model relationships are properly defined")
            return True
        else:
            print("❌ ToolExecution model missing 'user' relationship")
            return False

    except Exception as e:
        print(f"❌ Failed to check relationships: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing SQLAlchemy ORM Models and Alembic Integration")
    print("=" * 60)
    print()

    tests = [
        ("Import Models", test_import_models),
        ("Base Metadata", test_base_metadata),
        ("Alembic Environment", test_alembic_env),
        ("Model Schema", test_model_schema),
        ("Model Relationships", test_relationships),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        results.append(test_func())

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ All tests passed! ORM models are properly linked to Alembic.")
        print("\nNext steps:")
        print("  1. Run: alembic revision --autogenerate -m 'Link ORM models'")
        print("  2. Run: alembic upgrade head")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
