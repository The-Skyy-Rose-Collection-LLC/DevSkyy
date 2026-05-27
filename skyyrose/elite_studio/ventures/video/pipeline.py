"""Video & Animation venture pipeline.

Builds a compiled LangGraph for the venture. Video is the alpha
surface — the current graph runs a single `initialize` node that
stamps a venture-tagged status into state. Follow-up sessions add:
storyboard, scene generation, animation, audio bed, encoding,
and upload nodes.
"""

from __future__ import annotations

from typing import cast

from skyyrose.elite_studio.ventures._base import (
    AgentBinding,
    PipelineResult,
    VentureManifest,
    VentureStatus,
)

from .agents import VIDEO_AGENTS
from .config import DEFAULT_CONFIG, VideoVentureConfig
from .state import VideoState

MANIFEST = VentureManifest(
    slug="video",
    title="Video & Animation",
    summary=(
        "Animated product video pipeline composing AnigenAgent and the "
        "try-on video provider. Targets vertical (9:16) social-ready "
        "output by default. Least-wired venture — alpha status."
    ),
    status=VentureStatus.ALPHA,
    agent_bindings=VIDEO_AGENTS,
    default_models={
        "animation": "agents.anigen_agent",
        "tryon_video": "skyyrose.elite_studio.agents.tryon_agent",
    },
    notes=(
        "Default resolution: 1080x1920 (9:16 vertical).",
        f"Default duration: {DEFAULT_CONFIG.default_duration_seconds}s "
        f"at {DEFAULT_CONFIG.default_fps} fps.",
        "Pipeline graph: initialize → (scene + animation wired in follow-up).",
    ),
)


def _initialize_node(state: VideoState) -> VideoState:
    """Stamp venture identity + ready outputs/errors slots into state."""
    return cast(
        VideoState,
        {
            "status": "initialized",
            "outputs": {**state.get("outputs", {}), "venture": MANIFEST.slug},
            "errors": list(state.get("errors", [])),
            "duration_seconds": state.get(
                "duration_seconds", DEFAULT_CONFIG.default_duration_seconds
            ),
            "fps": state.get("fps", DEFAULT_CONFIG.default_fps),
            "resolution": state.get("resolution", DEFAULT_CONFIG.default_resolution),
        },
    )


def build_pipeline(config: VideoVentureConfig | None = None) -> object:
    """Construct and compile the venture's LangGraph.

    LangGraph is imported lazily so the surrounding package can be
    introspected without the dep present.
    """
    _ = config or DEFAULT_CONFIG
    from langgraph.graph import END, START, StateGraph  # noqa: PLC0415

    graph: StateGraph = StateGraph(VideoState)
    graph.add_node("initialize", _initialize_node)
    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", END)
    return graph.compile()


class VideoPipeline:
    """Operator-facing wrapper around the compiled LangGraph."""

    manifest: VentureManifest = MANIFEST

    def __init__(self, config: VideoVentureConfig | None = None) -> None:
        self.config: VideoVentureConfig = config or DEFAULT_CONFIG
        self._graph: object | None = None

    def build(self) -> object:
        if self._graph is None:
            self._graph = build_pipeline(self.config)
        return self._graph

    def run_smoke(self, sku: str = "smoke-001") -> PipelineResult:
        graph = self.build()
        initial: VideoState = cast(
            VideoState,
            {"sku": sku, "inputs": {}, "outputs": {}, "status": "pending", "errors": []},
        )
        from ..._observability import langfuse_config

        final = graph.invoke(initial, config=langfuse_config())  # type: ignore[attr-defined]
        return PipelineResult(
            venture=MANIFEST.slug,
            status=str(final.get("status", "unknown")),
            nodes_executed=("initialize",),
            final_state=cast("VideoState", final),
        )

    def list_agents(self) -> tuple[AgentBinding, ...]:
        return MANIFEST.agent_bindings
