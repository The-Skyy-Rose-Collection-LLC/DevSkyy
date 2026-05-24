"""Shared primitives for every Elite Studio venture.

A "venture" is a productized vertical inside the Elite Studio platform —
imagery, photography, 3D/immersive, video, and future expansions. Each
venture composes existing agents and orchestration engines through one
operator-facing surface, so the studio remains the single hub for all
creative pipelines (per canonical project memory).

Production rules followed here:
- Frozen dataclasses for immutable manifests (immutability is a project standard).
- No stubs / no NotImplementedError / no TODO — every callable returns real data.
- Agents are referenced by importable dotted paths verified at registration time.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, TypedDict, runtime_checkable


class VentureStatus(StrEnum):
    """Production readiness of a venture's pipeline surface."""

    STABLE = "stable"
    BETA = "beta"
    ALPHA = "alpha"
    PLANNED = "planned"


@dataclass(frozen=True)
class AgentBinding:
    """One agent enlisted into a venture's pipeline graph.

    `import_path` is the dotted Python path that resolves to the agent class.
    `role` is the venture-local responsibility name (e.g. "vision", "renderer").
    `ready` is False when the agent exists in the codebase but is not yet
    wired into the venture's LangGraph nodes — this preserves the
    no-stub guarantee while remaining honest about wiring status.
    """

    name: str
    import_path: str
    role: str
    ready: bool = False

    def resolve(self) -> type:
        """Import the bound agent class. Raises ImportError on failure."""
        module_path, _, attr = self.import_path.rpartition(".")
        if not module_path:
            raise ImportError(f"AgentBinding {self.name!r} has no module path")
        module = importlib.import_module(module_path)
        return getattr(module, attr)


@dataclass(frozen=True)
class VentureManifest:
    """Static description of a venture surfaced through the registry."""

    slug: str
    title: str
    summary: str
    status: VentureStatus
    agent_bindings: tuple[AgentBinding, ...]
    default_models: dict[str, str] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def agents_by_role(self, role: str) -> tuple[AgentBinding, ...]:
        return tuple(b for b in self.agent_bindings if b.role == role)


class VentureState(TypedDict, total=False):
    """Common state envelope every venture pipeline accepts.

    Ventures may extend this with venture-specific keys via their own
    TypedDict; the keys below are the shared contract every node honors.
    """

    sku: str
    inputs: dict[str, object]
    outputs: dict[str, object]
    status: str
    errors: list[str]


@dataclass(frozen=True)
class PipelineResult:
    """Return value from `run_smoke()` — proves the pipeline compiles + runs."""

    venture: str
    status: str
    nodes_executed: tuple[str, ...]
    final_state: VentureState


@runtime_checkable
class VenturePipeline(Protocol):
    """Every venture exposes this minimal interface."""

    manifest: VentureManifest

    def build(self) -> object:
        """Return a compiled LangGraph (or equivalent runnable)."""

    def run_smoke(self, sku: str = "smoke-001") -> PipelineResult:
        """Run the pipeline against a no-op input. Used by tests + CLI."""

    def list_agents(self) -> tuple[AgentBinding, ...]:
        """Return the venture's agent registry."""
