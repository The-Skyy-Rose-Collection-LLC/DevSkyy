"""Mock-based unit tests for the 9 RenderPipeline tool functions.

Each tool is tested in isolation by mocking the underlying nano_banana
function it wraps. Goals:
  1. Verify state writes happen with the right keys (downstream tools depend on these).
  2. Verify return shape matches the contract documented in tools/__init__.py.
  3. Verify error paths return informative dicts rather than raising.
  4. Verify learning recorders fire from qa_tournament_fn.

All tests run without google-adk installed — `tool_context` is a
SimpleNamespace stand-in (the real ADK ToolContext exposes the same
`.state` attribute we're using).

PATCHING STRATEGY: tools use lazy imports (`from nano_banana.X import Y`
inside the function body) for cold-start performance. This means
`patch.object(<consumer_module>, "<name>")` doesn't see the attribute —
we patch at the SOURCE module path instead (`nano_banana.X.Y`). Fully
verified pattern; gives us deterministic mocks regardless of when the
lazy import fires.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# Same sys.path setup as agent.py
_REPO = Path(__file__).resolve().parents[3]
for _p in (_REPO, _REPO / "scripts"):
    _ps = str(_p)
    if _ps not in sys.path:
        sys.path.insert(0, _ps)


def _make_ctx(initial_state: dict | None = None) -> SimpleNamespace:
    """ToolContext stand-in. `.state` is a dict — same shape as the real ADK
    ToolContext for our purposes (we only read/write state)."""
    return SimpleNamespace(state=dict(initial_state or {}))


# ---------------------------------------------------------------------------
# Tool 1 — load_dossier_fn
# ---------------------------------------------------------------------------


def test_load_dossier_fn_writes_state_and_returns_summary() -> None:
    from agents.render_pipeline.tools.load_dossier import load_dossier_fn

    fake_dossier = MagicMock()
    fake_dossier.garment_type_lock = "Long-sleeve crewneck pullover. Crew neckline. Ribbed cuffs."
    fake_dna = MagicMock()
    fake_dna.spec = "GARMENT TYPE LOCK:\nLong-sleeve crewneck pullover.\n\nBRANDING — exactly..."
    fake_dna.dossier = fake_dossier
    fake_dna.catalog = {"name": "BLACK Rose Crewneck", "collection": "black-rose"}

    with (
        patch("nano_banana.spec_builder.build_dna_from_sku", return_value=fake_dna),
        patch(
            "nano_banana.catalog.load_catalog",
            return_value={
                "br-001": {"name": "BLACK Rose Crewneck", "engine_override": "gemini-pro"}
            },
        ),
    ):
        ctx = _make_ctx()
        result = load_dossier_fn("br-001", ctx)

    assert result["loaded"] is True
    assert result["sku"] == "br-001"
    assert result["name"] == "BLACK Rose Crewneck"
    assert result["collection"] == "black-rose"
    assert result["spec_chars"] > 0
    assert result["engine_override"] == "gemini-pro"
    assert "Long-sleeve crewneck pullover" in result["garment_type_lock_excerpt"]
    assert ctx.state["sku"] == "br-001"
    assert ctx.state["product_name"] == "BLACK Rose Crewneck"
    assert ctx.state["collection"] == "black-rose"
    assert ctx.state["engine_override"] == "gemini-pro"


def test_load_dossier_fn_no_engine_override_when_blank() -> None:
    from agents.render_pipeline.tools.load_dossier import load_dossier_fn

    fake_dna = MagicMock()
    fake_dna.spec = "spec"
    fake_dna.dossier = MagicMock(garment_type_lock="")
    fake_dna.catalog = {"name": "Love Hurts Bomber", "collection": "love-hurts"}

    with (
        patch("nano_banana.spec_builder.build_dna_from_sku", return_value=fake_dna),
        patch(
            "nano_banana.catalog.load_catalog",
            return_value={"lh-004": {"name": "Love Hurts Bomber"}},
        ),
    ):
        ctx = _make_ctx()
        result = load_dossier_fn("lh-004", ctx)

    assert result["engine_override"] is None
    assert "engine_override" not in ctx.state


def test_load_dossier_fn_propagates_dossier_missing() -> None:
    """Tier 2 contract: missing dossier raises, NOT silent fallback."""
    from agents.render_pipeline.tools.load_dossier import load_dossier_fn

    with patch(
        "nano_banana.spec_builder.build_dna_from_sku",
        side_effect=KeyError("br-999 not in catalog"),
    ):
        with pytest.raises(KeyError):
            load_dossier_fn("br-999", _make_ctx())


# ---------------------------------------------------------------------------
# Tool 2 — resolve_source_fn
# ---------------------------------------------------------------------------


def test_resolve_source_fn_writes_path_to_state(tmp_path: Path) -> None:
    from agents.render_pipeline.tools import resolve_source as rs

    img = tmp_path / "br-001-crewneck.png"
    img.write_bytes(b"fake_png_data" * 100)

    fake_catalog = {
        "br-001": {"name": "BLACK Rose Crewneck", "source_override": "br-001-crewneck.png"}
    }

    # `_resolve` is module-level — patch.object works. `load_catalog` is lazy-imported.
    with (
        patch("nano_banana.catalog.load_catalog", return_value=fake_catalog),
        patch.object(rs, "_resolve", return_value=img),
    ):
        ctx = _make_ctx()
        result = rs.resolve_source_fn("br-001", ctx)

    assert result["sku"] == "br-001"
    assert result["source_path"] == str(img)
    assert result["filename"] == "br-001-crewneck.png"
    assert ctx.state["source_path"] == str(img)


def test_resolve_source_fn_returns_error_when_no_image_found() -> None:
    from agents.render_pipeline.tools import resolve_source as rs

    with (
        patch(
            "nano_banana.catalog.load_catalog",
            return_value={"br-999": {"name": "x"}},
        ),
        patch.object(rs, "_resolve", return_value=None),
    ):
        ctx = _make_ctx()
        result = rs.resolve_source_fn("br-999", ctx)

    assert result["source_path"] is None
    assert "no source image found" in result["error"]
    assert "source_path" not in ctx.state


# ---------------------------------------------------------------------------
# Tool 4 — route_engine_fn
# ---------------------------------------------------------------------------


def test_route_engine_fn_uses_catalog_override_when_pinned() -> None:
    from agents.render_pipeline.tools.route_engine import route_engine_fn

    fake_catalog = {"br-001": {"engine_override": "gemini-pro"}}
    with patch("nano_banana.catalog.load_catalog", return_value=fake_catalog):
        ctx = _make_ctx()
        result = route_engine_fn("br-001", "front", ctx)

    assert result["engine"] == "gemini-pro"
    assert result["override_applied"] is True
    assert "F3-pinned" in result["reason"]
    assert result["estimated_cost_usd"] == 0.04
    assert ctx.state["engine"] == "gemini-pro"
    assert ctx.state["estimated_cost_usd"] == 0.04


def test_route_engine_fn_falls_through_to_vision_routing() -> None:
    """When catalog has no override, falls through to route_product()."""
    from agents.render_pipeline.tools.route_engine import route_engine_fn

    fake_catalog = {"lh-004": {}}  # no engine_override
    fake_decision = MagicMock(
        engine="flux-pro",
        model_id="fal-ai/flux-pro/v1.1",
        reason="Standard garment",
        estimated_cost=0.075,
    )
    fake_dna = MagicMock(catalog={"sku": "lh-004"})

    with (
        patch("nano_banana.catalog.load_catalog", return_value=fake_catalog),
        patch("nano_banana.spec_builder.build_dna_from_sku", return_value=fake_dna),
        patch("nano_banana.router.route_product", return_value=[fake_decision]),
    ):
        ctx = _make_ctx()
        result = route_engine_fn("lh-004", "front", ctx)

    assert result["engine"] == "flux-pro"
    assert result["override_applied"] is False
    assert result["estimated_cost_usd"] == 0.075


def test_route_engine_fn_returns_error_when_no_decisions() -> None:
    from agents.render_pipeline.tools.route_engine import route_engine_fn

    fake_catalog = {"sg-007": {}}
    fake_dna = MagicMock(catalog={})
    with (
        patch("nano_banana.catalog.load_catalog", return_value=fake_catalog),
        patch("nano_banana.spec_builder.build_dna_from_sku", return_value=fake_dna),
        patch("nano_banana.router.route_product", return_value=[]),
    ):
        result = route_engine_fn("sg-007", "front", _make_ctx())
    assert "error" in result


# ---------------------------------------------------------------------------
# Tool 5 — articulate_layer0_fn
# ---------------------------------------------------------------------------


def test_articulate_layer0_fn_uses_fallback_when_no_anthropic_key(monkeypatch) -> None:
    from agents.render_pipeline.tools.articulate_layer0 import articulate_layer0_fn

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ctx = _make_ctx(
        {
            "product_name": "BLACK Rose Crewneck",
            "collection": "black-rose",
            "engine": "gemini-pro",
            "vision_consensus": {},
        }
    )
    result = articulate_layer0_fn("br-001", ctx)

    assert result["used_fallback"] is True
    assert result["engine_target"] == "gemini-pro"
    assert result["layer0_chars"] > 0
    assert ctx.state["layer0_directives"]
    # Fallback for gemini-pro must include "no model" rendering language
    assert "no model" in ctx.state["layer0_directives"].lower()


def test_articulate_layer0_fn_calls_sonnet_when_key_present(monkeypatch) -> None:
    from agents.render_pipeline.tools import articulate_layer0 as al

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake_key")

    fake_block = SimpleNamespace(
        type="tool_use",
        input={
            "layer0_directives": "Editorial product photo. Front view. Ghost mannequin. Studio lighting."
        },
    )
    fake_response = SimpleNamespace(content=[fake_block])
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response
    fake_anthropic_module = MagicMock()
    fake_anthropic_module.Anthropic.return_value = fake_client

    with patch.dict("sys.modules", {"anthropic": fake_anthropic_module}):
        ctx = _make_ctx(
            {
                "product_name": "X",
                "collection": "y",
                "engine": "flux-pro",
                "vision_consensus": {"fabric_appearance": "fleece"},
            }
        )
        result = al.articulate_layer0_fn("br-001", ctx)

    assert result["used_fallback"] is False
    assert result["engine_target"] == "flux-pro"
    assert "Editorial product photo" in ctx.state["layer0_directives"]
    fake_client.messages.create.assert_called_once()


def test_articulate_layer0_fn_falls_back_on_sonnet_error(monkeypatch) -> None:
    from agents.render_pipeline.tools import articulate_layer0 as al

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake_key")
    fake_anthropic_module = MagicMock()
    fake_anthropic_module.Anthropic.side_effect = RuntimeError("API down")

    with patch.dict("sys.modules", {"anthropic": fake_anthropic_module}):
        ctx = _make_ctx(
            {
                "product_name": "X",
                "collection": "y",
                "engine": "gpt-image",
                "vision_consensus": {},
            }
        )
        result = al.articulate_layer0_fn("br-001", ctx)

    assert result["used_fallback"] is True
    assert "error" in result
    assert ctx.state["layer0_directives"]


# ---------------------------------------------------------------------------
# Tool 6 — build_prompt_fn
# ---------------------------------------------------------------------------


def test_build_prompt_fn_uses_sonnet_layer0_when_present() -> None:
    from agents.render_pipeline.tools.build_prompt import build_prompt_fn

    sonnet_l0 = "Editorial product photo. Ghost mannequin. Studio lighting. 4K sharpness."
    fake_dna = MagicMock(catalog={"sku": "br-001", "name": "x", "collection": "black-rose"})

    with (
        patch("nano_banana.spec_builder.build_dna_from_sku", return_value=fake_dna),
        patch(
            "nano_banana.spec_builder.augment_prompt_with_dossier_positives",
            side_effect=lambda p, d: f"L3_PREPEND\n\n{p}",
        ),
        patch(
            "nano_banana.spec_builder.augment_prompt_with_dossier_negatives",
            side_effect=lambda p, d: f"{p}\n\nL2_APPEND",
        ),
    ):
        ctx = _make_ctx({"layer0_directives": sonnet_l0, "engine": "gemini-pro"})
        result = build_prompt_fn("br-001", "front", ctx)

    assert result["template_id"] == "sonnet_layer0"
    assert result["layer0_source"] == "sonnet"
    assert result["canonical_mode"] is True
    assert result["layer0_chars"] == len(sonnet_l0)
    assert result["layer3_chars"] > 0
    assert result["layer2_chars"] > 0
    assert ctx.state["prompt"].startswith("L3_PREPEND")
    assert sonnet_l0 in ctx.state["prompt"]
    assert ctx.state["prompt"].endswith("L2_APPEND")


def test_build_prompt_fn_falls_back_to_registry_when_no_sonnet_l0() -> None:
    from agents.render_pipeline.tools.build_prompt import build_prompt_fn

    fake_registry = MagicMock()
    fake_registry.get_prompt.return_value = ("REGISTRY_PROMPT", "canonical_mode_v1")
    fake_dna = MagicMock(catalog={"sku": "lh-004", "name": "Bomber", "collection": "love-hurts"})

    with (
        patch("nano_banana.spec_builder.build_dna_from_sku", return_value=fake_dna),
        patch("nano_banana.prompt_registry.PromptRegistry") as mock_registry_cls,
        patch(
            "nano_banana.spec_builder.augment_prompt_with_dossier_positives",
            side_effect=lambda p, d: p,
        ),
        patch(
            "nano_banana.spec_builder.augment_prompt_with_dossier_negatives",
            side_effect=lambda p, d: p,
        ),
    ):
        mock_registry_cls.load.return_value = fake_registry
        ctx = _make_ctx({"engine": "flux-pro"})
        result = build_prompt_fn("lh-004", "front", ctx)

    assert result["layer0_source"] == "registry_fallback"
    assert result["template_id"] == "canonical_mode_v1"
    assert ctx.state["prompt"] == "REGISTRY_PROMPT"


# ---------------------------------------------------------------------------
# Tool 7 — generate_image_fn
# ---------------------------------------------------------------------------


def test_generate_image_fn_returns_error_when_state_missing() -> None:
    from agents.render_pipeline.tools.generate_image import generate_image_fn

    ctx = _make_ctx()
    result = generate_image_fn("br-001", "front", ctx)
    assert result["output_path"] is None
    assert "missing required state" in result["error"]


def test_generate_image_fn_unsupported_engine_returns_error() -> None:
    from agents.render_pipeline.tools.generate_image import generate_image_fn

    ctx = _make_ctx({"engine": "stable-diffusion-3", "prompt": "x", "source_path": "/tmp/x.jpg"})
    result = generate_image_fn("br-001", "front", ctx)
    assert result["output_path"] is None
    assert "unsupported engine" in result["error"]


def test_generate_image_fn_dispatches_gemini_pro_to_gen_function(tmp_path: Path) -> None:
    from agents.render_pipeline.tools import generate_image as gi

    src = tmp_path / "src.png"
    src.write_bytes(b"src")
    fake_bytes = b"\x89PNG\r\n\x1a\n" + b"x" * 200

    # generate_gemini, save_image, get_genai_client are lazy-imported — patch at source
    with (
        patch("nano_banana.client.get_genai_client", return_value=MagicMock()),
        patch("nano_banana.generate.generate_gemini", return_value=fake_bytes) as mock_gen,
        patch("nano_banana.utils.save_image"),
        patch.object(gi, "_OUTPUT_DIR", tmp_path / "out"),
    ):
        ctx = _make_ctx({"engine": "gemini-pro", "prompt": "test prompt", "source_path": str(src)})
        result = gi.generate_image_fn("br-001", "front", ctx)

    assert result["output_path"] is not None
    assert result["bytes_size"] == len(fake_bytes)
    assert result["engine"] == "gemini-pro"
    assert ctx.state["candidate_path"] == result["output_path"]
    mock_gen.assert_called_once()


# ---------------------------------------------------------------------------
# Tool 8 — qa_tournament_fn
# ---------------------------------------------------------------------------


def test_qa_tournament_fn_records_to_learning_loops() -> None:
    """Loop 1 + Loop 2 always; Loop 3 (failure-mode) only on score<50."""
    from agents.render_pipeline.tools import qa_tournament as qa

    fake_judge = MagicMock(judge="gpt-5.5-pro", available=True, hallucination_veto=False)
    fake_judge.issues = []
    fake_synth = MagicMock(judge="claude-opus-4-7", hallucination_veto=False, overall=88)
    fake_result = MagicMock(
        aggregate_score=88.0,
        vision_pair_mean=87.0,
        synthesis_overall=88.0,
        passed_98=True,
        top_issues=[],
        all_fixes=[],
        judges=[fake_judge, fake_synth],
        synthesis_judge=fake_synth,
    )

    with (
        patch("nano_banana.spec_builder.build_dna_from_sku", return_value=MagicMock()),
        patch.object(
            qa, "_build_tournament_clients", return_value={"openai": 1, "gemini": 1, "anthropic": 1}
        ),
        patch("nano_banana.tournament.run_tournament", return_value=fake_result),
        patch("agents.render_pipeline.learning.recorder.record_engine_outcome") as mock_eng,
        patch("agents.render_pipeline.learning.recorder.record_template_score") as mock_tpl,
        patch("agents.render_pipeline.learning.recorder.record_failure_mode") as mock_fm,
    ):
        ctx = _make_ctx(
            {
                "source_path": "/tmp/src.png",
                "candidate_path": "/tmp/out.webp",
                "engine": "gemini-pro",
                "template_id": "sonnet_layer0",
                "estimated_cost_usd": 0.04,
            }
        )
        result = qa.qa_tournament_fn("br-001", ctx)

    assert result["aggregate_score"] == 88.0
    assert result["qa_passed"] is True
    assert result["should_refine"] is False
    mock_eng.assert_called_once()
    mock_tpl.assert_called_once()
    mock_fm.assert_not_called()


def test_qa_tournament_fn_records_failure_mode_on_low_score() -> None:
    from agents.render_pipeline.tools import qa_tournament as qa

    fake_synth = MagicMock(judge="claude-opus-4-7", hallucination_veto=True, overall=30)
    fake_result = MagicMock(
        aggregate_score=30.0,
        vision_pair_mean=28.0,
        synthesis_overall=30.0,
        passed_98=False,
        top_issues=["wrong color"],
        all_fixes=["fix color"],
        judges=[fake_synth],
        synthesis_judge=fake_synth,
    )

    with (
        patch("nano_banana.spec_builder.build_dna_from_sku", return_value=MagicMock()),
        patch.object(qa, "_build_tournament_clients", return_value={"gemini": 1}),
        patch("nano_banana.tournament.run_tournament", return_value=fake_result),
        patch("agents.render_pipeline.learning.recorder.record_engine_outcome"),
        patch("agents.render_pipeline.learning.recorder.record_template_score"),
        patch("agents.render_pipeline.learning.recorder.record_failure_mode") as mock_fm,
    ):
        ctx = _make_ctx(
            {
                "source_path": "/tmp/s.png",
                "candidate_path": "/tmp/c.webp",
                "engine": "flux-pro",
                "template_id": "sonnet_layer0",
                "estimated_cost_usd": 0.075,
            }
        )
        result = qa.qa_tournament_fn("br-001", ctx)

    assert result["should_refine"] is True
    assert result["hallucination_veto"] is True
    mock_fm.assert_called_once()
    fm_kwargs = mock_fm.call_args.kwargs
    assert fm_kwargs["sku"] == "br-001"
    assert fm_kwargs["hallucination_veto"] is True


def test_qa_tournament_fn_surfaces_infra_failures() -> None:
    """F5 — judges with available=False appear in infra_failures list."""
    from agents.render_pipeline.tools import qa_tournament as qa

    failed_judge = MagicMock(judge="gpt-5.5-pro", available=False)
    failed_judge.issues = ["TimeoutError: 504 DEADLINE_EXCEEDED"]
    ok_synth = MagicMock(
        judge="claude-opus-4-7", available=True, hallucination_veto=False, overall=0
    )
    fake_result = MagicMock(
        aggregate_score=0.0,
        vision_pair_mean=0.0,
        synthesis_overall=0.0,
        passed_98=False,
        top_issues=[],
        all_fixes=[],
        judges=[failed_judge, ok_synth],
        synthesis_judge=ok_synth,
    )

    with (
        patch("nano_banana.spec_builder.build_dna_from_sku", return_value=MagicMock()),
        patch.object(qa, "_build_tournament_clients", return_value={"gemini": 1}),
        patch("nano_banana.tournament.run_tournament", return_value=fake_result),
        patch("agents.render_pipeline.learning.recorder.record_engine_outcome"),
        patch("agents.render_pipeline.learning.recorder.record_template_score"),
        patch("agents.render_pipeline.learning.recorder.record_failure_mode"),
    ):
        ctx = _make_ctx(
            {
                "source_path": "/tmp/s.png",
                "candidate_path": "/tmp/c.webp",
                "engine": "gemini-pro",
                "template_id": "x",
                "estimated_cost_usd": 0.04,
            }
        )
        result = qa.qa_tournament_fn("br-001", ctx)

    assert len(result["infra_failures"]) == 1
    assert result["infra_failures"][0]["judge"] == "gpt-5.5-pro"
    assert "504" in result["infra_failures"][0]["reason"]


def test_qa_tournament_fn_returns_error_on_missing_state() -> None:
    from agents.render_pipeline.tools.qa_tournament import qa_tournament_fn

    result = qa_tournament_fn("br-001", _make_ctx())
    assert "error" in result
    assert "missing required state" in result["error"]


# ---------------------------------------------------------------------------
# Tool 9 — refine_image_fn
# ---------------------------------------------------------------------------


def test_refine_image_fn_uses_kontext_first(tmp_path: Path) -> None:
    from agents.render_pipeline.tools.refine_image import refine_image_fn

    cand = tmp_path / "out.webp"
    cand.write_bytes(b"existing render")
    fake_refined = b"\x89PNG\r\n\x1a\n" + b"refined" * 50

    with (
        patch("nano_banana.engine_fal.refine_with_kontext", return_value=fake_refined) as mock_kctx,
        patch("nano_banana.utils.save_image") as mock_save,
    ):
        ctx = _make_ctx(
            {
                "candidate_path": str(cand),
                "source_path": str(cand),
                "qa_score": 65.0,
                "hallucination_veto": False,
                "top_issues": ["wrong color"],
                "all_fixes": ["use canonical color"],
                "product_name": "BLACK Rose Crewneck",
            }
        )
        result = refine_image_fn("br-001", ctx)

    assert result["refined"] is True
    assert result["engine_used"] == "flux-kontext"
    assert ctx.state["refinement_applied"] is True
    assert ctx.state["refinement_engine"] == "flux-kontext"
    mock_kctx.assert_called_once()
    mock_save.assert_called_once()


def test_refine_image_fn_falls_back_to_gemini_composite(tmp_path: Path) -> None:
    from agents.render_pipeline.tools.refine_image import refine_image_fn

    cand = tmp_path / "out.webp"
    cand.write_bytes(b"existing")
    src = tmp_path / "src.png"
    src.write_bytes(b"source")
    fake_refined = b"refined_bytes" * 100

    with (
        patch("nano_banana.engine_fal.refine_with_kontext", return_value=None),
        patch("nano_banana.client.get_genai_client", return_value=MagicMock()),
        patch("nano_banana.generate.composite_gemini", return_value=fake_refined),
        patch("nano_banana.utils.save_image"),
    ):
        ctx = _make_ctx(
            {
                "candidate_path": str(cand),
                "source_path": str(src),
                "qa_score": 70.0,
                "hallucination_veto": False,
                "top_issues": [],
                "all_fixes": [],
                "product_name": "X",
            }
        )
        result = refine_image_fn("br-001", ctx)

    assert result["refined"] is True
    assert result["engine_used"] == "gemini-composite"


def test_refine_image_fn_returns_error_when_no_candidate() -> None:
    from agents.render_pipeline.tools.refine_image import refine_image_fn

    result = refine_image_fn("br-001", _make_ctx())
    assert result["refined"] is False
    assert "no candidate_path" in result["error"]


def test_refine_image_fn_builds_synthesis_aware_prompt() -> None:
    """Tier 1 prompt: hallucination_veto fires CRITICAL prefix; issues + fixes assembled."""
    from agents.render_pipeline.tools.refine_image import _build_refine_prompt

    prompt = _build_refine_prompt(
        name="BLACK Rose Crewneck",
        sku="br-001",
        score=30.0,
        veto=True,
        issues=["multi-color rose hallucination", "wrong neckband"],
        fixes=["use tonal embossed black-on-black", "remove white trim"],
    )
    assert "CRITICAL" in prompt
    assert "hallucinated decorative elements" in prompt
    assert "multi-color rose hallucination" in prompt
    assert "use tonal embossed black-on-black" in prompt
    assert "br-001" in prompt
    assert "30/100" in prompt


# ---------------------------------------------------------------------------
# Tool 3 — vision_consensus_fn (merge logic + cache)
# ---------------------------------------------------------------------------


def test_vision_consensus_merge_unions_colors_and_graphics() -> None:
    from agents.render_pipeline.tools.vision_consensus import _merge_consensus

    gemini = {
        "garment_type": "crewneck",
        "garment_subtype": "pullover",
        "silhouette": "relaxed",
        "fabric_appearance": "fleece",
        "colors": [{"area": "body", "color": "black", "finish": "matte"}],
        "graphics": [
            {
                "type": "embroidery",
                "content": "rose",
                "location": "left chest",
                "size": "3in",
            }
        ],
        "construction": "ribbed cuffs",
    }
    openai = {
        "garment_type": "crewneck",
        "garment_subtype": "",
        "silhouette": "",
        "fabric_appearance": "cotton fleece blend",
        "colors": [{"area": "neckband", "color": "white", "finish": ""}],
        "graphics": [
            {
                "type": "embroidery",
                "content": "rose",
                "location": "left chest",
                "size": "3in",
            }
        ],
        "construction": "",
    }
    merged = _merge_consensus(gemini, openai)

    assert merged["garment_type"] == "crewneck"
    assert merged["garment_subtype"] == "pullover"  # Gemini wins ties
    assert "fleece" in merged["fabric_appearance"]
    assert "cotton fleece blend" in merged["fabric_appearance"]
    areas = {c["area"] for c in merged["colors"]}
    assert areas == {"body", "neckband"}
    assert len(merged["graphics"]) == 1  # deduped by (location, content)
    assert merged["_providers_succeeded"] == 2


def test_vision_consensus_merge_handles_one_provider_failure() -> None:
    from agents.render_pipeline.tools.vision_consensus import _merge_consensus

    merged = _merge_consensus(
        {},
        {
            "garment_type": "hoodie",
            "fabric_appearance": "fleece",
            "garment_subtype": "",
            "silhouette": "",
            "construction": "",
            "colors": [],
            "graphics": [],
        },
    )
    assert merged["garment_type"] == "hoodie"
    assert merged["_providers_succeeded"] == 1


def test_vision_consensus_fn_uses_disk_cache(tmp_path: Path, monkeypatch) -> None:
    """Cached consensus loads without API calls."""
    import json

    from agents.render_pipeline.tools import vision_consensus as vc

    cache_dir = tmp_path / "data" / "vision-consensus"
    cache_dir.mkdir(parents=True)
    cached_payload = {
        "garment_type": "crewneck",
        "fabric_appearance": "fleece",
        "graphics": [],
        "colors": [],
        "_providers_succeeded": 2,
    }
    (cache_dir / "br-001.json").write_text(json.dumps(cached_payload))

    monkeypatch.setattr(vc, "REPO_ROOT", tmp_path)
    monkeypatch.delenv("VISION_CONSENSUS_NOCACHE", raising=False)

    ctx = _make_ctx({"source_path": "/tmp/src.png"})
    result = vc.vision_consensus_fn("br-001", ctx)

    assert result["cached"] is True
    assert result["providers_succeeded"] == 2
    assert ctx.state["vision_consensus"]["garment_type"] == "crewneck"


# ---------------------------------------------------------------------------
# Layer 0 fallback content
# ---------------------------------------------------------------------------


def test_fallback_layer0_engine_specific_styles() -> None:
    from agents.render_pipeline.tools.articulate_layer0 import _fallback_layer0

    flux = _fallback_layer0("flux-pro").lower()
    gpt = _fallback_layer0("gpt-image").lower()
    gem = _fallback_layer0("gemini-pro").lower()

    # All three include the "no model" constraint (luxury-rendering invariant)
    for name, s in (("flux", flux), ("gpt", gpt), ("gem", gem)):
        assert "front view" in s, f"{name} fallback missing 'front view'"
        assert "no model" in s, f"{name} fallback missing 'no model'"

    # FLUX is the terse engine — fallback should reflect that
    assert len(flux) < len(gpt)
