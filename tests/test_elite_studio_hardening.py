"""Tests for Elite Studio P1/P4/P5 hardening — budget, SKU-token guard,
TRELLIS timeout differentiation.

These are pure offline tests — no paid APIs, no GPU.
"""

from __future__ import annotations

import pytest

# --------------------------------------------------------------------------- #
# P1 — RunBudget
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_run_budget_spends_under_ceiling() -> None:
    from skyyrose.elite_studio.budget import RunBudget

    b = RunBudget(ceiling_usd=10.0)
    b.ensure_within_budget(3.0, stage="generation")
    b.spend(3.0, stage="generation")
    assert b.spent_usd == pytest.approx(3.0)
    assert b.remaining() == pytest.approx(7.0)
    snap = b.snapshot()
    assert snap["spent_usd"] == 3.0
    assert snap["by_stage"]["generation"] == 3.0


@pytest.mark.unit
def test_run_budget_blocks_breach() -> None:
    from skyyrose.elite_studio.budget import BudgetExceededError, RunBudget

    b = RunBudget(ceiling_usd=5.0)
    b.spend(3.0, stage="generation")
    with pytest.raises(BudgetExceededError) as exc:
        b.ensure_within_budget(2.50, stage="three_d")
    assert "ceiling" in str(exc.value)
    # Spent state unchanged after the rejection.
    assert b.spent_usd == pytest.approx(3.0)


@pytest.mark.unit
def test_run_budget_rejects_negative_cost() -> None:
    from skyyrose.elite_studio.budget import RunBudget

    b = RunBudget(ceiling_usd=10.0)
    with pytest.raises(ValueError):
        b.ensure_within_budget(-0.01, stage="bad")


@pytest.mark.unit
def test_run_budget_ignores_zero_spend() -> None:
    from skyyrose.elite_studio.budget import RunBudget

    b = RunBudget(ceiling_usd=10.0)
    b.spend(0.0, stage="ignored")
    b.spend(-1.0, stage="negative")  # silently ignored
    assert b.spent_usd == 0.0
    assert b.by_stage == {}


# --------------------------------------------------------------------------- #
# P4 — Round-table SKU-token cross-check
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_sku_tokens_consistent_matches() -> None:
    from orchestration.threed_round_table import _sku_tokens_consistent

    assert _sku_tokens_consistent("br-001", "/path/to/br-001-crewneck.webp") is True
    assert _sku_tokens_consistent("br-001_front", "/x/br-001-crewneck.webp") is True
    assert _sku_tokens_consistent("BR-001", "/x/br-001-crewneck.webp") is True


@pytest.mark.unit
def test_sku_tokens_consistent_rejects_cross_sku() -> None:
    from orchestration.threed_round_table import _sku_tokens_consistent

    assert _sku_tokens_consistent("br-001", "/path/to/lh-002-joggers.webp") is False
    assert _sku_tokens_consistent("sg-014", "/path/to/br-003-baseball.jpeg") is False


@pytest.mark.unit
def test_sku_tokens_consistent_permits_orphan() -> None:
    """When either side has no SKU token, we permit dispatch — covers
    ad-hoc smoke tests with synthetic task_ids."""
    from orchestration.threed_round_table import _sku_tokens_consistent

    assert _sku_tokens_consistent("smoke-test-123", "/x/br-001.webp") is True
    assert _sku_tokens_consistent("br-001", "/x/random.webp") is True
    assert _sku_tokens_consistent("task-xyz", "/x/anything.webp") is True


@pytest.mark.unit
def test_sku_tokens_consistent_handles_variant_suffixes() -> None:
    from orchestration.threed_round_table import _sku_tokens_consistent

    # Same variant family
    assert (
        _sku_tokens_consistent("br-003-oakland", "/x/br-003-baseball-classic-oakland.jpeg") is True
    )
    # Different variants of same family — current behavior rejects, which
    # is the safe default. If product expects br-003-oakland and the image
    # path leaks br-003-giants, we want to halt.
    assert (
        _sku_tokens_consistent("br-003-oakland", "/x/br-003-baseball-classic-giants.jpeg") is False
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_round_table_run_competition_raises_on_sku_mismatch() -> None:
    """Boundary-level test: _run_competition raises ValueError BEFORE any
    provider call when SKU tokens disagree."""
    from orchestration.threed_round_table import (
        GenerationType,
        HF3DFormat,
        HF3DQuality,
        ThreeDProvider,
        ThreeDRoundTable,
    )

    rt = ThreeDRoundTable(
        enable_tripo3d=False,
        enable_anigen=False,
        enable_meshy=False,
        enable_trellis=False,
    )
    with pytest.raises(ValueError) as exc:
        await rt._run_competition(
            providers=[ThreeDProvider.MESHY],
            generation_type=GenerationType.IMAGE_TO_3D,
            prompt="image:dummy",
            output_format=HF3DFormat.GLB,
            quality=HF3DQuality.PRODUCTION,
            task_id="br-001",
            image_path="/path/lh-002-joggers.webp",
        )
    assert "SKU mismatch" in str(exc.value)


# --------------------------------------------------------------------------- #
# P5 — TRELLIS timeout differentiation
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_trellis_timeout_error_is_subclass() -> None:
    from agents.trellis_agent import TrellisAgentError, TrellisTimeoutError

    assert issubclass(TrellisTimeoutError, TrellisAgentError)
    # Callers should be able to catch the parent and still distinguish.
    err = TrellisTimeoutError("timeout 600s")
    assert isinstance(err, TrellisAgentError)
    assert isinstance(err, TrellisTimeoutError)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_trellis_subprocess_timeout_raises_timeout_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """When the subprocess hangs past timeout, the agent must raise
    TrellisTimeoutError, not the generic TrellisAgentError."""
    import subprocess

    from agents.trellis_agent import TrellisAgent, TrellisTimeoutError

    repo = tmp_path / "TRELLIS.2"
    repo.mkdir()
    fake_python = tmp_path / "python"
    fake_python.write_text("#!/bin/sh\nsleep 60\n")
    fake_python.chmod(0o755)
    monkeypatch.setenv("TRELLIS_PYTHON", str(fake_python))

    agent = TrellisAgent(
        trellis_repo_path=repo,
        timeout_seconds=1,
    )
    image = tmp_path / "src.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")

    # Force is_available to True via the override (TRELLIS_PYTHON resolves the python).
    assert agent.is_available()

    # Bypass the actual TRELLIS imports by short-circuiting the subprocess to
    # raise TimeoutExpired directly via monkeypatch.
    def _fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=1)

    monkeypatch.setattr(subprocess, "run", _fake_run)

    with pytest.raises(TrellisTimeoutError):
        await agent.image_to_3d(image_path=str(image))


# --------------------------------------------------------------------------- #
# P7 — Engine selector (legacy vs adk-render)
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_create_initial_state_defaults_to_legacy_engine() -> None:
    from skyyrose.elite_studio.graph.state import create_initial_state

    s = create_initial_state(sku="br-001", view="front")
    assert s["engine"] == "legacy"


@pytest.mark.unit
def test_create_initial_state_accepts_adk_render_engine() -> None:
    from skyyrose.elite_studio.graph.state import create_initial_state

    s = create_initial_state(sku="br-001", view="front", engine="adk-render")
    assert s["engine"] == "adk-render"


@pytest.mark.unit
def test_create_initial_state_rejects_unknown_engine() -> None:
    from skyyrose.elite_studio.graph.state import create_initial_state

    with pytest.raises(ValueError) as exc:
        create_initial_state(sku="br-001", view="front", engine="midjourney")
    assert "unknown engine" in str(exc.value)


@pytest.mark.unit
def test_generator_node_routes_adk_engine_to_invoker(monkeypatch: pytest.MonkeyPatch) -> None:
    """When state['engine'] == 'adk-render', generator_node must call
    _invoke_adk_render_engine, NOT GeneratorAgent.generate."""
    from skyyrose.elite_studio.graph import nodes
    from skyyrose.elite_studio.graph.state import create_initial_state
    from skyyrose.elite_studio.models import GenerationResult

    called = {"adk": 0, "legacy": 0}

    def fake_adk(sku: str, view: str) -> GenerationResult:
        called["adk"] += 1
        return GenerationResult(
            success=True,
            provider="adk-render",
            model="gemini-3-pro-image-preview",
            output_path=f"/tmp/{sku}-{view}-render.webp",
            metadata={
                "engine": "gemini-pro",
                "qa_score": 88.0,
                "qa_passed": True,
                "cost_usd": 0.18,
            },
        )

    class _FailingGenerator:
        def generate(self, *_a, **_kw):  # pragma: no cover — must not be called
            called["legacy"] += 1
            raise AssertionError("legacy GeneratorAgent must not run when engine=adk-render")

    monkeypatch.setattr(nodes, "_invoke_adk_render_engine", fake_adk)
    monkeypatch.setattr(nodes, "GeneratorAgent", _FailingGenerator)

    state = create_initial_state(sku="br-001", view="front", engine="adk-render")
    out = nodes.generator_node(state)

    assert called["adk"] == 1
    assert called["legacy"] == 0
    assert out["generation_result"].success is True
    assert out["generation_result"].provider == "adk-render"
    assert out["generation_result"].metadata["qa_score"] == 88.0


@pytest.mark.unit
def test_generator_node_legacy_path_requires_vision(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default engine ('legacy') still demands a vision_result — no regression."""
    from skyyrose.elite_studio.graph import nodes
    from skyyrose.elite_studio.graph.state import create_initial_state

    state = create_initial_state(sku="br-001", view="front")  # engine defaults to 'legacy'
    # vision_result is None by default — legacy path should refuse.
    out = nodes.generator_node(state)
    assert out["status"] == "error"
    assert out["failed_step"] == "generation"
    assert "No vision result" in out["error"]


@pytest.mark.unit
def test_generator_node_adk_path_does_not_require_vision(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADK pipeline does its own dossier-driven prompting, so absence of
    vision_result must NOT block the adk-render engine."""
    from skyyrose.elite_studio.graph import nodes
    from skyyrose.elite_studio.graph.state import create_initial_state
    from skyyrose.elite_studio.models import GenerationResult

    def fake_adk(sku: str, view: str) -> GenerationResult:
        return GenerationResult(
            success=True,
            provider="adk-render",
            output_path=f"/tmp/{sku}-{view}.webp",
            metadata={"cost_usd": 0.18},
        )

    monkeypatch.setattr(nodes, "_invoke_adk_render_engine", fake_adk)

    state = create_initial_state(sku="br-001", view="front", engine="adk-render")
    out = nodes.generator_node(state)
    assert "generation_result" in out
    assert out["generation_result"].success is True


@pytest.mark.unit
def test_generator_node_adk_spend_uses_reported_cost(monkeypatch: pytest.MonkeyPatch) -> None:
    """Budget spend should debit the ADK-reported cost, not the est_cost constant."""
    from skyyrose.elite_studio.budget import RunBudget
    from skyyrose.elite_studio.graph import nodes
    from skyyrose.elite_studio.graph.state import create_initial_state
    from skyyrose.elite_studio.models import GenerationResult

    reported = 0.18

    def fake_adk(sku: str, view: str) -> GenerationResult:
        return GenerationResult(
            success=True,
            provider="adk-render",
            output_path=f"/tmp/{sku}-{view}.webp",
            metadata={"cost_usd": reported},
        )

    monkeypatch.setattr(nodes, "_invoke_adk_render_engine", fake_adk)

    state = create_initial_state(sku="br-001", view="front", engine="adk-render")
    state["budget"] = RunBudget(ceiling_usd=5.0)
    nodes.generator_node(state)

    assert state["budget"].spent_usd == pytest.approx(reported)
    assert state["budget"].by_stage["generation"] == pytest.approx(reported)
