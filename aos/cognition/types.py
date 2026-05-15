"""Cognition types — task graph, plan steps, and decomposed plans."""

from __future__ import annotations

import uuid
from collections import deque
from typing import Any

from pydantic import BaseModel, Field

from aos.kernel.types import ProcessPriority


class TaskNode(BaseModel):
    """Single unit of work in a TaskGraph. Immutable after construction."""

    model_config = {"frozen": True}

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    agent_type: str
    prompt: str
    deps: frozenset[str] = frozenset()
    priority: ProcessPriority = ProcessPriority.NORMAL
    budget_usd: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskGraph(BaseModel):
    """DAG of TaskNodes. Provides topological batch ordering via Kahn's algorithm."""

    model_config = {"frozen": True}

    goal: str
    nodes: dict[str, TaskNode]

    def topological_batches(self) -> list[list[TaskNode]]:
        """Return nodes grouped into parallel-safe wavefronts.

        Raises ValueError on unknown dependency references or cycles.
        """
        # Validate all deps reference known nodes
        for node in self.nodes.values():
            for dep in node.deps:
                if dep not in self.nodes:
                    msg = f"Node {node.id!r} depends on unknown node {dep!r}"
                    raise ValueError(msg)

        # Build in-degree and reverse adjacency
        in_degree: dict[str, int] = {nid: 0 for nid in self.nodes}
        dependents: dict[str, list[str]] = {nid: [] for nid in self.nodes}
        for nid, node in self.nodes.items():
            for dep in node.deps:
                in_degree[nid] += 1
                dependents[dep].append(nid)

        queue: deque[str] = deque(nid for nid, deg in in_degree.items() if deg == 0)
        batches: list[list[TaskNode]] = []
        visited = 0

        while queue:
            batch_size = len(queue)
            batch_ids = [queue.popleft() for _ in range(batch_size)]
            batches.append([self.nodes[nid] for nid in batch_ids])
            visited += batch_size
            for nid in batch_ids:
                for dependent_id in dependents[nid]:
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        queue.append(dependent_id)

        if visited != len(self.nodes):
            msg = "TaskGraph contains a cycle — cannot produce topological ordering"
            raise ValueError(msg)
        return batches


class PlanStep(BaseModel):
    """One wavefront in a DecomposedPlan — nodes that can execute in parallel."""

    model_config = {"frozen": True}

    batch_index: int
    nodes: tuple[TaskNode, ...]


class DecomposedPlan(BaseModel):
    """Ordered list of PlanSteps derived from a TaskGraph."""

    model_config = {"frozen": True}

    goal: str
    steps: tuple[PlanStep, ...]

    @property
    def total_nodes(self) -> int:
        """Total count of nodes across all steps."""
        return sum(len(step.nodes) for step in self.steps)
