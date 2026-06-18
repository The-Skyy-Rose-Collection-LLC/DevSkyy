"""Execution proof for the Claude (Anthropic) QC judge adapter.

The live model's *accuracy* is validated by the ground-truth eval harness
(scripts/oai-render-qc-eval.py), which needs ANTHROPIC_API_KEY. These tests
need no key: they inject a fake Anthropic client and prove the adapter CODE
path executes correctly — it builds the documented request shape (raw-base64
image blocks + forced tool call), parses the tool_use verdict, and maps it to
the right QCVerdict gates. This closes the "code never executed" gap that is
independent of the live API.
"""

from __future__ import annotations

import pytest

from scripts.oai_render.qc import _JUDGE_TOOL, QCGate, RenderExpectation


def _gate_with_fake_anthropic(verdict_input: dict):
    """A QCGate wired to a fake Anthropic client that returns ``verdict_input``.

    Returns ``(gate, captured)`` where ``captured`` records the create() kwargs.
    Built with use_judge=False so __init__ does NOT require a real key, then
    switched to the anthropic path with the fake client injected.
    """
    captured: dict = {}

    class _Block:
        type = "tool_use"
        name = _JUDGE_TOOL["name"]
        input = verdict_input

    class _Resp:
        content = [_Block()]

    class _Messages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return _Resp()

    class _FakeClient:
        messages = _Messages()

    gate = QCGate(use_judge=False)
    gate._provider = "anthropic"
    gate._client = _FakeClient()
    gate._model = "claude-sonnet-4-6"
    return gate, captured


def _exp() -> RenderExpectation:
    return RenderExpectation(
        sku="br-001",
        name="BLACK Rose Crewneck",
        style="ghost",
        view="front",
        is_pair=False,
        is_patch=False,
        branding_spec="front-chest: greyscale rose cluster on a cloud",
        reference_paths=(),
    )


_PASS_VERDICT = {
    "visual_analysis": "Black crewneck, greyscale rose cluster on chest, correct placement.",
    "is_single_photograph": True,
    "garment_matches_reference": True,
    "view_correct": True,
    "branding_legible_and_correct": True,
    "photorealistic_not_flat": True,
    "all_garments_present": True,
    "reason": "pass",
}


def test_claude_adapter_builds_documented_request_shape():
    gate, captured = _gate_with_fake_anthropic(_PASS_VERDICT)
    gate._judge(b"fake-png-bytes", _exp())

    assert captured["model"] == "claude-sonnet-4-6"
    assert captured["tool_choice"] == {"type": "any"}  # forces the structured verdict
    assert captured["tools"] == [_JUDGE_TOOL]
    content = captured["messages"][0]["content"]
    # text instruction first, then the candidate as a raw-base64 image block
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image"
    src = content[1]["source"]
    assert src["type"] == "base64" and src["media_type"] == "image/png"
    assert not src["data"].startswith("data:")  # raw base64, NOT an OpenAI data-URL


def test_claude_adapter_maps_pass_verdict():
    gate, _ = _gate_with_fake_anthropic(_PASS_VERDICT)
    verdict = gate._judge(b"fake-png-bytes", _exp())
    assert verdict.passed is True
    assert verdict.failure_tags == ()
    assert verdict.analysis  # the forced visual_analysis must flow through, auditable


def test_verdict_caps_analysis_at_construction():
    # The "analysis ≤ N chars" contract is enforced where QCVerdict is built, so
    # every downstream consumer (logs, runlog JSONL, monitor) inherits it.
    long_analysis = {**_PASS_VERDICT, "visual_analysis": "x" * 5000}
    gate, _ = _gate_with_fake_anthropic(long_analysis)
    verdict = gate._judge(b"fake-png-bytes", _exp())
    assert len(verdict.analysis) <= 601  # 600 + ellipsis


def test_claude_adapter_maps_failure_to_gate_tag():
    bad = {**_PASS_VERDICT, "branding_legible_and_correct": False, "reason": "wrong logo art"}
    gate, _ = _gate_with_fake_anthropic(bad)
    verdict = gate._judge(b"fake-png-bytes", _exp())
    assert verdict.passed is False
    assert "branding_drift" in verdict.failure_tags
    assert verdict.reason == "wrong logo art"


def test_claude_adapter_missing_tool_block_is_unavailable_not_silent_pass():
    # A response with no tool_use block must surface as judge_unavailable (tagged
    # for review), never a silent structural failure.
    gate, _ = _gate_with_fake_anthropic(_PASS_VERDICT)

    class _Empty:
        content = []

    gate._client.messages.create = lambda **kw: _Empty()
    verdict = gate._judge(b"fake-png-bytes", _exp())
    assert verdict.failure_tags == ("judge_unavailable",)


def test_anthropic_provider_fail_closed_without_key(monkeypatch):
    from scripts.oai_render import config

    monkeypatch.setattr(config, "QC_JUDGE_PROVIDER", "anthropic")
    monkeypatch.delenv(config.ANTHROPIC_API_KEY_ENV, raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        QCGate()
