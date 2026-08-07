"""Tests for the aggregated lookbook SOT generator and freshness guards."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_BUILD_LOOKBOOK_SOT = _REPO_ROOT / "scripts" / "build-lookbook-sot.py"
_BUILD_LOOKBOOK_FROM_SOT = _REPO_ROOT / "scripts" / "build-lookbook-from-sot.py"
_LOOKBOOK_COMPONENT = _REPO_ROOT / "scripts" / "sot" / "lookbook.py"
_LOOKBOOK_MANIFEST = _REPO_ROOT / "scripts" / "lookbook-manifest.json"


def _load(mod_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


lookbook = _load("sot_lookbook", _LOOKBOOK_COMPONENT)
validator = _load(
    "validate_catalog_consistency", _REPO_ROOT / "scripts" / "validate_catalog_consistency.py"
)


def _seed(tmp_dir: Path) -> tuple[dict[str, Any], Path, Path]:
    payload = lookbook.build_lookbook_payload(_LOOKBOOK_MANIFEST)
    sot_file = tmp_dir / "lookbook-sot.json"
    html_file = tmp_dir / "sot-lookbook.html"
    sot_file.write_text(lookbook.serialize(payload), encoding="utf-8")
    rendered, _ = lookbook.build_lookbook_html(payload)
    html_file.write_text(rendered, encoding="utf-8")
    return payload, sot_file, html_file


class TestLookbookSotGenerator:
    def test_compatibility_entrypoints_use_the_canonical_component(self) -> None:
        assert _LOOKBOOK_COMPONENT.is_file()
        assert "scripts.sot.lookbook" in _BUILD_LOOKBOOK_SOT.read_text(encoding="utf-8")
        assert "scripts.sot.lookbook" in _BUILD_LOOKBOOK_FROM_SOT.read_text(encoding="utf-8")
        legacy_sot = _load("legacy_lookbook_sot", _BUILD_LOOKBOOK_SOT)
        legacy_html = _load("legacy_lookbook_html", _BUILD_LOOKBOOK_FROM_SOT)
        assert Path(legacy_sot._lookbook.__file__).resolve() == _LOOKBOOK_COMPONENT
        assert Path(legacy_html._lookbook.__file__).resolve() == _LOOKBOOK_COMPONENT

    def test_compatibility_entrypoint_uses_directory_fallback_for_empty_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        collections_dir = tmp_path / "collections"
        collection_dir = collections_dir / "fallback"
        collection_dir.mkdir(parents=True)
        (collection_dir / "sot.json").write_text('{"name": "Fallback"}\n', encoding="utf-8")
        manifest = tmp_path / "empty-manifest.json"
        manifest.write_text(json.dumps({"sources": []}), encoding="utf-8")
        output = tmp_path / "lookbook-sot.json"
        legacy_sot = _load("legacy_lookbook_fallback", _BUILD_LOOKBOOK_SOT)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                str(_BUILD_LOOKBOOK_SOT),
                "--manifest",
                str(manifest),
                "--collections-dir",
                str(collections_dir),
                "--out",
                str(output),
            ],
        )

        assert legacy_sot.main() == 0
        assert (
            json.loads(output.read_text(encoding="utf-8"))["collections"][0]["collection"]
            == "fallback"
        )

    def test_compatibility_entrypoint_rejects_missing_manifest_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        collections_dir = tmp_path / "collections"
        fallback_dir = collections_dir / "fallback"
        fallback_dir.mkdir(parents=True)
        (fallback_dir / "sot.json").write_text('{"name": "Fallback"}\n', encoding="utf-8")
        manifest = tmp_path / "manifest.json"
        manifest.write_text(
            json.dumps({"sources": [{"slug": "missing", "sot": "missing/sot.json"}]}),
            encoding="utf-8",
        )
        legacy_sot = _load("legacy_lookbook_missing_source", _BUILD_LOOKBOOK_SOT)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                str(_BUILD_LOOKBOOK_SOT),
                "--manifest",
                str(manifest),
                "--collections-dir",
                str(collections_dir),
            ],
        )

        with pytest.raises(FileNotFoundError):
            legacy_sot.main()

    def test_build_payload_and_serialize_are_stable(self) -> None:
        payload = lookbook.build_lookbook_payload(_LOOKBOOK_MANIFEST)
        assert payload["domain"] == "wordpress-theme/skyyrose-flagship"
        assert payload["component"] == "lookbook"
        assert payload["collections"]
        assert lookbook.serialize(payload) == lookbook.serialize(payload)

    def test_generator_output_includes_expected_collections(self) -> None:
        payload = lookbook.build_lookbook_payload(_LOOKBOOK_MANIFEST)
        slugs = [item["collection"] for item in payload["collections"]]
        assert "black-rose" in slugs
        assert "love-hurts" in slugs
        assert "signature" in slugs
        assert "kids-capsule" in slugs

    def test_render_collection_escapes_title_after_normalizing_case(self) -> None:
        rendered = lookbook.render_collection(
            "example",
            {"name": "rose & 'thorn'", "products": [], "imagery": {}, "palette": {}},
            "/assets",
        )

        assert "<h2>Rose &amp; &#x27;Thorn&#x27;</h2>" in rendered


class TestLookbookSotFreshnessGuard:
    def test_guard_passes_when_fresh(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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

    def test_guard_fails_on_lookbook_drift(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        payload, _, html_file = _seed(tmp_path)
        sot_file = tmp_path / "lookbook-sot.json"
        corrupted = lookbook.serialize(payload)
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

    def test_guard_fails_on_missing_lookbook_html(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
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

    def test_guard_fails_when_canonical_component_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(validator, "_LOOKBOOK_COMPONENT", tmp_path / "missing.py")
        result = validator.check_lookbook_sot_current()
        assert not result.passed
        assert "canonical" in result.message.lower()

    def test_html_guard_fails_when_canonical_component_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
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
        monkeypatch.setattr(validator, "_LOOKBOOK_COMPONENT", tmp_path / "missing.py")
        result = validator.check_lookbook_html_current()
        assert not result.passed
        assert "canonical" in result.message.lower()
