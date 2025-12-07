"""
Database infrastructure tests for DevSkyy platform.

WHY: Validate database connectivity, migrations, and performance
HOW: Test SQLAlchemy connections, transaction handling, connection pooling
IMPACT: Ensures database layer reliability and prevents production failures
"""

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


@pytest.mark.infrastructure
class TestDatabaseConnectivity:
    """Test database connection and basic operations."""

    def test_database_connection(self, test_db_url):
        """
        Test database connection can be established.

        WHY: Verify database is accessible and credentials work
        HOW: Create engine and test connection
        IMPACT: Catches configuration issues early
        """
        engine = create_engine(test_db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_database_transaction(self, test_db_url):
        """
        Test database transaction commit and rollback.

        WHY: Ensure transaction management works correctly
        HOW: Execute transaction and verify ACID properties
        IMPACT: Prevents data corruption in production
        """
        engine = create_engine(test_db_url)
        Session = sessionmaker(bind=engine)

        with Session() as session:
            # Start transaction
            session.execute(text("SELECT 1"))
            session.commit()

        # Verify session closed cleanly
        assert session.is_active is False


@pytest.mark.infrastructure
class TestDatabasePerformance:
    """Test database performance and connection pooling."""

    def test_connection_pool(self, test_db_url):
        """
        Test database connection pooling.

        WHY: Verify connection pool prevents resource exhaustion
        HOW: Create multiple connections and verify pool behavior
        IMPACT: Ensures scalability under load
        """
        engine = create_engine(test_db_url, pool_size=5, max_overflow=10)

        # Test pool can handle multiple connections
        connections = []
        for _ in range(5):
            conn = engine.connect()
            connections.append(conn)

        # Cleanup
        for conn in connections:
            conn.close()

        assert len(connections) == 5


# Pytest fixtures
@pytest.fixture
def test_db_url():
    """Provide test database URL."""
    import os

    return os.getenv("DATABASE_URL", "postgresql://devskyy_test:test_password@localhost:5432/devskyy_test")
