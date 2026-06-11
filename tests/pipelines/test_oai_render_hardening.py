"""Unit tests for the oai_render hallucination-hardening layer.

Covers: injected-text sanitization, anti-collage prompt guardrails,
deterministic QC checks (decode / dimensions / collage bands), runtime
spend tracking, and the judged retry / quarantine loop in render_sku.
No network calls — the OpenAI client and QC judge are faked.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from scripts.oai_render import config
from scripts.oai_render import prompt as prompt_mod
from scripts.oai_render import qc
from scripts.oai_render.cost import SpendTracker
from scripts.oai_render.pipeline import SkuPlan, render_sku
from scripts.oai_render.prompt import (
    NEGATIVE_GUARDRAILS,
    PAIR_NEGATIVE_GUARDRAILS,
    build_pair_prompt,
    build_prompt,
    read_dossier,
    sanitize_injected_text,
    sanitize_name,
)
from scripts.oai_render.references import ReferenceImage

# ── Sanitizer ────────────────────────────────────────────────────────────────


def test_sanitizer_drops_view_enumeration_lines():
    text = (
        "## Construction\n"
        "Heavyweight 400gsm cotton fleece, ribbed cuffs.\n"
        "Front view shows the chest rose; back view shows the script.\n"
        "Double-needle stitching throughout."
    )
    out = sanitize_injected_text(text, source="test")
    assert "Front view" not in out
    assert "back view" not in out
    assert "Heavyweight 400gsm" in out
    assert "Double-needle" in out
    assert "## Construction" in out  # headings survive


def test_sanitizer_keeps_single_view_mention_and_colorway_facts():
    # Placement spec with ONE view mention and colorway construction facts are
    # legitimate dossier fidelity content — they must survive sanitization.
    text = (
        "Rose graphic sits on the LEFT thigh of the front view only.\n"
        "Embossed colorway — reduced 3-color palette of BLACK + WHITE + GREY.\n"
        "Front view shows the rose; back view shows the script; side view plain."
    )
    out = sanitize_injected_text(text, source="test")
    assert "LEFT thigh of the front view only" in out
    assert "Embossed colorway" in out
    assert "side view plain" not in out  # enumeration line (3 view mentions) dropped


def test_sanitizer_drops_availability_and_styling_lines():
    text = "Also available in crimson.\nPairs well when styled with the joggers.\nSilk lining."
    out = sanitize_injected_text(text, source="test")
    assert out == "Silk lining."


def test_sanitize_name_strips_triggers_and_flattens():
    assert sanitize_name("Black  Rose\nHoodie") == "Black Rose Hoodie"
    cleaned = sanitize_name("Bay Tee — available in white")
    assert "available in" not in cleaned
    assert cleaned.startswith("Bay Tee")


def test_read_dossier_sanitizes_and_caps(tmp_path: Path):
    dossier = tmp_path / "br-001.md"
    dossier.write_text(
        "---\nsku: br-001\n---\n"
        "## Construction\nFleece crewneck, embroidered rose.\n"
        "## Scene direction\nfront view, back view, three-quarter angles.\n"
        "## Materials\nShown from multiple angles in the lookbook.\nCotton-poly blend.\n",
        encoding="utf-8",
    )
    body = read_dossier(dossier)
    assert body is not None
    assert "Scene direction" not in body  # section strip
    assert "multiple angles" not in body  # line sanitizer
    assert "Fleece crewneck" in body
    assert "Cotton-poly blend" in body


# ── Prompt guardrails ────────────────────────────────────────────────────────


def test_guardrails_carry_anti_collage_enforcement():
    for block in (NEGATIVE_GUARDRAILS, PAIR_NEGATIVE_GUARDRAILS):
        assert "single full-bleed photograph" in block
        assert "No collage" in block


def test_build_prompt_sanitizes_name_and_indexes_references():
    p = build_prompt(
        name="Rose Tee — available in white",
        sku="sg-001",
        collection="signature",
        reference_labels=["REFERENCE IMAGE 1 — GARMENT TECH FLAT"],
        dossier_text=None,
        is_patch=False,
        style="ghost",
        view="front",
    )
    assert "available in" not in p.split("\n")[2]  # PRODUCT line is clean
    assert '"image 1" is the first' in p


def test_pair_prompt_assigns_body_zones_and_requires_both():
    p = build_pair_prompt(
        pair_label="br-001 + br-002",
        collection="black-rose",
        garments=[
            {
                "name": "Crewneck",
                "sku": "br-001",
                "reference_labels": [],
                "dossier_text": None,
                "is_patch": False,
            },
            {
                "name": "Joggers",
                "sku": "br-002",
                "reference_labels": [],
                "dossier_text": None,
                "is_patch": False,
            },
        ],
    )
    assert "upper body/torso" in p
    assert "lower body/legs" in p
    assert "BOTH garments MUST be visible" in p


# ── Deterministic QC checks ──────────────────────────────────────────────────


def _png_bytes(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


def _noise_render() -> np.ndarray:
    """A 'good' render: textured content crossing the central band everywhere."""
    w, h = config.EXPECTED_RENDER_SIZE
    rng = np.random.default_rng(7)
    return rng.integers(0, 255, size=(h, w, 3), dtype=np.uint8)


def test_deterministic_pass_on_clean_render():
    assert qc.deterministic_checks(_png_bytes(_noise_render())) == []


def test_deterministic_flags_invalid_bytes():
    assert qc.deterministic_checks(b"not a png") == ["invalid_image"]


def test_deterministic_flags_wrong_dimensions():
    arr = np.random.default_rng(7).integers(0, 255, size=(512, 512, 3), dtype=np.uint8)
    assert "wrong_dimensions" in qc.deterministic_checks(_png_bytes(arr))


def test_deterministic_flags_horizontal_collage_gutter():
    arr = _noise_render()
    mid = arr.shape[0] // 2
    arr[mid - 3 : mid + 3, :, :] = 255  # uniform full-width band through the center
    assert "collage_panels" in qc.deterministic_checks(_png_bytes(arr))


def test_deterministic_flags_vertical_collage_gutter():
    arr = _noise_render()
    mid = arr.shape[1] // 2
    arr[:, mid - 3 : mid + 3, :] = 250
    assert "collage_panels" in qc.deterministic_checks(_png_bytes(arr))


# ── Spend tracker ────────────────────────────────────────────────────────────


def test_spend_tracker_enforces_cap():
    t = SpendTracker(cap_usd=1.0)
    assert t.can_afford(0.40)
    t.add(0.40)
    t.add(0.40)
    assert not t.can_afford(0.40)
    assert t.remaining_usd == pytest.approx(0.20)


# ── render_sku judged retry loop ─────────────────────────────────────────────


class _FakeClient:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.calls = 0

    def edit(self, *, prompt: str, image_paths: list[Path]) -> bytes:
        self.calls += 1
        return self.payload


class _ScriptedGate:
    """QC gate double whose verdicts are scripted per attempt."""

    def __init__(self, verdicts: list[bool]):
        self._verdicts = verdicts
        self.calls = 0

    def check(self, data: bytes, exp) -> qc.QCVerdict:
        passed = self._verdicts[min(self.calls, len(self._verdicts) - 1)]
        self.calls += 1
        if passed:
            return qc.QCVerdict(passed=True, reason="pass")
        return qc.QCVerdict(passed=False, failure_tags=("collage_panels",), reason="scripted fail")


@pytest.fixture()
def _tmp_output(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "oai")
    monkeypatch.setattr(config, "REJECTED_DIR", tmp_path / "oai" / "_rejected")
    return tmp_path


def _plan() -> SkuPlan:
    return SkuPlan(
        sku="br-001",
        name="Black Rose Crewneck",
        collection="black-rose",
        output_slug="black-rose-crewneck",
        references=[ReferenceImage(label="ref 1", path=Path("/nonexistent.png"), kind="garment")],
        prompt="prompt",
    )


def test_render_sku_accepts_on_retry_after_qc_fail(_tmp_output):
    client = _FakeClient(b"png-bytes")
    gate = _ScriptedGate([False, True])
    result = render_sku(_plan(), client, gate=gate, spend=SpendTracker())
    assert result.status == "rendered"
    assert client.calls == 2
    rejected = list((config.REJECTED_DIR / "black-rose-crewneck").glob("*.png"))
    assert len(rejected) == 1  # first attempt quarantined


def test_render_sku_quarantines_after_exhausting_retries(_tmp_output):
    client = _FakeClient(b"png-bytes")
    gate = _ScriptedGate([False])  # every attempt fails
    result = render_sku(_plan(), client, gate=gate, spend=SpendTracker())
    assert result.status == "qc_failed"
    assert client.calls == 1 + config.QC_MAX_RENDER_RETRIES
    qdir = config.REJECTED_DIR / "black-rose-crewneck"
    assert len(list(qdir.glob("*.png"))) == client.calls
    meta = json.loads(sorted(qdir.glob("*.json"))[0].read_text())
    assert meta["failure_tags"] == ["collage_panels"]
    # accepted output was never written
    assert not (config.OUTPUT_DIR / "black-rose-crewneck" / "ghost.png").exists()


def test_render_sku_stops_when_budget_exhausted(_tmp_output):
    client = _FakeClient(b"png-bytes")
    spend = SpendTracker(cap_usd=0.10)  # cannot afford even one render
    result = render_sku(_plan(), client, gate=None, spend=spend)
    assert result.status == "error"
    assert "budget" in result.reason
    assert client.calls == 0


def test_render_sku_no_gate_accepts_first_render(_tmp_output):
    client = _FakeClient(b"png-bytes")
    result = render_sku(_plan(), client, gate=None, spend=SpendTracker())
    assert result.status == "rendered"
    assert client.calls == 1
    assert result.output_path is not None and result.output_path.exists()


# ── Founder review corrections (2026-06-09 review board) ────────────────────
def _write_corrections(tmp_path: Path, monkeypatch, corrections: dict) -> None:
    path = tmp_path / "render-corrections.json"
    path.write_text(json.dumps({"corrections": corrections}))
    monkeypatch.setattr(config, "CORRECTIONS_JSON", path)
    prompt_mod._load_corrections_file.cache_clear()


def test_founder_corrections_injected_verbatim(tmp_path: Path, monkeypatch):
    _write_corrections(
        tmp_path, monkeypatch, {"sg-007": ["[ghost] logo Is a patch not directly on beanie"]}
    )
    p = build_prompt(
        name="The Signature Beanie",
        sku="sg-007",
        collection="signature",
        reference_labels=[],
        dossier_text=None,
        is_patch=False,
        style="ghost",
        view="front",
    )
    assert "FOUNDER CORRECTIONS" in p
    assert "logo Is a patch not directly on beanie" in p
    prompt_mod._load_corrections_file.cache_clear()


def test_no_corrections_block_when_sku_has_none(tmp_path: Path, monkeypatch):
    _write_corrections(tmp_path, monkeypatch, {"sg-007": ["[ghost] note"]})
    p = build_prompt(
        name="Other Product",
        sku="br-001",
        collection="black-rose",
        reference_labels=[],
        dossier_text=None,
        is_patch=False,
        style="ghost",
        view="front",
    )
    assert "FOUNDER CORRECTIONS" not in p
    prompt_mod._load_corrections_file.cache_clear()


def test_corrections_missing_file_is_silent(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(config, "CORRECTIONS_JSON", tmp_path / "absent.json")
    prompt_mod._load_corrections_file.cache_clear()
    assert prompt_mod.corrections_for("sg-007") == []
    prompt_mod._load_corrections_file.cache_clear()


def test_base_procedure_carries_material_and_photorealism_directives():
    p = build_prompt(
        name="Love Hurts Bomber",
        sku="lh-004",
        collection="love-hurts",
        reference_labels=[],
        dossier_text=None,
        is_patch=False,
        style="ghost",
        view="front",
    )
    assert "MATERIAL:" in p and "satin" in p
    assert "PHOTOREALISM:" in p and "tech flats" in p
    assert "BRANDING IS EXHAUSTIVE" in p


def test_qc_schema_gates_flat_renders():
    props = qc._JUDGE_SCHEMA["schema"]["properties"]
    assert "photorealistic_not_flat" in props
    assert qc._GATE_TAGS["photorealistic_not_flat"] == "flat_render"
    assert "photorealistic_not_flat" in qc._JUDGE_SCHEMA["schema"]["required"]


def test_mint_lavender_skus_render_again_with_clean_dossiers():
    # bug-119 regression guard: the contamination was cleared 2026-06-10 by
    # re-authoring both dossiers from the real mint garments. These SKUs must
    # stay renderable, and their dossiers must never drift back to the
    # windbreaker-set design (white body + rainbow chevron zip-up).
    assert "sg-006" not in config.EXCLUDED_SKUS
    assert "sg-014" not in config.EXCLUDED_SKUS
    for slug, garment in (
        ("mint-lavender-hoodie", "PULLOVER"),
        ("mint-lavender-sweatpants", "sweatpants"),
    ):
        text = (config.DOSSIER_DIR / f"{slug}.md").read_text(encoding="utf-8")
        lock = text.split("**Garment type lock:**", 1)[1].split("##", 1)[0]
        assert garment in lock
        assert "mint green" in lock
        # exact phrasing the contaminated dossiers used for the wrong garment
        assert "solid **white**" not in lock
        assert "rainbow chevron color-block" not in lock
        assert "zip-up hoodie" not in lock.lower()


def test_pair_with_excluded_member_falls_back_to_solo(monkeypatch):
    from scripts.oai_render import pipeline, references

    monkeypatch.setitem(config.EXCLUDED_SKUS, "sg-014", "test: contaminated dossier")
    catalog = references.load_catalog()
    dossiers = references.build_dossier_index()
    result = pipeline.run(["sg-013"], catalog, dossiers, styles=["on-model"], dry_run=True)
    plans = [p for p in result["plans"] if p.error is None]
    assert len(plans) == 1
    assert plans[0].style == "on-model"
    assert not plans[0].output_slug.startswith("pair__")
