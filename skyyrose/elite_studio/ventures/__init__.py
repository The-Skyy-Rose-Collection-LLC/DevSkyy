"""Elite Studio ventures — productized verticals under one creative platform.

Per project canon (memory: `project_elite_studio_canonical.md`), every
creative pipeline runs through Elite Studio: product imagery, editorial
photography, 3D / immersive, video, and (future) social, marketing,
try-on. Each vertical is a "venture" — a dedicated pipeline surface that
composes the underlying agents and orchestration engines.

Current ventures:

- **imagery** — the original Elite Studio pipeline at
  `skyyrose.elite_studio` (coordinator + graph + synthesis + agents).
  NOT duplicated into `ventures/imagery/`; it remains the umbrella's
  reference implementation.
- **photo** — editorial / lifestyle photography direction + generation.
- **threed** — 3D model generation tournament (Tripo, Meshy, TRELLIS).
- **video** — animated / try-on video generation (alpha; least wired).

Each `ventures.<slug>` package exports a `MANIFEST` and a `Pipeline`
class implementing `_base.VenturePipeline`. The registry below is the
single source of truth other code (CLI, dashboards, MCP) should query.
"""

from __future__ import annotations

from ._base import (
    AgentBinding,
    PipelineResult,
    VentureManifest,
    VenturePipeline,
    VentureState,
    VentureStatus,
)

# Reference manifest for the original Imagery venture (lives at top-level
# `skyyrose.elite_studio` and is composed via `cli.py` / `graph/`).
# We register a manifest so the registry view of "all ventures" is complete
# without duplicating the umbrella package into ventures/imagery/.
IMAGERY_MANIFEST = VentureManifest(
    slug="imagery",
    title="Product Imagery",
    summary=(
        "Original Elite Studio pipeline — multi-agent product render "
        "pipeline (vision + generation + QC + compositor + 3D + try-on). "
        "Lives at `skyyrose.elite_studio` top-level, not under ventures/."
    ),
    status=VentureStatus.STABLE,
    agent_bindings=(
        AgentBinding(
            name="VisionAgent",
            import_path="skyyrose.elite_studio.agents.vision_agent.VisionAgent",
            role="vision",
            ready=True,
        ),
        AgentBinding(
            name="GeneratorAgent",
            import_path="skyyrose.elite_studio.agents.generator_agent.GeneratorAgent",
            role="renderer",
            ready=True,
        ),
        AgentBinding(
            name="QualityAgent",
            import_path="skyyrose.elite_studio.agents.quality_agent.QualityAgent",
            role="quality",
            ready=True,
        ),
        AgentBinding(
            name="CompositorAgent",
            import_path="skyyrose.elite_studio.agents.compositor_agent.CompositorAgent",
            role="compositor",
            ready=True,
        ),
    ),
    default_models={
        "vision": "gemini-3-flash-preview",
        "renderer": "gemini-3-pro-image-preview",
        "quality": "claude-sonnet-4",
        "compositor_brain": "claude-opus-4-6",
    },
    notes=(
        "Entry point: `python -m skyyrose.elite_studio produce <sku>`.",
        "LangGraph engine: `skyyrose.elite_studio.graph.build_graph`.",
    ),
)


def _photo_manifest() -> VentureManifest:
    from .photo import MANIFEST  # noqa: PLC0415 — defer to avoid import cycles

    return MANIFEST


def _threed_manifest() -> VentureManifest:
    from .threed import MANIFEST  # noqa: PLC0415

    return MANIFEST


def _video_manifest() -> VentureManifest:
    from .video import MANIFEST  # noqa: PLC0415

    return MANIFEST


def _social_manifest() -> VentureManifest:
    from .social import MANIFEST  # noqa: PLC0415

    return MANIFEST


_VENTURE_LOADERS: dict[str, object] = {
    "imagery": lambda: IMAGERY_MANIFEST,
    "photo": _photo_manifest,
    "threed": _threed_manifest,
    "video": _video_manifest,
    "social": _social_manifest,
}


def list_ventures() -> tuple[str, ...]:
    """Return every registered venture slug."""
    return tuple(_VENTURE_LOADERS.keys())


def get_manifest(slug: str) -> VentureManifest:
    """Return the manifest for `slug`. Raises KeyError if unknown."""
    if slug not in _VENTURE_LOADERS:
        raise KeyError(f"Unknown venture: {slug!r} (known: {list_ventures()})")
    loader = _VENTURE_LOADERS[slug]
    return loader()  # type: ignore[no-any-return,operator]


def all_manifests() -> tuple[VentureManifest, ...]:
    """Return every venture manifest (imagery + scaffolded ventures)."""
    return tuple(get_manifest(slug) for slug in list_ventures())


__all__ = [
    "AgentBinding",
    "IMAGERY_MANIFEST",
    "PipelineResult",
    "VentureManifest",
    "VenturePipeline",
    "VentureState",
    "VentureStatus",
    "all_manifests",
    "get_manifest",
    "list_ventures",
]
