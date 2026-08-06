"""Tests for the aggregated lookbook SOT generator and freshness guards."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_BUILD_LOOKBOOK_SOT = _REPO_ROOT / "scripts" / "build-lookbook-sot.py"
_BUILD_LOOKBOOK_FROM_SOT = _REPO_ROOT / "scripts" / "build-lookbook-from-sot.py"
_LOOKBOOK_MANIFEST = _REPO_ROOT / "scripts" / "lookbook-manifest.json"


def _load(mod_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


gen = _load("build_lookbook_sot", _BUILD_LOOKBOOK_SOT)
html_gen = _load("build_lookbook_from_sot", _BUILD_LOOKBOOK_FROM_SOT)
validator = _load(
    "validate_catalog_consistency", _REPO_ROOT / "scripts" / "validate_catalog_consistency.py"
)


def _seed(tmp_dir: Path):
    payload = gen.build_lookbook_payload(_LOOKBOOK_MANIFEST)
    sot_file = tmp_dir / "lookbook-sot.json"
    html_file = tmp_dir / "sot-lookbook.html"
    sot_file.write_text(gen.serialize(payload), encoding="utf-8")
    rendered, _ = html_gen.build_lookbook_html(payload)
    html_file.write_text(rendered, encoding="utf-8")
    return payload, sot_file, html_file


class TestLookbookSotGenerator:
    def test_build_payload_and_serialize_are_stable(self):
        payload = gen.build_lookbook_payload(_LOOKBOOK_MANIFEST)
        assert payload["domain"] == "wordpress-theme/skyyrose-flagship"
        assert payload["component"] == "lookbook"
        assert payload["collections"]
        assert gen.serialize(payload) == gen.serialize(payload)

    def test_generator_output_includes_expected_collections(self):
        payload = gen.build_lookbook_payload(_LOOKBOOK_MANIFEST)
        slugs = [item["collection"] for item in payload["collections"]]
        assert "black-rose" in slugs
        assert "love-hurts" in slugs
        assert "signature" in slugs
        assert "kids-capsule" in slugs


class TestLookbookSotFreshnessGuard:
    def test_guard_passes_when_fresh(self, tmp_path, monkeypatch):
        payload, sot_file, html_file = _seed(tmp_path)
        monkeypatch.setattr(
            validator,
            "_LOOKBOOK_SOT",
            sot_file,
        )
        monkeypatch.setattr(
            validator,
            "_LOOKBOOK_HTML",
            html_file,
        )
        assert validator.check_lookbook_sot_current().passed
        assert validator.check_lookbook_html_current().passed

    def test_guard_fails_on_lookbook_drift(self, tmp_path, monkeypatch):
        payload, _, html_file = _seed(tmp_path)
        sot_file = tmp_path / "lookbook-sot.json"
        corrupted = gen.serialize(payload)
        corrupted = corrupted.replace("lookbook", "lookbook-drift", 1)
        sot_file.write_text(corrupted, encoding="utf-8")
        monkeypatch.setattr(
            validator,
            "_LOOKBOOK_SOT",
            sot_file,
        )
        monkeypatch.setattr(
            validator,
            "_LOOKBOOK_HTML",
            html_file,
        )
        assert not validator.check_lookbook_sot_current().passed

    def test_guard_fails_on_missing_lookbook_html(self, tmp_path, monkeypatch):
        _payload, sot_file, _ = _seed(tmp_path)
        html_file = tmp_path / "sot-lookbook.html"
        html_file.unlink()
        monkeypatch.setattr(
            validator,
            "_LOOKBOOK_SOT",
            sot_file,
        )
        monkeypatch.setattr(
            validator,
            "_LOOKBOOK_HTML",
            html_file,
        )
        result = validator.check_lookbook_html_current()
        assert not result.passed

    def test_guard_skips_when_build_script_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(validator, "_BUILD_LOOKBOOK_SOT", tmp_path / "missing.py")
        result = validator.check_lookbook_sot_current()
        assert result.passed
        assert "skip" in result.message.lower()

    def test_html_guard_skips_when_build_script_missing(self, tmp_path, monkeypatch):
        _, sot_file, html_file = _seed(tmp_path)
        monkeypatch.setattr(
            validator,
            "_LOOKBOOK_SOT",
            sot_file,
        )
        monkeypatch.setattr(
            validator,
            "_LOOKBOOK_HTML",
            html_file,
        )
        monkeypatch.setattr(
            validator,
            "_LOOKBOOK_FROM_SOT",
            tmp_path / "missing.py",
        )
        result = validator.check_lookbook_html_current()
        assert result.passed
        assert "skip" in result.message.lower()
