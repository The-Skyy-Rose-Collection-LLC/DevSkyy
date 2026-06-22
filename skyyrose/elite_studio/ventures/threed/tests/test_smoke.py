"""Smoke tests for the 3D / Immersive venture (TRELLIS-only / self-hosted)."""

from __future__ import annotations

import pytest

from skyyrose.elite_studio.ventures import get_manifest, list_ventures
from skyyrose.elite_studio.ventures.threed import (
    MANIFEST,
    THREED_AGENTS,
    ThreeDPipeline,
    build_pipeline,
)


def test_venture_registered() -> None:
    assert "threed" in list_ventures()
    assert get_manifest("threed") is MANIFEST


def test_pipeline_compiles() -> None:
    pytest.importorskip("langgraph")
    graph = build_pipeline()
    assert hasattr(graph, "invoke"), "Compiled LangGraph must expose .invoke"


def test_pipeline_smoke_runs_verify_path() -> None:
    pytest.importorskip("langgraph")
    result = ThreeDPipeline().run_smoke()  # resolves to config.smoke_sku (br-001)
    assert result.venture == "threed"
    assert result.status == "assembled"
    for node in ("plan", "verify_capability", "generate", "select", "assemble"):
        assert node in result.nodes_executed


def test_verify_capability_proves_self_hosted_endpoint() -> None:
    """The verify node returns a real readiness proof (not 'is an API key set')."""
    pytest.importorskip("langgraph")
    conn = ThreeDPipeline().run_smoke().final_state.get("connectivity", {})
    assert conn, "verify_capability produced no connectivity report"
    assert conn["self_hosted"] is True
    assert conn["engine"] == "trellis"
    assert conn["model_repo"] == "microsoft/TRELLIS.2-4B"
    # These reflect the host: on a non-GPU box env_ready is False — the proof
    # still runs and reports honestly. We assert the SHAPE, not the value.
    assert "env_ready" in conn
    assert "ready_to_generate" in conn
    assert "conda_python" in conn
    assert "trellis_repo_present" in conn


def test_smoke_does_not_generate() -> None:
    """Compute gate defaults off: the model is never spun up in smoke."""
    pytest.importorskip("langgraph")
    outputs = ThreeDPipeline().run_smoke().final_state.get("outputs", {})
    assert outputs.get("generation") == "not_requested"
    assert outputs.get("generated") is False
    assert outputs.get("mesh_path", "") == ""


def test_agent_bindings_resolve() -> None:
    """Every AgentBinding must point at a real importable target."""
    for binding in THREED_AGENTS:
        try:
            resolved = binding.resolve()
        except (ImportError, KeyError, RuntimeError) as exc:
            pytest.skip(f"{binding.name}: optional dep/env missing ({exc})")
        assert resolved is not None, f"{binding.name}: resolve() returned None"


def test_trellis_is_the_only_ready_engine() -> None:
    """TRELLIS-only product: TrellisAgent ready; SaaS providers registered but not."""
    ready = {b.name for b in THREED_AGENTS if b.ready}
    assert ready == {"TrellisAgent"}, f"expected only TrellisAgent ready, got {ready}"
    by_name = {b.name: b for b in THREED_AGENTS}
    assert by_name["TripoAgent"].ready is False
    assert by_name["MeshyAgent"].ready is False


@pytest.mark.parametrize("role", ["generator", "replica_workflow", "tournament"])
def test_role_has_at_least_one_binding(role: str) -> None:
    assert MANIFEST.agents_by_role(role), f"No bindings registered for role {role!r}"
