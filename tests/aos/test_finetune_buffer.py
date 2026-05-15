"""Tests for FineTuneBuffer — quality gate, FIFO eviction, JSONL export, drain."""

from __future__ import annotations

import json

from aos.cognition.reflector import Reflector
from aos.observability.finetune_buffer import FineTuneBuffer
from aos.observability.learning_hook import LearningTrace


def _trace(
    agent_type: str = "test",
    prompt: str = "do x",
    result: str | None = "done",
    cost_usd: float = 0.0,
    latency_ms: float = 0.0,
) -> LearningTrace:
    return LearningTrace(
        agent_type=agent_type,
        prompt=prompt,
        result=result,
        success=True,
        error=None,
        retry_count=0,
        heal_categories=(),
        cost_usd=cost_usd,
        latency_ms=latency_ms,
    )


class _FakeOutcome:
    def __init__(self, pid: int = 1, success: bool = True) -> None:
        self.pid = pid
        self.success = success
        self.error = None
        self.heal_entries = ()


def _high_quality_reflection():
    reflector = Reflector()
    outcome = _FakeOutcome(success=True)
    return reflector.reflect(outcome, _trace())


def _low_quality_reflection():
    reflector = Reflector()
    outcome = _FakeOutcome(success=False)
    outcome.error = "some failure"
    return reflector.reflect(outcome, _trace())


class TestQualityGate:
    def test_high_quality_accepted(self):
        buf = FineTuneBuffer(quality_threshold=0.7)
        ref = _high_quality_reflection()
        assert ref.quality_score >= 0.7
        accepted = buf.add(ref)
        assert accepted is True
        assert buf.size == 1

    def test_low_quality_rejected(self):
        buf = FineTuneBuffer(quality_threshold=0.7)
        ref = _low_quality_reflection()
        assert ref.quality_score < 0.7
        accepted = buf.add(ref)
        assert accepted is False
        assert buf.size == 0

    def test_threshold_boundary_exact(self):
        buf = FineTuneBuffer(quality_threshold=1.0)
        ref = _low_quality_reflection()
        assert ref.quality_score < 1.0
        assert buf.add(ref) is False


class TestFIFOEviction:
    def test_oldest_dropped_at_capacity(self):
        buf = FineTuneBuffer(quality_threshold=0.0, max_capacity=3)
        reflector = Reflector()
        refs = []
        for i in range(4):
            outcome = _FakeOutcome(pid=i, success=True)
            ref = reflector.reflect(outcome, _trace(prompt=f"prompt {i}"))
            buf.add(ref)
            refs.append(ref)
        assert buf.size == 3
        records = buf.drain()
        prompts = [r.messages[1]["content"] for r in records]
        assert "prompt 0" not in prompts
        assert "prompt 1" in prompts
        assert "prompt 2" in prompts
        assert "prompt 3" in prompts


class TestExportJsonl:
    def test_jsonl_format(self, tmp_path):
        buf = FineTuneBuffer(quality_threshold=0.0)
        reflector = Reflector()
        outcome = _FakeOutcome(success=True)
        buf.add(reflector.reflect(outcome, _trace(agent_type="commerce", prompt="list skus")))

        dest = tmp_path / "export.jsonl"
        count = buf.export_jsonl(dest)
        assert count == 1
        lines = dest.read_text().strip().splitlines()
        assert len(lines) == 1
        row = json.loads(lines[0])
        assert "messages" in row
        assert row["messages"][0]["role"] == "system"
        assert row["messages"][1]["role"] == "user"
        assert row["messages"][2]["role"] == "assistant"

    def test_jsonl_creates_parent_dirs(self, tmp_path):
        buf = FineTuneBuffer(quality_threshold=0.0)
        reflector = Reflector()
        outcome = _FakeOutcome(success=True)
        buf.add(reflector.reflect(outcome, _trace()))
        dest = tmp_path / "deep" / "nested" / "out.jsonl"
        buf.export_jsonl(dest)
        assert dest.exists()

    def test_export_empty_buffer(self, tmp_path):
        buf = FineTuneBuffer()
        dest = tmp_path / "empty.jsonl"
        count = buf.export_jsonl(dest)
        assert count == 0
        assert dest.read_text() == ""


class TestDrain:
    def test_drain_returns_all_and_clears(self):
        buf = FineTuneBuffer(quality_threshold=0.0)
        reflector = Reflector()
        for i in range(3):
            outcome = _FakeOutcome(pid=i, success=True)
            buf.add(reflector.reflect(outcome, _trace()))
        records = buf.drain()
        assert len(records) == 3
        assert buf.size == 0

    def test_drain_empty(self):
        buf = FineTuneBuffer()
        assert buf.drain() == []
