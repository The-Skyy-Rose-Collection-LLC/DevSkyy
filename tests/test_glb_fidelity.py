"""Unit tests for the pure helpers in scripts/glb_fidelity.py (no browser, no server)."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "glb_fidelity", Path(__file__).resolve().parent.parent / "scripts" / "glb_fidelity.py"
)
glb_fidelity = importlib.util.module_from_spec(_SPEC)
sys.modules["glb_fidelity"] = glb_fidelity
_SPEC.loader.exec_module(glb_fidelity)


class TestCollectionSlug:
    def test_known_prefixes(self):
        assert glb_fidelity._collection_slug("br-001") == "black-rose"
        assert glb_fidelity._collection_slug("lh-004") == "love-hurts"
        assert glb_fidelity._collection_slug("sg-015") == "signature"
        assert glb_fidelity._collection_slug("kids-002") == "kids-capsule"

    def test_unknown_prefix_raises(self):
        with pytest.raises(ValueError, match="Unknown SKU prefix"):
            glb_fidelity._collection_slug("xx-001")


class TestSkuSanitization:
    def test_all_skus_skips_invalid_names(self, tmp_path, monkeypatch, capsys):
        for name in ("br-001.glb", "sg-002.glb", "Weird Name (1).glb", "..evil.glb"):
            (tmp_path / name).write_bytes(b"glTF")
        monkeypatch.setattr(glb_fidelity, "GLB_DIR", tmp_path)
        skus = glb_fidelity._all_skus()
        assert skus == ["br-001", "sg-002"]
        out = capsys.readouterr().out
        assert "skipping non-SKU glb name" in out

    def test_sku_regex_shape(self):
        assert glb_fidelity._SKU_RE.fullmatch("br-001")
        assert glb_fidelity._SKU_RE.fullmatch("kids-002")
        assert not glb_fidelity._SKU_RE.fullmatch("br 001")
        assert not glb_fidelity._SKU_RE.fullmatch("../etc")
        assert not glb_fidelity._SKU_RE.fullmatch("BR-001")


class TestSha256:
    def test_matches_hashlib(self, tmp_path):
        p = tmp_path / "blob.bin"
        p.write_bytes(b"skyyrose" * 1000)
        assert glb_fidelity._sha256(p) == hashlib.sha256(b"skyyrose" * 1000).hexdigest()


class TestFmtRow:
    def test_row_renders_none_scores(self):
        r = glb_fidelity.SKUResult(
            sku="br-009",
            glb="x.glb",
            master=None,
            screenshot=None,
            screenshot_ok=True,
            mv_loaded=True,
            mv_errored=False,
            color_delta_e=None,
            color_pass=None,
            clip_score=None,
            clip_pass=None,
            verdict="no_master",
        )
        row = glb_fidelity._fmt_row(r)
        assert "br-009" in row and "NO_MASTER" in row and "n/a" in row
