"""Unit tests for the dossier Pydantic schema and markdown parser."""

from __future__ import annotations

import pytest

from skyyrose.core.dossier_loader import Dossier as RawDossier
from skyyrose.core.dossier_loader import parse_dossier_markdown
from skyyrose.core.dossier_schema import (
    BrandingRegion,
    DossierSchema,
    DossierSchemaError,
    coverage_for,
    parse_branding_regions,
    parse_negative_list,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_VALID_BRANDING_BLOCK = """### Front
- **front-chest** (~10in tall × proportional width): Embossed Black Rose logo,
  tonal raised relief. **Technique:** embossed. **Color:** tonal black-on-black.

### Back
- **back-neck** (~2in wide): SR monogram in gold-tone thread. **Technique:**
  embroidered. **Color:** gold-tone (PMS 871C).

### Sleeves / Collar / Hem / Other
- **collar-outside / neckband**: White ribbed-knit neckband contrasting against
  the black body. **Technique:** stitched. **Color:** white (#FFFFFF).
"""


_VALID_NEGATIVE_BLOCK = """- NO printed graphics anywhere
- NO printed text — no "BLACK IS BEAUTIFUL" wording, no other words
- NO contrast piping at the seams
"""


@pytest.fixture
def raw_dossier() -> RawDossier:
    """Minimal raw dossier matching the markdown layout."""
    return RawDossier(
        sku="br-001",
        name="BLACK Rose Crewneck",
        collection="black-rose",
        slug="black-rose-crewneck",
        garment_type_lock="Crewneck sweatshirt — upper body only",
        branding_block=_VALID_BRANDING_BLOCK,
        negative_block=_VALID_NEGATIVE_BLOCK,
        scene_pose="three-quarter front",
        scene_setting="Bay Bridge night street",
        raw="...",
    )


# ---------------------------------------------------------------------------
# Branding parser
# ---------------------------------------------------------------------------


class TestParseBranding:
    def test_extracts_three_regions(self):
        regions = parse_branding_regions(_VALID_BRANDING_BLOCK)
        assert len(regions) == 3
        names = [r.region for r in regions]
        assert "front-chest" in names
        assert "back-neck" in names
        assert any("collar-outside" in n for n in names)

    def test_extracts_techniques(self):
        regions = parse_branding_regions(_VALID_BRANDING_BLOCK)
        techniques = sorted(r.technique for r in regions)
        assert techniques == ["embossed", "embroidered", "stitched"]

    def test_extracts_hex_when_present(self):
        regions = parse_branding_regions(_VALID_BRANDING_BLOCK)
        hex_for = {r.region: r.color_hex for r in regions}
        assert hex_for["back-neck"] is None  # only Pantone, no hex
        # The collar bullet has #FFFFFF
        assert any(r.color_hex == "#FFFFFF" for r in regions)

    def test_extracts_pantone_when_present(self):
        regions = parse_branding_regions(_VALID_BRANDING_BLOCK)
        pantones = [r.color_pantone for r in regions if r.color_pantone]
        assert any("871C" in p for p in pantones)

    def test_extracts_dimensions(self):
        regions = parse_branding_regions(_VALID_BRANDING_BLOCK)
        dims = {r.region: r.dimensions for r in regions}
        assert "10in" in (dims.get("front-chest") or "")
        assert "2in" in (dims.get("back-neck") or "")

    def test_skips_bullets_without_technique(self):
        block = """- **logo-reference**: see brand-assets/black-rose.svg
- **front-chest** (~10in): Embossed logo. **Technique:** embossed. **Color:** black."""
        regions = parse_branding_regions(block)
        assert len(regions) == 1
        assert regions[0].region == "front-chest"

    def test_empty_block_returns_empty(self):
        assert parse_branding_regions("") == []
        assert parse_branding_regions("\n\n   \n") == []


class TestParseNegative:
    def test_extracts_bulleted_items(self):
        items = parse_negative_list(_VALID_NEGATIVE_BLOCK)
        assert len(items) == 3
        assert items[0].startswith("NO printed graphics")

    def test_strips_marker_chars(self):
        block = "* NO contrast piping\n- NO embroidered text"
        items = parse_negative_list(block)
        assert items == ["NO contrast piping", "NO embroidered text"]

    def test_empty_block_returns_empty(self):
        assert parse_negative_list("") == []


# ---------------------------------------------------------------------------
# DossierSchema
# ---------------------------------------------------------------------------


class TestDossierSchema:
    def test_from_raw_succeeds_on_valid(self, raw_dossier):
        schema = DossierSchema.from_raw(raw_dossier)
        assert schema.sku == "br-001"
        assert schema.collection == "black-rose"
        assert len(schema.branding) == 3
        assert len(schema.negative) == 3
        assert schema.scene_pose == "three-quarter front"

    def test_from_raw_rejects_empty_branding(self, raw_dossier):
        raw_dossier_empty = RawDossier(
            sku="br-bad",
            name="Bad",
            collection="black-rose",
            slug="bad",
            garment_type_lock="lock",
            branding_block="",
            negative_block=_VALID_NEGATIVE_BLOCK,
        )
        with pytest.raises(DossierSchemaError):
            DossierSchema.from_raw(raw_dossier_empty)

    def test_from_raw_rejects_empty_negative(self, raw_dossier):
        raw_dossier_empty = RawDossier(
            sku="br-bad",
            name="Bad",
            collection="black-rose",
            slug="bad",
            garment_type_lock="lock",
            branding_block=_VALID_BRANDING_BLOCK,
            negative_block="",
        )
        with pytest.raises(DossierSchemaError):
            DossierSchema.from_raw(raw_dossier_empty)

    def test_from_raw_rejects_empty_garment_lock(self, raw_dossier):
        raw_dossier_empty = RawDossier(
            sku="br-bad",
            name="Bad",
            collection="black-rose",
            slug="bad",
            garment_type_lock="",
            branding_block=_VALID_BRANDING_BLOCK,
            negative_block=_VALID_NEGATIVE_BLOCK,
        )
        with pytest.raises(DossierSchemaError):
            DossierSchema.from_raw(raw_dossier_empty)

    def test_invalid_hex_format_rejected(self):
        with pytest.raises(ValueError):
            BrandingRegion(
                region="front-chest",
                description="x",
                technique="embroidered",
                color_hex="not-a-hex",
            )

    def test_valid_hex_normalized_uppercase(self):
        r = BrandingRegion(
            region="front-chest",
            description="x",
            technique="embroidered",
            color_hex="#abcdef",
        )
        assert r.color_hex == "#ABCDEF"


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------


class TestCoverage:
    def test_coverage_reports_partial_hex(self, raw_dossier):
        schema = DossierSchema.from_raw(raw_dossier)
        cov = coverage_for(schema)
        assert cov.region_count == 3
        # Only one region had a hex code in the fixture
        assert cov.hex_coverage_pct == round(100 / 3, 1)

    def test_coverage_warns_on_missing_hex(self, raw_dossier):
        schema = DossierSchema.from_raw(raw_dossier)
        cov = coverage_for(schema)
        assert any("color_hex" in w for w in cov.warnings)


# ---------------------------------------------------------------------------
# Round-trip with real markdown
# ---------------------------------------------------------------------------


class TestMarkdownRoundTrip:
    def test_full_dossier_parses_into_schema(self):
        markdown = """---
sku: lh-002
name: Love Hurts Tee
collection: love-hurts
slug: love-hurts-tee
---

# Love Hurts Tee

**Garment type lock:** Crewneck tee — short sleeve, no hood.

## Branding — what IS on this product

### Front
- **front-chest** (~6in wide): Heart logo. **Technique:** screen_print. **Color:** crimson (#DC143C).

## Negative — what is NOT on this product

- NO embroidery anywhere
- NO printed text on the back

## Scene direction

- **Pose:** three-quarter
- **Setting:** Beauty and the Beast cathedral interior
"""
        raw = parse_dossier_markdown(markdown)
        schema = DossierSchema.from_raw(raw)
        assert schema.sku == "lh-002"
        assert len(schema.branding) == 1
        assert schema.branding[0].color_hex == "#DC143C"
        assert len(schema.negative) == 2
        assert schema.scene_pose == "three-quarter"
