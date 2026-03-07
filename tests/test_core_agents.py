"""Tests for the Core Agent hierarchy.

Covers:
- categorize_failure() mapping
- SelfHealingMixin (circuit breaker, health_check, learning journal)
- CoreAgent (register_sub_agent, delegate, execute_safe, to_portal_node)
- All 8 concrete core agents (inheritance, core_type, name, sub-agents)
- Keyword routing per core agent
- Orchestrator (route_task, route, escalation, budget, system_health, to_portal_graph)
- Factory (create_orchestrator, budget_limit, graceful degradation)
- Legacy re-exports from agents.core.base
"""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.core.base import (
    CircuitBreakerState,
    CoreAgent,
    CoreAgentType,
    Diagnosis,
    FailureCategory,
    HealResult,
    SelfHealingMixin,
    categorize_failure,
)
from agents.core.orchestrator import Orchestrator
from agents.errors import AgentError, ErrorCategory

# =============================================================================
# Test Helpers
# =============================================================================


class _StubCoreAgent(CoreAgent):
    """Minimal concrete core agent for testing."""

    core_type = CoreAgentType.COMMERCE
    name = "stub_core"
    description = "Stub for testing"

    async def execute(self, task: str, **kwargs) -> dict:
        return {"success": True, "task": task}


class _FailingCoreAgent(CoreAgent):
    """Core agent that always raises."""

    core_type = CoreAgentType.CONTENT
    name = "failing_core"

    async def execute(self, task: str, **kwargs) -> dict:
        raise RuntimeError("always fails")


def _import_core_agent(module_path: str, class_name: str):
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


# =============================================================================
# Core Agent Registry (same as factory.py)
# =============================================================================

_CORE_AGENTS = [
    ("agents.core.commerce.agent", "CommerceCoreAgent", CoreAgentType.COMMERCE, "commerce_core"),
    ("agents.core.content.agent", "ContentCoreAgent", CoreAgentType.CONTENT, "content_core"),
    ("agents.core.creative.agent", "CreativeCoreAgent", CoreAgentType.CREATIVE, "creative_core"),
    (
        "agents.core.marketing.agent",
        "MarketingCoreAgent",
        CoreAgentType.MARKETING,
        "marketing_core",
    ),
    (
        "agents.core.operations.agent",
        "OperationsCoreAgent",
        CoreAgentType.OPERATIONS,
        "operations_core",
    ),
    (
        "agents.core.analytics.agent",
        "AnalyticsCoreAgent",
        CoreAgentType.ANALYTICS,
        "analytics_core",
    ),
    ("agents.core.imagery.agent", "ImageryCoreAgent", CoreAgentType.IMAGERY, "imagery_core"),
    (
        "agents.core.web_builder.agent",
        "WebBuilderCoreAgent",
        CoreAgentType.WEB_BUILDER,
        "web_builder_core",
    ),
]


# =============================================================================
# TestCategorizeFailure
# =============================================================================


class TestCategorizeFailure:
    """categorize_failure() maps errors to the right FailureCategory."""

    def test_config_keyword(self):
        assert categorize_failure("missing config file") == FailureCategory.CONFIG

    def test_external_keyword(self):
        assert categorize_failure("connection refused on port 443") == FailureCategory.EXTERNAL

    def test_provider_down_keyword(self):
        assert categorize_failure("503 service unavailable") == FailureCategory.PROVIDER_DOWN

    def test_data_quality_keyword(self):
        assert categorize_failure("invalid data in field X") == FailureCategory.DATA_QUALITY

    def test_agent_error_mapping(self):
        err = AgentError("timeout", category=ErrorCategory.TIMEOUT)
        assert categorize_failure(err) == FailureCategory.EXTERNAL

    def test_unknown_defaults_to_code_bug(self):
        assert categorize_failure("something weird happened") == FailureCategory.CODE_BUG

    def test_wrong_approach_keyword(self):
        assert categorize_failure("needs architectural redesign") == FailureCategory.WRONG_APPROACH


# =============================================================================
# TestSelfHealingMixin
# =============================================================================


class TestSelfHealingMixin:
    """SelfHealingMixin: circuit breaker, health_check, learning journal."""

    def _make_mixin(self):
        m = SelfHealingMixin()
        m.name = "test_agent"
        m.core_type = CoreAgentType.COMMERCE
        m.__init_healing__()
        return m

    def test_initial_state_healthy(self):
        m = self._make_mixin()
        assert m.circuit_breaker_allows()
        status = m.health_check()
        assert status.healthy
        assert status.circuit_breaker == "closed"

    def test_record_failure_increments(self):
        m = self._make_mixin()
        m._record_failure()
        assert m._consecutive_failures == 1
        assert m._circuit_state == CircuitBreakerState.CLOSED

    def test_circuit_opens_after_threshold(self):
        m = self._make_mixin()
        for _ in range(m._circuit_breaker_threshold):
            m._record_failure()
        assert m._circuit_state == CircuitBreakerState.OPEN
        assert not m.circuit_breaker_allows()

    def test_record_success_resets_failures(self):
        m = self._make_mixin()
        m._record_failure()
        m._record_failure()
        m._record_success()
        assert m._consecutive_failures == 0
        assert m._last_success_time is not None

    def test_diagnose_produces_diagnosis(self):
        m = self._make_mixin()
        d = m.diagnose("connection refused")
        assert isinstance(d, Diagnosis)
        assert d.failure_category == FailureCategory.EXTERNAL

    @pytest.mark.asyncio
    async def test_heal_records_in_journal(self):
        m = self._make_mixin()
        d = m.diagnose("some code bug")

        async def _always_fail(diag):
            return HealResult(success=False, message="nope")

        result = await m.heal(d, fixer=_always_fail)
        assert not result.success
        assert result.escalation_needed
        assert len(m._heal_journal) == m._max_heal_attempts

    @pytest.mark.asyncio
    async def test_heal_success_on_first_attempt(self):
        m = self._make_mixin()
        d = m.diagnose("some issue")

        async def _always_succeed(diag):
            return HealResult(success=True, message="fixed")

        result = await m.heal(d, fixer=_always_succeed)
        assert result.success
        assert result.attempts == 1


# =============================================================================
# TestCoreAgentBase
# =============================================================================


class TestCoreAgentBase:
    """CoreAgent: register_sub_agent, delegate, execute_safe, to_portal_node."""

    def test_register_sub_agent(self):
        agent = _StubCoreAgent()
        mock_sub = MagicMock()
        agent.register_sub_agent("test_sub", mock_sub)
        assert "test_sub" in agent.get_sub_agents()

    @pytest.mark.asyncio
    async def test_delegate_success(self):
        agent = _StubCoreAgent()
        mock_sub = AsyncMock()
        mock_sub.execute = AsyncMock(return_value={"success": True})
        agent.register_sub_agent("sub1", mock_sub)
        result = await agent.delegate("sub1", "do something")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_delegate_unknown_sub_agent_raises(self):
        agent = _StubCoreAgent()
        with pytest.raises(AgentError):
            await agent.delegate("nonexistent", "task")

    @pytest.mark.asyncio
    async def test_execute_safe_success(self):
        agent = _StubCoreAgent()
        result = await agent.execute_safe("do something")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_execute_safe_failure_triggers_healing(self):
        agent = _FailingCoreAgent()
        result = await agent.execute_safe("trigger failure")
        assert not result["success"]
        assert result.get("heal_attempted")
        assert result.get("escalation_needed")

    def test_to_portal_node(self):
        agent = _StubCoreAgent()
        agent.register_sub_agent("sub1", MagicMock())
        node = agent.to_portal_node()
        assert node["id"] == "stub_core"
        assert node["type"] == "commerce"
        assert "sub_agents" in node
        assert len(node["sub_agents"]) == 1


# =============================================================================
# TestConcreteCoreAgents (parametrized across all 8)
# =============================================================================


class TestConcreteCoreAgents:
    """Every concrete core agent must inherit CoreAgent and have correct metadata."""

    @pytest.mark.parametrize(
        "module_path,class_name,expected_type,expected_name",
        _CORE_AGENTS,
    )
    def test_inherits_from_core_agent(self, module_path, class_name, expected_type, expected_name):
        cls = _import_core_agent(module_path, class_name)
        assert issubclass(cls, CoreAgent), f"{class_name} must inherit CoreAgent"

    @pytest.mark.parametrize(
        "module_path,class_name,expected_type,expected_name",
        _CORE_AGENTS,
    )
    def test_correct_core_type(self, module_path, class_name, expected_type, expected_name):
        cls = _import_core_agent(module_path, class_name)
        assert cls.core_type == expected_type

    @pytest.mark.parametrize(
        "module_path,class_name,expected_type,expected_name",
        _CORE_AGENTS,
    )
    def test_correct_name(self, module_path, class_name, expected_type, expected_name):
        cls = _import_core_agent(module_path, class_name)
        assert cls.name == expected_name

    @pytest.mark.parametrize(
        "module_path,class_name,expected_type,expected_name",
        _CORE_AGENTS,
    )
    def test_instantiation_with_correlation_id(
        self, module_path, class_name, expected_type, expected_name
    ):
        cls = _import_core_agent(module_path, class_name)
        instance = cls(correlation_id="test-123")
        assert instance.correlation_id == "test-123"
        assert isinstance(instance, SelfHealingMixin)


# =============================================================================
# TestCoreAgentKeywordRouting
# =============================================================================


class TestCoreAgentKeywordRouting:
    """Orchestrator routes keywords to the correct core agent type."""

    def _make_orchestrator(self):
        return Orchestrator()

    @pytest.mark.parametrize(
        "task,expected_type",
        [
            ("Update product inventory levels", CoreAgentType.COMMERCE),
            ("Write blog copy for the collection", CoreAgentType.CONTENT),
            ("Create brand logo design", CoreAgentType.CREATIVE),
            ("Launch email campaign for audience", CoreAgentType.MARKETING),
            ("Deploy build to production", CoreAgentType.OPERATIONS),
            ("Generate analytics report on conversion", CoreAgentType.ANALYTICS),
            ("Render 3d model of the vton asset", CoreAgentType.IMAGERY),
            ("Update wordpress theme template", CoreAgentType.WEB_BUILDER),
        ],
    )
    def test_keyword_routing(self, task, expected_type):
        o = self._make_orchestrator()
        assert o.route_task(task) == expected_type

    def test_unknown_task_defaults_to_operations(self):
        o = self._make_orchestrator()
        assert o.route_task("something completely unrelated xyz") == CoreAgentType.OPERATIONS


# =============================================================================
# TestOrchestrator
# =============================================================================


class TestOrchestrator:
    """Orchestrator: route, escalation, budget, system_health, to_portal_graph."""

    def _make_wired_orchestrator(self):
        o = Orchestrator()
        agent = _StubCoreAgent()
        o.register_core_agent(agent)
        return o

    def test_register_and_get_core_agent(self):
        o = self._make_wired_orchestrator()
        agent = o.get_core_agent(CoreAgentType.COMMERCE)
        assert agent is not None
        assert agent.name == "stub_core"

    def test_get_missing_agent_returns_none(self):
        o = Orchestrator()
        assert o.get_core_agent(CoreAgentType.ANALYTICS) is None

    @pytest.mark.asyncio
    async def test_route_success(self):
        o = self._make_wired_orchestrator()
        result = await o.route("Check product inventory")
        assert result.get("success") or result.get("task")

    @pytest.mark.asyncio
    async def test_route_budget_exceeded(self):
        o = self._make_wired_orchestrator()
        o.set_budget_limit(10.0)
        o._budget_spent_usd = 15.0
        result = await o.route("Check product inventory")
        assert not result["success"]
        assert "Budget limit" in result["error"]

    @pytest.mark.asyncio
    async def test_route_escalation_on_failure(self):
        o = Orchestrator()
        failing = _FailingCoreAgent()
        failing.core_type = CoreAgentType.CONTENT
        o.register_core_agent(failing)
        result = await o.route("Write blog copy description")
        assert result.get("requires_human_approval") or result.get("escalation_needed")

    def test_system_health_report(self):
        o = self._make_wired_orchestrator()
        health = o.system_health()
        assert "orchestrator" in health
        assert "agents" in health
        assert "summary" in health
        assert health["summary"]["total_agents"] == 1

    def test_to_portal_graph(self):
        o = self._make_wired_orchestrator()
        graph = o.to_portal_graph()
        assert "nodes" in graph
        assert "connections" in graph
        node_ids = [n["id"] for n in graph["nodes"]]
        assert "orchestrator" in node_ids


# =============================================================================
# TestOrchestratorFactory
# =============================================================================


class TestOrchestratorFactory:
    """Factory: create_orchestrator wires up all 8 agents."""

    def test_import_factory(self):
        from agents.core.factory import create_orchestrator

        assert callable(create_orchestrator)

    def test_create_orchestrator_returns_orchestrator(self):
        from agents.core.factory import create_orchestrator

        o = create_orchestrator()
        assert isinstance(o, Orchestrator)

    def test_create_orchestrator_registers_agents(self):
        from agents.core.factory import create_orchestrator

        o = create_orchestrator()
        assert len(o._core_agents) == 8

    def test_create_orchestrator_with_budget(self):
        from agents.core.factory import create_orchestrator

        o = create_orchestrator(budget_limit_usd=100.0)
        assert o._budget_limit_usd == 100.0

    def test_create_orchestrator_with_correlation_id(self):
        from agents.core.factory import create_orchestrator

        o = create_orchestrator(correlation_id="test-corr-456")
        assert o.correlation_id == "test-corr-456"

    def test_graceful_degradation(self):
        """If a core agent fails to import, others still register."""

        with patch.dict(
            "sys.modules",
            {"agents.core.commerce.agent": None},
        ):
            # Force reimport to hit the patched module
            import agents.core.factory as factory_mod

            original_registry = factory_mod._CORE_AGENT_REGISTRY
            # Replace with a bad first entry
            factory_mod._CORE_AGENT_REGISTRY = [
                ("nonexistent.module", "BadAgent"),
                *original_registry[1:],
            ]
            try:
                o = factory_mod.create_orchestrator()
                # Should have 7 of 8 (one failed)
                assert len(o._core_agents) == 7
            finally:
                factory_mod._CORE_AGENT_REGISTRY = original_registry


# =============================================================================
# TestLegacyReExports
# =============================================================================


class TestLegacyReExports:
    """All 9 legacy symbols should be importable from agents.core.base."""

    @pytest.mark.parametrize(
        "symbol_name",
        [
            "AgentCapability",
            "LLMCategory",
            "AgentStatus",
            "AgentConfig",
            "PlanStep",
            "RetrievalContext",
            "ExecutionResult",
            "ValidationResult",
            "SuperAgent",
        ],
    )
    def test_legacy_symbol_importable(self, symbol_name):
        from agents.core import base as core_base

        assert hasattr(core_base, symbol_name), f"{symbol_name} not found in agents.core.base"

    def test_legacy_symbols_match_originals(self):
        """Re-exported symbols must be the same objects as in base_legacy."""
        from agents.base_legacy import AgentCapability as OrigCap
        from agents.base_legacy import SuperAgent as OrigSuper
        from agents.core.base import AgentCapability as ReexCap
        from agents.core.base import SuperAgent as ReexSuper

        assert OrigCap is ReexCap
        assert OrigSuper is ReexSuper
