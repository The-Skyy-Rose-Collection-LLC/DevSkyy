"""Smoke tests for the Social Media venture."""

from __future__ import annotations

import pytest

from skyyrose.elite_studio.ventures import get_manifest, list_ventures
from skyyrose.elite_studio.ventures.social import (
    MANIFEST,
    SOCIAL_AGENTS,
    SocialPipeline,
    build_pipeline,
)


def test_venture_registered() -> None:
    assert "social" in list_ventures()
    assert get_manifest("social") is MANIFEST


def test_pipeline_compiles() -> None:
    pytest.importorskip("langgraph")
    graph = build_pipeline()
    assert hasattr(graph, "invoke"), "Compiled LangGraph must expose .invoke"


def test_pipeline_smoke_runs_and_produces_real_post() -> None:
    pytest.importorskip("langgraph")
    pipeline = SocialPipeline()
    result = pipeline.run_smoke()  # resolves to config.smoke_sku (br-001)
    assert result.venture == "social"
    assert result.status == "assembled"
    for node in ("plan", "generate_posts", "compose_graphics", "strategize", "assemble"):
        assert node in result.nodes_executed
    # Free publisher path must yield at least one real post.
    posts = result.final_state.get("posts", [])
    assert posts, "publisher produced no posts for the smoke SKU"
    assert result.final_state.get("outputs", {}).get("post_count", 0) >= 1
    first = posts[0]
    assert first.get("caption"), "generated post is missing a caption"
    assert first.get("platform") in {"instagram", "tiktok", "twitter", "facebook"}


def test_smoke_does_not_trigger_paid_nodes() -> None:
    """Cost gates default off: graphics + strategy must not fire in smoke."""
    pytest.importorskip("langgraph")
    result = SocialPipeline().run_smoke()
    outputs = result.final_state.get("outputs", {})
    assert outputs.get("graphics") == "not_requested"
    assert outputs.get("strategy") == "not_requested"
    assert result.final_state.get("graphics", []) == []
    assert result.final_state.get("strategy", {}) == {}


def test_agent_bindings_resolve() -> None:
    """Every AgentBinding must point at a real importable target."""
    for binding in SOCIAL_AGENTS:
        try:
            resolved = binding.resolve()
        except (ImportError, KeyError, RuntimeError) as exc:
            pytest.skip(f"{binding.name}: optional dep/env missing ({exc})")
        assert resolved is not None, f"{binding.name}: resolve() returned None"


@pytest.mark.parametrize("role", ["publisher", "graphics", "strategist"])
def test_role_has_at_least_one_binding(role: str) -> None:
    assert MANIFEST.agents_by_role(role), f"No bindings registered for role {role!r}"
