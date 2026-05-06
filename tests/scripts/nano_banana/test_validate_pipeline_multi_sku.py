"""Mock-based tests for the multi-SKU validator driver loop.

Exercises the orchestration logic — env loading, catalog resolution,
preflight, cost cap, summary table — without paid SDK calls. Mirrors
the Phase 2 mock-coverage discipline from PR #487.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

# Module under test (leading-underscore filename → import as a module path
# rather than a clean top-level name).
import importlib.util

_validator_path = REPO / "scripts/nano_banana/_validate_pipeline_multi_sku.py"
_spec = importlib.util.spec_from_file_location("validate_pipeline_multi_sku", _validator_path)
validator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validator)

from nano_banana.pipeline import PipelineResult  # noqa: E402
from nano_banana.vision_context import VisionContext  # noqa: E402

from skyyrose.core.dossier_loader import Dossier, DossierMissingError  # noqa: E402

# ── _load (env file sourcing) ──────────────────────────────────────────────


def test_load_skips_missing_file(tmp_path):
    """Missing file must not raise — silent no-op."""
    validator._load(tmp_path / "nope.env")  # should not raise


def test_load_strips_quotes_and_skips_comments(tmp_path, monkeypatch):
    """KV pairs are loaded; comments + blank lines are skipped."""
    p = tmp_path / "f.env"
    p.write_text(
        "# comment\nFOO=bar\nBAZ='single-quoted'\nQUX=\"double-quoted\"\n\nMALFORMED-NO-EQUALS\n"
    )
    for var in ("FOO", "BAZ", "QUX", "MALFORMED-NO-EQUALS"):
        monkeypatch.delenv(var, raising=False)

    validator._load(p)

    import os

    assert os.environ.get("FOO") == "bar"
    assert os.environ.get("BAZ") == "single-quoted"
    assert os.environ.get("QUX") == "double-quoted"


# ── _resolve_products ──────────────────────────────────────────────────────


def test_resolve_products_returns_dict_for_each_sku(monkeypatch, tmp_path):
    """Catalog rows + valid source images → product dict; collisions surface as errors."""
    fake_catalog = {
        "br-001": {
            "name": "BLACK Rose Crewneck",
            "collection": "black-rose",
            "source_override": "br-001-crewneck.png",
            "image": "",
        },
        "lh-004": {
            "name": "Love Hurts Bomber",
            "collection": "love-hurts",
            "source_override": "lh-004-bomber.png",
        },
    }
    monkeypatch.setattr(validator, "REPO", tmp_path)  # so img_dir resolves under tmp_path

    img_dir = tmp_path / "wordpress-theme/skyyrose-flagship/assets/images/products"
    img_dir.mkdir(parents=True)
    (img_dir / "br-001-crewneck.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
    (img_dir / "lh-004-bomber.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")

    import nano_banana.catalog as cat_mod

    monkeypatch.setattr(cat_mod, "load_catalog", lambda: fake_catalog)

    products, errors = validator._resolve_products(["br-001", "lh-004"])

    assert errors == []
    assert len(products) == 2
    assert products[0]["sku"] == "br-001"
    assert products[0]["name"] == "BLACK Rose Crewneck"
    assert products[0]["collection"] == "black-rose"
    assert "br-001-crewneck.png" in products[0]["source_image"]
    # Second SKU used the `image` field as fallback when source_override empty
    assert "lh-004-bomber.png" in products[1]["source_image"]


def test_resolve_products_reports_missing_sku(monkeypatch, tmp_path):
    """SKU not in catalog → error entry, not in products."""
    monkeypatch.setattr(validator, "REPO", tmp_path)
    import nano_banana.catalog as cat_mod

    monkeypatch.setattr(cat_mod, "load_catalog", lambda: {})

    products, errors = validator._resolve_products(["xx-999"])

    assert products == []
    assert any("xx-999: not in catalog" in e for e in errors)


def test_resolve_products_reports_missing_image(monkeypatch, tmp_path):
    """SKU in catalog but image file missing → error entry."""
    monkeypatch.setattr(validator, "REPO", tmp_path)
    import nano_banana.catalog as cat_mod

    monkeypatch.setattr(
        cat_mod,
        "load_catalog",
        lambda: {
            "br-001": {
                "name": "X",
                "collection": "y",
                "source_override": "ghost.png",
            }
        },
    )

    products, errors = validator._resolve_products(["br-001"])

    assert products == []
    assert any("no source photo found" in e for e in errors)


def test_resolve_products_reports_no_source_field(monkeypatch, tmp_path):
    """SKU with empty source_override + no bundle + no products glob → error.

    The fallback chain (catalog override → bundle source-photo → bundle photo-front
    → products dir glob) only fires if at least one path resolves; when none do,
    the SKU surfaces with `no source photo found` and the loop continues.
    """
    monkeypatch.setattr(validator, "REPO", tmp_path)
    # Don't create any product image dir or bundle dir under tmp_path → all
    # candidate paths in _resolve_source_image will miss.
    import nano_banana.catalog as cat_mod

    monkeypatch.setattr(
        cat_mod,
        "load_catalog",
        lambda: {
            "br-001": {
                "name": "X",
                "collection": "y",
                "source_override": "",
            }
        },
    )

    products, errors = validator._resolve_products(["br-001"])

    assert products == []
    assert any("no source photo found" in e for e in errors)


def test_resolve_source_image_falls_back_to_bundle_source_photo(monkeypatch, tmp_path):
    """When source_override is empty/missing, the bundle's `source-photo.jpg` wins."""
    monkeypatch.setattr(validator, "REPO", tmp_path)

    # Bundle directory with a real source-photo.jpg (the canonical product photo)
    bundle = tmp_path / "data/product-bundles/Test Product"
    bundle.mkdir(parents=True)
    (bundle / "source-photo.jpg").write_bytes(b"\xff\xd8\xff\xe0fake-jpeg")

    found = validator._resolve_source_image("xx-001", "Test Product", "")
    assert found is not None
    assert found.name == "source-photo.jpg"


def test_resolve_source_image_falls_back_to_sku_glob_in_products_dir(monkeypatch, tmp_path):
    """If override + bundle both miss, glob `{sku}-*.{ext}` in products dir wins."""
    monkeypatch.setattr(validator, "REPO", tmp_path)

    img_dir = tmp_path / "wordpress-theme/skyyrose-flagship/assets/images/products"
    img_dir.mkdir(parents=True)
    (img_dir / "br-007.jpg").write_bytes(b"\xff\xd8\xff\xe0fake")

    found = validator._resolve_source_image("br-007", "", "")
    assert found is not None
    assert found.name == "br-007.jpg"


def test_resolve_source_image_skips_back_and_composite_variants(monkeypatch, tmp_path):
    """Glob fallback prefers main images over -back / -composite / -detail variants."""
    monkeypatch.setattr(validator, "REPO", tmp_path)

    img_dir = tmp_path / "wordpress-theme/skyyrose-flagship/assets/images/products"
    img_dir.mkdir(parents=True)
    # Drop several variants; only the main image should be picked
    (img_dir / "lh-004-bomber-back.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
    (img_dir / "lh-004-composite-front.webp").write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
    (img_dir / "lh-004-bomber.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")

    found = validator._resolve_source_image("lh-004", "", "")
    assert found is not None
    # Either the main bomber.png or some non-back/non-composite variant
    name_lower = found.name.lower()
    assert "-back" not in name_lower
    assert "-composite" not in name_lower
    assert "lh-004" in name_lower


def test_resolve_source_image_returns_none_when_nothing_found(monkeypatch, tmp_path):
    """No catalog override, no bundle, no glob match → None (validates the failure path)."""
    monkeypatch.setattr(validator, "REPO", tmp_path)
    # tmp_path has no products dir, no bundle dir
    assert validator._resolve_source_image("xx-999", "", "") is None


def test_resolve_source_image_prefers_catalog_override(monkeypatch, tmp_path):
    """Catalog-explicit source wins over bundle/glob when present."""
    monkeypatch.setattr(validator, "REPO", tmp_path)

    img_dir = tmp_path / "wordpress-theme/skyyrose-flagship/assets/images/products"
    img_dir.mkdir(parents=True)
    (img_dir / "br-001-crewneck.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")

    bundle = tmp_path / "data/product-bundles/BLACK Rose Crewneck"
    bundle.mkdir(parents=True)
    (bundle / "source-photo.jpg").write_bytes(b"\xff\xd8\xff\xe0fake-jpeg")

    found = validator._resolve_source_image("br-001", "BLACK Rose Crewneck", "br-001-crewneck.png")
    # Catalog override wins
    assert found is not None
    assert found.name == "br-001-crewneck.png"


# ── _preflight_dossiers ────────────────────────────────────────────────────


def test_preflight_passes_when_all_dossiers_load(monkeypatch):
    """All SKUs return VisionContext → empty failure list."""
    import nano_banana.spec_builder as sb_mod

    monkeypatch.setattr(
        sb_mod,
        "build_dna_from_sku",
        lambda sku: VisionContext(
            spec="...",
            dossier=Dossier(
                sku=sku,
                name=sku,
                collection="x",
                slug=sku,
                garment_type_lock="",
                branding_block="",
                negative_block="",
                scene_pose="",
                scene_setting="",
            ),
        ),
    )

    failures = validator._preflight_dossiers(["br-001", "lh-004"])
    assert failures == []


def test_preflight_reports_missing_dossier(monkeypatch):
    """DossierMissingError on any SKU surfaces in failure list with context."""
    import nano_banana.spec_builder as sb_mod

    def _maybe_raise(sku):
        if sku == "broken":
            raise DossierMissingError(f"no dossier for {sku}")
        return VisionContext()

    monkeypatch.setattr(sb_mod, "build_dna_from_sku", _maybe_raise)

    failures = validator._preflight_dossiers(["br-001", "broken"])
    assert len(failures) == 1
    assert "broken" in failures[0]
    assert "DossierMissingError" in failures[0]


def test_preflight_reports_unknown_sku(monkeypatch):
    """KeyError (SKU not in catalog) bubbles up as a preflight failure too."""
    import nano_banana.spec_builder as sb_mod

    def _raise_key(sku):
        raise KeyError(sku)

    monkeypatch.setattr(sb_mod, "build_dna_from_sku", _raise_key)

    failures = validator._preflight_dossiers(["xx-999"])
    assert len(failures) == 1
    assert "KeyError" in failures[0]


# ── _stop_and_show ─────────────────────────────────────────────────────────


def _fake_product(sku: str, tmp_path: Path) -> dict:
    """Build a product dict with a real on-disk source file."""
    src = tmp_path / f"{sku}.png"
    src.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    return {"sku": sku, "name": sku, "collection": "x", "source_image": str(src)}


def test_stop_and_show_proceeds_on_y(monkeypatch, tmp_path, capsys):
    """Stdin `y` → returns True; output includes SKU list and cost."""
    products = [_fake_product("br-001", tmp_path), _fake_product("lh-004", tmp_path)]
    monkeypatch.setattr("builtins.input", lambda *a, **kw: "y")

    result = validator._stop_and_show(products, max_usd=10.0)

    out = capsys.readouterr().out
    assert result is True
    assert "br-001" in out and "lh-004" in out
    assert "$10.00" in out


def test_stop_and_show_aborts_on_n(monkeypatch, tmp_path):
    """Stdin `n` → returns False; user aborts."""
    products = [_fake_product("br-001", tmp_path)]
    monkeypatch.setattr("builtins.input", lambda *a, **kw: "n")

    assert validator._stop_and_show(products, max_usd=10.0) is False


def test_stop_and_show_aborts_on_empty_input(monkeypatch, tmp_path):
    """Empty stdin → False (defensive default — never proceed without explicit y)."""
    products = [_fake_product("br-001", tmp_path)]
    monkeypatch.setattr("builtins.input", lambda *a, **kw: "")

    assert validator._stop_and_show(products, max_usd=10.0) is False


def test_stop_and_show_aborts_on_eof(monkeypatch, tmp_path):
    """EOF (no stdin attached) → False; tests + CI never accidentally trigger."""
    products = [_fake_product("br-001", tmp_path)]

    def _raise_eof(*a, **kw):
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise_eof)

    assert validator._stop_and_show(products, max_usd=10.0) is False


def test_stop_and_show_auto_confirms_via_env(monkeypatch, tmp_path):
    """STOP_CONFIRM=y in env → True without consulting stdin (used by tests)."""
    products = [_fake_product("br-001", tmp_path)]
    monkeypatch.setenv("STOP_CONFIRM", "y")

    # input() should NOT be called — wire it to a sentinel that fails the test
    monkeypatch.setattr("builtins.input", lambda *a, **kw: pytest.fail("input() called"))

    assert validator._stop_and_show(products, max_usd=10.0) is True


# ── _summary_table ─────────────────────────────────────────────────────────


def test_summary_table_renders_each_result_row():
    """Each PipelineResult contributes one row with key fields visible."""
    r1 = PipelineResult(
        sku="br-001",
        view="front",
        engine_used="gemini-pro",
        qa_score=92.0,
        qa_passed=True,
        attempts=1,
        cost_usd=0.04,
        refinement_applied=False,
    )
    r2 = PipelineResult(
        sku="lh-004",
        view="front",
        engine_used="flux-pro",
        qa_score=58.0,
        qa_passed=False,
        attempts=2,
        cost_usd=0.075,
        refinement_applied=True,
    )

    table = validator._summary_table([r1, r2])
    assert "br-001" in table
    assert "lh-004" in table
    assert "92.0" in table
    assert "58.0" in table
    assert "gemini-pro" in table
    assert "flux-pro" in table


def test_summary_table_handles_no_engine_gracefully():
    """Failed runs (no engine_used) print '(none)' rather than blank/error."""
    r = PipelineResult(sku="br-001", view="front", engine_used="", issues=["failed"])
    table = validator._summary_table([r])
    assert "(none)" in table


# ── _run_with_cost_cap ─────────────────────────────────────────────────────


def test_run_with_cost_cap_executes_each_sku_under_budget(monkeypatch, tmp_path):
    """All SKUs run when total cost stays under MAX_USD."""

    products = [_fake_product("br-001", tmp_path), _fake_product("lh-004", tmp_path)]

    def _fake_run_single(product, source_path, view="front"):
        return PipelineResult(
            sku=product["sku"],
            view=view,
            qa_score=80.0,
            qa_passed=True,
            cost_usd=0.04,
        )

    pipe = MagicMock()
    pipe.run_single = _fake_run_single

    results, exceeded = validator._run_with_cost_cap(pipe, products, max_usd=10.0)

    assert exceeded is False
    assert len(results) == 2
    assert all(r.qa_passed for r in results)


def test_run_with_cost_cap_aborts_when_budget_exceeded(monkeypatch, tmp_path):
    """Once running total >= MAX_USD, remaining SKUs get a 'Skipped' issue and the
    'exceeded' flag is True. Critical guardrail — prevents runaway spend."""
    products = [
        _fake_product("br-001", tmp_path),
        _fake_product("lh-004", tmp_path),
        _fake_product("sg-007", tmp_path),
    ]

    def _expensive_first_sku(product, source_path, view="front"):
        return PipelineResult(
            sku=product["sku"],
            view=view,
            qa_score=70.0,
            cost_usd=15.0,  # blow past max_usd=10 in one run
        )

    pipe = MagicMock()
    pipe.run_single = _expensive_first_sku

    results, exceeded = validator._run_with_cost_cap(pipe, products, max_usd=10.0)

    assert exceeded is True
    assert len(results) == 3
    # First SKU ran (cost 15 > cap, but assigned BEFORE check)
    assert results[0].sku == "br-001"
    assert results[0].cost_usd == 15.0
    # Subsequent SKUs were skipped with an explanatory issue
    assert any("MAX_USD" in i for i in results[1].issues)
    assert any("MAX_USD" in i for i in results[2].issues)


def test_run_with_cost_cap_records_pipeline_exception_per_sku(monkeypatch, tmp_path):
    """If pipe.run_single raises, the SKU gets a result with the exception in issues
    and the loop continues to the next SKU (no silent data loss)."""
    products = [
        _fake_product("br-001", tmp_path),
        _fake_product("lh-004", tmp_path),
    ]

    call_count = {"n": 0}

    def _first_raises_then_succeeds(product, source_path, view="front"):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("Gemini API 503")
        return PipelineResult(
            sku=product["sku"], view=view, qa_score=85.0, qa_passed=True, cost_usd=0.04
        )

    pipe = MagicMock()
    pipe.run_single = _first_raises_then_succeeds

    results, _ = validator._run_with_cost_cap(pipe, products, max_usd=10.0)

    assert len(results) == 2
    assert any("Gemini API 503" in i for i in results[0].issues)
    assert results[1].qa_passed is True


# ── _load_env_files ────────────────────────────────────────────────────────


def test_load_env_files_returns_missing_keys(monkeypatch, tmp_path):
    """Missing required keys are returned as a list — surfaces actionable errors."""
    monkeypatch.setattr(validator, "REPO", tmp_path)
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "FAL_KEY"):
        monkeypatch.delenv(var, raising=False)

    missing = validator._load_env_files()
    assert set(missing) == {"OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "FAL_KEY"}


def test_load_env_files_returns_empty_when_all_present(monkeypatch, tmp_path):
    """All keys present → empty list (no missing)."""
    monkeypatch.setattr(validator, "REPO", tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("GOOGLE_API_KEY", "x")
    monkeypatch.setenv("FAL_KEY", "x")

    assert validator._load_env_files() == []


# ── JSON output shape (smoke test) ─────────────────────────────────────────


def test_pipeline_result_to_dict_is_json_serializable():
    """Per-SKU PipelineResult.to_dict() round-trips through json.dumps."""
    r = PipelineResult(
        sku="br-001",
        view="front",
        output_path=Path("/tmp/out.webp"),
        engine_used="gemini-pro",
        qa_score=88.0,
        qa_passed=True,
        attempts=1,
        cost_usd=0.04,
        issues=[],
        refinement_applied=False,
    )
    serialized = json.dumps(r.to_dict())
    reloaded = json.loads(serialized)
    assert reloaded["sku"] == "br-001"
    assert reloaded["qa_score"] == 88.0
    assert reloaded["output_path"] == "/tmp/out.webp"
