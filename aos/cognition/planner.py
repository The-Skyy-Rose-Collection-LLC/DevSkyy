"""Planner — converts a TaskGraph into an ordered DecomposedPlan."""

from __future__ import annotations

from aos.cognition.types import DecomposedPlan, PlanStep, TaskGraph


class Planner:
    """Converts a TaskGraph into a DecomposedPlan using topological wavefront ordering.

    Each PlanStep contains nodes that have no unresolved dependencies and can
    execute in parallel. Steps must execute sequentially to satisfy dep ordering.
    """

    def plan(self, graph: TaskGraph) -> DecomposedPlan:
        """Produce an executable plan from a TaskGraph.

        Raises ValueError if the graph contains a cycle or references unknown deps.
        """
        batches = graph.topological_batches()
        steps = tuple(
            PlanStep(batch_index=i, nodes=tuple(batch)) for i, batch in enumerate(batches)
        )
        return DecomposedPlan(goal=graph.goal, steps=steps)
