"""Social Media venture pipeline.

A deep-wired LangGraph: the publisher node runs the real `SocialMediaAgent`
on every pass (free, template-based brand-voice generation), while the
graphics and strategy nodes are wired to `CreativeAgent` / `MarketingAgent`
but fire only behind explicit cost gates. The default path (every smoke
run and test) produces real posts without any paid or LLM call.

Graph: START → plan → generate_posts → compose_graphics → strategize → assemble → END
"""

from __future__ import annotations

import asyncio
import logging
from typing import cast

from skyyrose.elite_studio.ventures._base import (
    AgentBinding,
    PipelineResult,
    VentureManifest,
    VentureStatus,
)

from .agents import SOCIAL_AGENTS
from .config import DEFAULT_CONFIG, SUPPORTED_PLATFORMS, SocialVentureConfig
from .state import SocialState

logger = logging.getLogger(__name__)

MANIFEST = VentureManifest(
    slug="social",
    title="Social Media",
    summary=(
        "Brand-voice social content production layered on the Elite Studio "
        "agent stack. Live publisher (SocialMediaAgent) generates "
        "platform-optimized posts; CreativeAgent (graphics) and "
        "MarketingAgent (strategy) are wired but cost-gated."
    ),
    status=VentureStatus.BETA,
    agent_bindings=SOCIAL_AGENTS,
    default_models={
        "graphics": DEFAULT_CONFIG.graphics_model,
        "strategist": DEFAULT_CONFIG.strategist_model,
    },
    notes=(
        "Publisher is free + template-based; runs on every pass.",
        "Graphics/strategy fire only when generate_graphics/run_strategy flags are set.",
        "Skills library: .claude/skills/skyyrose-social-* + skyyrose-content-engine hub.",
        "Entry point: python -m skyyrose.elite_studio.ventures.social smoke.",
    ),
)


def _plan_node(state: SocialState) -> SocialState:
    """Normalize inputs into the working set the publisher consumes."""
    inputs = state.get("inputs", {})
    sku = state.get("sku", "")
    skus = state.get("skus") or ([sku] if sku else []) or list(inputs.get("skus", []))
    platforms = (
        state.get("platforms")
        or list(inputs.get("platforms", ()))
        or list(DEFAULT_CONFIG.default_platforms)
    )
    valid_platforms = [p for p in platforms if p in SUPPORTED_PLATFORMS]
    return cast(
        SocialState,
        {
            "status": "planned",
            "skus": skus,
            "platforms": valid_platforms,
            "content_type": state.get("content_type")
            or str(inputs.get("content_type", DEFAULT_CONFIG.default_content_type)),
            "collection": state.get("collection"),
            "generate_graphics": bool(state.get("generate_graphics", False)),
            "run_strategy": bool(state.get("run_strategy", False)),
            "outputs": {**state.get("outputs", {}), "venture": MANIFEST.slug},
            "errors": list(state.get("errors", [])),
        },
    )


def _generate_posts_node(state: SocialState) -> SocialState:
    """LIVE node — real SocialMediaAgent, free + template-based, no paid calls."""
    from agents.social_media_agent import SocialMediaAgent  # noqa: PLC0415

    agent = SocialMediaAgent()
    posts: list[dict[str, object]] = []
    errors = list(state.get("errors", []))
    content_type = state.get("content_type", DEFAULT_CONFIG.default_content_type)
    for sku in state.get("skus", []):
        for platform in state.get("platforms", []):
            post = agent.generate_post(sku, platform, content_type)
            if post is None:
                errors.append(f"no post for sku={sku} platform={platform}")
                continue
            posts.append(post.to_dict())
    return cast(
        SocialState,
        {
            "status": "posts_generated" if posts else "no_posts",
            "posts": posts,
            "errors": errors,
        },
    )


def _compose_graphics_node(state: SocialState) -> SocialState:
    """Cost-gated — CreativeAgent paid image generation. Off by default."""
    if not state.get("generate_graphics"):
        return cast(
            SocialState,
            {"graphics": [], "outputs": {**state.get("outputs", {}), "graphics": "not_requested"}},
        )
    from agents.creative_agent import CreativeAgent  # noqa: PLC0415

    agent = CreativeAgent()
    graphics: list[dict[str, object]] = []
    for post in state.get("posts", []):
        prompt = f"Social graphic for {post.get('product_sku', '')} on {post.get('platform', '')}"
        result = asyncio.run(agent.generate_image(prompt))
        graphics.append({"platform": post.get("platform"), "image": result})
    return cast(
        SocialState,
        {"graphics": graphics, "outputs": {**state.get("outputs", {}), "graphics": "generated"}},
    )


def _strategize_node(state: SocialState) -> SocialState:
    """Cost-gated — MarketingAgent LLM strategy. Off by default."""
    if not state.get("run_strategy"):
        return cast(
            SocialState,
            {"strategy": {}, "outputs": {**state.get("outputs", {}), "strategy": "not_requested"}},
        )
    from agents.marketing_agent import MarketingAgent  # noqa: PLC0415

    agent = MarketingAgent()
    topic = state.get("collection") or (state.get("skus") or ["the latest drop"])[0]
    platform = (state.get("platforms") or ["instagram"])[0]
    result = asyncio.run(agent.generate_social_content(str(topic), platform))
    return cast(
        SocialState,
        {
            "strategy": {"platform": platform, "content": getattr(result, "content", str(result))},
            "outputs": {**state.get("outputs", {}), "strategy": "generated"},
        },
    )


def _assemble_node(state: SocialState) -> SocialState:
    """Summarize the deliverable — counts + per-platform breakdown."""
    posts = state.get("posts", [])
    by_platform: dict[str, int] = {}
    for post in posts:
        platform = str(post.get("platform", "unknown"))
        by_platform[platform] = by_platform.get(platform, 0) + 1
    return cast(
        SocialState,
        {
            "status": "assembled",
            "outputs": {
                **state.get("outputs", {}),
                "post_count": len(posts),
                "by_platform": by_platform,
                "graphics_count": len(state.get("graphics", [])),
                "has_strategy": bool(state.get("strategy")),
            },
        },
    )


def build_pipeline(config: SocialVentureConfig | None = None) -> object:
    """Construct and compile the venture's LangGraph.

    LangGraph is imported lazily so the package stays inspectable
    (manifest, agents, config) on a thin environment without langgraph —
    matching the existing pattern in the photo venture and
    `skyyrose.elite_studio.creative.checkpointer`.
    """
    _ = config or DEFAULT_CONFIG  # reserved for future per-call overrides
    from langgraph.graph import END, START, StateGraph  # noqa: PLC0415

    graph: StateGraph = StateGraph(SocialState)
    graph.add_node("plan", _plan_node)
    graph.add_node("generate_posts", _generate_posts_node)
    graph.add_node("compose_graphics", _compose_graphics_node)
    graph.add_node("strategize", _strategize_node)
    graph.add_node("assemble", _assemble_node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "generate_posts")
    graph.add_edge("generate_posts", "compose_graphics")
    graph.add_edge("compose_graphics", "strategize")
    graph.add_edge("strategize", "assemble")
    graph.add_edge("assemble", END)
    return graph.compile()


class SocialPipeline:
    """Operator-facing wrapper around the compiled LangGraph."""

    manifest: VentureManifest = MANIFEST

    def __init__(self, config: SocialVentureConfig | None = None) -> None:
        self.config: SocialVentureConfig = config or DEFAULT_CONFIG
        self._graph: object | None = None

    def build(self) -> object:
        if self._graph is None:
            self._graph = build_pipeline(self.config)
        return self._graph

    def run_smoke(self, sku: str = "smoke-001") -> PipelineResult:
        """Run the free publisher path end-to-end against a real catalog SKU.

        The default `sku` is replaced with the config smoke SKU (`br-001`)
        when the caller passes the venture-generic placeholder, so the
        publisher resolves a real product and emits a real post.
        """
        graph = self.build()
        resolved_sku = self.config.smoke_sku if sku == "smoke-001" else sku
        initial: SocialState = cast(
            SocialState,
            {
                "sku": resolved_sku,
                "inputs": {},
                "outputs": {},
                "status": "pending",
                "errors": [],
                "generate_graphics": False,
                "run_strategy": False,
            },
        )
        from ..._observability import langfuse_config

        final = graph.invoke(initial, config=langfuse_config())  # type: ignore[attr-defined]
        return PipelineResult(
            venture=MANIFEST.slug,
            status=str(final.get("status", "unknown")),
            nodes_executed=("plan", "generate_posts", "compose_graphics", "strategize", "assemble"),
            final_state=cast("SocialState", final),
        )

    def list_agents(self) -> tuple[AgentBinding, ...]:
        return MANIFEST.agent_bindings
