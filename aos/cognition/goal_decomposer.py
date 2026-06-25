"""GoalDecomposer — rule-based goal-to-TaskGraph decomposer.

Three built-in domain templates cover product, marketing, and analytics goals.
Unknown goals fall back to a single-task default. LLM decomposition is additive
and can be wired in later without changing the rule-based path.
"""

from __future__ import annotations

from aos.cognition.types import TaskGraph, TaskNode
from aos.kernel.types import ProcessPriority

_PRODUCT_KEYWORDS = frozenset({"product", "catalog", "sku", "inventory", "listing"})
_MARKETING_KEYWORDS = frozenset({"market", "campaign", "social", "ads", "email", "promo"})
_ANALYTICS_KEYWORDS = frozenset({"analytics", "report", "metric", "data", "dashboard", "stats"})


class GoalDecomposer:
    """Decomposes a natural-language goal string into a TaskGraph.

    Domain is detected via keyword matching. Templates produce pre-wired DAGs
    with agent_type assignments that match the registered factory types.
    """

    def decompose(self, goal: str) -> TaskGraph:
        """Return a TaskGraph for the given goal.

        The returned graph is always acyclic and passes topological_batches().
        """
        domain = self._detect_domain(goal)
        nodes = self._build_template(domain, goal)
        return TaskGraph(goal=goal, nodes={n.id: n for n in nodes})

    def _detect_domain(self, goal: str) -> str:
        lower = goal.lower()
        if any(kw in lower for kw in _PRODUCT_KEYWORDS):
            return "product"
        if any(kw in lower for kw in _MARKETING_KEYWORDS):
            return "marketing"
        if any(kw in lower for kw in _ANALYTICS_KEYWORDS):
            return "analytics"
        return "default"

    def _build_template(self, domain: str, goal: str) -> list[TaskNode]:
        if domain == "product":
            return _product_template(goal)
        if domain == "marketing":
            return _marketing_template(goal)
        if domain == "analytics":
            return _analytics_template(goal)
        return _default_template(goal)


def _product_template(goal: str) -> list[TaskNode]:
    analyze = TaskNode(
        id="prod_analyze",
        agent_type="commerce_agent",
        prompt=f"Analyze the product catalog for: {goal}",
        priority=ProcessPriority.HIGH,
    )
    describe = TaskNode(
        id="prod_describe",
        agent_type="creative_agent",
        prompt=f"Create compelling product descriptions for: {goal}",
        deps=frozenset({"prod_analyze"}),
    )
    optimize = TaskNode(
        id="prod_optimize",
        agent_type="commerce_agent",
        prompt=f"Optimize product metadata for search and discovery: {goal}",
        deps=frozenset({"prod_describe"}),
    )
    return [analyze, describe, optimize]


def _marketing_template(goal: str) -> list[TaskNode]:
    research = TaskNode(
        id="mkt_research",
        agent_type="analytics_agent",
        prompt=f"Research target audience and competitive landscape for: {goal}",
        priority=ProcessPriority.HIGH,
    )
    plan = TaskNode(
        id="mkt_plan",
        agent_type="marketing_agent",
        prompt=f"Create campaign plan with messaging and channel strategy for: {goal}",
        deps=frozenset({"mkt_research"}),
    )
    execute = TaskNode(
        id="mkt_execute",
        agent_type="creative_agent",
        prompt=f"Generate content and creative assets for: {goal}",
        deps=frozenset({"mkt_plan"}),
    )
    report = TaskNode(
        id="mkt_report",
        agent_type="analytics_agent",
        prompt=f"Analyze campaign performance and generate results report for: {goal}",
        deps=frozenset({"mkt_execute"}),
    )
    return [research, plan, execute, report]


def _analytics_template(goal: str) -> list[TaskNode]:
    collect = TaskNode(
        id="ana_collect",
        agent_type="analytics_agent",
        prompt=f"Collect and aggregate data from all sources for: {goal}",
        priority=ProcessPriority.HIGH,
    )
    analyze = TaskNode(
        id="ana_analyze",
        agent_type="analytics_agent",
        prompt=f"Perform statistical analysis and surface insights for: {goal}",
        deps=frozenset({"ana_collect"}),
    )
    visualize = TaskNode(
        id="ana_visualize",
        agent_type="creative_agent",
        prompt=f"Create visualizations and summary report for: {goal}",
        deps=frozenset({"ana_analyze"}),
    )
    return [collect, analyze, visualize]


def _default_template(goal: str) -> list[TaskNode]:
    return [
        TaskNode(
            id="task_default",
            agent_type="operations_agent",
            prompt=goal,
        )
    ]
