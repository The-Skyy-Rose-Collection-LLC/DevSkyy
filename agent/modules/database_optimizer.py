import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json
import hashlib
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Advanced database optimization system with query caching and indexing strategies."""
    
    def __init__(self):
        self.query_cache = {}
        self.index_recommendations = {}
        self.slow_queries = []
        self.query_stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "slow_queries": 0,
            "avg_execution_time": 0
        }
    
    def query_cache_key(self, query: str, params: tuple = None) -> str:
        """Generate cache key for database query."""
        key_data = {
            'query': query.strip().lower(),
            'params': params or ()
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def cached_query(self, ttl: int = 300):
        """Decorator for caching database query results."""
        def decorator(func):
            @wraps(func)
            async def async_wrapper(query: str, *args, **kwargs):
                start_time = datetime.now()
                cache_key = self.query_cache_key(query, args)
                
                # Check cache first
                if cache_key in self.query_cache:
                    cached_data = self.query_cache[cache_key]
                    if datetime.now() - cached_data['timestamp'] < timedelta(seconds=ttl):
                        self.query_stats["cache_hits"] += 1
                        logger.debug(f"Query cache hit: {query[:50]}...")
                        return cached_data['result']
                
                # Execute query
                self.query_stats["cache_misses"] += 1
                result = await func(query, *args, **kwargs)
                
                # Cache result
                self.query_cache[cache_key] = {
                    'result': result,
                    'timestamp': datetime.now()
                }
                
                # Track performance
                execution_time = (datetime.now() - start_time).total_seconds()
                self.query_stats["total_queries"] += 1
                self._update_avg_execution_time(execution_time)
                
                if execution_time > 1.0:  # Slow query threshold
                    self.query_stats["slow_queries"] += 1
                    self.slow_queries.append({
                        'query': query,
                        'execution_time': execution_time,
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.warning(f"Slow query detected: {execution_time:.3f}s - {query[:100]}...")
                
                return result
            
            @wraps(func)
            def sync_wrapper(query: str, *args, **kwargs):
                start_time = datetime.now()
                cache_key = self.query_cache_key(query, args)
                
                # Check cache first
                if cache_key in self.query_cache:
                    cached_data = self.query_cache[cache_key]
                    if datetime.now() - cached_data['timestamp'] < timedelta(seconds=ttl):
                        self.query_stats["cache_hits"] += 1
                        logger.debug(f"Query cache hit: {query[:50]}...")
                        return cached_data['result']
                
                # Execute query
                self.query_stats["cache_misses"] += 1
                result = func(query, *args, **kwargs)
                
                # Cache result
                self.query_cache[cache_key] = {
                    'result': result,
                    'timestamp': datetime.now()
                }
                
                # Track performance
                execution_time = (datetime.now() - start_time).total_seconds()
                self.query_stats["total_queries"] += 1
                self._update_avg_execution_time(execution_time)
                
                if execution_time > 1.0:  # Slow query threshold
                    self.query_stats["slow_queries"] += 1
                    self.slow_queries.append({
                        'query': query,
                        'execution_time': execution_time,
                        'timestamp': datetime.now().isoformat()
                    })
                    logger.warning(f"Slow query detected: {execution_time:.3f}s - {query[:100]}...")
                
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def _update_avg_execution_time(self, execution_time: float):
        """Update average execution time."""
        total = self.query_stats["total_queries"]
        current_avg = self.query_stats["avg_execution_time"]
        self.query_stats["avg_execution_time"] = ((current_avg * (total - 1)) + execution_time) / total
    
    def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """Analyze query performance and provide optimization recommendations."""
        analysis = {
            "query": query,
            "complexity_score": self._calculate_query_complexity(query),
            "optimization_recommendations": [],
            "index_suggestions": [],
            "performance_score": 0
        }
        
        # Check for common performance issues
        if "SELECT *" in query.upper():
            analysis["optimization_recommendations"].append({
                "issue": "SELECT * usage",
                "severity": "medium",
                "recommendation": "Specify only needed columns to reduce data transfer",
                "impact": "20-40% performance improvement"
            })
        
        if "ORDER BY" in query.upper() and "LIMIT" not in query.upper():
            analysis["optimization_recommendations"].append({
                "issue": "ORDER BY without LIMIT",
                "severity": "high",
                "recommendation": "Add LIMIT clause or create appropriate index",
                "impact": "50-80% performance improvement"
            })
        
        if "LIKE '%" in query.upper():
            analysis["optimization_recommendations"].append({
                "issue": "Leading wildcard in LIKE",
                "severity": "high",
                "recommendation": "Avoid leading wildcards or use full-text search",
                "impact": "60-90% performance improvement"
            })
        
        if query.upper().count("JOIN") > 3:
            analysis["optimization_recommendations"].append({
                "issue": "Multiple JOINs",
                "severity": "medium",
                "recommendation": "Consider query decomposition or denormalization",
                "impact": "30-50% performance improvement"
            })
        
        # Generate index suggestions
        analysis["index_suggestions"] = self._suggest_indexes(query)
        
        # Calculate performance score
        analysis["performance_score"] = self._calculate_performance_score(analysis)
        
        return analysis
    
    def _calculate_query_complexity(self, query: str) -> int:
        """Calculate query complexity score."""
        complexity = 0
        query_upper = query.upper()
        
        # Basic complexity factors
        complexity += query_upper.count("SELECT") * 1
        complexity += query_upper.count("JOIN") * 2
        complexity += query_upper.count("WHERE") * 1
        complexity += query_upper.count("GROUP BY") * 2
        complexity += query_upper.count("ORDER BY") * 1
        complexity += query_upper.count("HAVING") * 2
        complexity += query_upper.count("UNION") * 3
        complexity += query_upper.count("SUBQUERY") * 3
        
        # Advanced complexity factors
        if "CASE" in query_upper:
            complexity += 2
        if "EXISTS" in query_upper:
            complexity += 3
        if "IN (" in query_upper:
            complexity += 2
        
        return complexity
    
    def _suggest_indexes(self, query: str) -> List[Dict[str, Any]]:
        """Suggest database indexes based on query analysis."""
        suggestions = []
        query_upper = query.upper()
        
        # Analyze WHERE clauses
        if "WHERE" in query_upper:
            # Simple column equality checks
            if "WHERE id =" in query_upper:
                suggestions.append({
                    "type": "primary_key",
                    "columns": ["id"],
                    "priority": "high",
                    "reason": "Primary key lookup optimization"
                })
            
            # Multiple column conditions
            if "WHERE" in query_upper and "AND" in query_upper:
                suggestions.append({
                    "type": "composite_index",
                    "columns": ["column1", "column2"],
                    "priority": "medium",
                    "reason": "Composite index for multi-column WHERE clause"
                })
        
        # Analyze ORDER BY clauses
        if "ORDER BY" in query_upper:
            suggestions.append({
                "type": "sort_index",
                "columns": ["ordered_column"],
                "priority": "high",
                "reason": "Index for ORDER BY optimization"
            })
        
        # Analyze JOIN conditions
        if "JOIN" in query_upper:
            suggestions.append({
                "type": "foreign_key",
                "columns": ["join_column"],
                "priority": "high",
                "reason": "Foreign key index for JOIN optimization"
            })
        
        return suggestions
    
    def _calculate_performance_score(self, analysis: Dict) -> int:
        """Calculate overall performance score (0-100)."""
        score = 100
        
        # Deduct points for issues
        for rec in analysis["optimization_recommendations"]:
            if rec["severity"] == "high":
                score -= 30
            elif rec["severity"] == "medium":
                score -= 15
            elif rec["severity"] == "low":
                score -= 5
        
        # Deduct points for complexity
        complexity = analysis["complexity_score"]
        if complexity > 20:
            score -= 25
        elif complexity > 10:
            score -= 15
        elif complexity > 5:
            score -= 10
        
        return max(0, score)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive database performance report."""
        cache_hit_rate = 0
        if self.query_stats["total_queries"] > 0:
            cache_hit_rate = (self.query_stats["cache_hits"] / 
                            (self.query_stats["cache_hits"] + self.query_stats["cache_misses"])) * 100
        
        return {
            "query_statistics": self.query_stats,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "slow_queries_count": len(self.slow_queries),
            "recent_slow_queries": self.slow_queries[-10:],  # Last 10 slow queries
            "index_recommendations": self.index_recommendations,
            "performance_grade": self._calculate_performance_grade(cache_hit_rate),
            "optimization_opportunities": self._identify_optimization_opportunities()
        }
    
    def _calculate_performance_grade(self, cache_hit_rate: float) -> str:
        """Calculate performance grade based on metrics."""
        if cache_hit_rate >= 90 and self.query_stats["avg_execution_time"] < 0.1:
            return "A+"
        elif cache_hit_rate >= 80 and self.query_stats["avg_execution_time"] < 0.2:
            return "A"
        elif cache_hit_rate >= 70 and self.query_stats["avg_execution_time"] < 0.5:
            return "B"
        elif cache_hit_rate >= 60 and self.query_stats["avg_execution_time"] < 1.0:
            return "C"
        else:
            return "D"
    
    def _identify_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify key optimization opportunities."""
        opportunities = []
        
        if self.query_stats["cache_hit_rate"] < 70:
            opportunities.append({
                "type": "caching",
                "priority": "high",
                "description": "Low cache hit rate - implement more aggressive caching",
                "potential_improvement": "30-50%"
            })
        
        if self.query_stats["avg_execution_time"] > 0.5:
            opportunities.append({
                "type": "query_optimization",
                "priority": "high",
                "description": "High average execution time - optimize slow queries",
                "potential_improvement": "40-70%"
            })
        
        if len(self.slow_queries) > 10:
            opportunities.append({
                "type": "indexing",
                "priority": "medium",
                "description": "Multiple slow queries detected - review indexing strategy",
                "potential_improvement": "20-40%"
            })
        
        return opportunities
    
    def clear_query_cache(self) -> int:
        """Clear query cache."""
        cache_size = len(self.query_cache)
        self.query_cache.clear()
        logger.info(f"Cleared {cache_size} cached queries")
        return cache_size
    
    def optimize_query(self, query: str) -> str:
        """Provide optimized version of query."""
        optimized = query.strip()
        
        # Basic optimizations
        optimized = optimized.replace("SELECT *", "SELECT specific_columns")
        optimized = optimized.replace("WHERE 1=1", "")
        optimized = optimized.replace("  ", " ")  # Remove double spaces
        
        # Add LIMIT if ORDER BY without LIMIT
        if "ORDER BY" in optimized.upper() and "LIMIT" not in optimized.upper():
            optimized += " LIMIT 1000"  # Add reasonable default limit
        
        return optimized

# Global database optimizer instance
db_optimizer = DatabaseOptimizer()

# Convenience decorator
def cached_query(ttl: int = 300):
    return db_optimizer.cached_query(ttl)