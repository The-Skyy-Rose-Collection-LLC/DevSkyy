"""Unit tests for the pure helpers in scripts/glb_publish_manifest.py (no browser, no server)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "glb_publish_manifest",
    Path(__file__).resolve().parent.parent / "scripts" / "glb_publish_manifest.py",
)
glb_publish_manifest = importlib.util.module_from_spec(_SPEC)
sys.modules["glb_publish_manifest"] = glb_publish_manifest
_SPEC.loader.exec_module(glb_publish_manifest)


class TestBuildPublishManifest:
    def test_only_includes_pass_verdicts(self, tmp_path):
        glb = tmp_path / "sg-001.glb"
        glb.write_bytes(b"glTF" * 100)
        rows = [
            {
                "sku": "sg-001",
                "glb": str(glb),
                "verdict": "pass",
                "color_delta_e": 7.3,
                "master": "m.webp",
            },
            {"sku": "sg-006", "glb": str(tmp_path / "sg-006.glb"), "verdict": "fail"},
            {"sku": "br-009", "glb": str(tmp_path / "br-009.glb"), "verdict": "no_master"},
        ]
        manifest = glb_publish_manifest.build_publish_manifest(rows)
        assert manifest["summary"]["count"] == 1
        assert manifest["entries"][0]["sku"] == "sg-001"
        assert manifest["entries"][0]["glb_bytes"] == 400

    def test_missing_glb_file_has_none_bytes(self, tmp_path):
        rows = [
            {
                "sku": "sg-002",
                "glb": str(tmp_path / "missing.glb"),
                "verdict": "pass",
                "color_delta_e": 8.8,
                "master": "m.webp",
            }
        ]
        manifest = glb_publish_manifest.build_publish_manifest(rows)
        assert manifest["entries"][0]["glb_bytes"] is None

    def test_empty_when_no_pass_rows(self):
        rows = [{"sku": "sg-006", "glb": "x.glb", "verdict": "fail"}]
        manifest = glb_publish_manifest.build_publish_manifest(rows)
        assert manifest["entries"] == []
        assert manifest["summary"]["count"] == 0

    def test_carries_color_delta_e_and_master(self, tmp_path):
        glb = tmp_path / "br-002.glb"
        glb.write_bytes(b"x")
        rows = [
            {
                "sku": "br-002",
                "glb": str(glb),
                "verdict": "pass",
                "color_delta_e": 7.31,
                "master": "/path/to/master.webp",
            }
        ]
        manifest = glb_publish_manifest.build_publish_manifest(rows)
        entry = manifest["entries"][0]
        assert entry["color_delta_e"] == 7.31
        assert entry["master"] == "/path/to/master.webp"
