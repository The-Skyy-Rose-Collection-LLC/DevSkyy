import asyncio
from datetime import datetime
from functools import wraps
import hashlib
import json
import logging
import time
from typing import Any


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Database query optimization and performance monitoring."""

    def __init__(self):
        self.query_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "cached_queries": 0,
            "optimized_queries": 0,
            "average_response_time": 0.0,
        }
        self.slow_query_threshold = 1.0  # seconds
        self.query_cache = {}
        self.index_recommendations = []

    def analyze_query(self, query: str, execution_time: float, params: dict | None = None) -> dict[str, Any]:
        """Analyze query performance and provide optimization suggestions."""
        analysis = {
            "query_hash": hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()[:8],
            "execution_time": execution_time,
            "is_slow": execution_time > self.slow_query_threshold,
            "optimization_suggestions": [],
            "index_recommendations": [],
            "performance_score": 0,
        }

        # Update statistics
        self.query_stats["total_queries"] += 1
        if analysis["is_slow"]:
            self.query_stats["slow_queries"] += 1

        # Analyze query patterns
        query_lower = query.lower()

        # Check for common performance issues
        if "select *" in query_lower:
            analysis["optimization_suggestions"].append(
                {
                    "type": "SELECT_OPTIMIZATION",
                    "severity": "MEDIUM",
                    "description": "Avoid SELECT * - specify only needed columns",
                    "impact": "Reduces data transfer and improves performance",
                }
            )

        if "order by" in query_lower and "limit" not in query_lower:
            analysis["optimization_suggestions"].append(
                {
                    "type": "ORDER_BY_OPTIMIZATION",
                    "severity": "HIGH",
                    "description": "ORDER BY without LIMIT can be expensive",
                    "impact": "Consider adding LIMIT or using pagination",
                }
            )

        if "like" in query_lower and query_lower.count("%") > 1:
            analysis["optimization_suggestions"].append(
                {
                    "type": "LIKE_OPTIMIZATION",
                    "severity": "MEDIUM",
                    "description": "Multiple LIKE patterns can be slow",
                    "impact": "Consider full-text search or better indexing",
                }
            )

        # Check for missing indexes
        if "where" in query_lower:
            where_columns = self._extract_where_columns(query)
            for column in where_columns:
                analysis["index_recommendations"].append(
                    {
                        "column": column,
                        "type": "INDEX",
                        "description": f"Consider adding index on {column}",
                        "impact": "Significantly improves WHERE clause performance",
                    }
                )

        # Calculate performance score
        analysis["performance_score"] = self._calculate_performance_score(analysis)

        return analysis

    def _extract_where_columns(self, query: str) -> list[str]:
        """Extract column names from WHERE clause."""
        import re

        where_pattern = r"where\s+([^)]+)"
        match = re.search(where_pattern, query.lower())
        if match:
            where_clause = match.group(1)
            # Simple extraction - look for column names before operators
            columns = re.findall(r"(\w+)\s*[=<>!]", where_clause)
            return columns
        return []

    def _calculate_performance_score(self, analysis: dict) -> int:
        """Calculate performance score (0-100)."""
        score = 100

        # Deduct points for slow queries
        if analysis["is_slow"]:
            score -= 30

        # Deduct points for optimization issues
        score -= len(analysis["optimization_suggestions"]) * 10

        # Deduct points for missing indexes
        score -= len(analysis["index_recommendations"]) * 5

        return max(0, score)

    def get_query_stats(self) -> dict[str, Any]:
        """Get query performance statistics."""
        if self.query_stats["total_queries"] > 0:
            slow_query_rate = (self.query_stats["slow_queries"] / self.query_stats["total_queries"]) * 100
            cache_hit_rate = (self.query_stats["cached_queries"] / self.query_stats["total_queries"]) * 100
        else:
            slow_query_rate = 0
            cache_hit_rate = 0

        return {
            **self.query_stats,
            "slow_query_rate": round(slow_query_rate, 2),
            "cache_hit_rate": round(cache_hit_rate, 2),
            "optimization_recommendations": len(self.index_recommendations),
        }


class DatabaseConnectionPool:
    """Optimized database connection pool with query caching."""

    def __init__(self, max_connections: int = 20, connection_timeout: int = 30):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections = asyncio.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.connection_stats = {
            "created": 0,
            "reused": 0,
            "closed": 0,
            "timeouts": 0,
            "errors": 0,
        }
        self.query_optimizer = QueryOptimizer()

    async def execute_query(self, query: str, params: dict | None = None, use_cache: bool = True) -> Any:
        """Execute query with optimization and caching."""
        start_time = time.time()

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(query, params)
            cached_result = self.query_optimizer.query_cache.get(cache_key)
            if cached_result:
                self.query_optimizer.query_stats["cached_queries"] += 1
                logger.debug(f"Query cache hit: {cache_key}")
                return cached_result

        # Execute query
        try:
            connection = await self.get_connection()
            result = await self._execute_with_connection(connection, query, params)
            await self.return_connection(connection)

            # Cache result if enabled
            if use_cache and result:
                self.query_optimizer.query_cache[cache_key] = result

            # Analyze query performance
            execution_time = time.time() - start_time
            analysis = self.query_optimizer.analyze_query(query, execution_time, params)

            if analysis["is_slow"]:
                logger.warning(f"Slow query detected: {execution_time:.2f}s - {query[:100]}...")

            return result

        except Exception as e:
            self.connection_stats["errors"] += 1
            logger.error(f"Query execution error: {e}")
            raise

    def _get_cache_key(self, query: str, params: dict | None = None) -> str:
        """Generate cache key for query."""
        key_data = {"query": query, "params": params or {}}
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()

    async def _execute_with_connection(self, connection, query: str, params: dict | None = None) -> Any:
        """Execute query with specific connection."""
        # This would be implemented based on your database driver
        # For now, return mock data
        return {"result": "query_executed", "rows": 1}

    async def get_connection(self):
        """Get connection from pool."""
        try:
            if not self.connections.empty():
                connection = await asyncio.wait_for(self.connections.get(), timeout=self.connection_timeout)
                self.connection_stats["reused"] += 1
                return connection
            elif self.active_connections < self.max_connections:
                connection = await self._create_connection()
                self.active_connections += 1
                self.connection_stats["created"] += 1
                return connection
            else:
                connection = await asyncio.wait_for(self.connections.get(), timeout=self.connection_timeout)
                self.connection_stats["reused"] += 1
                return connection
        except TimeoutError:
            self.connection_stats["timeouts"] += 1
            raise Exception("Connection pool timeout")

    async def return_connection(self, connection):
        """Return connection to pool."""
        try:
            if connection and not connection.is_closed():
                await self.connections.put(connection)
            else:
                self.active_connections -= 1
                self.connection_stats["closed"] += 1
        except Exception as e:
            self.connection_stats["errors"] += 1
            logger.error(f"Error returning connection: {e}")

    async def _create_connection(self):
        """Create new database connection."""

        # Mock connection - implement with actual database driver
        class MockConnection:
            def __init__(self):
                self.is_closed_flag = False

            def is_closed(self):
                return self.is_closed_flag

            async def close(self):
                self.is_closed_flag = True

        return MockConnection()

    def get_connection_stats(self) -> dict[str, Any]:
        """Get connection pool statistics."""
        return {
            "max_connections": self.max_connections,
            "active_connections": self.active_connections,
            "available_connections": self.connections.qsize(),
            "connection_stats": self.connection_stats,
            "query_stats": self.query_optimizer.get_query_stats(),
        }


class IndexOptimizer:
    """Database index optimization recommendations."""

    def __init__(self):
        self.index_recommendations = []
        self.existing_indexes = set()

    def analyze_table(self, table_name: str, query_patterns: list[str]) -> list[dict[str, Any]]:
        """Analyze table and recommend indexes."""
        recommendations = []

        # Analyze common query patterns
        for query in query_patterns:
            # Find WHERE clause columns
            where_columns = self._extract_where_columns(query)
            for column in where_columns:
                if f"{table_name}.{column}" not in self.existing_indexes:
                    recommendations.append(
                        {
                            "table": table_name,
                            "column": column,
                            "type": "SINGLE_COLUMN",
                            "priority": "HIGH",
                            "reason": "Frequently used in WHERE clauses",
                            "estimated_improvement": "50-80%",
                        }
                    )

            # Find ORDER BY columns
            order_columns = self._extract_order_columns(query)
            for column in order_columns:
                if f"{table_name}.{column}" not in self.existing_indexes:
                    recommendations.append(
                        {
                            "table": table_name,
                            "column": column,
                            "type": "SINGLE_COLUMN",
                            "priority": "MEDIUM",
                            "reason": "Used in ORDER BY clauses",
                            "estimated_improvement": "30-60%",
                        }
                    )

            # Find JOIN columns
            join_columns = self._extract_join_columns(query)
            for column in join_columns:
                if f"{table_name}.{column}" not in self.existing_indexes:
                    recommendations.append(
                        {
                            "table": table_name,
                            "column": column,
                            "type": "SINGLE_COLUMN",
                            "priority": "HIGH",
                            "reason": "Used in JOIN operations",
                            "estimated_improvement": "60-90%",
                        }
                    )

        # Remove duplicates
        unique_recommendations = []
        seen = set()
        for rec in recommendations:
            key = (rec["table"], rec["column"])
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)

        return unique_recommendations

    def _extract_where_columns(self, query: str) -> list[str]:
        """Extract columns from WHERE clause."""
        import re

        where_pattern = r"where\s+([^)]+)"
        match = re.search(where_pattern, query.lower())
        if match:
            where_clause = match.group(1)
            columns = re.findall(r"(\w+)\s*[=<>!]", where_clause)
            return columns
        return []

    def _extract_order_columns(self, query: str) -> list[str]:
        """Extract columns from ORDER BY clause."""
        import re

        order_pattern = r"order\s+by\s+([^)]+)"
        match = re.search(order_pattern, query.lower())
        if match:
            order_clause = match.group(1)
            columns = re.findall(r"(\w+)", order_clause)
            return columns
        return []

    def _extract_join_columns(self, query: str) -> list[str]:
        """Extract columns from JOIN clauses."""
        import re

        join_pattern = r"join\s+\w+\s+on\s+([^)]+)"
        matches = re.findall(join_pattern, query.lower())
        columns = []
        for match in matches:
            join_condition = match
            cols = re.findall(r"(\w+)\s*[=]", join_condition)
            columns.extend(cols)
        return columns


# Global instances
db_connection_pool = DatabaseConnectionPool(max_connections=20)
index_optimizer = IndexOptimizer()


def optimize_query(func):
    """Decorator for query optimization."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        # Execute the function
        result = await func(*args, **kwargs)

        # Log performance
        execution_time = time.time() - start_time
        if execution_time > 1.0:  # Log slow operations
            logger.warning(f"Slow operation: {func.__name__} took {execution_time:.2f}s")

        return result

    return wrapper


def get_database_stats() -> dict[str, Any]:
    """Get comprehensive database statistics."""
    return {
        "connection_pool": db_connection_pool.get_connection_stats(),
        "query_optimizer": db_connection_pool.query_optimizer.get_query_stats(),
        "timestamp": datetime.now().isoformat(),
    }
