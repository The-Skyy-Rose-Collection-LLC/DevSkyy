"""
Query Optimizer Utilities
==========================

SQLAlchemy query optimization helpers for preventing N+1 queries and
diagnosing slow queries using EXPLAIN ANALYZE.

Usage:
    from database.query_optimizer import QueryOptimizer

    # Optimize a product query
    query = select(Product)
    optimized = QueryOptimizer.optimize_product_query(query)

    # Analyze slow queries
    plan = await QueryOptimizer.explain_query(session, query)
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select

from database.db import Product

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    SQLAlchemy query optimization helpers.

    Provides:
    - Eager loading to prevent N+1 queries
    - EXPLAIN ANALYZE for performance diagnostics
    - Index hint recommendations
    """

    @staticmethod
    def optimize_product_query(query: Select) -> Select:
        """
        Add eager loading options to a product query.

        Prevents N+1 queries when accessing related data by loading
        order_items in a single additional query (selectinload).

        Args:
            query: Base SELECT query for Product model

        Returns:
            Optimized query with eager loading configured

        Example:
            query = select(Product).where(Product.is_active == True)
            optimized = QueryOptimizer.optimize_product_query(query)
            result = await session.execute(optimized)
        """
        return query.options(
            selectinload(Product.order_items),  # Prevents N+1 on order_items access
        )

    @staticmethod
    async def explain_query(session: AsyncSession, query: Select) -> list[str]:
        """
        Run EXPLAIN ANALYZE on a query and return the execution plan.

        Useful for identifying slow queries and missing indexes.
        Only runs on PostgreSQL (no-op on SQLite).

        Args:
            session: Active database session
            query: Query to analyze

        Returns:
            List of plan lines from EXPLAIN ANALYZE output

        Example:
            plan = await QueryOptimizer.explain_query(session, query)
            for line in plan:
                print(line)
        """
        try:
            # Compile query to SQL string
            compiled = query.compile(compile_kwargs={"literal_binds": True})
            sql = str(compiled)

            # Run EXPLAIN ANALYZE (PostgreSQL only)
            result = await session.execute(text(f"EXPLAIN ANALYZE {sql}"))
            rows = result.fetchall()
            plan_lines = [row[0] for row in rows]

            # Log slow queries (> 100ms)
            for line in plan_lines:
                if "actual time=" in line:
                    try:
                        # Parse: "actual time=0.123..456.789"
                        time_part = line.split("actual time=")[1].split(" ")[0]
                        max_time_ms = float(time_part.split("..")[1])
                        if max_time_ms > 100:
                            logger.warning(
                                f"Slow query detected ({max_time_ms:.1f}ms): "
                                f"{sql[:100]}..."
                            )
                    except (IndexError, ValueError):
                        pass

            return plan_lines

        except Exception as e:
            # SQLite or explain not supported
            logger.debug(f"EXPLAIN ANALYZE not available: {e}")
            return [f"EXPLAIN not available: {e}"]

    @staticmethod
    def detect_n_plus_one_risk(query: Select) -> list[str]:
        """
        Analyze a query for potential N+1 issues.

        Returns a list of warnings for relationships that may
        cause N+1 queries at access time.

        Args:
            query: SQLAlchemy SELECT query to analyze

        Returns:
            List of warning strings, empty if no issues detected
        """
        warnings: list[str] = []

        # Check if Product query has order_items eager loaded
        mapper = query.column_descriptions[0].get("entity") if query.column_descriptions else None
        if mapper is Product:
            # Check if selectinload/joinedload is configured
            options_str = str(query)
            if "order_items" not in options_str:
                warnings.append(
                    "Product query without eager loading for order_items — "
                    "accessing .order_items will cause N+1 queries. "
                    "Use QueryOptimizer.optimize_product_query() to fix."
                )

        return warnings

    @staticmethod
    def get_index_recommendations(table_name: str, filters: dict[str, Any]) -> list[str]:
        """
        Recommend indexes based on common query patterns.

        Args:
            table_name: Table being queried
            filters: Dict of column -> value pairs being filtered on

        Returns:
            List of CREATE INDEX statements that would help
        """
        recommendations: list[str] = []
        filter_cols = list(filters.keys())

        if len(filter_cols) >= 2:
            col_list = ", ".join(filter_cols)
            recommendations.append(
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS "
                f"idx_{table_name}_{'_'.join(filter_cols)} "
                f"ON {table_name}({col_list});"
            )
        elif len(filter_cols) == 1:
            col = filter_cols[0]
            if col not in ("id",):  # id already has a primary key index
                recommendations.append(
                    f"CREATE INDEX CONCURRENTLY IF NOT EXISTS "
                    f"idx_{table_name}_{col} "
                    f"ON {table_name}({col});"
                )

        return recommendations
