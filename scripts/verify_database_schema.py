#!/usr/bin/env python3
"""
Database Schema Verification Script

WHY: Verify consensus workflow schema is correctly set up
HOW: Query information_schema to check tables, columns, indexes
IMPACT: Ensures database is ready for production use

Usage:
    DATABASE_URL=postgresql://user:pass@host/db python scripts/verify_database_schema.py
"""

import logging
import os
import sys

import psycopg2


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

EXPECTED_TABLES = {
    "consensus_workflows": [
        "id",
        "topic",
        "iteration_count",
        "human_decision",
        "human_feedback",
        "approval_token",
        "rejection_token",
        "webhook_expires_at",
        "created_at",
        "updated_at",
    ],
    "content_drafts": [
        "id",
        "workflow_id",
        "version",
        "title",
        "content",
        "meta_description",
        "word_count",
        "keywords",
        "feedback_applied",
        "created_at",
    ],
    "agent_reviews": [
        "id",
        "workflow_id",
        "draft_id",
        "agent_name",
        "decision",
        "confidence",
        "feedback",
        "issues_found",
        "suggestions",
        "created_at",
    ],
    "consensus_votes": [
        "id",
        "workflow_id",
        "draft_id",
        "total_reviewers",
        "approved_count",
        "minor_issue_count",
        "major_issue_count",
        "requires_redraft",
        "consensus_feedback",
        "created_at",
    ],
    "woocommerce_products": [
        "id",
        "wordpress_product_id",
        "sku",
        "title",
        "regular_price",
        "sale_price",
        "category_ids",
        "image_url",
        "short_description",
        "description",
        "stock_quantity",
        "metatitle",
        "metadescription",
        "synced_at",
        "created_at",
    ],
    "content_publishing_log": [
        "id",
        "workflow_id",
        "wordpress_post_id",
        "wordpress_url",
        "title",
        "word_count",
        "image_url",
        "publish_status",
        "published_at",
        "created_at",
    ],
    "wordpress_categorization_cache": [
        "id",
        "post_id",
        "post_title",
        "assigned_category_id",
        "assigned_category_name",
        "confidence",
        "reasoning",
        "categorized_at",
    ],
}

EXPECTED_INDEXES = [
    "idx_workflows_human_decision",
    "idx_workflows_created_at",
    "idx_drafts_workflow",
    "idx_reviews_workflow",
    "idx_reviews_draft",
    "idx_votes_workflow",
    "idx_woo_products_sku",
    "idx_woo_products_synced",
    "idx_content_log_status",
    "idx_content_log_published",
    "idx_categorization_post",
]


def get_database_url() -> str | None:
    """Get database URL from environment"""
    return os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")


def check_tables(cursor) -> dict[str, bool]:
    """Check if all expected tables exist"""
    logger.info("Checking tables...")

    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """
    )

    existing_tables = {row[0] for row in cursor.fetchall()}
    results = {}

    for table_name in EXPECTED_TABLES:
        exists = table_name in existing_tables
        results[table_name] = exists

        if exists:
            logger.info(f"  ✓ {table_name}")
        else:
            logger.error(f"  ✗ {table_name} - MISSING")

    return results


def check_columns(cursor, table_name: str, expected_columns: list[str]) -> dict[str, bool]:
    """Check if all expected columns exist in table"""
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = %s
        ORDER BY ordinal_position;
    """,
        (table_name,),
    )

    existing_columns = {row[0] for row in cursor.fetchall()}
    results = {}

    for column_name in expected_columns:
        exists = column_name in existing_columns
        results[column_name] = exists

        if not exists:
            logger.error(f"    ✗ Column {column_name} missing from {table_name}")

    return results


def check_indexes(cursor) -> dict[str, bool]:
    """Check if all expected indexes exist"""
    logger.info("Checking indexes...")

    cursor.execute(
        """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
        ORDER BY indexname;
    """
    )

    existing_indexes = {row[0] for row in cursor.fetchall()}
    results = {}

    for index_name in EXPECTED_INDEXES:
        exists = index_name in existing_indexes
        results[index_name] = exists

        if exists:
            logger.info(f"  ✓ {index_name}")
        else:
            logger.error(f"  ✗ {index_name} - MISSING")

    return results


def check_foreign_keys(cursor) -> dict[str, bool]:
    """Check foreign key constraints"""
    logger.info("Checking foreign key constraints...")

    cursor.execute(
        """
        SELECT
            tc.table_name,
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
        ORDER BY tc.table_name;
    """
    )

    foreign_keys = cursor.fetchall()

    if foreign_keys:
        for fk in foreign_keys:
            logger.info(f"  ✓ {fk[0]}.{fk[2]} → {fk[3]}.{fk[4]}")
        return {f"{fk[0]}.{fk[2]}": True for fk in foreign_keys}
    else:
        logger.warning("  ⚠ No foreign keys found")
        return {}


def verify_schema(database_url: str) -> bool:
    """
    Verify complete database schema

    Args:
        database_url: PostgreSQL connection string

    Returns:
        True if all checks pass, False otherwise
    """
    try:
        logger.info("Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Check tables
        logger.info("\n" + "=" * 60)
        table_results = check_tables(cursor)
        tables_ok = all(table_results.values())

        # Check columns for each table
        logger.info("\n" + "=" * 60)
        logger.info("Checking columns...")
        columns_ok = True
        for table_name, expected_columns in EXPECTED_TABLES.items():
            if table_results.get(table_name):
                column_results = check_columns(cursor, table_name, expected_columns)
                if not all(column_results.values()):
                    columns_ok = False
                else:
                    logger.info(f"  ✓ {table_name} - all {len(expected_columns)} columns present")

        # Check indexes
        logger.info("\n" + "=" * 60)
        index_results = check_indexes(cursor)
        indexes_ok = all(index_results.values())

        # Check foreign keys
        logger.info("\n" + "=" * 60)
        fk_results = check_foreign_keys(cursor)
        fks_ok = len(fk_results) > 0

        # Get database statistics
        logger.info("\n" + "=" * 60)
        logger.info("Database statistics:")

        cursor.execute(
            """
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """
        )

        stats = cursor.fetchall()
        for stat in stats:
            logger.info(f"  {stat[1]}: {stat[2]}")

        cursor.close()
        conn.close()

        # Final results
        logger.info("\n" + "=" * 60)
        logger.info("Verification Summary:")
        logger.info(f"  Tables:        {'✅ PASS' if tables_ok else '❌ FAIL'}")
        logger.info(f"  Columns:       {'✅ PASS' if columns_ok else '❌ FAIL'}")
        logger.info(f"  Indexes:       {'✅ PASS' if indexes_ok else '❌ FAIL'}")
        logger.info(f"  Foreign Keys:  {'✅ PASS' if fks_ok else '⚠ WARNING'}")
        logger.info("=" * 60)

        return tables_ok and columns_ok and indexes_ok

    except Exception:
        logger.exception("❌ Schema verification failed")
        return False


def main():
    """Main entry point"""
    database_url = get_database_url()

    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        logger.info("Usage: DATABASE_URL=postgresql://user:pass@host/db python verify_database_schema.py")
        sys.exit(1)

    logger.info("DevSkyy Database Schema Verification")
    logger.info("=" * 60)

    success = verify_schema(database_url)

    if success:
        logger.info("\n✅ All schema checks passed!")
        logger.info("\nYour database is ready for:")
        logger.info("  • Consensus workflow orchestration")
        logger.info("  • E-commerce product management")
        logger.info("  • Content publishing tracking")
        logger.info("  • WordPress categorization caching")
        sys.exit(0)
    else:
        logger.error("\n❌ Some schema checks failed")
        logger.info("\nTo fix issues, run:")
        logger.info("  python scripts/setup_consensus_schema.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
