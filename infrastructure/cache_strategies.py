from datetime import datetime, timedelta
from infrastructure.redis_manager import redis_manager
import json

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import asyncio
import logging

"""
Enterprise Cache Invalidation Strategies
Implements intelligent cache invalidation for real-time data consistency
Fashion industry specific caching patterns and strategies
"""

logger = logging.getLogger(__name__)

class InvalidationStrategy(Enum):
    """Cache invalidation strategies"""

    IMMEDIATE = "immediate"  # Invalidate immediately
    DELAYED = "delayed"  # Invalidate after delay
    SCHEDULED = "scheduled"  # Invalidate at specific time
    PATTERN = "pattern"  # Invalidate by pattern
    DEPENDENCY = "dependency"  # Invalidate based on dependencies
    TTL_REFRESH = "ttl_refresh"  # Refresh TTL instead of invalidating

@dataclass
class InvalidationRule:
    """Cache invalidation rule configuration"""

    name: str
    strategy: InvalidationStrategy
    patterns: List[str]
    delay_seconds: int = 0
    schedule_time: Optional[datetime] = None
    dependencies: List[str] = None
    condition: Optional[Callable] = None
    fashion_context: bool = False  # Fashion industry specific rule

class CacheInvalidationManager:
    """Manages cache invalidation strategies and execution"""

    def __init__(self):
        self.invalidation_rules: Dict[str, InvalidationRule] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.scheduled_invalidations: List[Dict[str, Any]] = []
        self.invalidation_history: List[Dict[str, Any]] = []

        # Fashion industry specific cache dependencies
        self.fashion_dependencies = {
            "trends": ["recommendations", "analytics", "inventory"],
            "inventory": ["recommendations", "analytics", "pricing"],
            "user_preferences": ["recommendations", "personalization"],
            "seasonal_data": ["trends", "inventory", "pricing"],
            "product_catalog": ["recommendations", "search_index", "analytics"],
        }

        self._setup_default_rules()
        logger.info("Cache invalidation manager initialized")

    def _setup_default_rules(self):
        """Setup default invalidation rules for fashion e-commerce"""

        # Fashion trends - immediate invalidation for real-time updates
        self.add_rule(
            InvalidationRule(
                name="fashion_trends_update",
                strategy=InvalidationStrategy.IMMEDIATE,
                patterns=["trends:*", "rec:*", "analytics:trend_*"],
                fashion_context=True,
            )
        )

        # Inventory updates - delayed invalidation to batch updates
        self.add_rule(
            InvalidationRule(
                name="inventory_update",
                strategy=InvalidationStrategy.DELAYED,
                patterns=["inv:*", "rec:*", "analytics:inventory_*"],
                delay_seconds=30,  # Batch inventory updates
                fashion_context=True,
            )
        )

        # User preferences - immediate for personalization
        self.add_rule(
            InvalidationRule(
                name="user_preferences_update",
                strategy=InvalidationStrategy.IMMEDIATE,
                patterns=["user:*:preferences", "rec:user:*"],
                fashion_context=True,
            )
        )

        # Seasonal data - scheduled invalidation
        self.add_rule(
            InvalidationRule(
                name="seasonal_data_refresh",
                strategy=InvalidationStrategy.SCHEDULED,
                patterns=["trends:seasonal:*", "analytics:seasonal:*"],
                schedule_time=datetime.now().replace(
                    hour=2, minute=0, second=0
                ),  # 2 AM daily
                fashion_context=True,
            )
        )

        # API responses - TTL refresh for frequently accessed data
        self.add_rule(
            InvalidationRule(
                name="api_response_refresh",
                strategy=InvalidationStrategy.TTL_REFRESH,
                patterns=["api:*"],
                delay_seconds=300,  # Refresh TTL by 5 minutes
            )
        )

        # ML model results - dependency-based invalidation
        self.add_rule(
            InvalidationRule(
                name="ml_model_update",
                strategy=InvalidationStrategy.DEPENDENCY,
                patterns=["ml:*"],
                dependencies=["trends", "inventory", "user_preferences"],
            )
        )

    def add_rule(self, rule: InvalidationRule):
        """Add invalidation rule"""
        self.invalidation_rules[rule.name] = rule

        # Build dependency graph
        if rule.dependencies:
            for dep in rule.dependencies:
                if dep not in self.dependency_graph:
                    self.dependency_graph[dep] = set()
                self.dependency_graph[dep].add(rule.name)

        logger.debug(f"Added invalidation rule: {rule.name}")

    def remove_rule(self, rule_name: str):
        """Remove invalidation rule"""
        if rule_name in self.invalidation_rules:
            del self.invalidation_rules[rule_name]

            # Clean up dependency graph
            for deps in self.dependency_graph.values():
                deps.discard(rule_name)

            logger.debug(f"Removed invalidation rule: {rule_name}")

    async def invalidate(
        self,
        trigger: str,
        context: Dict[str, Any] = None,
        force_immediate: bool = False,
    ) -> Dict[str, Any]:
        """Execute cache invalidation based on trigger"""
        context = context or {}
        invalidation_results = {
            "trigger": trigger,
            "timestamp": datetime.now().isoformat(),
            "rules_executed": [],
            "keys_invalidated": 0,
            "errors": [],
        }

        # Find matching rules
        matching_rules = []
        for rule_name, rule in self.invalidation_rules.items():
            if self._rule_matches_trigger(rule, trigger, context):
                matching_rules.append(rule)

        # Execute invalidation for each matching rule
        for rule in matching_rules:
            try:
                result = await self._execute_rule(rule, context, force_immediate)
                invalidation_results["rules_executed"].append(
                    {
                        "rule_name": rule.name,
                        "strategy": rule.strategy.value,
                        "keys_invalidated": result.get("keys_invalidated", 0),
                        "execution_time_ms": result.get("execution_time_ms", 0),
                    }
                )
                invalidation_results["keys_invalidated"] += result.get(
                    "keys_invalidated", 0
                )

            except Exception as e:
                error_msg = f"Error executing rule {rule.name}: {str(e)}"
                logger.error(error_msg)
                invalidation_results["errors"].append(error_msg)

        # Record invalidation history
        self.invalidation_history.append(invalidation_results)

        # Keep only last 1000 invalidation records
        if len(self.invalidation_history) > 1000:
            self.invalidation_history = self.invalidation_history[-1000:]

        logger.info(
            f"Cache invalidation completed: {trigger} - {invalidation_results['keys_invalidated']} keys"
        )
        return invalidation_results

    def _rule_matches_trigger(
        self, rule: InvalidationRule, trigger: str, context: Dict[str, Any]
    ) -> bool:
        """Check if rule matches the trigger"""
        # Check if trigger matches any pattern
        for pattern in rule.patterns:
            if self._pattern_matches(pattern, trigger):
                # Check condition if specified
                if rule.condition and not rule.condition(trigger, context):
                    continue
                return True

        # Check dependency-based triggers
        if rule.strategy == InvalidationStrategy.DEPENDENCY and rule.dependencies:
            return trigger in rule.dependencies

        return False

    def _pattern_matches(self, pattern: str, trigger: str) -> bool:
        """Check if pattern matches trigger (supports wildcards)"""
        if "*" not in pattern:
            return pattern == trigger

        # Simple wildcard matching
        if pattern.endswith("*"):
            return trigger.startswith(pattern[:-1])
        elif pattern.startswith("*"):
            return trigger.endswith(pattern[1:])
        elif "*" in pattern:
            parts = pattern.split("*")
            return trigger.startswith(parts[0]) and trigger.endswith(parts[-1])

        return False

    async def _execute_rule(
        self,
        rule: InvalidationRule,
        context: Dict[str, Any],
        force_immediate: bool = False,
    ) -> Dict[str, Any]:
        """Execute specific invalidation rule"""
        start_time = datetime.now()
        keys_invalidated = 0

        if rule.strategy == InvalidationStrategy.IMMEDIATE or force_immediate:
            keys_invalidated = await self._immediate_invalidation(rule.patterns)

        elif rule.strategy == InvalidationStrategy.DELAYED:
            await self._delayed_invalidation(rule.patterns, rule.delay_seconds)

        elif rule.strategy == InvalidationStrategy.SCHEDULED:
            await self._scheduled_invalidation(rule)

        elif rule.strategy == InvalidationStrategy.PATTERN:
            keys_invalidated = await self._pattern_invalidation(rule.patterns)

        elif rule.strategy == InvalidationStrategy.DEPENDENCY:
            keys_invalidated = await self._dependency_invalidation(rule.dependencies)

        elif rule.strategy == InvalidationStrategy.TTL_REFRESH:
            keys_invalidated = await self._ttl_refresh(
                rule.patterns, rule.delay_seconds
            )

        execution_time = (datetime.now() - start_time).total_seconds() * 1000

        return {
            "keys_invalidated": keys_invalidated,
            "execution_time_ms": execution_time,
        }

    async def _immediate_invalidation(self, patterns: List[str]) -> int:
        """Immediate cache invalidation"""
        total_invalidated = 0

        for pattern in patterns:
            # Extract prefix and pattern
            if ":" in pattern:
                prefix_part = pattern.split(":")[0]
                pattern_part = ":".join(pattern.split(":")[1:])
            else:
                prefix_part = "api_cache"
                pattern_part = pattern

            invalidated = await redis_manager.invalidate_pattern(
                pattern_part, prefix_part
            )
            total_invalidated += invalidated

        return total_invalidated

    async def _delayed_invalidation(self, patterns: List[str], delay_seconds: int):
        """Delayed cache invalidation"""

        async def delayed_task():
            await asyncio.sleep(delay_seconds)
            await self._immediate_invalidation(patterns)

        # Schedule delayed invalidation
        asyncio.create_task(delayed_task())

    async def _scheduled_invalidation(self, rule: InvalidationRule):
        """Scheduled cache invalidation"""
        if rule.schedule_time:
            now = datetime.now()
            if rule.schedule_time > now:
                delay = (rule.schedule_time - now).total_seconds()
                await asyncio.sleep(delay)

            await self._immediate_invalidation(rule.patterns)

    async def _pattern_invalidation(self, patterns: List[str]) -> int:
        """Pattern-based cache invalidation"""
        return await self._immediate_invalidation(patterns)

    async def _dependency_invalidation(self, dependencies: List[str]) -> int:
        """Dependency-based cache invalidation"""
        total_invalidated = 0

        for dependency in dependencies:
            if dependency in self.fashion_dependencies:
                dependent_patterns = self.fashion_dependencies[dependency]
                for pattern in dependent_patterns:
                    invalidated = await redis_manager.invalidate_pattern(
                        f"{pattern}:*", pattern
                    )
                    total_invalidated += invalidated

        return total_invalidated

    async def _ttl_refresh(self, patterns: List[str], refresh_seconds: int) -> int:
        """Refresh TTL instead of invalidating"""
        total_refreshed = 0

        for pattern in patterns:
            # This would require getting all keys matching pattern and refreshing their TTL
            # For now, we'll implement a simplified version
            if ":" in pattern:
                prefix_part = pattern.split(":")[0]
                pattern_part = ":".join(pattern.split(":")[1:])
            else:
                prefix_part = "api_cache"
                pattern_part = pattern

            # In a real implementation, we'd get all matching keys and refresh their TTL
            # For now, we'll just log the refresh operation
            logger.debug(
                f"TTL refresh scheduled for pattern {pattern} (+{refresh_seconds}s)"
            )
            total_refreshed += 1

        return total_refreshed

    async def invalidate_fashion_trends(self, trend_categories: List[str] = None):
        """Invalidate fashion trend related caches"""
        context = {"categories": trend_categories or []}
        return await self.invalidate("fashion_trends_update", context)

    async def invalidate_inventory(self, product_ids: List[str] = None):
        """Invalidate inventory related caches"""
        context = {"product_ids": product_ids or []}
        return await self.invalidate("inventory_update", context)

    async def invalidate_user_data(self, user_id: str):
        """Invalidate user-specific caches"""
        context = {"user_id": user_id}
        return await self.invalidate("user_preferences_update", context)

    async def invalidate_ml_models(self, model_names: List[str] = None):
        """Invalidate ML model related caches"""
        context = {"model_names": model_names or []}
        return await self.invalidate("ml_model_update", context)

    async def get_invalidation_stats(self) -> Dict[str, Any]:
        """Get cache invalidation statistics"""
        recent_invalidations = [
            inv
            for inv in self.invalidation_history
            if datetime.fromisoformat(inv["timestamp"])
            > datetime.now() - timedelta(hours=24)
        ]

        total_keys_invalidated = sum(
            inv["keys_invalidated"] for inv in recent_invalidations
)
        total_rules_executed = sum()
            len(inv["rules_executed"]) for inv in recent_invalidations
        )

        return {
            "total_rules": len(self.invalidation_rules),
            "recent_invalidations_24h": len(recent_invalidations),
            "total_keys_invalidated_24h": total_keys_invalidated,
            "total_rules_executed_24h": total_rules_executed,
            "fashion_specific_rules": len()
                [r for r in self.invalidation_rules.values() if r.fashion_context]
            ),
            "dependency_graph_size": len(self.dependency_graph),
            "scheduled_invalidations": len(self.scheduled_invalidations),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health check for cache invalidation system"""
        try:
            stats = await self.get_invalidation_stats()
            redis_health = await redis_manager.health_check()

            return {
                "status": (
                    "healthy" if redis_health["status"] == "healthy" else "degraded"
                ),
                "invalidation_stats": stats,
                "redis_health": redis_health,
                "rules_configured": len(self.invalidation_rules),
                "fashion_context_enabled": True,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

# Global cache invalidation manager
cache_invalidation_manager = CacheInvalidationManager()
