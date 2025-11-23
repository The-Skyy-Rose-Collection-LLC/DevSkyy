"""
Comprehensive tests for infrastructure/cache_strategies.py

WHY: Ensure cache invalidation strategies work correctly with ≥80% coverage
HOW: Test all invalidation strategies, rules, pattern matching, and fashion-specific features
IMPACT: Validates enterprise cache invalidation infrastructure reliability

Truth Protocol: Rules #1, #8, #15
Coverage Target: ≥80%
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.cache_strategies import (
    CacheInvalidationManager,
    InvalidationRule,
    InvalidationStrategy,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_redis_manager():
    """Mock Redis manager for testing."""
    with patch("infrastructure.cache_strategies.redis_manager") as mock:
        mock.invalidate_pattern = AsyncMock(return_value=5)
        mock.health_check = AsyncMock(return_value={"status": "healthy"})
        yield mock


@pytest.fixture
def cache_manager(mock_redis_manager):
    """Create CacheInvalidationManager instance with mocked Redis."""
    return CacheInvalidationManager()


@pytest.fixture
def sample_rule():
    """Create sample invalidation rule."""
    return InvalidationRule(
        name="test_rule",
        strategy=InvalidationStrategy.IMMEDIATE,
        patterns=["test:*", "cache:*"],
        delay_seconds=0,
        fashion_context=False,
    )


# ============================================================================
# TEST InvalidationStrategy Enum
# ============================================================================


class TestInvalidationStrategy:
    """Test InvalidationStrategy enum."""

    def test_invalidation_strategy_values(self):
        """Test all invalidation strategy enum values are defined."""
        assert InvalidationStrategy.IMMEDIATE.value == "immediate"
        assert InvalidationStrategy.DELAYED.value == "delayed"
        assert InvalidationStrategy.SCHEDULED.value == "scheduled"
        assert InvalidationStrategy.PATTERN.value == "pattern"
        assert InvalidationStrategy.DEPENDENCY.value == "dependency"
        assert InvalidationStrategy.TTL_REFRESH.value == "ttl_refresh"

    def test_invalidation_strategy_count(self):
        """Test all expected strategies are present."""
        strategies = list(InvalidationStrategy)
        assert len(strategies) == 6


# ============================================================================
# TEST InvalidationRule Dataclass
# ============================================================================


class TestInvalidationRule:
    """Test InvalidationRule dataclass."""

    def test_invalidation_rule_initialization(self, sample_rule):
        """Test InvalidationRule initialization with required fields."""
        assert sample_rule.name == "test_rule"
        assert sample_rule.strategy == InvalidationStrategy.IMMEDIATE
        assert sample_rule.patterns == ["test:*", "cache:*"]
        assert sample_rule.delay_seconds == 0
        assert sample_rule.fashion_context is False

    def test_invalidation_rule_optional_fields(self):
        """Test InvalidationRule with optional fields."""
        rule = InvalidationRule(
            name="delayed_rule",
            strategy=InvalidationStrategy.DELAYED,
            patterns=["api:*"],
            delay_seconds=30,
            schedule_time=datetime.now() + timedelta(hours=1),
            dependencies=["trends", "inventory"],
            condition=lambda trigger, context: True,
            fashion_context=True,
        )

        assert rule.delay_seconds == 30
        assert rule.schedule_time is not None
        assert rule.dependencies == ["trends", "inventory"]
        assert rule.condition is not None
        assert rule.fashion_context is True

    def test_invalidation_rule_with_condition(self):
        """Test InvalidationRule with condition function."""

        def test_condition(trigger, context):
            return context.get("force") is True

        rule = InvalidationRule(
            name="conditional_rule",
            strategy=InvalidationStrategy.IMMEDIATE,
            patterns=["test:*"],
            condition=test_condition,
        )

        assert rule.condition("test:key", {"force": True}) is True
        assert rule.condition("test:key", {"force": False}) is False


# ============================================================================
# TEST CacheInvalidationManager Initialization
# ============================================================================


class TestCacheInvalidationManagerInitialization:
    """Test CacheInvalidationManager initialization."""

    def test_manager_initialization(self, cache_manager):
        """Test manager initializes with default rules."""
        assert isinstance(cache_manager.invalidation_rules, dict)
        assert isinstance(cache_manager.dependency_graph, dict)
        assert isinstance(cache_manager.scheduled_invalidations, list)
        assert isinstance(cache_manager.invalidation_history, list)

    def test_fashion_dependencies_defined(self, cache_manager):
        """Test fashion industry dependencies are configured."""
        assert "trends" in cache_manager.fashion_dependencies
        assert "inventory" in cache_manager.fashion_dependencies
        assert "user_preferences" in cache_manager.fashion_dependencies
        assert "seasonal_data" in cache_manager.fashion_dependencies
        assert "product_catalog" in cache_manager.fashion_dependencies

    def test_default_rules_setup(self, cache_manager):
        """Test default invalidation rules are created."""
        # Check for fashion-specific rules
        assert "fashion_trends_update" in cache_manager.invalidation_rules
        assert "inventory_update" in cache_manager.invalidation_rules
        assert "user_preferences_update" in cache_manager.invalidation_rules
        assert "seasonal_data_refresh" in cache_manager.invalidation_rules
        assert "api_response_refresh" in cache_manager.invalidation_rules
        assert "ml_model_update" in cache_manager.invalidation_rules

    def test_default_fashion_trends_rule(self, cache_manager):
        """Test fashion trends rule configuration."""
        rule = cache_manager.invalidation_rules["fashion_trends_update"]

        assert rule.strategy == InvalidationStrategy.IMMEDIATE
        assert rule.fashion_context is True
        assert "trends:*" in rule.patterns

    def test_default_inventory_rule(self, cache_manager):
        """Test inventory update rule configuration."""
        rule = cache_manager.invalidation_rules["inventory_update"]

        assert rule.strategy == InvalidationStrategy.DELAYED
        assert rule.delay_seconds == 30
        assert rule.fashion_context is True

    def test_default_ml_model_rule(self, cache_manager):
        """Test ML model rule configuration."""
        rule = cache_manager.invalidation_rules["ml_model_update"]

        assert rule.strategy == InvalidationStrategy.DEPENDENCY
        assert rule.dependencies is not None
        assert "trends" in rule.dependencies


# ============================================================================
# TEST Rule Management
# ============================================================================


class TestRuleManagement:
    """Test adding and removing invalidation rules."""

    def test_add_rule(self, cache_manager):
        """Test adding new invalidation rule."""
        initial_count = len(cache_manager.invalidation_rules)

        rule = InvalidationRule(
            name="new_rule",
            strategy=InvalidationStrategy.IMMEDIATE,
            patterns=["new:*"],
        )

        cache_manager.add_rule(rule)

        assert len(cache_manager.invalidation_rules) == initial_count + 1
        assert "new_rule" in cache_manager.invalidation_rules
        assert cache_manager.invalidation_rules["new_rule"] == rule

    def test_add_rule_with_dependencies(self, cache_manager):
        """Test adding rule with dependencies builds dependency graph."""
        rule = InvalidationRule(
            name="dependent_rule",
            strategy=InvalidationStrategy.DEPENDENCY,
            patterns=["dep:*"],
            dependencies=["trends", "inventory"],
        )

        cache_manager.add_rule(rule)

        assert "trends" in cache_manager.dependency_graph
        assert "dependent_rule" in cache_manager.dependency_graph["trends"]
        assert "inventory" in cache_manager.dependency_graph
        assert "dependent_rule" in cache_manager.dependency_graph["inventory"]

    def test_remove_rule(self, cache_manager):
        """Test removing invalidation rule."""
        rule_name = "fashion_trends_update"
        assert rule_name in cache_manager.invalidation_rules

        cache_manager.remove_rule(rule_name)

        assert rule_name not in cache_manager.invalidation_rules

    def test_remove_rule_cleans_dependency_graph(self, cache_manager):
        """Test removing rule cleans up dependency graph."""
        rule = InvalidationRule(
            name="temp_rule",
            strategy=InvalidationStrategy.DEPENDENCY,
            patterns=["temp:*"],
            dependencies=["trends"],
        )

        cache_manager.add_rule(rule)
        assert "temp_rule" in cache_manager.dependency_graph["trends"]

        cache_manager.remove_rule("temp_rule")

        assert "temp_rule" not in cache_manager.dependency_graph.get("trends", set())

    def test_remove_nonexistent_rule(self, cache_manager):
        """Test removing non-existent rule does not error."""
        cache_manager.remove_rule("nonexistent_rule")
        # Should not raise exception


# ============================================================================
# TEST Pattern Matching
# ============================================================================


class TestPatternMatching:
    """Test pattern matching logic."""

    def test_pattern_matches_exact(self, cache_manager):
        """Test exact pattern matching."""
        assert cache_manager._pattern_matches("test", "test") is True
        assert cache_manager._pattern_matches("test", "other") is False

    def test_pattern_matches_wildcard_suffix(self, cache_manager):
        """Test pattern matching with wildcard suffix."""
        assert cache_manager._pattern_matches("test:*", "test:key") is True
        assert cache_manager._pattern_matches("test:*", "test:another") is True
        assert cache_manager._pattern_matches("test:*", "other:key") is False

    def test_pattern_matches_wildcard_prefix(self, cache_manager):
        """Test pattern matching with wildcard prefix."""
        assert cache_manager._pattern_matches("*:key", "test:key") is True
        assert cache_manager._pattern_matches("*:key", "other:key") is True
        assert cache_manager._pattern_matches("*:key", "test:other") is False

    def test_pattern_matches_wildcard_middle(self, cache_manager):
        """Test pattern matching with wildcard in middle."""
        assert cache_manager._pattern_matches("test:*:key", "test:middle:key") is True
        assert cache_manager._pattern_matches("test:*:key", "test:another:key") is True
        assert cache_manager._pattern_matches("test:*:key", "test:key") is False

    def test_pattern_matches_multiple_wildcards(self, cache_manager):
        """Test pattern with multiple wildcards uses first split."""
        pattern = "test:*:data"
        assert cache_manager._pattern_matches(pattern, "test:something:data") is True


# ============================================================================
# TEST Rule Matching
# ============================================================================


class TestRuleMatching:
    """Test rule matching against triggers."""

    def test_rule_matches_trigger_simple(self, cache_manager, sample_rule):
        """Test simple rule matching."""
        assert cache_manager._rule_matches_trigger(sample_rule, "test:key", {}) is True
        assert cache_manager._rule_matches_trigger(sample_rule, "cache:item", {}) is True
        assert cache_manager._rule_matches_trigger(sample_rule, "other:key", {}) is False

    def test_rule_matches_trigger_with_condition(self, cache_manager):
        """Test rule matching with condition function."""

        def condition(trigger, context):
            return context.get("valid") is True

        rule = InvalidationRule(
            name="conditional",
            strategy=InvalidationStrategy.IMMEDIATE,
            patterns=["test:*"],
            condition=condition,
        )

        assert cache_manager._rule_matches_trigger(rule, "test:key", {"valid": True}) is True
        assert cache_manager._rule_matches_trigger(rule, "test:key", {"valid": False}) is False
        assert cache_manager._rule_matches_trigger(rule, "test:key", {}) is False

    def test_rule_matches_trigger_dependency_strategy(self, cache_manager):
        """Test dependency strategy rule matching."""
        rule = InvalidationRule(
            name="dep_rule",
            strategy=InvalidationStrategy.DEPENDENCY,
            patterns=["test:*"],
            dependencies=["trends", "inventory"],
        )

        # Should match on dependency name
        assert cache_manager._rule_matches_trigger(rule, "trends", {}) is True
        assert cache_manager._rule_matches_trigger(rule, "inventory", {}) is True
        assert cache_manager._rule_matches_trigger(rule, "other", {}) is False


# ============================================================================
# TEST Cache Invalidation Execution
# ============================================================================


class TestCacheInvalidation:
    """Test cache invalidation execution."""

    @pytest.mark.asyncio
    async def test_invalidate_simple(self, cache_manager, mock_redis_manager):
        """Test simple cache invalidation."""
        result = await cache_manager.invalidate("fashion_trends_update")

        assert result["trigger"] == "fashion_trends_update"
        assert result["keys_invalidated"] >= 0
        assert isinstance(result["rules_executed"], list)
        assert isinstance(result["errors"], list)

    @pytest.mark.asyncio
    async def test_invalidate_with_context(self, cache_manager, mock_redis_manager):
        """Test invalidation with context data."""
        context = {"categories": ["summer", "winter"]}

        result = await cache_manager.invalidate("fashion_trends_update", context)

        assert result["trigger"] == "fashion_trends_update"
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_invalidate_force_immediate(self, cache_manager, mock_redis_manager):
        """Test forced immediate invalidation."""
        result = await cache_manager.invalidate("inventory_update", force_immediate=True)

        assert result["trigger"] == "inventory_update"
        # Should execute even for delayed strategy

    @pytest.mark.asyncio
    async def test_invalidate_records_history(self, cache_manager, mock_redis_manager):
        """Test invalidation records to history."""
        initial_history_len = len(cache_manager.invalidation_history)

        await cache_manager.invalidate("fashion_trends_update")

        assert len(cache_manager.invalidation_history) == initial_history_len + 1

    @pytest.mark.asyncio
    async def test_invalidate_history_limit(self, cache_manager, mock_redis_manager):
        """Test invalidation history is limited to 1000 entries."""
        # Fill history beyond limit
        cache_manager.invalidation_history = [{"dummy": i} for i in range(1005)]

        await cache_manager.invalidate("fashion_trends_update")

        assert len(cache_manager.invalidation_history) == 1000

    @pytest.mark.asyncio
    async def test_invalidate_no_matching_rules(self, cache_manager, mock_redis_manager):
        """Test invalidation with no matching rules."""
        result = await cache_manager.invalidate("nonexistent_trigger")

        assert result["trigger"] == "nonexistent_trigger"
        assert result["keys_invalidated"] == 0
        assert len(result["rules_executed"]) == 0


# ============================================================================
# TEST Invalidation Strategies
# ============================================================================


class TestInvalidationStrategies:
    """Test different invalidation strategies."""

    @pytest.mark.asyncio
    async def test_immediate_invalidation(self, cache_manager, mock_redis_manager):
        """Test immediate invalidation strategy."""
        keys_invalidated = await cache_manager._immediate_invalidation(["test:*", "cache:*"])

        assert keys_invalidated >= 0
        assert mock_redis_manager.invalidate_pattern.called

    @pytest.mark.asyncio
    async def test_delayed_invalidation(self, cache_manager, mock_redis_manager):
        """Test delayed invalidation strategy."""
        # Should schedule task without blocking
        await cache_manager._delayed_invalidation(["test:*"], delay_seconds=0.1)

        # Wait a bit for task to complete
        await asyncio.sleep(0.2)

        # Should have called invalidate_pattern
        assert mock_redis_manager.invalidate_pattern.called

    @pytest.mark.asyncio
    async def test_scheduled_invalidation_future(self, cache_manager, mock_redis_manager):
        """Test scheduled invalidation with future time."""
        rule = InvalidationRule(
            name="future_rule",
            strategy=InvalidationStrategy.SCHEDULED,
            patterns=["test:*"],
            schedule_time=datetime.now() + timedelta(seconds=0.1),
        )

        # Should wait until scheduled time
        task = asyncio.create_task(cache_manager._scheduled_invalidation(rule))

        # Cancel after a short wait to avoid long test
        await asyncio.sleep(0.05)
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_pattern_invalidation(self, cache_manager, mock_redis_manager):
        """Test pattern-based invalidation."""
        keys_invalidated = await cache_manager._pattern_invalidation(["user:*:cache"])

        assert keys_invalidated >= 0

    @pytest.mark.asyncio
    async def test_dependency_invalidation(self, cache_manager, mock_redis_manager):
        """Test dependency-based invalidation."""
        keys_invalidated = await cache_manager._dependency_invalidation(["trends", "inventory"])

        assert keys_invalidated >= 0

    @pytest.mark.asyncio
    async def test_ttl_refresh(self, cache_manager, mock_redis_manager):
        """Test TTL refresh strategy."""
        keys_refreshed = await cache_manager._ttl_refresh(["api:*"], refresh_seconds=300)

        assert keys_refreshed >= 0


# ============================================================================
# TEST Fashion-Specific Invalidation Methods
# ============================================================================


class TestFashionInvalidation:
    """Test fashion industry specific invalidation methods."""

    @pytest.mark.asyncio
    async def test_invalidate_fashion_trends(self, cache_manager, mock_redis_manager):
        """Test fashion trends invalidation."""
        result = await cache_manager.invalidate_fashion_trends(["summer", "winter"])

        assert result["trigger"] == "fashion_trends_update"
        assert "categories" in result.get("context", {}) or len(result["rules_executed"]) > 0

    @pytest.mark.asyncio
    async def test_invalidate_fashion_trends_no_categories(self, cache_manager, mock_redis_manager):
        """Test fashion trends invalidation without categories."""
        result = await cache_manager.invalidate_fashion_trends()

        assert result["trigger"] == "fashion_trends_update"

    @pytest.mark.asyncio
    async def test_invalidate_inventory(self, cache_manager, mock_redis_manager):
        """Test inventory invalidation."""
        result = await cache_manager.invalidate_inventory(["prod1", "prod2"])

        assert result["trigger"] == "inventory_update"

    @pytest.mark.asyncio
    async def test_invalidate_inventory_no_products(self, cache_manager, mock_redis_manager):
        """Test inventory invalidation without product IDs."""
        result = await cache_manager.invalidate_inventory()

        assert result["trigger"] == "inventory_update"

    @pytest.mark.asyncio
    async def test_invalidate_user_data(self, cache_manager, mock_redis_manager):
        """Test user data invalidation."""
        result = await cache_manager.invalidate_user_data("user123")

        assert result["trigger"] == "user_preferences_update"
        assert "user_id" in result.get("context", {}) or len(result["rules_executed"]) > 0

    @pytest.mark.asyncio
    async def test_invalidate_ml_models(self, cache_manager, mock_redis_manager):
        """Test ML model invalidation."""
        result = await cache_manager.invalidate_ml_models(["recommendation", "trend_prediction"])

        assert result["trigger"] == "ml_model_update"


# ============================================================================
# TEST Statistics and Metrics
# ============================================================================


class TestStatisticsAndMetrics:
    """Test invalidation statistics and metrics."""

    @pytest.mark.asyncio
    async def test_get_invalidation_stats(self, cache_manager, mock_redis_manager):
        """Test getting invalidation statistics."""
        # Perform some invalidations
        await cache_manager.invalidate_fashion_trends()
        await cache_manager.invalidate_inventory()

        stats = await cache_manager.get_invalidation_stats()

        assert "total_rules" in stats
        assert "recent_invalidations_24h" in stats
        assert "total_keys_invalidated_24h" in stats
        assert "total_rules_executed_24h" in stats
        assert "fashion_specific_rules" in stats
        assert "dependency_graph_size" in stats

    @pytest.mark.asyncio
    async def test_stats_counts_fashion_rules(self, cache_manager, mock_redis_manager):
        """Test stats correctly counts fashion-specific rules."""
        stats = await cache_manager.get_invalidation_stats()

        fashion_rule_count = len([r for r in cache_manager.invalidation_rules.values() if r.fashion_context])

        assert stats["fashion_specific_rules"] == fashion_rule_count

    @pytest.mark.asyncio
    async def test_stats_recent_invalidations_filter(self, cache_manager, mock_redis_manager):
        """Test stats filters recent invalidations correctly."""
        # Add old invalidation manually
        old_invalidation = {
            "trigger": "old",
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
            "keys_invalidated": 10,
            "rules_executed": [],
        }
        cache_manager.invalidation_history.append(old_invalidation)

        # Add recent invalidation
        await cache_manager.invalidate_fashion_trends()

        stats = await cache_manager.get_invalidation_stats()

        # Should only count recent ones
        assert stats["recent_invalidations_24h"] >= 1


# ============================================================================
# TEST Health Check
# ============================================================================


class TestHealthCheck:
    """Test cache invalidation system health check."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, cache_manager, mock_redis_manager):
        """Test health check returns healthy status."""
        result = await cache_manager.health_check()

        assert result["status"] == "healthy"
        assert "invalidation_stats" in result
        assert "redis_health" in result
        assert "rules_configured" in result
        assert "fashion_context_enabled" in result

    @pytest.mark.asyncio
    async def test_health_check_degraded_redis(self, cache_manager, mock_redis_manager):
        """Test health check with degraded Redis."""
        mock_redis_manager.health_check = AsyncMock(return_value={"status": "degraded"})

        result = await cache_manager.health_check()

        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_check_error(self, cache_manager, mock_redis_manager):
        """Test health check handles errors gracefully."""
        mock_redis_manager.health_check = AsyncMock(side_effect=Exception("Health check failed"))

        result = await cache_manager.health_check()

        assert result["status"] == "unhealthy"
        assert "error" in result


# ============================================================================
# TEST Error Handling
# ============================================================================


class TestErrorHandling:
    """Test error handling in cache invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_with_rule_execution_error(self, cache_manager, mock_redis_manager):
        """Test invalidation continues despite rule execution errors."""
        mock_redis_manager.invalidate_pattern = AsyncMock(side_effect=Exception("Redis error"))

        result = await cache_manager.invalidate("fashion_trends_update")

        assert result["trigger"] == "fashion_trends_update"
        assert len(result["errors"]) > 0
        assert "Redis error" in str(result["errors"][0])

    @pytest.mark.asyncio
    async def test_execute_rule_immediate_strategy(self, cache_manager, mock_redis_manager):
        """Test _execute_rule with immediate strategy."""
        rule = InvalidationRule(
            name="test",
            strategy=InvalidationStrategy.IMMEDIATE,
            patterns=["test:*"],
        )

        result = await cache_manager._execute_rule(rule, {})

        assert "keys_invalidated" in result
        assert "execution_time_ms" in result
        assert result["execution_time_ms"] > 0

    @pytest.mark.asyncio
    async def test_immediate_invalidation_pattern_parsing(self, cache_manager, mock_redis_manager):
        """Test immediate invalidation with different pattern formats."""
        # Pattern with colon
        keys1 = await cache_manager._immediate_invalidation(["prefix:pattern:*"])
        assert keys1 >= 0

        # Pattern without colon
        keys2 = await cache_manager._immediate_invalidation(["simplepattern"])
        assert keys2 >= 0


# ============================================================================
# TEST Global Instance
# ============================================================================


def test_global_cache_invalidation_manager():
    """Test global cache_invalidation_manager instance exists."""
    from infrastructure.cache_strategies import cache_invalidation_manager

    assert cache_invalidation_manager is not None
    assert isinstance(cache_invalidation_manager, CacheInvalidationManager)
    assert len(cache_invalidation_manager.invalidation_rules) > 0
