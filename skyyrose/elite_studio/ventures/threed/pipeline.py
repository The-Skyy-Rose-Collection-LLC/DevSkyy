"""3D / Immersive venture pipeline.

Builds a compiled LangGraph for the venture. The current graph runs a
single `initialize` node that stamps a venture-tagged status into state.
Follow-up sessions add: source-image selection, tournament dispatch,
mesh scoring, winner selection, polish, and asset upload nodes.
"""

from __future__ import annotations

from typing import cast

from skyyrose.elite_studio.ventures._base import (
    AgentBinding,
    PipelineResult,
    VentureManifest,
    VentureStatus,
)

from .agents import THREED_AGENTS
from .config import DEFAULT_CONFIG, ThreeDVentureConfig
from .state import ThreeDState

MANIFEST = VentureManifest(
    slug="threed",
    title="3D / Immersive",
    summary=(
        "3D model generation pipeline composing Tripo, Meshy, TRELLIS "
        "via the round-table tournament orchestrator. Feeds the "
        "/experience-* immersive pages and the WordPress product gallery."
    ),
    status=VentureStatus.BETA,
    agent_bindings=THREED_AGENTS,
    default_models={
        "tournament": "orchestration.threed_round_table",
        "polish": "skyyrose.elite_studio.agents.three_d_agent",
    },
    notes=(
        "Tournament: orchestration/threed_round_table.py.",
        f"Default providers: {', '.join(DEFAULT_CONFIG.providers)}.",
        "Pipeline graph: initialize → (tournament + scoring wired in follow-up).",
    ),
)


def _initialize_node(state: ThreeDState) -> ThreeDState:
    """Stamp venture identity + ready outputs/errors slots into state."""
    return cast(
        ThreeDState,
        {
            "status": "initialized",
            "outputs": {**state.get("outputs", {}), "venture": MANIFEST.slug},
            "errors": list(state.get("errors", [])),
            "polycount": state.get("polycount", DEFAULT_CONFIG.default_polycount),
            "texture_size": state.get("texture_size", DEFAULT_CONFIG.default_texture_size),
        },
    )


def build_pipeline(config: ThreeDVentureConfig | None = None) -> object:
    """Construct and compile the venture's LangGraph.

    LangGraph is imported lazily so the surrounding package can be
    introspected without the dep present.
    """
    _ = config or DEFAULT_CONFIG
    from langgraph.graph import END, START, StateGraph  # noqa: PLC0415

    graph: StateGraph = StateGraph(ThreeDState)
    graph.add_node("initialize", _initialize_node)
    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", END)
    return graph.compile()


class ThreeDPipeline:
    """Operator-facing wrapper around the compiled LangGraph."""

    manifest: VentureManifest = MANIFEST

    def __init__(self, config: ThreeDVentureConfig | None = None) -> None:
        self.config: ThreeDVentureConfig = config or DEFAULT_CONFIG
        self._graph: object | None = None

    def build(self) -> object:
        if self._graph is None:
            self._graph = build_pipeline(self.config)
        return self._graph

    def run_smoke(self, sku: str = "smoke-001") -> PipelineResult:
        graph = self.build()
        initial: ThreeDState = cast(
            ThreeDState,
            {"sku": sku, "inputs": {}, "outputs": {}, "status": "pending", "errors": []},
        )
        final = graph.invoke(initial)  # type: ignore[attr-defined]
        return PipelineResult(
            venture=MANIFEST.slug,
            status=str(final.get("status", "unknown")),
            nodes_executed=("initialize",),
            final_state=cast("ThreeDState", final),
        )

    def list_agents(self) -> tuple[AgentBinding, ...]:
        return MANIFEST.agent_bindings
