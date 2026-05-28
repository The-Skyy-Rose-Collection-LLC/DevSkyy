"""3D / Immersive venture pipeline — TRELLIS-only / self-hosted.

Deep-wired so the venture OWNS 3D replica generation instead of referring out
to a SaaS vendor: the generation node runs microsoft/TRELLIS.2-4B on our own
GPU via `agents.trellis_agent.TrellisAgent` (isolated `trellis2` conda env).

Graph: START → plan → verify_capability → generate → select → assemble → END

- `verify_capability` is FREE and runs every pass — it proves the self-hosted
  endpoint is real: conda env python resolvable, TRELLIS.2 repo present, model
  repo configured, output dir writable, dossier resolvable for the SKU. This is
  the "proven endpoints" gate (a self-hosted readiness proof, not "is a key set").
- `generate` is COMPUTE-GATED behind `state["generate_3d"]` (default False). It
  spins up the local model (heavy GPU + minutes per mesh) only when explicitly
  requested, so smoke runs and tests never start a generation.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
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

logger = logging.getLogger(__name__)

MANIFEST = VentureManifest(
    slug="threed",
    title="3D / Immersive",
    summary=(
        "Self-hosted 3D replica generation. Owns the engine: runs "
        "microsoft/TRELLIS.2-4B on our GPU (trellis2 conda env) via "
        "TrellisAgent — no SaaS round-trip. Feeds /experience-* immersive "
        "pages and the WordPress product gallery."
    ),
    status=VentureStatus.BETA,
    agent_bindings=THREED_AGENTS,
    default_models={
        "generator": DEFAULT_CONFIG.model_repo,
    },
    notes=(
        f"Engine: self-hosted {DEFAULT_CONFIG.model_repo} (conda env "
        f"{DEFAULT_CONFIG.conda_env}); free verify path, compute-gated generation.",
        "Tripo/Meshy registered but ready=False (legacy SaaS, not invoked).",
        "Entry point: python -m skyyrose.elite_studio.ventures.threed verify | smoke.",
    ),
)


def _plan_node(state: ThreeDState, config: ThreeDVentureConfig) -> ThreeDState:
    """Normalize inputs into the working set the generator consumes."""
    inputs = state.get("inputs", {})
    return cast(
        ThreeDState,
        {
            "status": "planned",
            "source_image": state.get("source_image") or str(inputs.get("source_image", "")),
            "product_name": state.get("product_name")
            or str(inputs.get("product_name", state.get("sku", "product"))),
            "selected_provider": config.engine,
            "generate_3d": bool(state.get("generate_3d", inputs.get("generate_3d", False))),
            "decimation_target": int(
                state.get("decimation_target", config.default_decimation_target)
            ),
            "texture_size": int(state.get("texture_size", config.default_texture_size)),
            "outputs": {**state.get("outputs", {}), "venture": MANIFEST.slug},
            "errors": list(state.get("errors", [])),
        },
    )


def _probe_output_writable(output_dir: Path) -> bool:
    """Best-effort write probe for the venture output dir (never raises)."""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        probe = output_dir / ".verify_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except OSError as exc:
        logger.info("threed verify: output dir not writable: %s", exc)
        return False


def _probe_dossier(sku: str) -> str:
    """Best-effort dossier-resolution status for the SKU (never raises).

    Returns one of: 'not_checked' (no SKU), 'present', 'missing', or
    'loader_unavailable: <err>' when the dossier loader cannot be imported.
    """
    if not sku:
        return "not_checked"
    try:
        from skyyrose.core.dossier_loader import (  # noqa: PLC0415
            DossierMissingError,
            get_product_with_dossier,
        )
    except ImportError as exc:
        return f"loader_unavailable: {exc}"
    try:
        get_product_with_dossier(sku)
        return "present"
    except DossierMissingError:
        return "missing"


def _verify_capability_node(state: ThreeDState, config: ThreeDVentureConfig) -> ThreeDState:
    """FREE self-hosted readiness proof — no model spin-up, no network, no cost.

    Proves the owned TRELLIS.2 endpoint is real and wired: conda env python
    resolvable, TRELLIS.2 repo present, model repo configured, output dir
    writable, and (best-effort) the dossier resolvable for the target SKU.
    """
    from agents.trellis_agent import TrellisAgent  # noqa: PLC0415

    agent = TrellisAgent(
        conda_env=config.conda_env,
        model_repo=config.model_repo,
        output_dir=config.output_dir,
    )
    env_ready = agent.is_available()  # checks conda python + TRELLIS.2 repo dir
    conda_python = agent._resolve_conda_python(config.conda_env)  # noqa: SLF001 — readiness probe
    output_writable = _probe_output_writable(config.output_dir)
    dossier_detail = _probe_dossier(state.get("sku", ""))

    connectivity: dict[str, object] = {
        "engine": config.engine,
        "self_hosted": True,
        "model_repo": config.model_repo,
        "conda_env": config.conda_env,
        "conda_python": conda_python,
        "trellis_repo_present": bool(agent.trellis_repo_path.is_dir()),
        "trellis_repo_path": str(agent.trellis_repo_path),
        "env_ready": env_ready,
        "output_writable": output_writable,
        "dossier": dossier_detail,
        "ready_to_generate": bool(env_ready and output_writable),
    }
    return cast(
        ThreeDState,
        {
            "status": "verified",
            "connectivity": connectivity,
            "outputs": {**state.get("outputs", {}), "capability": connectivity},
        },
    )


def _generation_blocker(state: ThreeDState) -> ThreeDState | None:
    """Pre-flight gate for generation. Returns an early-exit state when the
    model must not run, or None when all preconditions hold.

    Order matters: the compute gate (`generate_3d`) is checked first, then the
    self-hosted readiness proof, then the required source image. Hard-states are
    honest (no silent fallback to a SaaS vendor).
    """
    if not state.get("generate_3d"):
        return cast(
            ThreeDState,
            {"outputs": {**state.get("outputs", {}), "generation": "not_requested"}},
        )

    if not state.get("connectivity", {}).get("ready_to_generate"):
        return cast(
            ThreeDState,
            {
                "status": "engine_unavailable",
                "errors": [
                    *state.get("errors", []),
                    "generate_3d requested but TRELLIS.2 self-hosted env not ready",
                ],
                "outputs": {**state.get("outputs", {}), "generation": "engine_unavailable"},
            },
        )

    if not state.get("source_image", ""):
        return cast(
            ThreeDState,
            {
                "status": "missing_input",
                "errors": [
                    *state.get("errors", []),
                    "generate_3d requested but no source_image provided",
                ],
                "outputs": {**state.get("outputs", {}), "generation": "missing_input"},
            },
        )

    return None


def _generate_node(state: ThreeDState, config: ThreeDVentureConfig) -> ThreeDState:
    """COMPUTE-GATED — runs the self-hosted TRELLIS.2 model. Off by default.

    Fires only when `generate_3d` is True. Heavy GPU + minutes per mesh, so it
    is never exercised by smoke/tests. Honest hard-states when requested but the
    environment is not ready (no silent fallback to a SaaS vendor).
    """
    blocked = _generation_blocker(state)
    if blocked is not None:
        return blocked

    from agents.trellis_agent import TrellisAgent, TrellisAgentError  # noqa: PLC0415

    agent = TrellisAgent(
        conda_env=config.conda_env,
        model_repo=config.model_repo,
        output_dir=config.output_dir,
        decimation_target=state.get("decimation_target", config.default_decimation_target),
        texture_size=state.get("texture_size", config.default_texture_size),
    )
    try:
        result = asyncio.run(
            agent.image_to_3d(
                image_path=state.get("source_image", ""),
                product_name=state.get("product_name", state.get("sku", "product")),
            )
        )
    except TrellisAgentError as exc:
        return cast(
            ThreeDState,
            {
                "status": "generation_failed",
                "errors": [*state.get("errors", []), f"TRELLIS.2 generation failed: {exc}"],
                "outputs": {**state.get("outputs", {}), "generation": "failed"},
            },
        )
    return cast(
        ThreeDState,
        {
            "status": "generated",
            "winning_mesh_path": str(result.get("local_path", "")),
            "outputs": {
                **state.get("outputs", {}),
                "generation": "completed",
                "mesh": result,
            },
        },
    )


def _select_node(state: ThreeDState) -> ThreeDState:
    """Record the winning mesh (single self-hosted engine — no tournament)."""
    mesh_path = state.get("winning_mesh_path", "")
    return cast(
        ThreeDState,
        {
            "outputs": {
                **state.get("outputs", {}),
                "winner": {
                    "provider": state.get("selected_provider", DEFAULT_CONFIG.engine),
                    "mesh_path": mesh_path,
                    "has_mesh": bool(mesh_path and Path(mesh_path).exists()),
                },
            }
        },
    )


def _assemble_node(state: ThreeDState) -> ThreeDState:
    """Summarize the deliverable."""
    connectivity = state.get("connectivity", {})
    return cast(
        ThreeDState,
        {
            "status": "assembled",
            "outputs": {
                **state.get("outputs", {}),
                "engine": DEFAULT_CONFIG.engine,
                "ready_to_generate": bool(connectivity.get("ready_to_generate")),
                "generated": state.get("outputs", {}).get("generation") == "completed",
                "mesh_path": state.get("winning_mesh_path", ""),
            },
        },
    )


def build_pipeline(config: ThreeDVentureConfig | None = None) -> object:
    """Construct and compile the venture's LangGraph.

    LangGraph is imported lazily so the package can be introspected
    (manifest, agents, config) without the dep present — matching the
    photo/social ventures and `skyyrose.elite_studio.creative.checkpointer`.
    """
    cfg = config or DEFAULT_CONFIG
    from langgraph.graph import END, START, StateGraph  # noqa: PLC0415

    graph: StateGraph = StateGraph(ThreeDState)
    graph.add_node("plan", lambda s: _plan_node(s, cfg))
    graph.add_node("verify_capability", lambda s: _verify_capability_node(s, cfg))
    graph.add_node("generate", lambda s: _generate_node(s, cfg))
    graph.add_node("select", _select_node)
    graph.add_node("assemble", _assemble_node)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "verify_capability")
    graph.add_edge("verify_capability", "generate")
    graph.add_edge("generate", "select")
    graph.add_edge("select", "assemble")
    graph.add_edge("assemble", END)
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
        """Run the free verify path end-to-end (generation gate stays off).

        The generic placeholder SKU is swapped for the config smoke SKU so the
        dossier-resolution probe references a real catalog product.
        """
        graph = self.build()
        resolved_sku = self.config.smoke_sku if sku == "smoke-001" else sku
        initial: ThreeDState = cast(
            ThreeDState,
            {
                "sku": resolved_sku,
                "inputs": {},
                "outputs": {},
                "status": "pending",
                "errors": [],
                "generate_3d": False,
            },
        )
        from ..._observability import langfuse_config

        final = graph.invoke(initial, config=langfuse_config())  # type: ignore[attr-defined]
        return PipelineResult(
            venture=MANIFEST.slug,
            status=str(final.get("status", "unknown")),
            nodes_executed=("plan", "verify_capability", "generate", "select", "assemble"),
            final_state=cast("ThreeDState", final),
        )

    def list_agents(self) -> tuple[AgentBinding, ...]:
        return MANIFEST.agent_bindings
