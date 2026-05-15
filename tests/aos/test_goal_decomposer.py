"""Tests for GoalDecomposer — domain detection and valid TaskGraph output."""

from __future__ import annotations

import pytest

from aos.cognition.goal_decomposer import GoalDecomposer
from aos.cognition.types import TaskGraph
from aos.kernel.types import ProcessPriority


class TestDomainDetection:
    def setup_method(self):
        self.decomposer = GoalDecomposer()

    def _decompose(self, goal: str) -> TaskGraph:
        return self.decomposer.decompose(goal)

    def test_product_keyword_detected(self):
        graph = self._decompose("Optimize the product catalog for Black Rose collection")
        node_ids = set(graph.nodes)
        assert "prod_analyze" in node_ids
        assert "prod_describe" in node_ids
        assert "prod_optimize" in node_ids

    def test_sku_keyword_triggers_product(self):
        graph = self._decompose("Update SKU metadata for new inventory")
        assert "prod_analyze" in graph.nodes

    def test_marketing_keyword_detected(self):
        graph = self._decompose("Plan a social media campaign for launch")
        node_ids = set(graph.nodes)
        assert "mkt_research" in node_ids
        assert "mkt_plan" in node_ids
        assert "mkt_execute" in node_ids
        assert "mkt_report" in node_ids

    def test_analytics_keyword_detected(self):
        graph = self._decompose("Generate a dashboard report of sales metrics")
        node_ids = set(graph.nodes)
        assert "ana_collect" in node_ids
        assert "ana_analyze" in node_ids
        assert "ana_visualize" in node_ids

    def test_default_fallback(self):
        graph = self._decompose("Do something completely unrelated")
        assert "task_default" in graph.nodes
        assert len(graph.nodes) == 1

    def test_case_insensitive_detection(self):
        graph = self._decompose("PRODUCT optimization for SKU catalog")
        assert "prod_analyze" in graph.nodes


class TestTaskGraphValidity:
    def setup_method(self):
        self.decomposer = GoalDecomposer()

    def test_product_graph_is_acyclic(self):
        graph = self.decomposer.decompose("optimize catalog")
        batches = graph.topological_batches()
        assert len(batches) == 3

    def test_marketing_graph_is_acyclic(self):
        graph = self.decomposer.decompose("create email campaign")
        batches = graph.topological_batches()
        assert len(batches) == 4

    def test_analytics_graph_is_acyclic(self):
        graph = self.decomposer.decompose("build analytics dashboard")
        batches = graph.topological_batches()
        assert len(batches) == 3

    def test_product_first_node_has_high_priority(self):
        graph = self.decomposer.decompose("optimize product catalog")
        assert graph.nodes["prod_analyze"].priority == ProcessPriority.HIGH

    def test_marketing_first_node_has_high_priority(self):
        graph = self.decomposer.decompose("run email campaign")
        assert graph.nodes["mkt_research"].priority == ProcessPriority.HIGH

    def test_goal_preserved_in_graph(self):
        goal = "Build a dashboard for revenue analytics"
        graph = self.decomposer.decompose(goal)
        assert graph.goal == goal

    def test_all_deps_reference_known_nodes(self):
        for goal in [
            "optimize product catalog",
            "launch social media campaign",
            "generate analytics report",
            "do something unknown",
        ]:
            graph = self.decomposer.decompose(goal)
            for node in graph.nodes.values():
                for dep in node.deps:
                    assert dep in graph.nodes, f"Unknown dep {dep!r} in graph for {goal!r}"
