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


def _v(passed, score=1.0, mode="hard_gate"):
    return Verdict(
        domain="test",
        passed=passed,
        score=score,
        gate_results={},
        failure_tags=() if passed else ("x",),
        reason="",
        cost_usd=0.01,
        mode=mode,
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


async def test_gate_returns_pass_immediately_without_revisions():
    core = EvaluationCore(judge_fn=lambda req: ({}, 0.01))
    ad = _Adapter(det=[], verdicts=[_v(True)])

    async def _producer(ref):
        return "initial"

    v = await core.gate(ad, ref={}, producer=_producer, cap=2)
    assert v.passed is True and v.attempts == 0


async def test_gate_exhausts_cap_and_returns_failing_verdict():
    core = EvaluationCore(judge_fn=lambda req: ({}, 0.01))
    ad = _Adapter(det=[], verdicts=[_v(False), _v(False), _v(False)])

    async def _producer(ref):
        return "initial"

    v = await core.gate(ad, ref={}, producer=_producer, cap=2)
    assert v.passed is False and v.attempts == 2


async def test_gate_soft_signal_does_not_revise():
    """soft_signal verdict (uncalibrated judge) must not trigger the revise loop."""
    revise_calls = 0

    class _TrackingAdapter(_Adapter):
        async def revise(self, ref, critique):
            nonlocal revise_calls
            revise_calls += 1
            return "revised"

    core = EvaluationCore(judge_fn=lambda req: ({}, 0.01))
    ad = _TrackingAdapter(det=[], verdicts=[_v(False, mode="soft_signal")])

    async def _producer(ref):
        return "initial"

    v = await core.gate(ad, ref={}, producer=_producer, cap=3)
    assert v.passed is False
    assert v.attempts == 0  # loop never entered
    assert revise_calls == 0  # revise never called


async def test_gate_hard_gate_revises_to_cap():
    """hard_gate failing verdict must run the revise loop up to cap."""
    core = EvaluationCore(judge_fn=lambda req: ({}, 0.01))
    # Three failing hard_gate verdicts; cap=2 means 2 revisions maximum.
    ad = _Adapter(det=[], verdicts=[_v(False), _v(False), _v(False)])

    async def _producer(ref):
        return "initial"

    v = await core.gate(ad, ref={}, producer=_producer, cap=2)
    assert v.passed is False
    assert v.attempts == 2  # revise loop ran the full cap
