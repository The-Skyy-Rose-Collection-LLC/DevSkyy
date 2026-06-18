import json

from evaluation.contracts import Verdict
from evaluation.observer import Observer, judge_human_agreement


def _v(passed):
    return Verdict(
        domain="imagery",
        passed=passed,
        score=1.0 if passed else 0.0,
        gate_results={},
        failure_tags=() if passed else ("wrong_garment",),
        reason="",
        cost_usd=0.02,
    )


def test_record_writes_jsonl(tmp_path):
    log = tmp_path / "run.jsonl"
    obs = Observer(log_path=log)
    obs.record(subject_id="br-006/ghost.png", verdict=_v(False), duration_ms=900)
    obs.record(subject_id="br-001/ghost.png", verdict=_v(True), duration_ms=850)
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 2
    row = json.loads(lines[0])
    assert row["subject_id"] == "br-006/ghost.png" and row["passed"] is False
    assert row["failure_tags"] == ["wrong_garment"]
    summary = obs.summary()
    assert summary["total"] == 2 and summary["passed"] == 1
    assert round(summary["cost_usd"], 2) == 0.04


def test_agreement():
    assert judge_human_agreement([True, False, True], [True, False, False]) == 2 / 3
