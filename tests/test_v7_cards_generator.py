"""Tests for the V7 card generator and the catalog pre-order invariants.

Covers the consolidation that made ``v7-cards.json`` a generated view:
  * ``scripts/build_v7_cards.py``        — generator (CSV fields × served-tree imagery)
  * ``scripts/validate_catalog_consistency.py``:
        - ``preorder_consistency``       — badge ⟺ is_preorder invariant
        - ``v7_cards_current``           — generated-artifact-up-to-date guard

The generator and validator live in ``scripts/`` (not an importable package), so
both are loaded by file path — the same mechanism the validator's guard uses in CI.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _load(mod_name: str, rel_path: str):
    spec = importlib.util.spec_from_file_location(mod_name, _REPO_ROOT / rel_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Register before exec so @dataclass can resolve cls.__module__ (py3.12+/3.14).
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


gen = _load("build_v7_cards", "scripts/build_v7_cards.py")
validator = _load("validate_catalog_consistency", "scripts/validate_catalog_consistency.py")


def _row(sku: str, *, badge: str = "", is_preorder: str = "0", **over) -> dict:
    """Minimal CSV row dict for the columns the generator reads."""
    base = {
        "sku": sku,
        "name": f"Test {sku}",
        "price": "100",
        "collection": "black-rose",
        "badge": badge,
        "edition_size": "250",
        "is_preorder": is_preorder,
        "published": "1",
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class TestV7Generator:
    def test_build_cards_real_tree_structure(self):
        """Against the real served tree: sorted, front-first, typed fields."""
        cards = gen.build_cards()
        assert cards, "expected at least one V7 card from the served tree"
        skus = [c["sku"] for c in cards]
        assert skus == sorted(skus), "cards must be in lexicographic SKU order"
        for c in cards:
            assert c["shots"], f"{c['sku']} has no shots"
            assert c["shots"][0]["face"] == "front", f"{c['sku']} first shot must be front"
            assert isinstance(c["preorder"], bool)
            assert isinstance(c["price"], int)
            assert c["edition"] is None or isinstance(c["edition"], int)
            for shot in c["shots"]:
                assert shot["uri"].startswith("assets/images/products/v7/")

    def test_preorder_follows_is_preorder_not_badge(self):
        """preorder is computed from is_preorder, never from the badge text.

        br-001 has a real served dir, so it yields a card. A contradictory row
        (badge says pre-order, flag says no) must resolve to the FLAG.
        """
        contradictory = gen.build_cards([_row("br-001", badge="Pre-Order", is_preorder="0")])
        assert contradictory[0]["preorder"] is False

        flag_on = gen.build_cards([_row("br-001", badge="", is_preorder="1")])
        assert flag_on[0]["preorder"] is True

    def test_badge_passthrough(self):
        cards = gen.build_cards([_row("br-001", badge="Pre-Order", is_preorder="1")])
        assert cards[0]["badge"] == "Pre-Order"
        cards = gen.build_cards([_row("br-001", badge="", is_preorder="0")])
        assert cards[0]["badge"] == ""

    def test_sku_without_served_dir_produces_no_card(self):
        """A SKU with no promoted served dir falls back to holo (no card)."""
        assert gen.build_cards([_row("zz-999")]) == []

    def test_serialize_deterministic_and_trailing_newline(self):
        a = gen.serialize(gen.build_document())
        b = gen.serialize(gen.build_document())
        assert a == b
        assert a.endswith("\n")

    def test_document_count_matches_cards(self):
        doc = gen.build_document()
        assert doc["_count"] == len(doc["cards"])
        assert "_generated_by" in doc


# ---------------------------------------------------------------------------
# Validator — preorder_consistency invariant
# ---------------------------------------------------------------------------


class TestPreorderConsistencyCheck:
    def _write_csv(self, tmp_path: Path, rows: list[dict]) -> Path:
        cols = ["sku", "name", "badge", "is_preorder", "published"]
        lines = [",".join(cols)]
        for r in rows:
            lines.append(",".join(r.get(c, "") for c in cols))
        p = tmp_path / "catalog.csv"
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return p

    def test_passes_when_badge_and_flag_agree(self, tmp_path, monkeypatch):
        csv_path = self._write_csv(
            tmp_path,
            [
                _row("a-1", badge="Pre-Order", is_preorder="1"),
                _row("a-2", badge="", is_preorder="0"),
            ],
        )
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_preorder_consistency()
        assert result.passed, result.message

    def test_fails_on_badge_says_preorder_flag_off(self, tmp_path, monkeypatch):
        csv_path = self._write_csv(tmp_path, [_row("br-014", badge="Pre-Order", is_preorder="0")])
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_preorder_consistency()
        assert not result.passed
        assert any("br-014" in d for d in result.details)

    def test_fails_on_flag_on_badge_empty(self, tmp_path, monkeypatch):
        csv_path = self._write_csv(tmp_path, [_row("x-1", badge="", is_preorder="1")])
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        result = validator.check_preorder_consistency()
        assert not result.passed

    def test_badge_normalization(self, tmp_path, monkeypatch):
        """Whitespace/case variants of the badge still satisfy the invariant."""
        csv_path = self._write_csv(tmp_path, [_row("x-1", badge="  pre-order  ", is_preorder="1")])
        monkeypatch.setattr(validator, "_CATALOG_CSV", csv_path)
        assert validator.check_preorder_consistency().passed


# ---------------------------------------------------------------------------
# Validator — v7_cards_current guard
# ---------------------------------------------------------------------------


class TestV7CardsCurrentGuard:
    def test_guard_passes_when_file_matches_generator(self, tmp_path, monkeypatch):
        generated = gen.serialize(gen.build_document())
        f = tmp_path / "v7-cards.json"
        f.write_text(generated, encoding="utf-8")
        monkeypatch.setattr(validator, "_V7_CARDS_JSON", f)
        result = validator.check_v7_cards_current()
        assert result.passed, result.message

    def test_guard_fails_when_file_drifts(self, tmp_path, monkeypatch):
        generated = gen.serialize(gen.build_document())
        f = tmp_path / "v7-cards.json"
        f.write_text(
            generated.replace('"preorder": false', '"preorder": true', 1), encoding="utf-8"
        )
        monkeypatch.setattr(validator, "_V7_CARDS_JSON", f)
        result = validator.check_v7_cards_current()
        assert not result.passed

    def test_guard_fails_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validator, "_V7_CARDS_JSON", tmp_path / "nope.json")
        result = validator.check_v7_cards_current()
        assert not result.passed
