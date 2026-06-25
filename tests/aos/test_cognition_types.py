"""Tests for TaskGraph, TaskNode, PlanStep, and DecomposedPlan."""

from __future__ import annotations

import pytest

from aos.cognition.types import DecomposedPlan, PlanStep, TaskGraph, TaskNode
from aos.kernel.types import ProcessPriority


def _node(id: str, deps: frozenset[str] = frozenset()) -> TaskNode:
    return TaskNode(id=id, agent_type="test_agent", prompt=f"prompt for {id}", deps=deps)


class TestTopologicalBatches:
    def test_single_node(self):
        graph = TaskGraph(goal="g", nodes={"a": _node("a")})
        batches = graph.topological_batches()
        assert len(batches) == 1
        assert batches[0][0].id == "a"

    def test_linear_chain(self):
        a = _node("a")
        b = _node("b", deps=frozenset({"a"}))
        c = _node("c", deps=frozenset({"b"}))
        graph = TaskGraph(goal="g", nodes={"a": a, "b": b, "c": c})
        batches = graph.topological_batches()
        assert len(batches) == 3
        assert batches[0][0].id == "a"
        assert batches[1][0].id == "b"
        assert batches[2][0].id == "c"

    def test_parallel_roots(self):
        a = _node("a")
        b = _node("b")
        c = _node("c", deps=frozenset({"a", "b"}))
        graph = TaskGraph(goal="g", nodes={"a": a, "b": b, "c": c})
        batches = graph.topological_batches()
        assert len(batches) == 2
        first_ids = {n.id for n in batches[0]}
        assert first_ids == {"a", "b"}
        assert batches[1][0].id == "c"

    def test_diamond_dependency(self):
        a = _node("a")
        b = _node("b", deps=frozenset({"a"}))
        c = _node("c", deps=frozenset({"a"}))
        d = _node("d", deps=frozenset({"b", "c"}))
        graph = TaskGraph(goal="g", nodes={"a": a, "b": b, "c": c, "d": d})
        batches = graph.topological_batches()
        assert len(batches) == 3
        assert batches[0][0].id == "a"
        assert {n.id for n in batches[1]} == {"b", "c"}
        assert batches[2][0].id == "d"

    def test_cycle_raises(self):
        a = _node("a", deps=frozenset({"b"}))
        b = _node("b", deps=frozenset({"a"}))
        graph = TaskGraph(goal="g", nodes={"a": a, "b": b})
        with pytest.raises(ValueError, match="cycle"):
            graph.topological_batches()

    def test_unknown_dep_raises(self):
        a = _node("a", deps=frozenset({"missing"}))
        graph = TaskGraph(goal="g", nodes={"a": a})
        with pytest.raises(ValueError, match="unknown node"):
            graph.topological_batches()

    def test_empty_graph(self):
        graph = TaskGraph(goal="empty", nodes={})
        assert graph.topological_batches() == []


class TestTaskNode:
    def test_default_priority(self):
        node = _node("x")
        assert node.priority == ProcessPriority.NORMAL

    def test_explicit_priority(self):
        node = TaskNode(id="y", agent_type="a", prompt="p", priority=ProcessPriority.HIGH)
        assert node.priority == ProcessPriority.HIGH

    def test_frozen(self):
        node = _node("z")
        with pytest.raises(Exception):
            node.id = "mutated"  # type: ignore[misc]


class TestDecomposedPlan:
    def test_total_nodes(self):
        a = _node("a")
        b = _node("b")
        c = _node("c")
        plan = DecomposedPlan(
            goal="g",
            steps=(
                PlanStep(batch_index=0, nodes=(a, b)),
                PlanStep(batch_index=1, nodes=(c,)),
            ),
        )
        assert plan.total_nodes == 3

    def test_empty_plan(self):
        plan = DecomposedPlan(goal="nothing", steps=())
        assert plan.total_nodes == 0
