"""Editorial Photography venture pipeline.

Builds a compiled LangGraph for the venture. The current graph runs a
single `initialize` node that stamps a venture-tagged status into state
— it compiles, runs, and round-trips state under `pytest`. Additional
nodes (prompt enrichment, vision audit, render dispatch, QC, retouch)
are added in follow-up sessions per the per-venture roadmap.
"""

from __future__ import annotations

from typing import cast

from skyyrose.elite_studio.ventures._base import (
    AgentBinding,
    PipelineResult,
    VentureManifest,
    VentureStatus,
)

from .agents import PHOTO_AGENTS
from .config import DEFAULT_CONFIG, PhotoVentureConfig
from .state import PhotoState

MANIFEST = VentureManifest(
    slug="photo",
    title="Editorial Photography",
    summary=(
        "Lifestyle and editorial photography direction layered on the "
        "Elite Studio image generation stack. Uses the project's "
        "PhotographyStandard catalog plus vision/generator/quality agents."
    ),
    status=VentureStatus.BETA,
    agent_bindings=PHOTO_AGENTS,
    default_models={
        "vision": DEFAULT_CONFIG.vision_model,
        "renderer": DEFAULT_CONFIG.generator_model,
        "quality": DEFAULT_CONFIG.quality_model,
    },
    notes=(
        "Photography standards live at skyyrose.elite_studio.fashion.photography.",
        "Pipeline graph: initialize → (nodes wired in follow-up).",
    ),
)


def _initialize_node(state: PhotoState) -> PhotoState:
    """Stamp venture identity + ready outputs/errors slots into state."""
    return cast(
        PhotoState,
        {
            "status": "initialized",
            "outputs": {**state.get("outputs", {}), "venture": MANIFEST.slug},
            "errors": list(state.get("errors", [])),
            "style": state.get("style", DEFAULT_CONFIG.default_style),
        },
    )


def build_pipeline(config: PhotoVentureConfig | None = None) -> object:
    """Construct and compile the venture's LangGraph.

    LangGraph is imported lazily so the surrounding `skyyrose.elite_studio.
    ventures.photo` package can be inspected (manifest, agents, config)
    even on a thin environment without langgraph installed. This matches
    the existing optional-import pattern in
    `skyyrose.elite_studio.creative.checkpointer`.
    """
    _ = config or DEFAULT_CONFIG  # reserved for future per-call overrides
    from langgraph.graph import END, START, StateGraph  # noqa: PLC0415

    graph: StateGraph = StateGraph(PhotoState)
    graph.add_node("initialize", _initialize_node)
    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", END)
    return graph.compile()


class PhotoPipeline:
    """Operator-facing wrapper around the compiled LangGraph."""

    manifest: VentureManifest = MANIFEST

    def __init__(self, config: PhotoVentureConfig | None = None) -> None:
        self.config: PhotoVentureConfig = config or DEFAULT_CONFIG
        self._graph: object | None = None

    def build(self) -> object:
        if self._graph is None:
            self._graph = build_pipeline(self.config)
        return self._graph

    def run_smoke(self, sku: str = "smoke-001") -> PipelineResult:
        graph = self.build()
        initial: PhotoState = cast(
            PhotoState,
            {"sku": sku, "inputs": {}, "outputs": {}, "status": "pending", "errors": []},
        )
        from ..._observability import langfuse_config

        final = graph.invoke(initial, config=langfuse_config())  # type: ignore[attr-defined]
        return PipelineResult(
            venture=MANIFEST.slug,
            status=str(final.get("status", "unknown")),
            nodes_executed=("initialize",),
            final_state=cast("PhotoState", final),
        )

    def list_agents(self) -> tuple[AgentBinding, ...]:
        return MANIFEST.agent_bindings
