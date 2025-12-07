#!/usr/bin/env python3
"""
Consensus Workflow Database Schema Setup

WHY: Create PostgreSQL schema for consensus workflow persistence
HOW: Execute SQL DDL statements to create tables and indexes
IMPACT: Enables persistent storage of workflow state and audit trails

Usage:
    DATABASE_URL=postgresql://user:pass@host/db python scripts/setup_consensus_schema.py
"""

import logging
import os
import sys

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CONSENSUS_SCHEMA_SQL = """
-- Consensus Workflows Table
CREATE TABLE IF NOT EXISTS consensus_workflows (
    id UUID PRIMARY KEY,
    topic VARCHAR(200) NOT NULL,
    iteration_count INTEGER DEFAULT 0,
    human_decision VARCHAR(20) DEFAULT 'pending',
    human_feedback TEXT,
    approval_token VARCHAR(255) UNIQUE NOT NULL,
    rejection_token VARCHAR(255) UNIQUE NOT NULL,
    webhook_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Content Drafts Table
CREATE TABLE IF NOT EXISTS content_drafts (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES consensus_workflows(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    meta_description VARCHAR(160),
    word_count INTEGER,
    keywords JSONB,
    feedback_applied TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(workflow_id, version)
);

-- Agent Reviews Table
CREATE TABLE IF NOT EXISTS agent_reviews (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES consensus_workflows(id) ON DELETE CASCADE,
    draft_id UUID REFERENCES content_drafts(id) ON DELETE CASCADE,
    agent_name VARCHAR(100) NOT NULL,
    decision VARCHAR(20) NOT NULL,
    confidence DECIMAL(3,2) CHECK (confidence >= 0.0 AND confidence <= 1.0),
    feedback TEXT,
    issues_found JSONB,
    suggestions JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Consensus Votes Table
CREATE TABLE IF NOT EXISTS consensus_votes (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES consensus_workflows(id) ON DELETE CASCADE,
    draft_id UUID REFERENCES content_drafts(id) ON DELETE CASCADE,
    total_reviewers INTEGER,
    approved_count INTEGER,
    minor_issue_count INTEGER,
    major_issue_count INTEGER,
    requires_redraft BOOLEAN,
    consensus_feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflows_human_decision ON consensus_workflows(human_decision);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON consensus_workflows(created_at);
CREATE INDEX IF NOT EXISTS idx_drafts_workflow ON content_drafts(workflow_id);
CREATE INDEX IF NOT EXISTS idx_reviews_workflow ON agent_reviews(workflow_id);
CREATE INDEX IF NOT EXISTS idx_reviews_draft ON agent_reviews(draft_id);
CREATE INDEX IF NOT EXISTS idx_votes_workflow ON consensus_votes(workflow_id);

-- E-Commerce Tables (for WooCommerce integration)
CREATE TABLE IF NOT EXISTS woocommerce_products (
    id SERIAL PRIMARY KEY,
    wordpress_product_id INTEGER UNIQUE,
    sku VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    regular_price DECIMAL(10, 2),
    sale_price DECIMAL(10, 2),
    category_ids JSONB,
    image_url TEXT,
    short_description TEXT,
    description TEXT,
    stock_quantity INTEGER,
    metatitle VARCHAR(60),
    metadescription VARCHAR(160),
    synced_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Content Publishing Log
CREATE TABLE IF NOT EXISTS content_publishing_log (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES consensus_workflows(id) ON DELETE SET NULL,
    wordpress_post_id INTEGER,
    wordpress_url TEXT,
    title VARCHAR(200) NOT NULL,
    word_count INTEGER,
    image_url TEXT,
    publish_status VARCHAR(20) DEFAULT 'draft',
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- WordPress Categorization Cache
CREATE TABLE IF NOT EXISTS wordpress_categorization_cache (
    id SERIAL PRIMARY KEY,
    post_id INTEGER UNIQUE NOT NULL,
    post_title VARCHAR(200) NOT NULL,
    assigned_category_id INTEGER NOT NULL,
    assigned_category_name VARCHAR(100),
    confidence DECIMAL(3,2),
    reasoning TEXT,
    categorized_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for e-commerce and content tables
CREATE INDEX IF NOT EXISTS idx_woo_products_sku ON woocommerce_products(sku);
CREATE INDEX IF NOT EXISTS idx_woo_products_synced ON woocommerce_products(synced_at);
CREATE INDEX IF NOT EXISTS idx_content_log_status ON content_publishing_log(publish_status);
CREATE INDEX IF NOT EXISTS idx_content_log_published ON content_publishing_log(published_at);
CREATE INDEX IF NOT EXISTS idx_categorization_post ON wordpress_categorization_cache(post_id);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_consensus_workflows_updated_at
    BEFORE UPDATE ON consensus_workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO devskyy_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO devskyy_user;
"""


def get_database_url() -> str | None:
    """Get database URL from environment"""
    return os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")


def setup_schema(database_url: str) -> bool:
    """
    Setup consensus workflow schema

    Args:
        database_url: PostgreSQL connection string

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Connecting to database...")
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        logger.info("Creating consensus workflow schema...")
        cursor.execute(CONSENSUS_SCHEMA_SQL)

        logger.info("Verifying tables created...")
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN (
                'consensus_workflows',
                'content_drafts',
                'agent_reviews',
                'consensus_votes',
                'woocommerce_products',
                'content_publishing_log',
                'wordpress_categorization_cache'
            )
            ORDER BY table_name;
        """
        )

        tables = cursor.fetchall()
        logger.info(f"Tables created: {len(tables)}")
        for table in tables:
            logger.info(f"  ✓ {table[0]}")

        cursor.close()
        conn.close()

        logger.info("✅ Schema setup completed successfully!")
        return True

    except Exception:
        logger.exception("❌ Schema setup failed")
        return False


def main():
    """Main entry point"""
    database_url = get_database_url()

    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not set")
        logger.info("Usage: DATABASE_URL=postgresql://user:pass@host/db python setup_consensus_schema.py")
        sys.exit(1)

    logger.info("DevSkyy Consensus Workflow Schema Setup")
    logger.info("=" * 50)

    success = setup_schema(database_url)

    if success:
        logger.info("=" * 50)
        logger.info("✅ Setup completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Verify schema: python scripts/verify_database_schema.py")
        logger.info("2. Start FastAPI server: uvicorn main:app --reload")
        logger.info("3. Test consensus workflow: POST /api/v1/consensus/workflow")
        sys.exit(0)
    else:
        logger.error("=" * 50)
        logger.error("❌ Setup failed - please check errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()
