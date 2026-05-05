"""Mock-based tests for ProductionPipeline.run_single / run_batch.

Covers the orchestration logic with all paid SDK calls mocked at their
source modules:
- vision: `nano_banana.vision_describe.describe_product`
- canonical spec: `nano_banana.spec_builder.build_dna_from_sku`
- routing: `nano_banana.router.route_product`
- generation: `nano_banana.generate.{generate_gemini,generate_gpt,composite_gemini}`
- FAL: `nano_banana.engine_fal.{generate_flux_fal,refine_with_kontext}`
- prompt registry: `nano_banana.prompt_registry.PromptRegistry.load`
- QA: `nano_banana.tournament.run_tournament`
- utils: `nano_banana.utils.quality_gate`

PROJECT_ROOT is monkeypatched to tmp_path so saved images don't leak
into the live wordpress theme directory.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

import nano_banana.engine_fal as engine_fal_mod  # noqa: E402
import nano_banana.generate as generate_mod  # noqa: E402
import nano_banana.pipeline as pipeline_mod  # noqa: E402
import nano_banana.prompt_registry as registry_mod  # noqa: E402
import nano_banana.router as router_mod  # noqa: E402
import nano_banana.spec_builder as spec_builder_mod  # noqa: E402
import nano_banana.tournament as tournament_mod  # noqa: E402
import nano_banana.utils as utils_mod  # noqa: E402
import nano_banana.vision_describe as vision_describe_mod  # noqa: E402
from nano_banana.pipeline import (  # noqa: E402
    PipelineResult,
    ProductionPipeline,
    _build_refinement_prompt,
    _find_bundle_dir,
    _load_bundle_refs,
    _source_env_file,
)
from nano_banana.router import RouteDecision  # noqa: E402
from nano_banana.tournament import JudgmentScore, TournamentResult  # noqa: E402
from nano_banana.vision_context import VisionContext  # noqa: E402

from skyyrose.core.dossier_loader import Dossier, DossierMissingError  # noqa: E402

# ── Test fixtures & helpers ────────────────────────────────────────────────


def _png_bytes(size: int = 1024) -> bytes:
    """Return a real PNG byte string > 15KB so quality_gate passes."""
    img = Image.new("RGB", (size, size), color=(20, 20, 20))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_route_decision(engine: str = "gemini-pro", cost: float = 0.04) -> RouteDecision:
    return RouteDecision(
        engine=engine,
        model_id=f"{engine}-stub-id",
        reason=f"test routing → {engine}",
        estimated_cost=cost,
        priority=1,
    )


def _make_judgment(
    *,
    judge: str,
    overall: int = 85,
    text: int = 85,
    logo: int = 85,
    color: int = 85,
) -> JudgmentScore:
    return JudgmentScore(
        judge=judge,
        garment_type=overall,
        color_accuracy=color,
        text_accuracy=text,
        logo_accuracy=logo,
        construction_accuracy=overall,
        no_hallucinations=overall,
        overall=overall,
        issues=[],
        suggested_fixes=[],
        raw_response="",
    )


def _make_tournament_result(
    *,
    score: float = 85.0,
    text: int = 85,
    logo: int = 85,
    veto: bool = False,
    candidate_path: str = "/tmp/cand.png",
) -> TournamentResult:
    gpt = _make_judgment(judge="gpt-stub", overall=int(score), text=text, logo=logo)
    gem = _make_judgment(judge="gem-stub", overall=int(score), text=text, logo=logo)
    synth = JudgmentScore(
        judge="claude-opus-4-7",
        garment_type=int(score),
        color_accuracy=int(score),
        text_accuracy=text,
        logo_accuracy=logo,
        construction_accuracy=int(score),
        no_hallucinations=int(score),
        overall=int(score),
        issues=[],
        suggested_fixes=[],
        raw_response="",
        rationale="...",
        vision_consensus="agree",
        hallucination_veto=veto,
    )
    return TournamentResult(
        candidate_path=candidate_path,
        judges=[gpt, gem, synth],
        aggregate_score=score,
        # Match the production threshold (PipelineConfig.qa_auto_approve = 80.0)
        # rather than the dataclass field name's literal "98" — the pipeline
        # passes `passing_threshold=cfg.qa_auto_approve` to run_tournament.
        passed_98=score >= 80.0,
        top_issues=[],
        all_fixes=[],
        vision_pair_mean=score,
        synthesis_overall=score,
    )


def _stub_vision_desc() -> dict:
    return {
        "garment_type": "crewneck sweatshirt",
        "fabric_appearance": "heavyweight cotton fleece",
        "graphics": [],
    }


@pytest.fixture()
def isolated_project_root(tmp_path: Path, monkeypatch) -> Path:
    """Redirect PROJECT_ROOT to tmp_path so writes don't escape into the theme.

    Pre-creates `data/product-bundles/` because the pipeline's
    `_find_bundle_dir` iterates that directory unconditionally; in
    production it always exists, so the fixture mirrors that invariant.
    """
    monkeypatch.setattr(pipeline_mod, "PROJECT_ROOT", tmp_path)
    (tmp_path / "data" / "product-bundles").mkdir(parents=True)
    return tmp_path


@pytest.fixture()
def fake_source_image(tmp_path: Path) -> Path:
    img = Image.new("RGB", (200, 200), color=(255, 0, 0))
    p = tmp_path / "techflat.jpg"
    img.save(p, format="JPEG")
    return p


@pytest.fixture()
def stub_registry(monkeypatch):
    """Replace PromptRegistry.load() with a MagicMock that returns a stub registry."""
    fake_registry = MagicMock()
    fake_registry.get_prompt.return_value = ("STUB PROMPT", "stub-template-v1")
    fake_registry.record_score = MagicMock()
    fake_registry.save = MagicMock()
    monkeypatch.setattr(registry_mod.PromptRegistry, "load", classmethod(lambda cls: fake_registry))
    return fake_registry


@pytest.fixture()
def stub_dependencies(monkeypatch):
    """Patch every paid/external surface to a controlled stub."""
    monkeypatch.setattr(
        vision_describe_mod, "describe_product", lambda *a, **kw: _stub_vision_desc()
    )
    monkeypatch.setattr(router_mod, "route_product", lambda *a, **kw: [_make_route_decision()])
    # Default: dossier loads happily. Build a real Dossier so the
    # VisionContext invariant (dossier present → spec may be set) holds.
    monkeypatch.setattr(
        spec_builder_mod,
        "build_dna_from_sku",
        lambda sku: VisionContext(
            inferred={},
            catalog={"sku": sku, "name": sku},
            spec="CANONICAL SPEC FOR " + sku,
            dossier=Dossier(
                sku=sku,
                name=sku,
                collection="test",
                slug=sku,
                garment_type_lock="",
                branding_block="",
                negative_block="",
                scene_pose="",
                scene_setting="",
            ),
        ),
    )
    # By default no negative augmentation (passthrough)
    monkeypatch.setattr(spec_builder_mod, "augment_prompt_with_dossier_negatives", lambda p, dna: p)
    monkeypatch.setattr(generate_mod, "generate_gemini", lambda *a, **kw: _png_bytes())
    monkeypatch.setattr(generate_mod, "generate_gpt", lambda *a, **kw: _png_bytes())
    monkeypatch.setattr(generate_mod, "composite_gemini", lambda *a, **kw: _png_bytes())
    monkeypatch.setattr(engine_fal_mod, "generate_flux_fal", lambda *a, **kw: _png_bytes())
    monkeypatch.setattr(engine_fal_mod, "refine_with_kontext", lambda *a, **kw: _png_bytes())
    monkeypatch.setattr(utils_mod, "quality_gate", lambda b, sku, view: True)
    # Default tournament: passing score, no refinement triggered
    monkeypatch.setattr(
        tournament_mod, "run_tournament", lambda *a, **kw: _make_tournament_result(score=92.0)
    )


def _build_pipeline() -> ProductionPipeline:
    """Construct a ProductionPipeline with all-mock clients."""
    return ProductionPipeline(
        genai_client=MagicMock(),
        openai_client=MagicMock(),
        anthropic_client=MagicMock(),
        fal_available=True,
    )


def _sample_product(sku: str = "br-001") -> dict:
    return {
        "sku": sku,
        "name": "BLACK Rose Crewneck",
        "collection": "black-rose",
    }


# ── PipelineResult dataclass ───────────────────────────────────────────────


def test_pipeline_result_to_dict_serializes_path():
    """Path objects in PipelineResult.to_dict are stringified for JSON."""
    out = Path("/tmp/x.webp")
    r = PipelineResult(sku="br-001", view="front", output_path=out, qa_score=88.0)
    d = r.to_dict()
    assert d["output_path"] == str(out)
    assert d["qa_score"] == 88.0
    assert "vision_desc" not in d  # excluded from JSON serialization


def test_pipeline_result_to_dict_handles_none_output():
    """None output_path serializes as None, not 'None' string."""
    d = PipelineResult(sku="br-001", view="front").to_dict()
    assert d["output_path"] is None


# ── _source_env_file ───────────────────────────────────────────────────────


def test_source_env_file_loads_key_value_pairs(tmp_path, monkeypatch):
    """KV pairs in env file are loaded into os.environ via setdefault."""
    p = tmp_path / "fake.env"
    p.write_text("# comment\nFOO_KEY=bar\nQUOTED='quoted-val'\nDOUBLE=\"dbl\"\n\n=ignored\n")
    monkeypatch.delenv("FOO_KEY", raising=False)
    monkeypatch.delenv("QUOTED", raising=False)
    monkeypatch.delenv("DOUBLE", raising=False)

    _source_env_file(p)

    import os

    assert os.environ.get("FOO_KEY") == "bar"
    assert os.environ.get("QUOTED") == "quoted-val"
    assert os.environ.get("DOUBLE") == "dbl"


def test_source_env_file_skips_comments_and_blanks(tmp_path):
    """Comments and blank lines don't crash."""
    p = tmp_path / "weird.env"
    p.write_text("\n\n# only a comment\n   \n# another\n")
    _source_env_file(p)  # should not raise


# ── _find_bundle_dir / _load_bundle_refs ───────────────────────────────────


def test_find_bundle_dir_returns_none_when_no_matching_sku(isolated_project_root):
    """Bundle root exists but no name match and no manifest match → None."""
    # isolated_project_root creates the bundle root but with no entries
    assert _find_bundle_dir("Unknown Product", "xx-999") is None


def test_find_bundle_dir_finds_by_product_name(isolated_project_root):
    """Bundle directory keyed by product name (preferred path)."""
    bundle_root = isolated_project_root / "data" / "product-bundles"
    name_dir = bundle_root / "BLACK Rose Crewneck"
    name_dir.mkdir(parents=True)

    found = _find_bundle_dir("BLACK Rose Crewneck", "br-001")
    assert found == name_dir


def test_find_bundle_dir_falls_back_to_manifest_search(isolated_project_root):
    """When name match misses, search manifest.json for matching SKU."""
    bundle_root = isolated_project_root / "data" / "product-bundles"
    other_dir = bundle_root / "weirdly-named-folder"
    other_dir.mkdir(parents=True)
    (other_dir / "manifest.json").write_text('{"sku": "br-001", "name": "X"}')

    found = _find_bundle_dir("Mismatched Name", "br-001")
    assert found == other_dir


def test_load_bundle_refs_excludes_logo_refs(isolated_project_root, fake_source_image):
    """Logo/patch refs are intentionally NOT included — they cause hallucinated branding."""
    bundle = isolated_project_root / "data" / "product-bundles" / "Test Product"
    bundle.mkdir(parents=True)
    Image.new("RGB", (10, 10)).save(bundle / "logo-ref.png", format="PNG")
    Image.new("RGB", (10, 10)).save(bundle / "source-photo.jpg", format="JPEG")
    Image.new("RGB", (10, 10)).save(bundle / "techflat-front.jpg", format="JPEG")

    refs = _load_bundle_refs("Test Product", "br-001", fake_source_image, "front")

    paths = [str(p) for _label, p in refs]
    assert any("source-photo" in p for p in paths)
    assert any("techflat-front" in p for p in paths)
    # CRITICAL: logo-ref.png must NOT be in refs
    assert not any("logo-ref" in p for p in paths)


def test_load_bundle_refs_picks_back_techflat_for_back_view(
    isolated_project_root, fake_source_image
):
    """`view='back'` includes techflat-back, not techflat-front."""
    bundle = isolated_project_root / "data" / "product-bundles" / "Test Product"
    bundle.mkdir(parents=True)
    Image.new("RGB", (10, 10)).save(bundle / "techflat-front.jpg", format="JPEG")
    Image.new("RGB", (10, 10)).save(bundle / "techflat-back.jpg", format="JPEG")

    refs = _load_bundle_refs("Test Product", "br-001", fake_source_image, "back")

    paths = [str(p) for _label, p in refs]
    assert any("techflat-back" in p for p in paths)
    assert not any("techflat-front" in p for p in paths)


def test_load_bundle_refs_no_bundle_returns_empty(isolated_project_root, fake_source_image):
    """Missing bundle dir → empty refs list (logged, not raised)."""
    refs = _load_bundle_refs("nonexistent", "xx-999", fake_source_image, "front")
    assert refs == []


# ── run_single — happy path ────────────────────────────────────────────────


def test_run_single_happy_path_no_refinement(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies
):
    """Score above qa_auto_approve → no refinement, output saved, cost recorded."""
    pipe = _build_pipeline()
    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert result.qa_passed is True
    assert result.qa_score == 92.0
    assert result.refinement_applied is False
    assert result.output_path is not None
    assert result.output_path.exists()
    assert result.engine_used == "gemini-pro"
    assert result.attempts == 1
    assert result.cost_usd == pytest.approx(0.04)


# ── run_single — refinement triggers ───────────────────────────────────────


def test_run_single_text_threshold_triggers_refinement(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """Vision judge with text_accuracy < 70 triggers Kontext refinement."""
    # First QA call: low text accuracy. Second QA call (post-refine): clean.
    qa_results = [
        _make_tournament_result(score=72.0, text=55, logo=80),  # below threshold 70
        _make_tournament_result(score=88.0, text=90, logo=90),  # post-refine
    ]
    monkeypatch.setattr(tournament_mod, "run_tournament", lambda *a, **kw: qa_results.pop(0))

    refine_calls = []

    def _spy_refine(path, prompt):
        refine_calls.append(prompt)
        return _png_bytes()

    monkeypatch.setattr(engine_fal_mod, "refine_with_kontext", _spy_refine)

    pipe = _build_pipeline()
    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert result.refinement_applied is True
    assert result.qa_score == 88.0  # post-refine score wins
    assert len(refine_calls) == 1


def test_run_single_logo_threshold_triggers_refinement(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """logo_accuracy < 70 triggers refinement (independent of text_accuracy)."""
    qa_results = [
        _make_tournament_result(score=72.0, text=85, logo=50),
        _make_tournament_result(score=88.0, text=90, logo=92),
    ]
    monkeypatch.setattr(tournament_mod, "run_tournament", lambda *a, **kw: qa_results.pop(0))
    refine_calls = []
    monkeypatch.setattr(
        engine_fal_mod,
        "refine_with_kontext",
        lambda p, prompt: (refine_calls.append(prompt), _png_bytes())[1],
    )

    pipe = _build_pipeline()
    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert result.refinement_applied is True
    assert len(refine_calls) == 1


def test_run_single_hallucination_veto_triggers_refinement_even_with_high_scores(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """Synthesis hallucination_veto fires refinement regardless of vision-pair scores."""
    qa_results = [
        # Vision scores are GOOD, but synthesis judge vetoes
        _make_tournament_result(score=72.0, text=92, logo=92, veto=True),
        _make_tournament_result(score=85.0, text=92, logo=92, veto=False),
    ]
    monkeypatch.setattr(tournament_mod, "run_tournament", lambda *a, **kw: qa_results.pop(0))
    refine_calls = []
    monkeypatch.setattr(
        engine_fal_mod,
        "refine_with_kontext",
        lambda p, prompt: (refine_calls.append(prompt), _png_bytes())[1],
    )

    pipe = _build_pipeline()
    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert result.refinement_applied is True
    assert len(refine_calls) == 1


# ── run_single — dossier paths ─────────────────────────────────────────────


def test_run_single_dossier_soft_fail_falls_back_to_inferred_dna(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch, caplog
):
    """Missing dossier file: pipeline logs warning and continues with inferred DNA."""

    def _raise_missing(sku):
        raise DossierMissingError(f"no dossier for {sku}")

    monkeypatch.setattr(spec_builder_mod, "build_dna_from_sku", _raise_missing)

    import logging

    pipe = _build_pipeline()
    with caplog.at_level(logging.WARNING, logger="nano_banana.pipeline"):
        result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    # Pipeline still produced an output (didn't hard-fail)
    assert result.output_path is not None
    # Vision desc lacks the canonical spec key
    assert "spec" not in result.vision_desc
    assert "_dossier" not in result.vision_desc
    # Warning was logged
    assert any("DOSSIER" in rec.message and "falling back" in rec.message for rec in caplog.records)


def test_run_single_dossier_negatives_appended_to_generator_prompt(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """The dossier negative block reaches the generator, not just the judges."""
    captured_prompts = []

    def _augment(prompt: str, dna: dict) -> str:
        return prompt + "\n\nDO NOT RENDER (authored canonical negatives):\nNO printed graphics."

    monkeypatch.setattr(spec_builder_mod, "augment_prompt_with_dossier_negatives", _augment)

    def _spy_generate(client, source_path, prompt, **kwargs):
        captured_prompts.append(prompt)
        return _png_bytes()

    monkeypatch.setattr(generate_mod, "generate_gemini", _spy_generate)

    pipe = _build_pipeline()
    pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert len(captured_prompts) == 1
    assert "DO NOT RENDER (authored canonical negatives)" in captured_prompts[0]
    assert "NO printed graphics." in captured_prompts[0]


# ── run_single — failure paths ─────────────────────────────────────────────


def test_run_single_router_returns_no_decisions_returns_empty_result(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """Empty router decisions list → result has issues, no output_path."""
    monkeypatch.setattr(router_mod, "route_product", lambda *a, **kw: [])

    pipe = _build_pipeline()
    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert result.output_path is None
    assert any("Router returned no" in i for i in result.issues)


def test_run_single_all_attempts_fail_records_failure(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """All max_attempts generation calls return None → failure result."""
    monkeypatch.setattr(generate_mod, "generate_gemini", lambda *a, **kw: None)
    # No retry delay so the test runs fast
    pipe = _build_pipeline()
    pipe.config.retry_delay_seconds = 0.0

    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert result.output_path is None
    assert result.attempts == pipe.config.max_attempts
    assert any("Generation failed" in i for i in result.issues)


def test_run_single_qa_exception_records_issue_but_returns_result(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """QA tournament exception is caught and surfaced as an issue without crashing."""
    monkeypatch.setattr(
        tournament_mod,
        "run_tournament",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("tournament crashed")),
    )

    pipe = _build_pipeline()
    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    # Output WAS saved (generation completed); QA failed and issue captured
    assert result.output_path is not None
    assert any("QA failed" in i for i in result.issues)


def test_run_single_auto_reject_below_threshold(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """Score below qa_auto_reject (50) marks qa_passed=False even after refine."""
    # Returns 30/100 → below 50 auto-reject; refinement won't help but tracker
    # should still mark passed=False.
    monkeypatch.setattr(
        tournament_mod, "run_tournament", lambda *a, **kw: _make_tournament_result(score=30.0)
    )
    # Disable Kontext to skip refinement path (text/logo scores are 30 each so it would trigger)
    monkeypatch.setattr(engine_fal_mod, "refine_with_kontext", lambda *a, **kw: None)
    monkeypatch.setattr(generate_mod, "composite_gemini", lambda *a, **kw: None)

    pipe = _build_pipeline()
    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert result.qa_passed is False
    assert result.qa_score == 30.0


def test_run_single_caches_vision_description_across_views(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """Repeated calls for the same SKU hit the in-memory vision cache."""
    call_count = {"n": 0}

    def _count_describe(*a, **kw):
        call_count["n"] += 1
        return _stub_vision_desc()

    monkeypatch.setattr(vision_describe_mod, "describe_product", _count_describe)

    pipe = _build_pipeline()
    pipe.run_single(_sample_product(), fake_source_image, view="front")
    pipe.run_single(_sample_product(), fake_source_image, view="back")

    # describe_product called once; second view used the cached vision_desc
    assert call_count["n"] == 1


# ── run_batch ──────────────────────────────────────────────────────────────


def test_run_batch_aggregates_pass_fail_skip_counts(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """run_batch summary counts passing, failing (had output, low score), and skipped products."""
    products = [
        {**_sample_product("br-001"), "source_image": str(fake_source_image)},
        {**_sample_product("br-002"), "source_image": str(fake_source_image)},
        {**_sample_product("br-003"), "source_image": "/nonexistent/path.jpg"},  # skipped
    ]

    # br-001 passes (score=92), br-002 fails QA (score=40) → not refined since refine returns None
    qa_scores = iter([92.0, 40.0])

    def _qa(*a, **kw):
        return _make_tournament_result(score=next(qa_scores))

    monkeypatch.setattr(tournament_mod, "run_tournament", _qa)
    monkeypatch.setattr(engine_fal_mod, "refine_with_kontext", lambda *a, **kw: None)
    monkeypatch.setattr(generate_mod, "composite_gemini", lambda *a, **kw: None)

    pipe = _build_pipeline()
    pipe.config.retry_delay_seconds = 0.0
    results = pipe.run_batch(products, views=["front"])

    assert len(results) == 3
    # br-001: output + passed
    # br-002: output + not passed (low QA)
    # br-003: no output (skipped, missing source)
    has_output = [r for r in results if r.output_path]
    no_output = [r for r in results if not r.output_path]
    assert len(has_output) == 2
    assert len(no_output) == 1
    assert no_output[0].sku == "br-003"
    assert any("No source image" in i for i in no_output[0].issues)


def test_run_batch_skip_emits_one_result_per_view(
    isolated_project_root, stub_registry, stub_dependencies
):
    """A skipped product still emits one result per requested view (for accounting)."""
    products = [{**_sample_product("br-x"), "source_image": "/nope.jpg"}]
    pipe = _build_pipeline()
    pipe.config.retry_delay_seconds = 0.0
    results = pipe.run_batch(products, views=["front", "back", "branding"])

    assert len(results) == 3
    assert all(r.output_path is None for r in results)
    assert {r.view for r in results} == {"front", "back", "branding"}


# ── _build_refinement_prompt edges (extra coverage on top of test_refinement_prompt.py) ──


def test_build_refinement_prompt_includes_score_and_sku_in_header():
    """Header always carries the SKU and the QA score for traceability."""
    result = _make_tournament_result(score=42.0)
    prompt = _build_refinement_prompt("Test Product", "test-001", result)
    assert "test-001" in prompt
    assert "42/100" in prompt


# ── from_env factory (90% coverage push) ───────────────────────────────────


@pytest.fixture()
def env_factory_isolation(tmp_path: Path, monkeypatch):
    """Isolate from_env() from real environment + real client SDKs.

    Redirects PROJECT_ROOT, clears API key env vars, and stubs the
    client constructors so no real SDK initialization happens.
    """
    monkeypatch.setattr(pipeline_mod, "PROJECT_ROOT", tmp_path)
    for var in ("ANTHROPIC_API_KEY", "FAL_KEY", "FAL_AI_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    # Stub client factories — both live in nano_banana.client
    import nano_banana.client as client_mod

    monkeypatch.setattr(client_mod, "get_genai_client", lambda: MagicMock(name="genai"))
    monkeypatch.setattr(client_mod, "get_openai_client", lambda: MagicMock(name="openai"))
    return tmp_path


def test_from_env_constructs_pipeline_without_secrets_or_anthropic(env_factory_isolation):
    """No .env.secrets, no Anthropic key → still constructs with anthropic=None, fal=False."""
    pipe = ProductionPipeline.from_env()

    assert pipe.genai is not None
    assert pipe.openai is not None
    assert pipe.anthropic is None  # no ANTHROPIC_API_KEY
    assert pipe.fal_available is False  # no FAL_KEY


def test_from_env_loads_env_secrets_when_present(env_factory_isolation, monkeypatch):
    """A .env.secrets file at PROJECT_ROOT is read and injects vars into os.environ."""
    secrets_path = env_factory_isolation / ".env.secrets"
    secrets_path.write_text("ANTHROPIC_API_KEY=test-anthropic-key\nFAL_KEY=test-fal-key\n")

    # Stub the anthropic SDK so creating the client doesn't make a real call
    fake_anthropic_module = MagicMock()
    fake_anthropic_module.Anthropic = MagicMock(return_value=MagicMock(name="anthropic-client"))
    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic_module)

    pipe = ProductionPipeline.from_env()

    assert pipe.anthropic is not None
    assert pipe.fal_available is True
    fake_anthropic_module.Anthropic.assert_called_once_with(api_key="test-anthropic-key")


def test_from_env_creates_anthropic_when_key_already_in_env(env_factory_isolation, monkeypatch):
    """ANTHROPIC_API_KEY already in environ (no .env.secrets file) still constructs the client."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "preset-key")
    fake_anthropic_module = MagicMock()
    fake_anthropic_module.Anthropic = MagicMock(return_value=MagicMock(name="anthropic"))
    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic_module)

    pipe = ProductionPipeline.from_env()

    assert pipe.anthropic is not None
    fake_anthropic_module.Anthropic.assert_called_once()


def test_from_env_skips_anthropic_on_import_error(env_factory_isolation, monkeypatch, caplog):
    """When ANTHROPIC_API_KEY is set but the anthropic package isn't installed, log + continue."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "some-key")

    real_import = (
        __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__
    )

    def _fake_import(name, *args, **kwargs):
        if name == "anthropic":
            raise ImportError("anthropic not installed in test env")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", _fake_import)

    import logging

    with caplog.at_level(logging.WARNING, logger="nano_banana.pipeline"):
        pipe = ProductionPipeline.from_env()

    assert pipe.anthropic is None
    assert any("anthropic package not installed" in rec.message for rec in caplog.records)


def test_from_env_loads_pipeline_config_from_json(env_factory_isolation):
    """A pipeline-config.json file at PROJECT_ROOT/data/ is loaded instead of production preset."""
    config_path = env_factory_isolation / "data" / "pipeline-config.json"
    config_path.parent.mkdir(parents=True)
    # Override max_attempts to 99 to confirm the JSON beat the production default (3)
    config_path.write_text('{"max_attempts": 99}')

    pipe = ProductionPipeline.from_env()
    assert pipe.config.max_attempts == 99


def test_from_env_falls_back_to_production_config_without_json(env_factory_isolation):
    """No pipeline-config.json → PipelineConfig.production() defaults."""
    pipe = ProductionPipeline.from_env()
    assert pipe.config.max_attempts == 3  # production default


# ── Engine-branch coverage (gpt-image / flux-pro / unavailable) ────────────


def test_run_single_uses_gpt_image_engine(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """Router returning gpt-image dispatches to generate_gpt with openai client."""
    monkeypatch.setattr(
        router_mod,
        "route_product",
        lambda *a, **kw: [_make_route_decision(engine="gpt-image", cost=0.08)],
    )
    gpt_calls = []

    def _spy_gpt(client, prompt, source_path):
        gpt_calls.append((client, prompt, source_path))
        return _png_bytes()

    monkeypatch.setattr(generate_mod, "generate_gpt", _spy_gpt)

    pipe = _build_pipeline()
    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert result.engine_used == "gpt-image"
    assert len(gpt_calls) == 1
    assert result.cost_usd == pytest.approx(0.08)


def test_run_single_uses_flux_pro_engine(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """Router returning flux-pro dispatches to generate_flux_fal when fal_available."""
    monkeypatch.setattr(
        router_mod,
        "route_product",
        lambda *a, **kw: [_make_route_decision(engine="flux-pro", cost=0.035)],
    )
    flux_calls = []

    def _spy_flux(source_path, prompt):
        flux_calls.append((source_path, prompt))
        return _png_bytes()

    monkeypatch.setattr(engine_fal_mod, "generate_flux_fal", _spy_flux)

    pipe = _build_pipeline()
    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert result.engine_used == "flux-pro"
    assert len(flux_calls) == 1


def test_run_single_skips_engine_when_required_client_missing(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch, caplog
):
    """Engine 'gpt-image' with self.openai=None → warn 'Engine unavailable' and continue."""
    monkeypatch.setattr(
        router_mod,
        "route_product",
        lambda *a, **kw: [_make_route_decision(engine="gpt-image", cost=0.08)],
    )

    pipe = ProductionPipeline(
        genai_client=MagicMock(),
        openai_client=None,  # ← gpt-image engine cannot dispatch
        anthropic_client=MagicMock(),
        fal_available=False,
    )
    pipe.config.retry_delay_seconds = 0.0

    import logging

    with caplog.at_level(logging.WARNING, logger="nano_banana.pipeline"):
        result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert any("Engine gpt-image unavailable" in rec.message for rec in caplog.records)
    assert result.output_path is None
    assert any("Generation failed" in i for i in result.issues)


def test_run_single_handles_generation_exception(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """When the generation function raises, the attempt loop logs and retries."""
    call_count = {"n": 0}

    def _raise_then_succeed(*a, **kw):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("Gemini API 503")
        return _png_bytes()

    monkeypatch.setattr(generate_mod, "generate_gemini", _raise_then_succeed)
    pipe = _build_pipeline()
    pipe.config.retry_delay_seconds = 0.0

    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert result.attempts >= 2
    assert result.output_path is not None  # second attempt succeeded


# ── QA source bundle photo ────────────────────────────────────────────────


def test_run_single_uses_real_product_photo_for_qa_when_available(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """When the bundle has photo-front.jpg, QA uses it (not the techflat) as source."""
    bundle = isolated_project_root / "data" / "product-bundles" / "BLACK Rose Crewneck"
    bundle.mkdir(parents=True)
    photo_front = bundle / "photo-front.jpg"
    Image.new("RGB", (10, 10)).save(photo_front, format="JPEG")

    qa_calls = []

    def _spy_tournament(*a, **kw):
        qa_calls.append(kw.get("source_path") or a[1])
        return _make_tournament_result(score=92.0)

    monkeypatch.setattr(tournament_mod, "run_tournament", _spy_tournament)

    pipe = _build_pipeline()
    pipe.run_single(_sample_product(), fake_source_image, view="front")

    # First QA call's source_path should be the bundle's photo-front, not the techflat
    assert len(qa_calls) >= 1
    assert qa_calls[0] == photo_front


# ── Refinement fallback paths ──────────────────────────────────────────────


def test_run_single_falls_back_to_composite_gemini_when_kontext_returns_none(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """Kontext returning None falls back to Gemini composite_gemini with same prompt."""
    qa_results = [
        _make_tournament_result(score=72.0, text=55, logo=80),  # triggers refine
        _make_tournament_result(score=85.0, text=90, logo=90),  # post-refine
    ]
    monkeypatch.setattr(tournament_mod, "run_tournament", lambda *a, **kw: qa_results.pop(0))
    monkeypatch.setattr(engine_fal_mod, "refine_with_kontext", lambda *a, **kw: None)

    composite_calls = []

    def _spy_composite(client, candidate_path, source_path, prompt):
        composite_calls.append(prompt)
        return _png_bytes()

    monkeypatch.setattr(generate_mod, "composite_gemini", _spy_composite)

    pipe = _build_pipeline()
    result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert len(composite_calls) == 1
    assert result.refinement_applied is True


def test_run_single_post_refine_qa_exception_logged_but_pipeline_continues(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch, caplog
):
    """Post-refine tournament raising is caught — pipeline returns the result, logs the failure."""
    call_count = {"n": 0}

    def _qa_first_ok_then_raises(*a, **kw):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _make_tournament_result(score=72.0, text=55, logo=80)  # triggers refine
        raise RuntimeError("post-refine QA crashed")

    monkeypatch.setattr(tournament_mod, "run_tournament", _qa_first_ok_then_raises)

    import logging

    pipe = _build_pipeline()
    with caplog.at_level(logging.ERROR, logger="nano_banana.pipeline"):
        result = pipe.run_single(_sample_product(), fake_source_image, view="front")

    assert result.refinement_applied is True
    assert any("Post-refine QA failed" in rec.message for rec in caplog.records)


# ── run_batch defaults ─────────────────────────────────────────────────────


def test_run_batch_uses_default_views_when_views_none(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies
):
    """Calling run_batch(views=None) uses config.default_views (front+back+branding)."""
    products = [{**_sample_product(), "source_image": str(fake_source_image)}]
    pipe = _build_pipeline()
    pipe.config.retry_delay_seconds = 0.0

    results = pipe.run_batch(products, views=None)

    assert len(results) == 3
    assert {r.view for r in results} == {"front", "back", "branding"}


def test_run_batch_overrides_output_dir_when_provided(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, tmp_path
):
    """Passing output_dir to run_batch overrides config.output_dir."""
    products = [{**_sample_product(), "source_image": str(fake_source_image)}]
    pipe = _build_pipeline()
    pipe.config.retry_delay_seconds = 0.0

    custom_dir = tmp_path / "custom-out"
    pipe.run_batch(products, views=["front"], output_dir=custom_dir)

    assert pipe.config.output_dir == str(custom_dir)


# ── _get_or_cache_vision disk paths ────────────────────────────────────────


def test_get_or_cache_vision_loads_from_disk_cache(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies
):
    """A pre-existing JSON cache file is loaded instead of calling describe_product."""
    pipe = _build_pipeline()
    cache_dir = isolated_project_root / pipe.config.vision_cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached = {"garment_type": "DISK_CACHED", "fabric_appearance": "from-disk"}
    (cache_dir / "br-001-vision.json").write_text(json.dumps(cached))

    ctx = pipe._get_or_cache_vision({"sku": "br-001"}, fake_source_image)

    assert ctx.inferred["garment_type"] == "DISK_CACHED"
    assert ctx.inferred["fabric_appearance"] == "from-disk"


def test_get_or_cache_vision_falls_through_on_corrupted_disk_cache(
    isolated_project_root, fake_source_image, stub_registry, stub_dependencies, monkeypatch
):
    """Invalid JSON in disk cache is silently dropped — pipeline calls describe_product instead."""
    pipe = _build_pipeline()
    cache_dir = isolated_project_root / pipe.config.vision_cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "br-001-vision.json").write_text("{ not valid json }")

    describe_calls = []

    def _spy_describe(*a, **kw):
        describe_calls.append(1)
        return {"garment_type": "fresh-describe"}

    monkeypatch.setattr(vision_describe_mod, "describe_product", _spy_describe)

    ctx = pipe._get_or_cache_vision({"sku": "br-001"}, fake_source_image)

    assert len(describe_calls) == 1
    assert ctx.inferred["garment_type"] == "fresh-describe"


def test_get_or_cache_vision_returns_empty_context_when_describe_returns_none(
    isolated_project_root, fake_source_image, stub_registry, monkeypatch
):
    """describe_product returning None yields VisionContext(inferred={}), not crashes."""
    monkeypatch.setattr(vision_describe_mod, "describe_product", lambda *a, **kw: None)

    pipe = _build_pipeline()
    ctx = pipe._get_or_cache_vision({"sku": "br-x"}, fake_source_image)

    assert isinstance(ctx, VisionContext)
    assert ctx.inferred == {}


# ── _find_bundle_dir manifest-search edge cases ───────────────────────────


def test_find_bundle_dir_skips_non_directory_entries(isolated_project_root):
    """A file (not directory) in the bundle root is skipped during manifest search."""
    bundle_root = isolated_project_root / "data" / "product-bundles"
    # A loose file in bundle_root — should be skipped without error
    (bundle_root / "loose-file.txt").write_text("not a bundle")

    result = _find_bundle_dir("Nonexistent Product", "br-x")
    assert result is None


def test_find_bundle_dir_handles_corrupted_manifest_json(isolated_project_root):
    """A directory with malformed manifest.json is silently skipped."""
    bundle_root = isolated_project_root / "data" / "product-bundles"
    bad_dir = bundle_root / "bad-manifest"
    bad_dir.mkdir()
    (bad_dir / "manifest.json").write_text("{ unclosed brace")

    # No match by name OR by manifest → None (no exception bubbled up)
    result = _find_bundle_dir("Different Name", "any-sku")
    assert result is None


def test_find_bundle_dir_skips_directories_without_manifest(isolated_project_root):
    """Directories lacking manifest.json don't raise during the SKU search."""
    bundle_root = isolated_project_root / "data" / "product-bundles"
    (bundle_root / "no-manifest-here").mkdir()

    result = _find_bundle_dir("Different Name", "any-sku")
    assert result is None


# ── _load_bundle_refs branch coverage ─────────────────────────────────────


def test_load_bundle_refs_back_view_includes_techflat_back(
    isolated_project_root, fake_source_image
):
    """view='back' should include techflat-back when present."""
    bundle = isolated_project_root / "data" / "product-bundles" / "Test Product"
    bundle.mkdir(parents=True)
    Image.new("RGB", (10, 10)).save(bundle / "techflat-back.jpg", format="JPEG")

    refs = _load_bundle_refs("Test Product", "br-001", fake_source_image, "back")
    assert any("techflat-back" in str(p) for _label, p in refs)


def test_load_bundle_refs_branding_view_includes_no_techflat(
    isolated_project_root, fake_source_image
):
    """view='branding' (neither front nor back) skips both techflats."""
    bundle = isolated_project_root / "data" / "product-bundles" / "Test Product"
    bundle.mkdir(parents=True)
    Image.new("RGB", (10, 10)).save(bundle / "techflat-front.jpg", format="JPEG")
    Image.new("RGB", (10, 10)).save(bundle / "techflat-back.jpg", format="JPEG")

    refs = _load_bundle_refs("Test Product", "br-001", fake_source_image, "branding")
    assert all("techflat" not in str(p) for _label, p in refs)


def test_load_bundle_refs_excludes_files_matching_source_path(isolated_project_root, tmp_path):
    """A bundle file at the same path as source_path is filtered out (no self-reference)."""
    bundle = isolated_project_root / "data" / "product-bundles" / "Test Product"
    bundle.mkdir(parents=True)
    source_in_bundle = bundle / "source-photo.jpg"
    Image.new("RGB", (10, 10)).save(source_in_bundle, format="JPEG")

    # Pass the bundle file ITSELF as the source — it should be excluded from refs
    refs = _load_bundle_refs("Test Product", "br-001", source_in_bundle, "front")
    assert all(p != source_in_bundle for _label, p in refs)


def test_load_bundle_refs_caps_at_5_references(isolated_project_root, fake_source_image):
    """Even with many possible refs, the function returns at most 5."""
    bundle = isolated_project_root / "data" / "product-bundles" / "Test Product"
    bundle.mkdir(parents=True)
    # Only photo + techflat are scanned (others excluded by tag), so this is more
    # a smoke test of the cap. Drop several candidates of each tag.
    for stem in ("source-photo", "photo-front"):
        for ext, fmt in (("jpg", "JPEG"), ("png", "PNG"), ("webp", "WEBP")):
            Image.new("RGB", (10, 10)).save(bundle / f"{stem}.{ext}", format=fmt)
    Image.new("RGB", (10, 10)).save(bundle / "techflat-front.jpg", format="JPEG")

    refs = _load_bundle_refs("Test Product", "br-001", fake_source_image, "front")
    assert len(refs) <= 5


# ── _source_env_file edge cases ────────────────────────────────────────────


def test_source_env_file_skips_lines_without_equals(tmp_path):
    """Lines without `=` are skipped, not crashed on."""
    p = tmp_path / "weird.env"
    p.write_text("VALID=ok\nNO_EQUALS_HERE\nOTHER=fine\n")
    _source_env_file(p)

    import os

    assert os.environ.get("VALID") == "ok"


def test_source_env_file_skips_missing_file(tmp_path):
    """Pointing to a non-existent file should not raise (function checks exists upstream)."""
    # Note: _source_env_file itself doesn't check existence; from_env does. But the
    # function uses path.read_text() which raises FileNotFoundError. Pipeline only
    # calls it when path.exists() is True, so the function's contract assumes existence.
    # This test documents that contract by asserting the function raises on missing.
    import pytest

    nonexistent = tmp_path / "nope.env"
    with pytest.raises(FileNotFoundError):
        _source_env_file(nonexistent)
