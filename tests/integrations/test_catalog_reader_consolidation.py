"""Static regression guards — every catalog reader must route through the
canonical `skyyrose.core.catalog_loader.read_catalog_rows`.

Closes D8 of the plan. The earlier exploration flagged
`scripts/nano-banana-vton.py` as a divergent reader (it had a local
`_load_catalog()` using `csv.DictReader` directly). That has since been
consolidated to delegate to the canonical reader. These tests prevent the
divergent pattern from creeping back in.

Why static (file-text) checks instead of import-time validation:
    The script's filename contains hyphens (`nano-banana-vton.py`) which
    makes it unimportable via the regular `import` statement. Loading via
    `importlib.util.spec_from_file_location` would execute the whole module
    (Together API client init, side effects). Static-text inspection avoids
    all of that AND is faster.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def nano_banana_vton_source() -> str:
    """Read the nano-banana-vton.py source as text once per test module."""
    return (REPO_ROOT / "scripts" / "nano-banana-vton.py").read_text(encoding="utf-8")


class TestNanoBananaVtonConsolidation:
    """nano-banana-vton.py must NOT have its own catalog reader."""

    def test_no_csv_dictreader(self, nano_banana_vton_source: str) -> None:
        """csv.DictReader anywhere = local parsing = divergence risk."""
        assert "csv.DictReader" not in nano_banana_vton_source, (
            "nano-banana-vton.py contains csv.DictReader — local catalog parsing is "
            "forbidden. Route through skyyrose.core.catalog_loader.read_catalog_rows "
            "(D8 consolidation, 2026-05-22)."
        )

    def test_no_csv_import(self, nano_banana_vton_source: str) -> None:
        """`import csv` is the smoking gun for local CSV parsing."""
        # Allow `import csv` only inside comments / docstrings — match real statements.
        import_lines = [
            line
            for line in nano_banana_vton_source.splitlines()
            if re.match(r"^\s*import\s+csv\b", line) or re.match(r"^\s*from\s+csv\b", line)
        ]
        assert not import_lines, (
            f"nano-banana-vton.py imports csv module: {import_lines}. "
            "Route through skyyrose.core.catalog_loader instead."
        )

    def test_no_direct_open_of_catalog_csv(self, nano_banana_vton_source: str) -> None:
        """open(...catalog.csv...) bypasses the canonical reader."""
        pattern = re.compile(r"open\s*\([^)]*catalog[^)]*\.csv", re.IGNORECASE)
        matches = pattern.findall(nano_banana_vton_source)
        assert not matches, (
            f"nano-banana-vton.py opens catalog CSV directly: {matches}. "
            "Use skyyrose.core.catalog_loader.read_catalog_rows()."
        )

    def test_imports_canonical_reader(self, nano_banana_vton_source: str) -> None:
        """Positive assertion: the canonical import MUST be present."""
        assert "from skyyrose.core.catalog_loader import" in nano_banana_vton_source, (
            "nano-banana-vton.py must import from skyyrose.core.catalog_loader. "
            "If you're refactoring, ensure the canonical reader is still in use."
        )
        assert (
            "read_catalog_rows" in nano_banana_vton_source
        ), "nano-banana-vton.py must use read_catalog_rows() from the canonical loader."


class TestCanonicalReaderAuthority:
    """The canonical reader at skyyrose.core.catalog_loader must remain authoritative."""

    def test_canonical_reader_exists(self) -> None:
        from skyyrose.core.catalog_loader import read_catalog_rows

        rows = read_catalog_rows()
        assert isinstance(rows, list)
        assert len(rows) > 0, "canonical reader returned empty catalog"

    def test_canonical_returns_sku_keyed_rows(self) -> None:
        from skyyrose.core.catalog_loader import read_catalog_rows

        rows = read_catalog_rows()
        assert all("sku" in row for row in rows), "every catalog row must have a sku field"


class TestValidateDossierReadersCoverage:
    """validate_dossier_readers() must include every importable catalog-reading module."""

    def test_audit_includes_all_three_readers(self) -> None:
        from skyyrose.elite_studio.config import validate_dossier_readers

        results = validate_dossier_readers(sku="br-001")
        # Three readers per D8 plan: core, elite_studio, nano_banana
        expected_readers = {
            "skyyrose.core.catalog_loader",
            "skyyrose.elite_studio.catalog",
            "scripts.nano_banana.catalog",
        }
        actual_readers = set(results.keys())
        assert expected_readers.issubset(actual_readers), (
            f"validate_dossier_readers() missing readers: "
            f"{expected_readers - actual_readers}. "
            f"Got: {sorted(actual_readers)}"
        )
