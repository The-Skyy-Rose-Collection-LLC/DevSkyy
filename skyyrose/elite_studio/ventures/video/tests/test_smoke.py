"""Smoke tests for the Video & Animation venture."""

from __future__ import annotations

import pytest

from skyyrose.elite_studio.ventures import get_manifest, list_ventures
from skyyrose.elite_studio.ventures.video import (
    MANIFEST,
    VIDEO_AGENTS,
    VideoPipeline,
    build_pipeline,
)


def test_venture_registered() -> None:
    assert "video" in list_ventures()
    assert get_manifest("video") is MANIFEST


def test_pipeline_compiles() -> None:
    pytest.importorskip("langgraph")
    graph = build_pipeline()
    assert hasattr(graph, "invoke"), "Compiled LangGraph must expose .invoke"


def test_pipeline_smoke_runs() -> None:
    pytest.importorskip("langgraph")
    pipeline = VideoPipeline()
    result = pipeline.run_smoke(sku="smoke-001")
    assert result.venture == "video"
    assert result.status == "initialized"
    assert "initialize" in result.nodes_executed
    assert result.final_state.get("outputs", {}).get("venture") == "video"


def test_agent_bindings_resolve() -> None:
    """Every AgentBinding must point at a real importable target."""
    for binding in VIDEO_AGENTS:
        try:
            resolved = binding.resolve()
        except ImportError as exc:
            pytest.skip(f"{binding.name}: optional dep missing ({exc})")
        assert resolved is not None, f"{binding.name}: resolve() returned None"


@pytest.mark.parametrize("role", ["animation", "tryon_video"])
def test_role_has_at_least_one_binding(role: str) -> None:
    assert MANIFEST.agents_by_role(role), f"No bindings registered for role {role!r}"
