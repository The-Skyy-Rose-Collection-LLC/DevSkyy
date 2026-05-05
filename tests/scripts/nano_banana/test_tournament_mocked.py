"""Mock-based tests for the 3-judge tournament.

Layered coverage:
- Inner helpers (`_parse_json`, `_dna_to_spec`, `_build_judgment_from_json`,
  `_exception_repr`, `_zero_judgment`): pure-function tests, no mocks.
- Provider adapters (`judge_with_gpt`, `judge_with_gemini`,
  `judge_with_opus_synthesis`): mock the inner `_judge_call_*`/
  `_opus_synthesis_call` to exercise the `judge_with` scaffold and JSON
  parsing.
- Orchestrator (`run_tournament`): mock the three top-level judge
  functions to verify aggregation, missing-client paths, and the
  ValueError on zero vision judges.

No paid API calls.
"""

from __future__ import annotations

import concurrent.futures
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

import nano_banana.tournament as tournament  # noqa: E402
from nano_banana.tournament import (  # noqa: E402
    GEMINI_JUDGE_MODEL,
    GPT_JUDGE_MODEL,
    OPUS_SYNTHESIS_MODEL,
    JudgmentScore,
    TournamentResult,
    _build_judgment_from_json,
    _dna_to_spec,
    _exception_repr,
    _parse_json,
    _zero_judgment,
    judge_with_gemini,
    judge_with_gpt,
    judge_with_opus_synthesis,
    run_tournament,
)


@pytest.fixture()
def fake_image_pair(tmp_path: Path) -> tuple[Path, Path]:
    """Two real JPEG files on disk — small but valid."""
    src = tmp_path / "source.jpg"
    cand = tmp_path / "candidate.jpg"
    Image.new("RGB", (32, 32), color=(0, 0, 0)).save(src, format="JPEG")
    Image.new("RGB", (32, 32), color=(50, 50, 50)).save(cand, format="JPEG")
    return src, cand


# ── _parse_json ────────────────────────────────────────────────────────────


def test_parse_json_clean_object():
    assert _parse_json('{"overall": 75, "issues": []}') == {"overall": 75, "issues": []}


def test_parse_json_strips_markdown_fences():
    text = '```json\n{"overall": 80}\n```'
    assert _parse_json(text) == {"overall": 80}


def test_parse_json_repairs_truncated_brace():
    """Truncated JSON missing closing brace is repaired."""
    text = '{"overall": 65, "garment_type": 70'
    result = _parse_json(text)
    assert result.get("overall") == 65
    assert result.get("garment_type") == 70


def test_parse_json_regex_fallback_extracts_numeric_fields():
    """Garbage non-JSON with embedded numeric fields → regex extract."""
    text = 'WAS NOT JSON. "overall": 55, "color_accuracy": 60, the model rambled'
    result = _parse_json(text)
    assert result.get("overall") == 55
    assert result.get("color_accuracy") == 60


def test_parse_json_empty_input_returns_empty_dict():
    assert _parse_json("") == {}
    assert _parse_json("   \n  ") == {}


# ── _dna_to_spec lossy fallback path ───────────────────────────────────────


def test_dna_to_spec_renders_text_content_list():
    """text_content list with dicts gets formatted with location."""
    dna = {
        "garment_type": "varsity jacket",
        "base_color": "#0a0a0a",
        "text_content": [
            {"text": "LOVE HURTS", "location": "back"},
            {"text": "1995", "location": "right sleeve"},
        ],
    }
    out = _dna_to_spec(dna)
    assert 'Text: "LOVE HURTS" at back; "1995" at right sleeve' in out


def test_dna_to_spec_renders_logos_list():
    dna = {
        "garment_type": "crewneck",
        "logos": [{"type": "embroidered rose", "position": "front chest"}],
    }
    out = _dna_to_spec(dna)
    assert "Logos: embroidered rose at front chest" in out


def test_dna_to_spec_construction_dict_truncates_to_5_items():
    """Construction dict caps at 5 entries to avoid prompt bloat."""
    dna = {
        "garment_type": "hoodie",
        "construction": {f"feature_{i}": f"value_{i}" for i in range(8)},
    }
    out = _dna_to_spec(dna)
    # Feature 0-4 present, 5+ omitted
    assert "feature_0: value_0" in out
    assert "feature_5" not in out


def test_dna_to_spec_construction_list_form():
    dna = {
        "garment_type": "shorts",
        "construction": ["elastic waist", "side pockets", "drawstring"],
    }
    out = _dna_to_spec(dna)
    assert "Construction: elastic waist, side pockets, drawstring" in out


def test_dna_to_spec_includes_fabric_when_present():
    dna = {"garment_type": "shorts", "fabric": "french terry cotton"}
    out = _dna_to_spec(dna)
    assert "Fabric: french terry cotton" in out


# ── _build_judgment_from_json ──────────────────────────────────────────────


def test_build_judgment_coerces_non_int_to_zero():
    """Malformed numeric fields default to 0 instead of raising."""
    data = {
        "overall": "not a number",
        "color_accuracy": None,
        "issues": ["one"],
        "suggested_fixes": [],
    }
    j = _build_judgment_from_json("test-judge", data, raw="...")
    assert j.overall == 0
    assert j.color_accuracy == 0
    assert j.issues == ["one"]
    assert j.judge == "test-judge"


def test_build_judgment_synthesis_fields_propagate():
    """rationale + vision_consensus + hallucination_veto round-trip from JSON."""
    data = {
        "overall": 45,
        "rationale": "GPT and Gemini disagreed on logo placement",
        "vision_consensus": "partial",
        "hallucination_veto": True,
    }
    j = _build_judgment_from_json("opus-test", data, raw="...")
    assert j.rationale.startswith("GPT and Gemini")
    assert j.vision_consensus == "partial"
    assert j.hallucination_veto is True


# ── _exception_repr / _zero_judgment ───────────────────────────────────────


def test_exception_repr_handles_empty_str_exception():
    """concurrent.futures.TimeoutError() has empty str() — repr should still show class."""
    exc = concurrent.futures.TimeoutError()
    rendered = _exception_repr(exc)
    assert "TimeoutError" in rendered


def test_exception_repr_includes_message_when_present():
    rendered = _exception_repr(RuntimeError("boom"))
    assert "RuntimeError" in rendered
    assert "boom" in rendered


def test_zero_judgment_marks_unavailable():
    """Zero-score judgment has available=False and reason in issues."""
    j = _zero_judgment("model-x", "client not configured")
    assert j.available is False
    assert j.overall == 0
    assert "client not configured" in j.issues[0]


# ── judge_with_gpt scaffold ────────────────────────────────────────────────


def test_judge_with_gpt_parses_json_response(monkeypatch, fake_image_pair):
    """Real `judge_with` scaffold + mocked inner adapter → valid JudgmentScore."""
    src, cand = fake_image_pair
    monkeypatch.setattr(
        tournament,
        "_judge_call_gpt",
        lambda *args, **kwargs: (
            '{"garment_type": 80, "color_accuracy": 75, "text_accuracy": 70, '
            '"logo_accuracy": 72, "construction_accuracy": 78, "no_hallucinations": 85, '
            '"overall": 76, "issues": ["minor color drift"], "suggested_fixes": ["match #0a0a0a"]}'
        ),
    )

    j = judge_with_gpt(client=MagicMock(), source_path=src, candidate_path=cand, dna={})

    assert j.judge == GPT_JUDGE_MODEL
    assert j.overall == 76
    assert j.color_accuracy == 75
    assert "minor color drift" in j.issues
    assert "match #0a0a0a" in j.suggested_fixes


def test_judge_with_gpt_returns_zero_on_adapter_exception(monkeypatch, fake_image_pair):
    """Inner adapter exception is caught — scaffold returns zero JudgmentScore."""
    src, cand = fake_image_pair

    def _boom(*args, **kwargs):
        raise RuntimeError("OpenAI API 503")

    monkeypatch.setattr(tournament, "_judge_call_gpt", _boom)

    j = judge_with_gpt(client=MagicMock(), source_path=src, candidate_path=cand, dna={})

    assert j.overall == 0
    assert j.judge == GPT_JUDGE_MODEL
    assert any("OpenAI API 503" in s for s in j.issues)


def test_judge_with_gpt_returns_zero_on_empty_response(monkeypatch, fake_image_pair):
    """Empty string response → ValueError inside scaffold → zero JudgmentScore."""
    src, cand = fake_image_pair
    monkeypatch.setattr(tournament, "_judge_call_gpt", lambda *args, **kwargs: "")

    j = judge_with_gpt(client=MagicMock(), source_path=src, candidate_path=cand, dna={})

    assert j.overall == 0


def test_judge_with_gemini_parses_json_response(monkeypatch, fake_image_pair):
    """Gemini scaffold path mirrors GPT — same parser, different model label."""
    src, cand = fake_image_pair
    monkeypatch.setattr(
        tournament,
        "_judge_call_gemini",
        lambda *args, **kwargs: (
            '{"overall": 88, "color_accuracy": 90, "garment_type": 85, '
            '"text_accuracy": 80, "logo_accuracy": 88, "construction_accuracy": 90, '
            '"no_hallucinations": 92, "issues": [], "suggested_fixes": []}'
        ),
    )

    j = judge_with_gemini(client=MagicMock(), source_path=src, candidate_path=cand, dna={})

    assert j.judge == GEMINI_JUDGE_MODEL
    assert j.overall == 88


def test_judge_with_gpt_uses_dossier_spec_when_present(monkeypatch, fake_image_pair):
    """When dna has `spec`, the judge prompt uses it verbatim instead of synthesizing."""
    src, cand = fake_image_pair
    captured = {}

    def _capture(*args, **kwargs):
        # Adapter signature: (client, source_path, candidate_path, src_b64, src_mime, cand_b64, cand_mime, spec)
        captured["spec"] = args[7]
        return '{"overall": 70, "issues": [], "suggested_fixes": []}'

    monkeypatch.setattr(tournament, "_judge_call_gpt", _capture)

    canonical_spec = "CANONICAL_DOSSIER_SPEC_TEXT_HERE"
    judge_with_gpt(
        client=MagicMock(),
        source_path=src,
        candidate_path=cand,
        dna={"spec": canonical_spec, "garment_type": "ignored"},
    )

    assert captured["spec"] == canonical_spec


# ── judge_with_opus_synthesis ──────────────────────────────────────────────


def _vision_score(judge: str, overall: int = 70) -> JudgmentScore:
    """Helper: build a vision-judge JudgmentScore for synthesis input."""
    return JudgmentScore(
        judge=judge,
        garment_type=overall,
        color_accuracy=overall,
        text_accuracy=overall,
        logo_accuracy=overall,
        construction_accuracy=overall,
        no_hallucinations=overall,
        overall=overall,
        issues=[],
        suggested_fixes=[],
        raw_response="",
    )


def test_judge_with_opus_synthesis_parses_json_with_synth_fields(monkeypatch):
    """Opus returns rationale + consensus + veto fields; all propagate."""
    monkeypatch.setattr(
        tournament,
        "_opus_synthesis_call",
        lambda *args, **kwargs: (
            '{"overall": 55, "garment_type": 80, "color_accuracy": 70, '
            '"text_accuracy": 60, "logo_accuracy": 50, "construction_accuracy": 80, '
            '"no_hallucinations": 40, "rationale": "Logo wrong shape", '
            '"vision_consensus": "agree", "hallucination_veto": true, '
            '"issues": ["wrong logo"], "suggested_fixes": ["fix logo"]}'
        ),
    )

    gpt = _vision_score(GPT_JUDGE_MODEL, 60)
    gem = _vision_score(GEMINI_JUDGE_MODEL, 65)
    j = judge_with_opus_synthesis(client=MagicMock(), gpt=gpt, gemini=gem, dna={"spec": "..."})

    assert j.judge == OPUS_SYNTHESIS_MODEL
    assert j.overall == 55
    assert j.rationale.startswith("Logo wrong")
    assert j.vision_consensus == "agree"
    assert j.hallucination_veto is True


def test_judge_with_opus_synthesis_zero_score_on_empty_response(monkeypatch):
    """Empty string from Opus → zero JudgmentScore with synthesis error reason."""
    monkeypatch.setattr(tournament, "_opus_synthesis_call", lambda *args, **kwargs: "")

    j = judge_with_opus_synthesis(
        client=MagicMock(),
        gpt=_vision_score(GPT_JUDGE_MODEL),
        gemini=_vision_score(GEMINI_JUDGE_MODEL),
        dna={"spec": "..."},
    )

    assert j.overall == 0
    assert j.judge == OPUS_SYNTHESIS_MODEL
    assert any("synthesis error" in s for s in j.issues)


def test_judge_with_opus_synthesis_zero_score_on_api_exception(monkeypatch):
    """Anthropic SDK exception → zero JudgmentScore (matches GPT/Gemini path)."""
    monkeypatch.setattr(
        tournament,
        "_opus_synthesis_call",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("Anthropic 429 rate limit")),
    )

    j = judge_with_opus_synthesis(
        client=MagicMock(),
        gpt=_vision_score(GPT_JUDGE_MODEL),
        gemini=_vision_score(GEMINI_JUDGE_MODEL),
        dna={"spec": "..."},
    )

    assert j.overall == 0


# ── run_tournament orchestration ───────────────────────────────────────────


def _vision_with_overall(overall: int) -> JudgmentScore:
    """Vision-judge result with explicit overall (for aggregation tests)."""
    return JudgmentScore(
        judge="vision-stub",
        garment_type=overall,
        color_accuracy=overall,
        text_accuracy=overall,
        logo_accuracy=overall,
        construction_accuracy=overall,
        no_hallucinations=overall,
        overall=overall,
        issues=[],
        suggested_fixes=[],
        raw_response="",
    )


def _synthesis_with_overall(overall: int, veto: bool = False) -> JudgmentScore:
    return JudgmentScore(
        judge=OPUS_SYNTHESIS_MODEL,
        garment_type=overall,
        color_accuracy=overall,
        text_accuracy=overall,
        logo_accuracy=overall,
        construction_accuracy=overall,
        no_hallucinations=overall,
        overall=overall,
        issues=[],
        suggested_fixes=[],
        raw_response="",
        rationale="...",
        vision_consensus="agree",
        hallucination_veto=veto,
    )


def test_run_tournament_aggregate_equals_synthesis_overall(monkeypatch, fake_image_pair):
    """With all three judges present, aggregate_score = synthesis_overall."""
    src, cand = fake_image_pair
    monkeypatch.setattr(tournament, "judge_with_gpt", lambda *a, **kw: _vision_with_overall(80))
    monkeypatch.setattr(tournament, "judge_with_gemini", lambda *a, **kw: _vision_with_overall(70))
    monkeypatch.setattr(
        tournament, "judge_with_opus_synthesis", lambda *a, **kw: _synthesis_with_overall(65)
    )

    clients = {"openai": MagicMock(), "gemini": MagicMock(), "anthropic": MagicMock()}
    result = run_tournament(clients, src, cand, dna={"spec": "..."})

    assert isinstance(result, TournamentResult)
    assert result.aggregate_score == 65.0  # synthesis canonical
    assert result.synthesis_overall == 65.0
    assert result.vision_pair_mean == 75.0  # (80 + 70) / 2
    assert len(result.judges) == 3


def test_run_tournament_falls_back_to_vision_pair_mean_without_synthesis(
    monkeypatch, fake_image_pair
):
    """No anthropic client → no synthesis judge → aggregate = vision_pair_mean."""
    src, cand = fake_image_pair
    monkeypatch.setattr(tournament, "judge_with_gpt", lambda *a, **kw: _vision_with_overall(82))
    monkeypatch.setattr(tournament, "judge_with_gemini", lambda *a, **kw: _vision_with_overall(78))

    clients = {"openai": MagicMock(), "gemini": MagicMock()}  # no anthropic
    result = run_tournament(clients, src, cand, dna={"spec": "..."})

    assert result.synthesis_overall is None
    assert result.aggregate_score == 80.0  # (82 + 78) / 2
    assert result.vision_pair_mean == 80.0
    assert len(result.judges) == 2


def test_run_tournament_one_vision_judge_runs_with_warning(monkeypatch, fake_image_pair, caplog):
    """Only one vision client → tournament runs degraded; missing slot is placeholder."""
    src, cand = fake_image_pair
    monkeypatch.setattr(tournament, "judge_with_gpt", lambda *a, **kw: _vision_with_overall(72))
    # judge_with_gemini should NOT be called since gemini client is missing
    monkeypatch.setattr(
        tournament,
        "judge_with_gemini",
        lambda *a, **kw: pytest.fail("gemini judge ran without a client"),
    )
    # Synthesis still runs against the placeholder
    monkeypatch.setattr(
        tournament, "judge_with_opus_synthesis", lambda *a, **kw: _synthesis_with_overall(60)
    )

    import logging

    clients = {"openai": MagicMock(), "anthropic": MagicMock()}
    with caplog.at_level(logging.WARNING, logger="nano_banana.tournament"):
        result = run_tournament(clients, src, cand, dna={"spec": "..."})

    assert any("running with 1/2 judges" in rec.message.lower() for rec in caplog.records)
    assert result.aggregate_score == 60.0  # synthesis still runs
    assert result.vision_pair_mean == 72.0  # Only the available vision judge counts


def test_run_tournament_zero_vision_judges_raises(fake_image_pair):
    """No vision clients at all → ValueError. Synthesis without vision is meaningless."""
    src, cand = fake_image_pair
    with pytest.raises(ValueError, match="no vision-judge clients"):
        run_tournament(
            clients={"anthropic": MagicMock()}, source_path=src, candidate_path=cand, dna={}
        )


def test_run_tournament_dedupes_fixes_across_judges(monkeypatch, fake_image_pair):
    """all_fixes dedupes case-insensitively across the three judges."""
    src, cand = fake_image_pair

    def _make_with_fixes(label: str, overall: int, fixes: list[str]) -> JudgmentScore:
        j = _vision_with_overall(overall)
        return JudgmentScore(
            judge=label,
            garment_type=j.garment_type,
            color_accuracy=j.color_accuracy,
            text_accuracy=j.text_accuracy,
            logo_accuracy=j.logo_accuracy,
            construction_accuracy=j.construction_accuracy,
            no_hallucinations=j.no_hallucinations,
            overall=j.overall,
            issues=[],
            suggested_fixes=fixes,
            raw_response="",
        )

    monkeypatch.setattr(
        tournament,
        "judge_with_gpt",
        lambda *a, **kw: _make_with_fixes(GPT_JUDGE_MODEL, 70, ["Match #0a0a0a", "Sharpen logo"]),
    )
    monkeypatch.setattr(
        tournament,
        "judge_with_gemini",
        lambda *a, **kw: _make_with_fixes(
            GEMINI_JUDGE_MODEL, 70, ["match #0a0a0a", "Remove cloud"]
        ),
    )

    result = run_tournament(
        clients={"openai": MagicMock(), "gemini": MagicMock()},
        source_path=src,
        candidate_path=cand,
        dna={},
    )

    # "Match #0a0a0a" / "match #0a0a0a" collapse to one entry; the order
    # is whoever's was emitted first (GPT runs first in this configuration).
    fixes_lower = [f.lower() for f in result.all_fixes]
    assert fixes_lower.count("match #0a0a0a") == 1
    assert "sharpen logo" in fixes_lower
    assert "remove cloud" in fixes_lower


def test_run_tournament_passing_threshold_drives_passed_98(monkeypatch, fake_image_pair):
    """passed_98 reflects aggregate_score against the configured threshold."""
    src, cand = fake_image_pair
    monkeypatch.setattr(tournament, "judge_with_gpt", lambda *a, **kw: _vision_with_overall(95))
    monkeypatch.setattr(tournament, "judge_with_gemini", lambda *a, **kw: _vision_with_overall(95))

    # Threshold 80 → 95 passes
    r1 = run_tournament(
        clients={"openai": MagicMock(), "gemini": MagicMock()},
        source_path=src,
        candidate_path=cand,
        dna={},
        passing_threshold=80.0,
    )
    assert r1.passed_98 is True

    # Threshold 98 → 95 fails (despite the field name, threshold is configurable)
    r2 = run_tournament(
        clients={"openai": MagicMock(), "gemini": MagicMock()},
        source_path=src,
        candidate_path=cand,
        dna={},
        passing_threshold=98.0,
    )
    assert r2.passed_98 is False


def test_run_tournament_propagates_synthesis_judgment_to_judges_list(monkeypatch, fake_image_pair):
    """Synthesis JudgmentScore is appended to .judges so callers can inspect veto/rationale."""
    src, cand = fake_image_pair
    monkeypatch.setattr(tournament, "judge_with_gpt", lambda *a, **kw: _vision_with_overall(70))
    monkeypatch.setattr(tournament, "judge_with_gemini", lambda *a, **kw: _vision_with_overall(70))
    monkeypatch.setattr(
        tournament,
        "judge_with_opus_synthesis",
        lambda *a, **kw: _synthesis_with_overall(45, veto=True),
    )

    result = run_tournament(
        clients={"openai": MagicMock(), "gemini": MagicMock(), "anthropic": MagicMock()},
        source_path=src,
        candidate_path=cand,
        dna={"spec": "..."},
    )

    assert result.synthesis_judge is not None
    assert result.synthesis_judge.hallucination_veto is True
    assert result.synthesis_judge.judge == OPUS_SYNTHESIS_MODEL
