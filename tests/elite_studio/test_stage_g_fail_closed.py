"""Phase 1 / P-failclosed-G: stage G visual QA must fail closed on oracle error.

Model-free — analyze_vision is a stub; no Gemini call. A provider error or an
unparseable response must return status="fail" (with an error_type discriminator),
not "warn" — otherwise a transient 503 silently passes the QA gate. A legitimate
low-confidence rubric "warn" is preserved.

Covers BOTH copies: the LIVE inline CompositorAgent._visual_qa and the parallel
module stage_g_visual_qa.visual_qa.
"""

from __future__ import annotations

import pytest
from PIL import Image

import skyyrose.elite_studio.agents.compositor_agent as compositor_agent
from skyyrose.elite_studio.agents.compositor import stage_g_visual_qa
from skyyrose.elite_studio.agents.compositor.orchestrator import CompositorAgent

pytestmark = pytest.mark.unit


def _png(tmp_path):
    p = tmp_path / "composite.png"
    Image.new("RGB", (8, 8)).save(p)
    return str(p)


def _agent():
    return CompositorAgent.__new__(CompositorAgent)


# ---- LIVE inline path: CompositorAgent._visual_qa ----


def test_inline_provider_error_is_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(
        compositor_agent, "analyze_vision", lambda **_: {"success": False, "error": "503"}
    )
    out = _agent()._visual_qa(_png(tmp_path), "scene", "black-rose")
    assert out["status"] == "fail" and out["error_type"] == "qa_provider_error"


def test_inline_parse_error_is_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(
        compositor_agent, "analyze_vision", lambda **_: {"success": True, "text": "not json!!!"}
    )
    out = _agent()._visual_qa(_png(tmp_path), "scene", "signature")
    assert out["status"] == "fail" and out["error_type"] == "qa_parse_error"


def test_inline_legitimate_warn_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(
        compositor_agent,
        "analyze_vision",
        lambda **_: {"success": True, "text": '{"status": "warn"}'},
    )
    out = _agent()._visual_qa(_png(tmp_path), "scene", "love-hurts")
    assert out["status"] == "warn" and "error_type" not in out


# ---- module copy: stage_g_visual_qa.visual_qa ----


def test_module_provider_error_is_fail(tmp_path):
    out = stage_g_visual_qa.visual_qa(
        _png(tmp_path), "s", "c", analyze_vision=lambda **_: {"success": False, "error": "x"}
    )
    assert out["status"] == "fail" and out["error_type"] == "qa_provider_error"


def test_module_parse_error_is_fail(tmp_path):
    out = stage_g_visual_qa.visual_qa(
        _png(tmp_path), "s", "c", analyze_vision=lambda **_: {"success": True, "text": "not json"}
    )
    assert out["status"] == "fail" and out["error_type"] == "qa_parse_error"


def test_module_legitimate_warn_preserved(tmp_path):
    out = stage_g_visual_qa.visual_qa(
        _png(tmp_path),
        "s",
        "c",
        analyze_vision=lambda **_: {"success": True, "text": '{"status": "warn"}'},
    )
    assert out["status"] == "warn" and "error_type" not in out
