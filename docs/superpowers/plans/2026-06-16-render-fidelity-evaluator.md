# Render Fidelity Evaluator — Implementation Plan (Phase 0 core + Phase 1 imagery)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** A shared evaluation core + the Render Fidelity Evaluator (imagery domain): a Claude **vision** judge that scores a generated product photo against the real garment for 100% replication, reusing the proven `scripts/oai_render/qc.py` machinery, calibrated against the 81 founder labels.

**Architecture:** New `evaluation/` package = domain-agnostic core (deterministic gate → judge → verdict → revise loop → calibration → observer) behind a `DomainAdapter` port. The imagery adapter reuses `qc.deterministic_checks`, `references.build_references`, the 6-gate schema, and `RenderExpectation`; swaps the on-disk `gpt-4o-mini` judge for a Claude vision judge (forced tool-use, leading `visual_analysis` CoT). Wired into the render pipeline at the existing `QCGate` seam via a `QC_JUDGE_PROVIDER` switch — no pipeline-loop changes.

**Tech Stack:** Python 3.11+, `anthropic` 0.83.0 (verified installed), pytest (`asyncio_mode=auto`). Reuses `scripts/oai_render/{qc,references,config,cost}.py`, `skyyrose/core/dossier_loader.py`, `renders/oai/_review/review-state.json`.

**Companion spec:** `docs/superpowers/specs/2026-06-16-evaluation-system-two-domains-design.html`

---

## Verified facts this plan is built on (file:line)

| Fact | Source |
|---|---|
| `deterministic_checks(data: bytes) -> list[str]` (invalid_image/wrong_dimensions/collage_panels) | `scripts/oai_render/qc.py:173` |
| 6-gate schema + `_GATE_TAGS` + `QCVerdict(passed, failure_tags, reason, judge_cost_usd)` + `RenderExpectation(sku,name,style,view,is_pair,is_patch,reference_paths)` | `qc.py:33,91,104,116` |
| `QCGate.__init__(use_judge)`, `.check(data, exp)`, `._judge()` hardwired to OpenAI | `qc.py:243,261,273` |
| `build_references(sku, collection, *, include_back, view) -> list[ReferenceImage(label,path,kind)]`, `MissingReferenceError` | `scripts/oai_render/references.py:361,26` |
| `EXCLUDED_SKUS`, `QC_*` config, `EXPECTED_RENDER_SIZE`, `DOSSIER_DIR` | `scripts/oai_render/config.py:55,66` |
| `Dossier` dataclass has NO `reference_image`/`extra_references` (silent-fallback bug) | `skyyrose/core/dossier_loader.py:40,150` |
| Anthropic: `messages.create(model,max_tokens,messages,tools,tool_choice={"type":"tool","name":...,"disable_parallel_tool_use":True})`; image block `{"type":"image","source":{"type":"base64","media_type":...,"data":...}}`; parse `[b for b in resp.content if b.type=="tool_use"][0].input`; `resp.usage.input_tokens/output_tokens` | Context7 `/anthropics/anthropic-sdk-python` (verified 2026-06-16) |
| `config.settings.ANTHROPIC_API_KEY` exists (Pydantic), not in live env | `config/settings.py:63` |
| 81 founder labels: `{<slug>/<file>.png: {approved, flagged, comment, updated}}` | `renders/oai/_review/review-state.json` |

---

## File structure

| File | Responsibility | Phase |
|---|---|---|
| `evaluation/__init__.py` | package marker | 0 |
| `evaluation/contracts.py` | `Verdict`, `Severity` | 0 |
| `evaluation/adapter.py` | `DomainAdapter` Protocol | 0 |
| `evaluation/judge.py` | `ClaudeJudge` (vision+text, forced tool-use, usage→cost) + anthropic pricing | 0 |
| `evaluation/core.py` | `EvaluationCore.score()` + `.gate()` | 0 |
| `evaluation/calibration.py` | `cohen_kappa` + `decide_mode` | 0 |
| `evaluation/observer.py` | domain-tagged JSONL record + agreement | 0 |
| `skyyrose/core/dossier_loader.py` | **modify**: add `reference_image`/`extra_references` | 1 |
| `evaluation/domains/__init__.py` + `imagery.py` | `ImageryAdapter` | 1 |
| `evaluation/agents.py` | `RenderFidelityEvaluator` (job-title binding) | 1 |
| `scripts/oai_render/config.py` | **modify**: `QC_JUDGE_PROVIDER` + anthropic judge consts | 1 |
| `scripts/oai_render/qc.py` | **modify**: `QCGate._judge` delegates to Claude judge when provider=anthropic | 1 |
| `scripts/oai-render-qc-eval.py` | eval harness (κ vs review-state.json) | 1 |
| `tests/quality/*`, `tests/fixtures/qc_ground_truth/` | tests + ground truth | 0/1 |

---

# PHASE 0 — Shared core

## Task 1: Package + contracts

**Files:** Create `evaluation/__init__.py`, `evaluation/contracts.py`; Test `tests/quality/test_eval_contracts.py`

- [ ] **Step 1: Package marker**
```python
# evaluation/__init__.py
"""Domain-agnostic evaluation core + domain adapters (imagery, content)."""
```
- [ ] **Step 2: Failing test**
```python
# tests/quality/test_eval_contracts.py
import dataclasses
from evaluation.contracts import Verdict, Severity


def test_verdict_passed_and_score():
    v = Verdict(domain="imagery", passed=True, score=1.0, gate_results={"a": True},
                failure_tags=(), reason="pass", cost_usd=0.01, attempts=0, mode="hard_gate")
    assert v.passed and v.score == 1.0
    try:
        v.passed = False
        assert False
    except dataclasses.FrozenInstanceError:
        pass


def test_severity_order():
    assert Severity.PAGE > Severity.TICKET > Severity.DASHBOARD
```
- [ ] **Step 3: Run → fail** `python -m pytest tests/quality/test_eval_contracts.py -v` → `ModuleNotFoundError`
- [ ] **Step 4: Implement**
```python
# evaluation/contracts.py
"""Normalized verdict shared across evaluation domains."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal


class Severity(IntEnum):
    DASHBOARD = 1
    TICKET = 2
    PAGE = 3


@dataclass(frozen=True)
class Verdict:
    domain: str                       # "imagery" | "copy"
    passed: bool
    score: float                      # 0..1 (imagery: gates_passed/total; copy: composite/5)
    gate_results: dict                # imagery: {gate: bool}; copy: {dimension: int}
    failure_tags: tuple[str, ...] = ()
    reason: str = ""
    cost_usd: float = 0.0
    attempts: int = 0
    mode: Literal["hard_gate", "soft_signal"] = "soft_signal"
    detail: dict = field(default_factory=dict)
```
- [ ] **Step 5: Run → pass.** **Step 6: Commit** `git add evaluation/__init__.py evaluation/contracts.py tests/quality/test_eval_contracts.py && git commit -m "feat(eval): normalized Verdict contract"`

---

## Task 2: DomainAdapter port

**Files:** Create `evaluation/adapter.py`; Test `tests/quality/test_eval_adapter.py`

- [ ] **Step 1: Failing test**
```python
# tests/quality/test_eval_adapter.py
from evaluation.adapter import DomainAdapter


def test_protocol_runtime_checkable():
    class Dummy:
        domain = "x"
        def deterministic_checks(self, subject, ref): return []
        def build_judge_request(self, subject, ref): return {}
        def parse_verdict(self, judge_output, det_failures): ...
        async def revise(self, ref, critique): ...
        def load_ground_truth(self): return []
    assert isinstance(Dummy(), DomainAdapter)
```
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Implement**
```python
# evaluation/adapter.py
"""The port that makes one core serve many domains."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from evaluation.contracts import Verdict


@runtime_checkable
class DomainAdapter(Protocol):
    domain: str

    def deterministic_checks(self, subject: Any, ref: Any) -> list[str]:
        """Free, un-hallucinatable hard-fail tags (empty = clean)."""
        ...

    def build_judge_request(self, subject: Any, ref: Any) -> dict:
        """Return {messages, tools, tool_name, model} for the judge."""
        ...

    def parse_verdict(self, judge_output: dict, det_failures: list[str]) -> Verdict:
        ...

    async def revise(self, ref: Any, critique: dict) -> Any:
        """Produce a revised subject (content: re-call agent; imagery: re-render)."""
        ...

    def load_ground_truth(self) -> list[dict]:
        """Labeled examples for calibration: [{subject, ref, label_pass: bool}]."""
        ...
```
- [ ] **Step 4: Run → pass. Step 5: Commit** `git add evaluation/adapter.py tests/quality/test_eval_adapter.py && git commit -m "feat(eval): DomainAdapter port"`

---

## Task 3: Calibration (Cohen's κ + mode)

**Files:** Create `evaluation/calibration.py`; Test `tests/quality/test_eval_calibration.py`

- [ ] **Step 1: Failing test**
```python
# tests/quality/test_eval_calibration.py
from evaluation.calibration import cohen_kappa, decide_mode


def test_perfect(): assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0
def test_chance(): assert cohen_kappa([1, 1, 1, 1], [1, 0, 1, 0]) <= 0.0
def test_mode():
    assert decide_mode(0.70) == "hard_gate"
    assert decide_mode(0.65) == "hard_gate"
    assert decide_mode(0.64) == "soft_signal"
```
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Implement** (no sklearn dependency)
```python
# evaluation/calibration.py
"""Cohen's kappa (binary pass/fail) → evaluator mode. Floor 0.65 (research-backed)."""
from __future__ import annotations

from collections import Counter
from typing import Literal

KAPPA_FLOOR = 0.65


def cohen_kappa(judge: list[int], human: list[int]) -> float:
    if len(judge) != len(human) or not judge:
        raise ValueError("equal-length non-empty rating lists required")
    n = len(judge)
    po = sum(1 for a, b in zip(judge, human) if a == b) / n
    cj, ch = Counter(judge), Counter(human)
    cats = set(judge) | set(human)
    pe = sum((cj.get(c, 0) / n) * (ch.get(c, 0) / n) for c in cats)
    return 1.0 if pe == 1.0 else (po - pe) / (1 - pe)


def decide_mode(kappa: float) -> Literal["hard_gate", "soft_signal"]:
    return "hard_gate" if kappa >= KAPPA_FLOOR else "soft_signal"
```
- [ ] **Step 4: Run → pass. Step 5: Commit** `git add evaluation/calibration.py tests/quality/test_eval_calibration.py && git commit -m "feat(eval): cohen kappa + mode decision"`

---

## Task 4: ClaudeJudge (vision + text, forced tool-use, usage→cost)

**Files:** Create `evaluation/judge.py`; Test `tests/quality/test_eval_judge.py`

- [ ] **Step 1: Failing test (fake anthropic client — no network)**
```python
# tests/quality/test_eval_judge.py
from evaluation.judge import ClaudeJudge, anthropic_cost_usd


class _Block:
    type = "tool_use"
    def __init__(self, inp): self.input = inp; self.name = "render_qc_verdict"


class _Usage:
    def __init__(self): self.input_tokens = 1200; self.output_tokens = 180


class _Resp:
    def __init__(self, inp): self.content = [_Block(inp)]; self.usage = _Usage(); self.stop_reason = "tool_use"


class _Messages:
    def __init__(self, inp): self._inp = inp; self.calls = []
    def create(self, **kw): self.calls.append(kw); return _Resp(self._inp)


class _Client:
    def __init__(self, inp): self.messages = _Messages(inp)


def test_judge_returns_tool_input_and_cost():
    payload = {"visual_analysis": "navy bomber, white script", "is_single_photograph": True,
               "reason": "pass"}
    client = _Client(payload)
    judge = ClaudeJudge(client=client, model="claude-sonnet-4-6")
    out, cost = judge.run(messages=[{"role": "user", "content": [{"type": "text", "text": "x"}]}],
                          tool={"name": "render_qc_verdict", "input_schema": {"type": "object"}})
    assert out["is_single_photograph"] is True
    assert out["visual_analysis"].startswith("navy")
    assert cost > 0
    # forced tool_choice on exactly one tool
    sent = client.messages.calls[0]
    assert sent["tool_choice"] == {"type": "tool", "name": "render_qc_verdict",
                                   "disable_parallel_tool_use": True}


def test_cost_formula():
    # sonnet-4-6: $3/M in, $15/M out
    assert round(anthropic_cost_usd("claude-sonnet-4-6", 1_000_000, 0), 4) == 3.0
    assert round(anthropic_cost_usd("claude-sonnet-4-6", 0, 1_000_000), 4) == 15.0


def test_judge_raises_when_no_tool_use():
    class _Empty(_Client):
        def __init__(self): self.messages = type("M", (), {"create": lambda s, **k: type(
            "R", (), {"content": [], "usage": _Usage(), "stop_reason": "end_turn"})()})()
    judge = ClaudeJudge(client=_Empty(), model="claude-sonnet-4-6")
    import pytest
    with pytest.raises(RuntimeError):
        judge.run(messages=[], tool={"name": "t", "input_schema": {}})
```
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Implement** (anthropic API verified via Context7)
```python
# evaluation/judge.py
"""Claude judge — vision or text — via forced tool-use (Anthropic structured output).

Anthropic has no OpenAI-style json_schema response_format; the reliable structured
path is tools + tool_choice={"type":"tool", name, disable_parallel_tool_use:True},
then read the single tool_use block's `.input`. Verified against anthropic 0.83.0.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# USD per 1M tokens (input, output). Keep in sync with model-routing doc.
_PRICING: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-8": (15.0, 75.0),
}


def anthropic_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    pin, pout = _PRICING.get(model, (3.0, 15.0))
    return input_tokens / 1_000_000 * pin + output_tokens / 1_000_000 * pout


def make_client():
    """Construct an Anthropic client from config.settings.ANTHROPIC_API_KEY."""
    from anthropic import Anthropic

    from config.settings import settings  # Pydantic settings; key field exists

    key = (settings.ANTHROPIC_API_KEY or "").strip()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is empty — set it before running the judge.")
    return Anthropic(api_key=key)


def image_block(b64_data: str, media_type: str = "image/png") -> dict:
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64_data}}


class ClaudeJudge:
    def __init__(self, client: Any, model: str, max_tokens: int = 1500) -> None:
        self._client = client
        self._model = model
        self._max_tokens = max_tokens

    def run(self, *, messages: list[dict], tool: dict) -> tuple[dict, float]:
        """Force one call to `tool` and return (tool_input, cost_usd)."""
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=messages,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"], "disable_parallel_tool_use": True},
        )
        blocks = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        cost = anthropic_cost_usd(self._model, resp.usage.input_tokens, resp.usage.output_tokens)
        if not blocks:
            raise RuntimeError(f"judge returned no tool_use block (stop={resp.stop_reason})")
        return dict(blocks[0].input), cost
```
- [ ] **Step 4: Run → pass. Step 5: Commit** `git add evaluation/judge.py tests/quality/test_eval_judge.py && git commit -m "feat(eval): ClaudeJudge vision+text via forced tool-use + cost"`

---

## Task 5: EvaluationCore (score + gate)

**Files:** Create `evaluation/core.py`; Test `tests/quality/test_eval_core.py`

- [ ] **Step 1: Failing test**
```python
# tests/quality/test_eval_core.py
from evaluation.contracts import Verdict
from evaluation.core import EvaluationCore


class _Adapter:
    domain = "test"
    def __init__(self, det, verdicts): self._det = det; self._v = list(verdicts); self.calls = 0
    def deterministic_checks(self, subject, ref): return list(self._det)
    def build_judge_request(self, subject, ref): return {"judge": True}
    def parse_verdict(self, judge_output, det_failures):
        v = self._v[min(self.calls, len(self._v) - 1)]; self.calls += 1
        return v
    async def revise(self, ref, critique): return "revised"
    def load_ground_truth(self): return []


def _v(passed, score=1.0):
    return Verdict(domain="test", passed=passed, score=score, gate_results={},
                   failure_tags=() if passed else ("x",), reason="", cost_usd=0.01)


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
    producer = ad  # revise() returns a new subject; here adapter is the producer

    async def _producer(ref): return "ignored"
    v = await core.gate(ad, ref={}, producer=_producer, cap=2)
    assert v.passed is True and v.attempts == 1  # one revision, early-exit
```
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Implement**
```python
# evaluation/core.py
"""Domain-agnostic evaluation orchestration.

score():  deterministic gate -> judge -> verdict (single shot). Used by the render
          pipeline seam (the pipeline owns re-render) and by the calibration harness.
gate():   score -> if fail, adapter.revise -> re-score, cap N, early-exit. Used by the
          content domain (the core owns the revise loop).
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Awaitable, Callable

from evaluation.adapter import DomainAdapter
from evaluation.contracts import Verdict

JudgeFn = Callable[[dict], tuple[dict, float]]  # request -> (judge_output, cost_usd)


class EvaluationCore:
    def __init__(self, judge_fn: JudgeFn) -> None:
        self._judge = judge_fn

    async def score(self, adapter: DomainAdapter, subject: Any, ref: Any) -> Verdict:
        det = adapter.deterministic_checks(subject, ref)
        if det:
            return Verdict(domain=adapter.domain, passed=False, score=0.0, gate_results={},
                           failure_tags=tuple(det), reason="deterministic pre-check failed",
                           cost_usd=0.0)
        request = adapter.build_judge_request(subject, ref)
        judge_output, cost = self._judge(request)
        verdict = adapter.parse_verdict(judge_output, det)
        return replace(verdict, cost_usd=verdict.cost_usd or cost)

    async def gate(self, adapter: DomainAdapter, ref: Any,
                   producer: Callable[[Any], Awaitable[Any]], cap: int = 2) -> Verdict:
        subject = await producer(ref)
        verdict = await self.score(adapter, subject, ref)
        attempts = 0
        while not verdict.passed and attempts < cap:
            attempts += 1
            critique = {"failure_tags": verdict.failure_tags, "reason": verdict.reason,
                        "detail": verdict.detail}
            subject = await adapter.revise(ref, critique)
            verdict = await self.score(adapter, subject, ref)
            if verdict.passed:
                break
        return replace(verdict, attempts=attempts)
```
- [ ] **Step 4: Run → pass. Step 5: Commit** `git add evaluation/core.py tests/quality/test_eval_core.py && git commit -m "feat(eval): EvaluationCore score + revise-loop gate"`

---

## Task 6: Observer (domain-tagged JSONL + agreement)

**Files:** Create `evaluation/observer.py`; Test `tests/quality/test_eval_observer.py`

- [ ] **Step 1: Failing test**
```python
# tests/quality/test_eval_observer.py
import json

from evaluation.contracts import Verdict
from evaluation.observer import Observer, judge_human_agreement


def _v(passed): return Verdict(domain="imagery", passed=passed, score=1.0 if passed else 0.0,
                               gate_results={}, failure_tags=() if passed else ("wrong_garment",),
                               reason="", cost_usd=0.02)


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
    # judge pass/fail vs human pass/fail
    assert judge_human_agreement([True, False, True], [True, False, False]) == 2 / 3
```
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Implement**
```python
# evaluation/observer.py
"""Domain-tagged evaluation observability: per-evaluation JSONL + batch summary +
judge-vs-human agreement. Alert+recommend only (never auto-acts)."""
from __future__ import annotations

import json
from pathlib import Path

from evaluation.contracts import Verdict


class Observer:
    def __init__(self, log_path: Path) -> None:
        self._log = Path(log_path)
        self._log.parent.mkdir(parents=True, exist_ok=True)
        self._rows: list[dict] = []

    def record(self, *, subject_id: str, verdict: Verdict, duration_ms: int) -> None:
        row = {
            "subject_id": subject_id, "domain": verdict.domain, "passed": verdict.passed,
            "score": verdict.score, "failure_tags": list(verdict.failure_tags),
            "reason": verdict.reason, "cost_usd": verdict.cost_usd,
            "attempts": verdict.attempts, "mode": verdict.mode, "duration_ms": duration_ms,
        }
        self._rows.append(row)
        with self._log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")

    def summary(self) -> dict:
        total = len(self._rows)
        passed = sum(1 for r in self._rows if r["passed"])
        cost = sum(r["cost_usd"] for r in self._rows)
        tags: dict[str, int] = {}
        for r in self._rows:
            for t in r["failure_tags"]:
                tags[t] = tags.get(t, 0) + 1
        return {"total": total, "passed": passed, "flagged": total - passed,
                "flag_rate": (total - passed) / total if total else 0.0,
                "cost_usd": cost, "failure_tags": tags}


def judge_human_agreement(judge_pass: list[bool], human_pass: list[bool]) -> float:
    if len(judge_pass) != len(human_pass) or not judge_pass:
        raise ValueError("equal-length non-empty lists required")
    return sum(1 for a, b in zip(judge_pass, human_pass) if a == b) / len(judge_pass)
```
- [ ] **Step 4: Run → pass. Step 5: Commit** `git add evaluation/observer.py tests/quality/test_eval_observer.py && git commit -m "feat(eval): Observer jsonl record + summary + agreement"`

---

# PHASE 1 — Render Fidelity Evaluator (imagery)

## Task 7: Pre-fix — Dossier ground-truth photo fields

**Files:** Modify `skyyrose/core/dossier_loader.py`; Test `tests/quality/test_dossier_refs.py`

- [ ] **Step 1: Failing test**
```python
# tests/quality/test_dossier_refs.py
from skyyrose.core.dossier_loader import parse_dossier_markdown

_DOSSIER = """---
sku: br-006
name: Black Rose Bomber Sherpa
collection: black-rose
reference_image: product-references/br-006-real-front.jpg
extra_references:
  - product-references/br-006-real-back.jpg
---
**Garment type lock:** bomber jacket
## Branding
- region: chest
## Negative
- no extra logos
"""


def test_dossier_carries_reference_image_and_extras():
    d = parse_dossier_markdown(_DOSSIER)
    assert d.reference_image == "product-references/br-006-real-front.jpg"
    assert d.extra_references == ["product-references/br-006-real-back.jpg"]
```
- [ ] **Step 2: Run → fail** (`AttributeError: 'Dossier' has no attribute 'reference_image'`)
- [ ] **Step 3: Add fields to `Dossier` + parse them.** In `skyyrose/core/dossier_loader.py`:

In the `Dossier` dataclass (after `logo_reference` line ~51), add:
```python
    reference_image: str = ""
    extra_references: list[str] = field(default_factory=list)
```
In `to_dict()` (after `logo_reference`), add:
```python
            "reference_image": self.reference_image,
            "extra_references": list(self.extra_references),
```
In `parse_dossier_markdown()` return (after `logo_reference=fm.get("logo_reference", "")`), add:
```python
        reference_image=fm.get("reference_image", ""),
        extra_references=fm_lists.get("extra_references", []),
```
- [ ] **Step 4: Run → pass.**
- [ ] **Step 5: Regression** `python -m pytest tests/ -k dossier -v` → existing dossier tests still pass.
- [ ] **Step 6: Commit** `git add skyyrose/core/dossier_loader.py tests/quality/test_dossier_refs.py && git commit -m "fix(dossier): carry reference_image + extra_references (no silent fallback)"`

---

## Task 8: ImageryAdapter

**Files:** Create `evaluation/domains/__init__.py`, `evaluation/domains/imagery.py`; Test `tests/quality/test_imagery_adapter.py`

- [ ] **Step 1: Failing test**
```python
# tests/quality/test_imagery_adapter.py
from pathlib import Path

from evaluation.domains.imagery import ImageryAdapter, IMAGERY_TOOL
from scripts.oai_render.qc import RenderExpectation


def _exp(sku="br-006"):
    return RenderExpectation(sku=sku, name="Black Rose Bomber Sherpa", style="ghost",
                             view="front", is_pair=False, is_patch=False, reference_paths=())


def test_excluded_sku_hard_fails_deterministically():
    ad = ImageryAdapter()
    tags = ad.deterministic_checks(subject=b"\x89PNG...", ref=_exp("sg-006"))
    assert "excluded_sku" in tags


def test_tool_schema_has_visual_analysis_first_and_six_gates():
    props = list(IMAGERY_TOOL["input_schema"]["properties"].keys())
    assert props[0] == "visual_analysis"   # CoT leads
    for gate in ("is_single_photograph", "garment_matches_reference", "view_correct",
                 "branding_legible_and_correct", "photorealistic_not_flat", "all_garments_present"):
        assert gate in props


def test_parse_verdict_maps_gates_to_tags():
    ad = ImageryAdapter()
    judge_output = {"visual_analysis": "...", "is_single_photograph": True,
                    "garment_matches_reference": False, "view_correct": True,
                    "branding_legible_and_correct": True, "photorealistic_not_flat": True,
                    "all_garments_present": True, "reason": "wrong garment"}
    v = ad.parse_verdict(judge_output, det_failures=[])
    assert v.passed is False
    assert "wrong_garment" in v.failure_tags
    assert v.score == 5 / 6   # one of six gates failed
    assert v.domain == "imagery"


def test_load_ground_truth_from_review_state(tmp_path, monkeypatch):
    import json
    state = {"black-rose-crewneck/ghost.png": {"approved": True, "flagged": False, "comment": ""},
             "black-rose-joggers/ghost.png": {"approved": False, "flagged": True, "comment": "logo"}}
    f = tmp_path / "review-state.json"; f.write_text(json.dumps(state))
    ad = ImageryAdapter(review_state_path=f)
    gt = ad.load_ground_truth()
    by = {g["subject_id"]: g["label_pass"] for g in gt}
    assert by["black-rose-crewneck/ghost.png"] is True
    assert by["black-rose-joggers/ghost.png"] is False
```
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Implement** (reuses qc.deterministic_checks, _GATE_TAGS, _b64_data_url, _ref_data_url, _judge_instructions; references.build_references)
```python
# evaluation/domains/__init__.py
"""Evaluation domain adapters."""
```
```python
# evaluation/domains/imagery.py
"""Render Fidelity Evaluator — imagery domain adapter.

Reuses the proven render-QC machinery (scripts/oai_render/qc.py + references.py) and
swaps the OpenAI judge for a Claude VISION judge via forced tool-use with a leading
visual_analysis chain-of-thought field. Subject = PNG bytes; ref = RenderExpectation.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.oai_render import config as render_config
from scripts.oai_render.qc import (
    _GATE_TAGS,
    _b64_data_url,
    _judge_instructions,
    _ref_data_url,
    deterministic_checks,
)
from scripts.oai_render.qc import RenderExpectation

from evaluation.contracts import Verdict
from evaluation.judge import image_block

_GATES = tuple(_GATE_TAGS.keys())  # canonical 6 gates, in qc.py order

# Anthropic tool = OpenAI _JUDGE_SCHEMA's 6 gates, with a LEADING visual_analysis CoT
# field (forces the model to describe hue/material/logo BEFORE committing booleans).
IMAGERY_TOOL: dict = {
    "name": "render_qc_verdict",
    "description": "Report the QC verdict for the candidate render against its references.",
    "input_schema": {
        "type": "object",
        "properties": {
            "visual_analysis": {
                "type": "string",
                "description": "FIRST describe the candidate's garment hue, material, silhouette, "
                "and each logo/graphic panel, comparing to the reference images, BEFORE the gates.",
            },
            "is_single_photograph": {"type": "boolean"},
            "garment_matches_reference": {"type": "boolean"},
            "view_correct": {"type": "boolean"},
            "branding_legible_and_correct": {"type": "boolean"},
            "photorealistic_not_flat": {"type": "boolean"},
            "all_garments_present": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["visual_analysis", *(_GATES), "reason"],
        "additionalProperties": False,
    },
}


class ImageryAdapter:
    domain = "imagery"

    def __init__(self, review_state_path: Path | None = None) -> None:
        self._review_state = review_state_path or (
            render_config.OUTPUT_DIR / "_review" / "review-state.json"
        )

    def deterministic_checks(self, subject: bytes, ref: RenderExpectation) -> list[str]:
        if ref.sku in render_config.EXCLUDED_SKUS:
            return ["excluded_sku"]
        return deterministic_checks(subject)

    def build_judge_request(self, subject: bytes, ref: RenderExpectation) -> dict:
        content: list[dict] = [{"type": "text", "text": _judge_instructions(ref)}]
        content.append(image_block(_b64_data_url(subject).split(",", 1)[1], "image/png"))
        for path in ref.reference_paths[:3]:
            url = _ref_data_url(path)
            if url:
                # data URL: "data:<mime>;base64,<data>"
                head, b64 = url.split(",", 1)
                mime = head[len("data:"):].split(";", 1)[0]
                content.append(image_block(b64, mime))
        return {"messages": [{"role": "user", "content": content}], "tool": IMAGERY_TOOL}

    def parse_verdict(self, judge_output: dict, det_failures: list[str]) -> Verdict:
        tags = tuple(tag for gate, tag in _GATE_TAGS.items() if judge_output.get(gate) is False)
        passed = not tags and not det_failures
        gate_results = {g: bool(judge_output.get(g)) for g in _GATES}
        score = sum(1 for g in _GATES if judge_output.get(g) is True) / len(_GATES)
        return Verdict(
            domain="imagery", passed=passed, score=score, gate_results=gate_results,
            failure_tags=tuple(det_failures) + tags,
            reason=str(judge_output.get("reason", ""))[:300],
            detail={"visual_analysis": judge_output.get("visual_analysis", "")},
        )

    async def revise(self, ref, critique):  # pipeline owns re-render; not used in score() path
        raise NotImplementedError("imagery re-render is owned by scripts/oai_render pipeline")

    def load_ground_truth(self) -> list[dict]:
        if not self._review_state.exists():
            return []
        state = json.loads(self._review_state.read_text(encoding="utf-8"))
        out = []
        for subject_id, entry in state.items():
            # approved & not flagged → pass; flagged → fail
            label_pass = bool(entry.get("approved")) and not bool(entry.get("flagged"))
            out.append({"subject_id": subject_id, "label_pass": label_pass,
                        "comment": entry.get("comment", "")})
        return out
```
- [ ] **Step 4: Run → pass.**
- [ ] **Step 5: Commit** `git add evaluation/domains tests/quality/test_imagery_adapter.py && git commit -m "feat(eval): ImageryAdapter — Claude vision judge, reuses qc.py + references"`

---

## Task 9: RenderFidelityEvaluator agent (job-title binding)

**Files:** Create `evaluation/agents.py`; Test `tests/quality/test_render_fidelity_agent.py`

- [ ] **Step 1: Failing test**
```python
# tests/quality/test_render_fidelity_agent.py
from evaluation.agents import RenderFidelityEvaluator
from scripts.oai_render.qc import RenderExpectation


def _exp(): return RenderExpectation(sku="br-001", name="X", style="ghost", view="front",
                                     is_pair=False, is_patch=False, reference_paths=())


async def test_agent_scores_via_core_and_judge():
    captured = {}
    def fake_judge(req):
        captured["req"] = req
        return ({"visual_analysis": "ok", "is_single_photograph": True,
                 "garment_matches_reference": True, "view_correct": True,
                 "branding_legible_and_correct": True, "photorealistic_not_flat": True,
                 "all_garments_present": True, "reason": "pass"}, 0.03)
    agent = RenderFidelityEvaluator(judge_fn=fake_judge)
    assert agent.job_title == "Render Fidelity Evaluator"
    v = await agent.evaluate(subject=b"\x89PNG", ref=_exp())
    assert v.passed is True and v.domain == "imagery" and v.cost_usd == 0.03
    assert "tool" in captured["req"]
```
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Implement**
```python
# evaluation/agents.py
"""The two job-title evaluator agents. Thin: identity + adapter + core."""
from __future__ import annotations

from typing import Any

from evaluation.core import EvaluationCore, JudgeFn
from evaluation.domains.imagery import ImageryAdapter


class RenderFidelityEvaluator:
    """Imagery domain: does a generated product photo 100%-replicate the real garment?"""

    job_title = "Render Fidelity Evaluator"

    def __init__(self, judge_fn: JudgeFn, adapter: ImageryAdapter | None = None) -> None:
        self._core = EvaluationCore(judge_fn=judge_fn)
        self._adapter = adapter or ImageryAdapter()

    async def evaluate(self, subject: bytes, ref: Any):
        return await self._core.score(self._adapter, subject, ref)

    def adapter(self) -> ImageryAdapter:
        return self._adapter
```
- [ ] **Step 4: Run → pass. Step 5: Commit** `git add evaluation/agents.py tests/quality/test_render_fidelity_agent.py && git commit -m "feat(eval): RenderFidelityEvaluator job-title agent"`

---

## Task 10: Wire the Claude judge into the render pipeline (provider switch)

**Files:** Modify `scripts/oai_render/config.py`, `scripts/oai_render/qc.py`; Test `tests/quality/test_qc_provider_switch.py`

- [ ] **Step 1: Add config** to `scripts/oai_render/config.py` (after `EST_JUDGE_COST_USD`, line ~60):
```python
QC_JUDGE_PROVIDER = "openai"  # "openai" (gpt-4o-mini) | "anthropic" (Claude vision)
QC_JUDGE_ANTHROPIC_MODEL = "claude-sonnet-4-6"
QC_JUDGE_ANTHROPIC_MAX_TOKENS = 1500  # room for the visual_analysis CoT field
```
- [ ] **Step 2: Failing test**
```python
# tests/quality/test_qc_provider_switch.py
from scripts.oai_render import config
from scripts.oai_render.qc import QCGate, RenderExpectation


def _exp(): return RenderExpectation(sku="br-001", name="X", style="ghost", view="front",
                                     is_pair=False, is_patch=False, reference_paths=())


def test_anthropic_provider_uses_claude_judge(monkeypatch):
    monkeypatch.setattr(config, "QC_JUDGE_PROVIDER", "anthropic")
    calls = {}
    def fake_judge(req):
        calls["req"] = req
        return ({"visual_analysis": "v", "is_single_photograph": True,
                 "garment_matches_reference": True, "view_correct": True,
                 "branding_legible_and_correct": True, "photorealistic_not_flat": True,
                 "all_garments_present": True, "reason": "pass"}, 0.02)
    # inject the judge_fn so no network + no client construction
    gate = QCGate(use_judge=True, judge_fn=fake_judge)
    # deterministic_checks needs a real PNG; monkeypatch to clean
    monkeypatch.setattr("scripts.oai_render.qc.deterministic_checks", lambda data: [])
    verdict = gate.check(b"\x89PNG", _exp())
    assert verdict.passed is True
    assert verdict.judge_cost_usd == 0.02
    assert "req" in calls
```
- [ ] **Step 3: Run → fail** (`QCGate` has no `judge_fn` param / no anthropic branch).
- [ ] **Step 4: Modify `QCGate`** in `scripts/oai_render/qc.py`. Update `__init__` and `_judge`:

Replace `QCGate.__init__` (line 246) with:
```python
    def __init__(self, *, use_judge: bool = True, judge_fn=None) -> None:
        self._use_judge = use_judge and config.QC_ENABLED
        self._provider = config.QC_JUDGE_PROVIDER
        self._judge_fn = judge_fn          # injectable for tests; built lazily otherwise
        self._client = None
        if self._use_judge and judge_fn is None and self._provider == "openai":
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=config.get_api_key(), timeout=config.REQUEST_TIMEOUT_S
                )
            except Exception as exc:
                raise RuntimeError(f"QC judge client failed to initialize: {exc}") from exc
```
Add an anthropic branch in `_judge` (line 273). After the existing `content` build but before the OpenAI call, branch on provider:
```python
    def _judge(self, data: bytes, exp: RenderExpectation) -> QCVerdict:
        if self._provider == "anthropic" or self._judge_fn is not None:
            return self._judge_anthropic(data, exp)
        # ... existing OpenAI content build + call unchanged ...
```
Add the new method:
```python
    def _judge_anthropic(self, data: bytes, exp: RenderExpectation) -> QCVerdict:
        from evaluation.domains.imagery import ImageryAdapter
        from evaluation.judge import ClaudeJudge, make_client

        adapter = ImageryAdapter()
        request = adapter.build_judge_request(data, exp)
        judge_fn = self._judge_fn
        if judge_fn is None:
            judge = ClaudeJudge(client=make_client(),
                                model=config.QC_JUDGE_ANTHROPIC_MODEL,
                                max_tokens=config.QC_JUDGE_ANTHROPIC_MAX_TOKENS)
            def judge_fn(req):  # noqa: E306
                return judge.run(messages=req["messages"], tool=req["tool"])
        try:
            output, cost = judge_fn(request)
        except Exception as exc:
            log.error("Claude QC judge failed for %s: %s — accepting unjudged", exp.sku, exc)
            return QCVerdict(passed=True, failure_tags=("judge_unavailable",),
                             reason=f"judge error: {exc}")
        verdict = adapter.parse_verdict(output, det_failures=[])
        return QCVerdict(passed=verdict.passed, failure_tags=verdict.failure_tags,
                         reason=verdict.reason, judge_cost_usd=cost)
```
> Note the soft-fail-open is retained for parity, but `QC_JUDGE_PROVIDER=anthropic` runs only after calibration; hard-gate enforcement (block on `judge_unavailable`) is a config follow-up once κ ≥ 0.65.
- [ ] **Step 5: Run → pass.**
- [ ] **Step 6: Regression** `python -m pytest tests/pipelines/test_oai_render_hardening.py -v` → existing QC tests still pass (OpenAI path untouched by default).
- [ ] **Step 7: Commit** `git add scripts/oai_render/config.py scripts/oai_render/qc.py tests/quality/test_qc_provider_switch.py && git commit -m "feat(qc): config-selectable Claude vision judge at the QCGate seam"`

---

## Task 11: Calibration harness + ground-truth seed

**Files:** Create `scripts/oai-render-qc-eval.py`, `tests/fixtures/qc_ground_truth/README.md`; Test `tests/quality/test_qc_eval_harness.py`

- [ ] **Step 1: Failing test** (harness logic is pure; judge faked, images faked)
```python
# tests/quality/test_qc_eval_harness.py
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "qc_eval", Path("scripts/oai-render-qc-eval.py"))
qc_eval = importlib.util.module_from_spec(spec); spec.loader.exec_module(qc_eval)


def test_compute_kappa_from_pairs():
    # judge verdicts vs human labels (pass=1/fail=0)
    judge = [1, 0, 1, 1, 0]
    human = [1, 0, 1, 0, 0]
    k = qc_eval.kappa_from_pairs(judge, human)
    assert -1.0 <= k <= 1.0
    assert qc_eval.mode_for(k) in ("hard_gate", "soft_signal")
```
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Implement the harness**
```python
#!/usr/bin/env python3
# scripts/oai-render-qc-eval.py
"""Calibrate the imagery judge against founder labels.

Loads labeled examples (review-state.json via ImageryAdapter.load_ground_truth, or a
fixtures labels.json), runs the Claude vision judge on each example image, compares the
judge pass/fail to the human label, and reports Cohen's kappa + the recommended mode.

Usage:
  python scripts/oai-render-qc-eval.py --images-dir renders/oai --report renders/oai/_qc-eval.json
PAID: makes one Claude vision judge call per labeled image with a resolvable render PNG.
Prints a cost estimate and requires --yes before any paid call (STOP-AND-SHOW).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.calibration import cohen_kappa, decide_mode  # noqa: E402


def kappa_from_pairs(judge: list[int], human: list[int]) -> float:
    return cohen_kappa(judge, human)


def mode_for(kappa: float) -> str:
    return decide_mode(kappa)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images-dir", default="renders/oai")
    ap.add_argument("--report", default="renders/oai/_qc-eval.json")
    ap.add_argument("--yes", action="store_true", help="confirm paid Claude judge calls")
    args = ap.parse_args(argv)

    from evaluation.domains.imagery import ImageryAdapter
    from evaluation.judge import ClaudeJudge, anthropic_cost_usd, make_client
    from scripts.oai_render import config, references
    from scripts.oai_render.qc import RenderExpectation, deterministic_checks

    adapter = ImageryAdapter()
    images_dir = Path(args.images_dir)
    labeled = adapter.load_ground_truth()
    # keep only examples whose render PNG still exists on disk
    resolvable = [g for g in labeled if (images_dir / g["subject_id"]).exists()]
    print(f"labeled={len(labeled)} resolvable_on_disk={len(resolvable)}")
    if not resolvable:
        print("No labeled images on disk — re-render a calibration subset first.")
        return 2

    est = len(resolvable) * 0.01  # ~$0.01/vision judge call (sonnet, low-detail refs)
    print(f"STOP-AND-SHOW: {len(resolvable)} paid Claude judge calls, est ${est:.2f}")
    if not args.yes:
        print("Re-run with --yes to proceed."); return 2

    judge = ClaudeJudge(client=make_client(), model=config.QC_JUDGE_ANTHROPIC_MODEL,
                        max_tokens=config.QC_JUDGE_ANTHROPIC_MAX_TOKENS)
    judge_pass: list[int] = []
    human_pass: list[int] = []
    rows = []
    for g in resolvable:
        subject = (images_dir / g["subject_id"]).read_bytes()
        slug = g["subject_id"].split("/")[0]
        # minimal expectation; sku resolved from slug via catalog is a follow-up refinement
        exp = RenderExpectation(sku=slug, name=slug, style="ghost", view="front",
                                is_pair=False, is_patch=False, reference_paths=())
        det = deterministic_checks(subject)
        if det:
            verdict_pass = False; cost = 0.0
        else:
            req = adapter.build_judge_request(subject, exp)
            output, cost = judge.run(messages=req["messages"], tool=req["tool"])
            verdict_pass = adapter.parse_verdict(output, det_failures=[]).passed
        judge_pass.append(int(verdict_pass)); human_pass.append(int(g["label_pass"]))
        rows.append({"subject_id": g["subject_id"], "judge_pass": verdict_pass,
                     "human_pass": g["label_pass"], "cost_usd": cost})

    k = cohen_kappa(judge_pass, human_pass)
    report = {"n": len(rows), "kappa": k, "recommended_mode": decide_mode(k),
              "total_cost_usd": sum(r["cost_usd"] for r in rows), "rows": rows}
    Path(args.report).write_text(json.dumps(report, indent=2))
    print(f"kappa={k:.3f} mode={decide_mode(k)} report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
- [ ] **Step 4: Run the unit test → pass.**
- [ ] **Step 5: Document the ground-truth fixture**
```markdown
<!-- tests/fixtures/qc_ground_truth/README.md -->
# Imagery QC ground truth
The labeled set is `renders/oai/_review/review-state.json` (81 founder labels:
approved & not flagged → pass; flagged → fail). Most original render PNGs were deleted
2026-06-09, so calibration runs only on labels whose image still exists on disk. Re-render
a small subset, label it on the :8944 board, then run:
  python scripts/oai-render-qc-eval.py --yes
Output: kappa + recommended mode → set QC_JUDGE_PROVIDER=anthropic and the hard/soft mode.
```
- [ ] **Step 6: Commit** `git add scripts/oai-render-qc-eval.py tests/fixtures/qc_ground_truth/README.md tests/quality/test_qc_eval_harness.py && git commit -m "feat(qc): Claude-judge calibration harness (kappa vs founder labels)"`

---

## Task 12: End-to-end + docs

**Files:** Create `tests/quality/test_render_fidelity_e2e.py`; Modify `.wolf/anatomy.md`, `docs/model-routing.md`

- [ ] **Step 1: E2E test (full chain, fake judge, real adapter + core + qc reuse)**
```python
# tests/quality/test_render_fidelity_e2e.py
from evaluation.agents import RenderFidelityEvaluator
from scripts.oai_render.qc import RenderExpectation


def _exp(sku): return RenderExpectation(sku=sku, name="X", style="ghost", view="front",
                                        is_pair=False, is_patch=False, reference_paths=())


async def test_excluded_sku_blocks_before_judge():
    called = {"judge": False}
    def judge(req): called["judge"] = True; return ({}, 0.0)
    agent = RenderFidelityEvaluator(judge_fn=judge)
    v = await agent.evaluate(subject=b"\x89PNG", ref=_exp("sg-006"))  # excluded
    assert v.passed is False and "excluded_sku" in v.failure_tags
    assert called["judge"] is False  # deterministic gate blocked the paid judge


async def test_clean_render_passes_through_vision_judge(monkeypatch):
    monkeypatch.setattr("evaluation.domains.imagery.deterministic_checks", lambda d: [])
    def judge(req):
        return ({"visual_analysis": "navy bomber white script matches reference",
                 "is_single_photograph": True, "garment_matches_reference": True,
                 "view_correct": True, "branding_legible_and_correct": True,
                 "photorealistic_not_flat": True, "all_garments_present": True,
                 "reason": "pass"}, 0.012)
    agent = RenderFidelityEvaluator(judge_fn=judge)
    v = await agent.evaluate(subject=b"\x89PNG", ref=_exp("br-001"))
    assert v.passed is True and v.score == 1.0 and v.cost_usd == 0.012
    assert v.detail["visual_analysis"].startswith("navy")
```
- [ ] **Step 2: Run → pass.**
- [ ] **Step 3: Full suite + lint** `python -m pytest tests/quality/ -v && ruff check evaluation scripts/oai-render-qc-eval.py && black --check evaluation`
- [ ] **Step 4: Docs** — add `evaluation/*` to `.wolf/anatomy.md`; note in `docs/model-routing.md` the imagery judge uses `claude-sonnet-4-6` (vision) and the `QC_JUDGE_PROVIDER` switch.
- [ ] **Step 5: Commit** `git add tests/quality/test_render_fidelity_e2e.py .wolf/anatomy.md docs/model-routing.md && git commit -m "test(eval): render-fidelity e2e + docs"`

---

## After the build: the photos path (paid — STOP-AND-SHOW)

1. Founder sets `ANTHROPIC_API_KEY` (lands in `config.settings`).
2. Re-render a small calibration subset (≈6–10 SKUs spanning collections + br-005 hue / br-006 sherpa) via the existing CLI — **paid, STOP-AND-SHOW manifest first**.
3. Founder labels them on the :8944 board.
4. `python scripts/oai-render-qc-eval.py --yes` → κ + recommended mode.
5. Set `QC_JUDGE_PROVIDER=anthropic`; if κ ≥ 0.65 enable hard-gate.
6. Full re-render (existing CLI, gated by the new judge) — **paid, STOP-AND-SHOW** — → photos for the senior dev.

## Self-review notes
- **Spec coverage:** shared core (Tasks 1–6), DomainAdapter port (2), Claude vision judge w/ visual_analysis CoT + forced tool-use (4, 8), reuse of qc.py/references (8, 10), pre-fix dossier silent-fallback (7), calibration from 81 labels (11), Observer (6), pipeline wiring via provider switch (10). Content domain = separate later plan (`2026-06-16-evaluator-agent.md` re-homed).
- **No silent fallback:** dossier fix (7); excluded-SKU hard-fail before judge (8); judge soft-fail-open retained but hard-gate noted as κ-gated follow-up.
- **Paid actions:** every paid step (calibration render, judge eval, full re-render) is STOP-AND-SHOW gated; cost is real Claude pricing (Task 4 `anthropic_cost_usd`), not the old $0.0002 constant.
- **Type consistency:** `Verdict`, `RenderExpectation`, `ImageryAdapter`, `ClaudeJudge.run()->(dict,float)`, `EvaluationCore.score/gate`, `_GATE_TAGS` reuse — consistent across tasks.
- **Open refinement (named):** the eval harness resolves SKU from slug minimally; richer SKU→RenderExpectation (with `build_references` reference images fed to the judge) is a Task-11 follow-up once calibration images exist.
