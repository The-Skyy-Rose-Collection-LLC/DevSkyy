from evaluation.contracts import Verdict
from evaluation.core import EvaluationCore


class _Adapter:
    domain = "test"

    def __init__(self, det, verdicts):
        self._det = det
        self._v = list(verdicts)
        self.calls = 0

    def deterministic_checks(self, subject, ref):
        return list(self._det)

    def build_judge_request(self, subject, ref):
        return {"judge": True}

    def parse_verdict(self, judge_output, det_failures):
        v = self._v[min(self.calls, len(self._v) - 1)]
        self.calls += 1
        return v

    async def revise(self, ref, critique):
        return "revised"

    def load_ground_truth(self):
        return []


def _v(passed, score=1.0):
    return Verdict(
        domain="test",
        passed=passed,
        score=score,
        gate_results={},
        failure_tags=() if passed else ("x",),
        reason="",
        cost_usd=0.01,
    )


async def test_score_short_circuits_on_deterministic_fail():
    core = EvaluationCore(judge_fn=lambda req: ({}, 0.0))
    ad = _Adapter(det=["wrong_dimensions"], verdicts=[_v(True)])
    v = await core.score(ad, subject=b"x", ref={})
    assert v.passed is False and "wrong_dimensions" in v.failure_tags
    assert ad.calls == 0  # judge never called when deterministic fails


async def test_score_calls_judge_when_clean():
    core = EvaluationCore(judge_fn=lambda req: ({"ok": True}, 0.02))
    ad = _Adapter(det=[], verdicts=[_v(True)])
    v = await core.score(ad, subject=b"x", ref={})
    assert v.passed is True and ad.calls == 1


async def test_gate_revises_until_pass_with_cap_and_early_exit():
    core = EvaluationCore(judge_fn=lambda req: ({}, 0.01))
    ad = _Adapter(det=[], verdicts=[_v(False), _v(True)])  # fail then pass

    async def _producer(ref):
        return "ignored"

    v = await core.gate(ad, ref={}, producer=_producer, cap=2)
    assert v.passed is True and v.attempts == 1  # one revision, early-exit
