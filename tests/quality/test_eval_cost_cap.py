"""EvaluationCore.gate() cost-cap (Q-costcap) — model-free.

The discriminating assertion for "blocked before any paid call" is that the
judge_fn call-count is 0 when the budget is exhausted: a raise that happens
AFTER the call would still satisfy a naive ``pytest.raises`` check, so we assert
the paid call never fired (mirrors the flux_lora ``mock_post.assert_not_called()``
pattern). No Anthropic client, no network — judge_fn is a plain counter.
"""

import pytest

from evaluation.budget import CostCapExceeded, EvalBudget
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


def _v(passed, cost=0.01, mode="hard_gate"):
    return Verdict(
        domain="test",
        passed=passed,
        score=1.0 if passed else 0.0,
        gate_results={},
        failure_tags=() if passed else ("x",),
        reason="",
        cost_usd=cost,
        mode=mode,
    )


class _CountingJudge:
    """judge_fn that counts invocations so we can assert it was never called."""

    def __init__(self, cost=0.01):
        self.calls = 0
        self._cost = cost

    def __call__(self, request):
        self.calls += 1
        return ({"ok": True}, self._cost)


async def _producer(ref):
    return "subject"


# ── EvalBudget unit ────────────────────────────────────────────────────────


def test_budget_can_afford_and_accumulates():
    b = EvalBudget(cap_usd=1.0)
    assert b.can_afford(0.4) and b.remaining_usd == 1.0
    b.add(0.4)
    assert b.remaining_usd == pytest.approx(0.6)
    b.add(0.4)
    assert not b.can_afford(0.4)  # 0.8 + 0.4 > 1.0
    assert b.remaining_usd == pytest.approx(0.2)


# ── gate() cost-cap ────────────────────────────────────────────────────────


async def test_gate_raises_before_any_paid_call_when_budget_exhausted():
    judge = _CountingJudge()
    core = EvaluationCore(judge_fn=judge)
    ad = _Adapter(det=[], verdicts=[_v(True)])
    budget = EvalBudget(cap_usd=0.0)  # cannot afford even one call

    with pytest.raises(CostCapExceeded):
        await core.gate(
            ad, ref={}, producer=_producer, cap=2, budget=budget, est_call_cost_usd=0.05
        )

    assert judge.calls == 0  # the paid call never fired
    assert ad.calls == 0  # producer/score never reached
    assert budget.spent_usd == 0.0


async def test_gate_stops_mid_loop_when_budget_runs_out():
    # cap affords the initial call (est 0.05) but not a revision: after the initial
    # call spends 0.01 actual, remaining 0.04 < est 0.05 -> the revision is blocked.
    judge = _CountingJudge(cost=0.01)
    core = EvaluationCore(judge_fn=judge)
    ad = _Adapter(det=[], verdicts=[_v(False), _v(True)])
    budget = EvalBudget(cap_usd=0.05)

    with pytest.raises(CostCapExceeded):
        await core.gate(
            ad, ref={}, producer=_producer, cap=2, budget=budget, est_call_cost_usd=0.05
        )

    assert judge.calls == 1  # only the initial judge call fired; revision blocked pre-call
    assert budget.spent_usd == pytest.approx(0.01)


async def test_gate_without_budget_is_unbounded_back_compat():
    judge = _CountingJudge()
    core = EvaluationCore(judge_fn=judge)
    ad = _Adapter(det=[], verdicts=[_v(False), _v(False), _v(False)])

    v = await core.gate(ad, ref={}, producer=_producer, cap=2)  # budget=None

    assert v.attempts == 2 and judge.calls == 3  # current behavior preserved


async def test_gate_accumulates_total_cost_into_budget_and_verdict():
    # score() sets verdict.cost_usd from the judge_fn's returned cost (not the
    # adapter verdict), so 2 judge calls at 0.01 each accumulate to 0.02.
    judge = _CountingJudge(cost=0.01)
    core = EvaluationCore(judge_fn=judge)
    ad = _Adapter(det=[], verdicts=[_v(False), _v(True)])
    budget = EvalBudget(cap_usd=1.0)

    v = await core.gate(ad, ref={}, producer=_producer, cap=2, budget=budget)

    assert judge.calls == 2
    assert budget.spent_usd == pytest.approx(0.02)  # 2 judge calls x 0.01 accumulated
    assert v.cost_usd == pytest.approx(0.02)  # verdict reports the loop total
    assert v.attempts == 1
