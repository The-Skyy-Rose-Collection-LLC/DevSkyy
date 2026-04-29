"""
DevSkyy LangGraph Integration
=============================

Thin adapter over the real `langgraph` library.

Historically this module contained a parallel reimplementation of
LangGraph (`WorkflowGraph`, `WorkflowManager`, `AgentNode`, etc.). That
custom engine was never used in production — only the data types
(`WorkflowState`, `WorkflowStatus`) escaped, as base classes for the
workflows in `devskyy_workflows/`.

This module now:
    1. Re-exports the canonical `langgraph` primitives so all DevSkyy
       code imports from one place (`StateGraph`, `END`, `START`,
       `add_messages`).
    2. Keeps the data types (`WorkflowState`, `WorkflowStatus`,
       `NodeType`, `EdgeType`, `WorkflowEdge`, `ConditionalEdge`) that
       describe workflow shape and status — used by
       `devskyy_workflows/*` and any future graph wiring.

The canonical integration lives at
`skyyrose/elite_studio/creative/router.py` (Creative Operations Hub).

References:
    - LangGraph: https://langchain-ai.github.io/langgraph/
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, TypeVar

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

S = TypeVar("S", bound="WorkflowState")


# =============================================================================
# Enums (data types)
# =============================================================================


class NodeType(StrEnum):
    """Node types in workflow."""

    AGENT = "agent"
    TOOL = "tool"
    ROUTER = "router"
    AGGREGATOR = "aggregator"
    CHECKPOINT = "checkpoint"
    END = "end"


class EdgeType(StrEnum):
    """Edge types."""

    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"


class WorkflowStatus(StrEnum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# State (data types)
# =============================================================================


class WorkflowState(BaseModel):
    """Base workflow state.

    All workflow state classes inherit from this. It carries enough
    bookkeeping (id, status, history, errors, messages) to be useful as
    a stand-alone in-process state container, while remaining
    serializable for LangGraph checkpointing.
    """

    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_node: str | None = None

    started_at: str | None = None
    completed_at: str | None = None
    node_history: list[str] = []

    inputs: dict[str, Any] = {}
    outputs: dict[str, Any] = {}
    context: dict[str, Any] = {}

    errors: list[dict[str, Any]] = []
    retry_count: int = 0
    max_retries: int = 3

    messages: list[dict[str, Any]] = []

    def add_message(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append a message to state."""
        self.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": metadata or {},
            }
        )

    def get_last_output(self, node_name: str | None = None) -> Any:
        """Return the output from a specific node, or the most recent one."""
        if node_name and node_name in self.outputs:
            return self.outputs[node_name]
        if self.node_history:
            last_node = self.node_history[-1]
            return self.outputs.get(last_node)
        return None

    def record_error(
        self,
        node: str,
        error: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record an error in state."""
        self.errors.append(
            {
                "node": node,
                "error": error,
                "details": details or {},
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    def to_checkpoint(self) -> dict[str, Any]:
        """Serialize for persistence (legacy custom checkpointing).

        For new code, prefer LangGraph's built-in checkpointers
        (e.g. `AsyncPostgresSaver`) which serialize the whole state
        automatically — no custom shape is needed.
        """
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "current_node": self.current_node,
            "node_history": self.node_history,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "context": self.context,
            "errors": self.errors,
            "messages": self.messages,
            "checkpoint_time": datetime.now(UTC).isoformat(),
        }

    @classmethod
    def from_checkpoint(cls, data: dict[str, Any]) -> WorkflowState:
        """Restore from a `to_checkpoint()` payload."""
        data["status"] = WorkflowStatus(data.get("status", "pending"))
        return cls(**data)


# =============================================================================
# Edge descriptors (data types)
# =============================================================================


class WorkflowEdge(BaseModel):
    """Descriptor for an edge between two nodes.

    This is a passive data type — it documents intended graph topology.
    Actual edge wiring is done via `StateGraph.add_edge()` /
    `StateGraph.add_conditional_edges()` from the langgraph library
    (re-exported above).
    """

    source: str
    target: str
    edge_type: EdgeType = EdgeType.SEQUENTIAL
    condition: str | None = None

    def __hash__(self) -> int:
        return hash((self.source, self.target))


class ConditionalEdge(WorkflowEdge):
    """Descriptor for a conditional edge with multiple targets."""

    edge_type: EdgeType = EdgeType.CONDITIONAL
    conditions: dict[str, str] = {}  # target -> condition expression
    default_target: str | None = None


__all__ = [
    # langgraph re-exports — single source of truth for all DevSkyy code
    "StateGraph",
    "END",
    "START",
    "add_messages",
    # data types
    "NodeType",
    "EdgeType",
    "WorkflowStatus",
    "WorkflowState",
    "WorkflowEdge",
    "ConditionalEdge",
]
