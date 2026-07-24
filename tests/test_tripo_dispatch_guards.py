"""Regression tests for tripo_dispatch.py hallucination-prevention guards.

Tracks RCA #BUG-tripo-hallu-001: the May 8 Tripo multiview batch wrote 120
hallucinated branded renders to renders/output/tripo/ because the dispatch
boundary had no guard. The guards under test here BLOCK branded SKUs and
SKUs without a clean tech-flat source from ever reaching the Tripo API,
since Tripo's `generate_multiview_image` template feeds a naked image into
FLUX.1 Kontext with no prompt, no logo overlay, no canon anchor.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# --------------------------------------------------------------------------- #
# _load_dossier_logo_reference
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_load_dossier_logo_reference_returns_value_when_present(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When the dossier frontmatter has `logo_reference: ...`, the helper
    returns the trimmed value (no fence, no quotes)."""
    from scripts import tripo_dispatch

    dossier_dir = tmp_path / "dossiers"
    dossier_dir.mkdir()
    dossier = dossier_dir / "black-rose-crewneck.md"
    dossier.write_text(
        "---\n"
        "sku: br-001\n"
        "name: BLACK Rose Crewneck\n"
        "logo_reference: data/brand-logos/black-rose-logo.md\n"
        "extra_logos:\n"
        "  - data/brand-logos/sr-monogram.md\n"
        "---\n"
        "\n"
        "# body content\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(tripo_dispatch, "DOSSIER_DIR", dossier_dir)

    row = {"sku": "br-001", "dossier_slug": "black-rose-crewneck"}
    assert tripo_dispatch._load_dossier_logo_reference(row) == "data/brand-logos/black-rose-logo.md"


@pytest.mark.unit
def test_load_dossier_logo_reference_returns_empty_when_field_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts import tripo_dispatch

    dossier_dir = tmp_path / "dossiers"
    dossier_dir.mkdir()
    dossier = dossier_dir / "the-fannie.md"
    dossier.write_text(
        "---\nsku: lh-005\nname: The Fannie\n---\n# body\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(tripo_dispatch, "DOSSIER_DIR", dossier_dir)

    row = {"sku": "lh-005", "dossier_slug": "the-fannie"}
    assert tripo_dispatch._load_dossier_logo_reference(row) == ""


@pytest.mark.unit
def test_load_dossier_logo_reference_returns_empty_when_dossier_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts import tripo_dispatch

    monkeypatch.setattr(tripo_dispatch, "DOSSIER_DIR", tmp_path / "missing")
    row = {"sku": "x", "dossier_slug": "nonexistent"}
    assert tripo_dispatch._load_dossier_logo_reference(row) == ""


@pytest.mark.unit
def test_load_dossier_logo_reference_returns_empty_when_dossier_slug_blank() -> None:
    from scripts import tripo_dispatch

    assert tripo_dispatch._load_dossier_logo_reference({"sku": "x", "dossier_slug": ""}) == ""
    assert tripo_dispatch._load_dossier_logo_reference({"sku": "x"}) == ""


# --------------------------------------------------------------------------- #
# _has_tech_flat_source
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_has_tech_flat_source_true_when_image_resolves(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts import tripo_dispatch

    theme_root = tmp_path / "theme"
    (theme_root / "assets/images/products").mkdir(parents=True)
    tf = theme_root / "assets/images/products/sg-002.webp"
    tf.write_bytes(b"webp")
    monkeypatch.setattr(tripo_dispatch, "THEME_ROOT", theme_root)

    row = {"sku": "sg-002", "image": "assets/images/products/sg-002.webp"}
    assert tripo_dispatch._has_tech_flat_source(row) is True


@pytest.mark.unit
def test_has_tech_flat_source_false_when_image_field_empty() -> None:
    from scripts import tripo_dispatch

    # br-001 in real catalog has empty `image` column — only front_model_image
    # populated. That is exactly the regression: Tripo got fed a model-on shot.
    assert tripo_dispatch._has_tech_flat_source({"sku": "br-001", "image": ""}) is False
    assert tripo_dispatch._has_tech_flat_source({"sku": "br-001"}) is False


@pytest.mark.unit
def test_has_tech_flat_source_false_when_file_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts import tripo_dispatch

    monkeypatch.setattr(tripo_dispatch, "THEME_ROOT", tmp_path / "theme")
    row = {"sku": "x", "image": "assets/images/products/x.webp"}
    assert tripo_dispatch._has_tech_flat_source(row) is False


@pytest.mark.unit
def test_has_tech_flat_source_follows_override_when_image_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Regression for the validation-target mismatch: the guard must check
    the file `resolve_source_image()` will ACTUALLY dispatch (which prefers
    `render_source_override`), not re-derive a path from `image` alone.
    """
    from scripts import tripo_dispatch

    theme_root = tmp_path / "theme"
    (theme_root / "assets/images/products").mkdir(parents=True)
    override_file = theme_root / "assets/images/products/override.webp"
    override_file.write_bytes(b"webp")
    monkeypatch.setattr(tripo_dispatch, "THEME_ROOT", theme_root)

    row = {
        "sku": "x-006",
        "image": "",  # no canonical tech-flat field populated
        "render_source_override": "override.webp",
    }
    assert tripo_dispatch._has_tech_flat_source(row) is True


@pytest.mark.unit
def test_has_tech_flat_source_false_when_override_file_missing_despite_valid_image(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The guard must not silently fall back to a validated `image` file
    when `render_source_override` is populated but its target is missing —
    that target is what dispatch will actually try to send.
    """
    from scripts import tripo_dispatch

    theme_root = tmp_path / "theme"
    (theme_root / "assets/images/products").mkdir(parents=True)
    (theme_root / "assets/images/products/flat.webp").write_bytes(b"webp")
    monkeypatch.setattr(tripo_dispatch, "THEME_ROOT", theme_root)

    row = {
        "sku": "x-007",
        "image": "assets/images/products/flat.webp",  # exists
        "render_source_override": "missing-override.webp",  # does not exist
    }
    assert tripo_dispatch._has_tech_flat_source(row) is False


# --------------------------------------------------------------------------- #
# _source_matches_declared_image — validation-target mismatch guard
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_source_matches_declared_image_true_when_no_override() -> None:
    from scripts import tripo_dispatch

    row = {"sku": "x", "image": "assets/images/products/x.webp"}
    assert tripo_dispatch._source_matches_declared_image(row) is True


@pytest.mark.unit
def test_source_matches_declared_image_true_when_override_resolves_to_same_file() -> None:
    """Real catalog convention: `render_source_override` stores a bare
    basename while `image` stores the full relative path — they resolve to
    the identical file. Comparison must be path-based, not string-based, or
    every one of the 33 real catalog rows would be falsely flagged as
    diverging.
    """
    from scripts import tripo_dispatch

    row = {
        "sku": "br-001",
        "image": "assets/images/products/br-001-crewneck.png",
        "render_source_override": "br-001-crewneck.png",
    }
    assert tripo_dispatch._source_matches_declared_image(row) is True


@pytest.mark.unit
def test_source_matches_declared_image_false_when_override_diverges() -> None:
    """The exact bug-096 reopening scenario: `render_source_override` points
    at a genuinely different file than the catalog `image` field.
    """
    from scripts import tripo_dispatch

    row = {
        "sku": "x-008",
        "image": "assets/images/products/clean-flat.webp",
        "render_source_override": "assets/images/products/different-branded.webp",
    }
    assert tripo_dispatch._source_matches_declared_image(row) is False


# --------------------------------------------------------------------------- #
# classify_skus — full guard pipeline
# --------------------------------------------------------------------------- #


def _scaffold_classify_fixture(monkeypatch, tmp_path):
    """Wire DOSSIER_DIR + THEME_ROOT for an isolated classify_skus run.

    Returns (dossier_dir, theme_root).
    """
    from scripts import tripo_dispatch

    dossier_dir = tmp_path / "dossiers"
    dossier_dir.mkdir()
    theme_root = tmp_path / "theme"
    (theme_root / "assets/images/products").mkdir(parents=True)
    monkeypatch.setattr(tripo_dispatch, "DOSSIER_DIR", dossier_dir)
    monkeypatch.setattr(tripo_dispatch, "THEME_ROOT", theme_root)
    return dossier_dir, theme_root


@pytest.mark.unit
def test_classify_blocks_branded_sku(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts import tripo_dispatch

    dossier_dir, theme_root = _scaffold_classify_fixture(monkeypatch, tmp_path)
    (dossier_dir / "branded.md").write_text(
        "---\nlogo_reference: data/brand-logos/black-rose-logo.md\n---\n",
        encoding="utf-8",
    )
    tf = theme_root / "assets/images/products/branded.webp"
    tf.write_bytes(b"webp")

    rows = [
        {
            "sku": "br-001",
            "name": "Branded SKU",
            "image": "assets/images/products/branded.webp",
            "render_is_tech_flat": "1",
            "dossier_slug": "branded",
        }
    ]
    approved, blocked = tripo_dispatch.classify_skus(rows)
    assert approved == []
    assert len(blocked) == 1
    assert blocked[0][0]["sku"] == "br-001"
    assert "BRANDED" in blocked[0][1]
    assert "ADK render_pipeline" in blocked[0][1]


@pytest.mark.unit
def test_classify_blocks_sku_without_tech_flat(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts import tripo_dispatch

    dossier_dir, _ = _scaffold_classify_fixture(monkeypatch, tmp_path)
    (dossier_dir / "unbranded.md").write_text("---\n---\n", encoding="utf-8")

    rows = [
        {
            "sku": "x-002",
            "name": "Unbranded but no tech-flat",
            "image": "",  # empty → no canonical tech-flat
            "render_is_tech_flat": "1",  # claim flag set, but file missing
            "dossier_slug": "unbranded",
        }
    ]
    approved, blocked = tripo_dispatch.classify_skus(rows)
    assert approved == []
    assert len(blocked) == 1
    assert "NO TECH-FLAT FILE" in blocked[0][1]


@pytest.mark.unit
def test_classify_approves_unbranded_sku_with_tech_flat(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts import tripo_dispatch

    dossier_dir, theme_root = _scaffold_classify_fixture(monkeypatch, tmp_path)
    (dossier_dir / "clean.md").write_text("---\n---\n", encoding="utf-8")
    tf = theme_root / "assets/images/products/clean.webp"
    tf.write_bytes(b"webp")

    rows = [
        {
            "sku": "x-003",
            "name": "Unbranded clean tech-flat",
            "image": "assets/images/products/clean.webp",
            "render_is_tech_flat": "1",
            "dossier_slug": "clean",
        }
    ]
    approved, blocked = tripo_dispatch.classify_skus(rows)
    assert blocked == []
    assert len(approved) == 1
    assert approved[0]["sku"] == "x-003"


@pytest.mark.unit
def test_classify_force_branded_overrides_branded_block(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """--force-branded escape hatch: branded SKUs pass when allow_branded=True,
    but only if they also have a tech-flat."""
    from scripts import tripo_dispatch

    dossier_dir, theme_root = _scaffold_classify_fixture(monkeypatch, tmp_path)
    (dossier_dir / "branded.md").write_text(
        "---\nlogo_reference: data/brand-logos/black-rose-logo.md\n---\n",
        encoding="utf-8",
    )
    tf = theme_root / "assets/images/products/branded.webp"
    tf.write_bytes(b"webp")

    rows = [
        {
            "sku": "br-001",
            "name": "Branded SKU",
            "image": "assets/images/products/branded.webp",
            "render_is_tech_flat": "1",
            "dossier_slug": "branded",
        }
    ]
    approved, blocked = tripo_dispatch.classify_skus(rows, allow_branded=True)
    assert blocked == []
    assert approved[0]["sku"] == "br-001"


@pytest.mark.unit
def test_classify_force_branded_still_requires_tech_flat(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Even with --force-branded, a missing tech-flat still blocks (the
    second guard layer)."""
    from scripts import tripo_dispatch

    dossier_dir, _ = _scaffold_classify_fixture(monkeypatch, tmp_path)
    (dossier_dir / "branded.md").write_text(
        "---\nlogo_reference: data/brand-logos/x.md\n---\n",
        encoding="utf-8",
    )

    rows = [
        {
            "sku": "br-001",
            "name": "Branded no tech-flat",
            "image": "",
            "render_is_tech_flat": "1",
            "dossier_slug": "branded",
        }
    ]
    approved, blocked = tripo_dispatch.classify_skus(rows, allow_branded=True)
    assert approved == []
    assert "NO TECH-FLAT FILE" in blocked[0][1]


@pytest.mark.unit
def test_classify_blocks_diverging_override_even_when_image_is_validated(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The discriminating regression test for the validation-target
    mismatch: dossier is unbranded, `image` is a real, flagged tech-flat
    (`render_is_tech_flat=1`), but `render_source_override` points at a
    DIFFERENT existing file that was never vetted for branding or
    tech-flatness.

    Pre-fix, `classify_skus` validated only `row["image"]` — this SKU would
    have sailed through as APPROVED while dispatch actually sent the
    unvalidated override file, reopening bug-096. Post-fix it must be
    BLOCKED.
    """
    from scripts import tripo_dispatch

    dossier_dir, theme_root = _scaffold_classify_fixture(monkeypatch, tmp_path)
    (dossier_dir / "unbranded.md").write_text("---\n---\n", encoding="utf-8")
    (theme_root / "assets/images/products/clean-flat.webp").write_bytes(b"webp")
    (theme_root / "assets/images/products/different-branded.webp").write_bytes(b"webp")

    rows = [
        {
            "sku": "x-009",
            "name": "Validated image, diverging unvalidated override",
            "image": "assets/images/products/clean-flat.webp",
            "render_is_tech_flat": "1",
            "render_source_override": "assets/images/products/different-branded.webp",
            "dossier_slug": "unbranded",
        }
    ]
    approved, blocked = tripo_dispatch.classify_skus(rows)
    assert approved == []
    assert len(blocked) == 1
    assert blocked[0][0]["sku"] == "x-009"
    assert "SOURCE OVERRIDE UNVALIDATED" in blocked[0][1]


@pytest.mark.unit
def test_classify_approves_when_override_matches_image_basename_convention(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Non-regression: today's real catalog rows all populate
    `render_source_override` as a bare basename of the `image` file — that
    must still resolve as a match and be approved, not newly blocked.
    """
    from scripts import tripo_dispatch

    dossier_dir, theme_root = _scaffold_classify_fixture(monkeypatch, tmp_path)
    (dossier_dir / "clean.md").write_text("---\n---\n", encoding="utf-8")
    (theme_root / "assets/images/products/clean.webp").write_bytes(b"webp")

    rows = [
        {
            "sku": "x-010",
            "name": "Override matches image via basename convention",
            "image": "assets/images/products/clean.webp",
            "render_is_tech_flat": "1",
            "render_source_override": "clean.webp",
            "dossier_slug": "clean",
        }
    ]
    approved, blocked = tripo_dispatch.classify_skus(rows)
    assert blocked == []
    assert len(approved) == 1
    assert approved[0]["sku"] == "x-010"


@pytest.mark.unit
def test_classify_force_branded_does_not_bypass_source_override_check(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`--force-branded` is a branding-only escape hatch. A diverging
    `render_source_override` is a separate source-integrity defect that
    must stay blocked even when the branding guard is disabled.
    """
    from scripts import tripo_dispatch

    dossier_dir, theme_root = _scaffold_classify_fixture(monkeypatch, tmp_path)
    (dossier_dir / "branded.md").write_text(
        "---\nlogo_reference: data/brand-logos/x.md\n---\n",
        encoding="utf-8",
    )
    (theme_root / "assets/images/products/clean-flat.webp").write_bytes(b"webp")
    (theme_root / "assets/images/products/different-branded.webp").write_bytes(b"webp")

    rows = [
        {
            "sku": "x-011",
            "name": "Branded + diverging override",
            "image": "assets/images/products/clean-flat.webp",
            "render_is_tech_flat": "1",
            "render_source_override": "assets/images/products/different-branded.webp",
            "dossier_slug": "branded",
        }
    ]
    approved, blocked = tripo_dispatch.classify_skus(rows, allow_branded=True)
    assert approved == []
    assert len(blocked) == 1
    assert "SOURCE OVERRIDE UNVALIDATED" in blocked[0][1]


# --------------------------------------------------------------------------- #
# _is_catalog_tech_flat + render_is_tech_flat=0 guard layer
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_is_catalog_tech_flat_true_only_when_flag_is_one() -> None:
    """Catalog flag `render_is_tech_flat` is the authoritative declaration.

    Only the literal "1" counts as a tech-flat. Anything else — "0",
    "true", empty, or absent — is treated as NOT a tech-flat. This is
    the second-tier guard added after br-011: that SKU had a tech-flat
    PNG on disk (so `_has_tech_flat_source` returned True) but the
    catalog explicitly marked it as a branded product render via
    `render_is_tech_flat=0`. The file-existence check alone would have
    let it through; the flag check stops it.
    """
    from scripts import tripo_dispatch

    assert tripo_dispatch._is_catalog_tech_flat({"render_is_tech_flat": "1"}) is True
    assert tripo_dispatch._is_catalog_tech_flat({"render_is_tech_flat": "0"}) is False
    assert tripo_dispatch._is_catalog_tech_flat({"render_is_tech_flat": ""}) is False
    assert tripo_dispatch._is_catalog_tech_flat({"render_is_tech_flat": "true"}) is False
    assert tripo_dispatch._is_catalog_tech_flat({}) is False


@pytest.mark.unit
def test_classify_blocks_when_catalog_tech_flat_flag_is_zero(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """br-011 regression: PNG file exists but catalog marks it as NOT a
    tech-flat (`render_is_tech_flat=0`). The flag guard must block before
    the file-existence guard.
    """
    from scripts import tripo_dispatch

    dossier_dir, theme_root = _scaffold_classify_fixture(monkeypatch, tmp_path)
    (dossier_dir / "unbranded.md").write_text("---\n---\n", encoding="utf-8")
    # File exists on disk → file-existence guard would pass.
    tf = theme_root / "assets/images/products/product-render.png"
    tf.write_bytes(b"png")

    rows = [
        {
            "sku": "x-004",
            "name": "Unbranded but product render, not tech-flat",
            "image": "assets/images/products/product-render.png",
            "render_is_tech_flat": "0",  # catalog says NO
            "dossier_slug": "unbranded",
        }
    ]
    approved, blocked = tripo_dispatch.classify_skus(rows)
    assert approved == []
    assert len(blocked) == 1
    assert "NOT A TECH-FLAT" in blocked[0][1]
    assert "render_is_tech_flat" in blocked[0][1]


@pytest.mark.unit
def test_classify_blocks_when_catalog_tech_flat_flag_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Default-safe behavior: a row that omits the column is treated as
    NOT a tech-flat. Operators must explicitly opt in by setting "1".
    """
    from scripts import tripo_dispatch

    dossier_dir, theme_root = _scaffold_classify_fixture(monkeypatch, tmp_path)
    (dossier_dir / "unbranded.md").write_text("---\n---\n", encoding="utf-8")
    tf = theme_root / "assets/images/products/something.webp"
    tf.write_bytes(b"webp")

    rows = [
        {
            "sku": "x-005",
            "name": "Column missing entirely",
            "image": "assets/images/products/something.webp",
            "dossier_slug": "unbranded",
        }
    ]
    approved, blocked = tripo_dispatch.classify_skus(rows)
    assert approved == []
    assert "NOT A TECH-FLAT" in blocked[0][1]


# --------------------------------------------------------------------------- #
# dispatch_sku — dead-param removal guard
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_dispatch_sku_does_not_pass_dead_model_version_param(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``model_version`` was a misleading dead param: the tripo SDK call
    ``client.generate_multiview_image(image=...)`` accepts no such kwarg,
    and ``tripo_generate_node`` reads only ``params["image_path"]``. The
    param implied a knob we did not have — and risked future callers
    chasing it. This regression test locks in the cleanup.
    """
    from scripts import tripo_dispatch

    captured: dict = {}

    def _fake_run_creative(*, intent: str, params: dict, sku: str):
        captured["intent"] = intent
        captured["params"] = dict(params)
        captured["sku"] = sku
        return {"tripo_result": {"success": True, "views": []}}

    # Inject a fake `run_creative` into the lazy import path used by
    # `dispatch_sku`. Easiest hook: monkeypatch the module it imports from.
    fake_runner_mod = type(
        "_FakeRunnerModule",
        (),
        {"run_creative": _fake_run_creative},
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "skyyrose.elite_studio.creative.runner",
        fake_runner_mod,
    )
    monkeypatch.setattr(tripo_dispatch, "THEME_ROOT", tmp_path)
    (tmp_path / "img.webp").write_bytes(b"x")

    row = {
        "sku": "x-001",
        "image": "img.webp",
        "render_source_override": "",
    }
    tripo_dispatch.dispatch_sku(row)

    assert captured["intent"] == "tripo-generate"
    assert captured["sku"] == "x-001"
    assert set(captured["params"].keys()) == {"image_path"}
    assert "model_version" not in captured["params"]
