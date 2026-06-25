"""Phase 1 / P-existcheck-audit: gate path pre-check + audit fingerprint.

Model-free. (1) embedding_gate.evaluate must reject a missing path without
touching the encoder. (2) write_audit_log must fingerprint the scored image
(sha256 + size) so the audit can prove which bytes were evaluated.
"""

from __future__ import annotations

import hashlib
import json
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from skyyrose.elite_studio.agents.compositor.audit import write_audit_log
from skyyrose.elite_studio.quality.embedding_gate import GateVerdict, evaluate

pytestmark = pytest.mark.unit


def _centroid(threshold: float = 0.7):
    c = MagicMock()
    c.threshold = threshold
    return c


# ---- (1) path pre-check ----


def test_evaluate_rejects_missing_path_without_encoder(tmp_path):
    with patch("skyyrose.elite_studio.quality.embedding_gate.score_against_centroid") as scorer:
        verdict = evaluate(tmp_path / "ghost.png", _centroid())
    scorer.assert_not_called()
    assert isinstance(verdict, GateVerdict)
    assert verdict.accepted is False
    assert verdict.score == 0.0


def test_evaluate_rejects_missing_str_path(tmp_path):
    with patch("skyyrose.elite_studio.quality.embedding_gate.score_against_centroid") as scorer:
        verdict = evaluate(str(tmp_path / "nope.jpg"), _centroid())
    scorer.assert_not_called()
    assert verdict.accepted is False


def test_evaluate_pil_image_bypasses_path_guard():
    img = Image.new("RGB", (8, 8))
    with patch(
        "skyyrose.elite_studio.quality.embedding_gate.score_against_centroid", return_value=0.9
    ):
        assert evaluate(img, _centroid(0.0)).accepted is True


# ---- (2) audit fingerprint ----


def _result(output_path: str):
    return types.SimpleNamespace(
        collection="signature",
        success=True,
        provider="anthropic",
        model="x",
        output_path=output_path,
        alpha_path=None,
        qa_status="pass",
        qa_details={},
        stages_completed=6,
        used_fallback=False,
        fallback_provider=None,
        error=None,
    )


def test_audit_records_sha256_and_size(tmp_path):
    f = tmp_path / "render.png"
    f.write_bytes(b"data")
    log = write_audit_log("br-001", "t", {}, _result(str(f)), str(tmp_path))
    body = json.loads(Path(log).read_text())
    assert body["result"]["scored_image_sha256"] == hashlib.sha256(b"data").hexdigest()
    assert body["result"]["scored_image_size_bytes"] == 4


def test_audit_handles_missing_output_path(tmp_path):
    log = write_audit_log("br-002", "s", {}, _result(str(tmp_path / "nope.png")), str(tmp_path))
    body = json.loads(Path(log).read_text())
    assert body["result"]["scored_image_sha256"] == ""
    assert body["result"]["scored_image_size_bytes"] == 0
