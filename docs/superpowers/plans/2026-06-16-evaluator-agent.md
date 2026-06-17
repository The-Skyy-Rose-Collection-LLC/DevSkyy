# Evaluator / Critic Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gate agent-produced content/copy before a human reviewer sees it: a free deterministic catalog-fact gate, then a single Claude judge (0–5, criterion-separated, chain-of-thought), then a bounded external-feedback revise loop (cap 2 + early-exit), calibration-gated between hard-gate and soft-signal modes.

**Architecture:** Plugs into the same `agents/quality/hooks.py::after_execute` built in Plan 1. When the executing agent's `core_type == CoreAgentType.CONTENT`, the hook calls `Evaluator.gate(...)`. The revise loop re-invokes the originating agent's `execute()` **directly** (NOT `execute_safe`) to avoid recursively re-triggering the hook. Scoring/critique logic is pure and unit-tested with a fake LLM client; the deterministic gate reuses `skyyrose/core/catalog_loader.py`.

**Tech Stack:** Python 3.11+, pytest. Reuses `skyyrose/core/catalog_loader.py` (`get_product_with_dossier`, `read_catalog_rows`), `llm/providers/anthropic.py` (`AnthropicClient.complete`), `llm/base.py` (`Message`, `CompletionResponse`).

**Depends on:** Plan 1 (`docs/superpowers/plans/2026-06-16-observability-agent.md`) — needs `agents/quality/contracts.py`, `agents/quality/hooks.py`, and `CoreAgentType.CONTENT`.

**Companion spec:** `docs/superpowers/specs/2026-06-16-evaluator-observability-agents-design.html`

---

## Deviations from spec (grounded in code reads)

| Spec said | Plan does | Why |
|---|---|---|
| Route critique back via `delegate()` | Re-invoke originating agent's `execute()` directly with critique-augmented task, bypassing `execute_safe` | `delegate()` only dispatches *forward* to sub-agents (`base.py:558`); calling `execute_safe` would recursively re-trigger the evaluator hook (infinite loop) |
| Judge wired to a specific Claude client | Judge depends on an injected `llm_client` Protocol (`complete(messages, model)`) | Keeps scoring unit-testable with a fake; production injects `AnthropicClient` |

---

## File structure

| File | Responsibility |
|---|---|
| `agents/quality/contracts.py` | Modify: add `EvalVerdict` |
| `agents/quality/eval_config.py` | `EvaluatorConfig` (weights, threshold, cap, mode, judge model) |
| `agents/quality/deterministic_gate.py` | Catalog-fact + placeholder + banned-phrase + structure checks |
| `agents/quality/judge.py` | `LLMJudge` — criterion-separated CoT prompts, parse, composite |
| `agents/quality/revise_loop.py` | Critique builder + bounded re-invocation |
| `agents/quality/evaluator.py` | `Evaluator.gate(...)` orchestration; hard-gate vs soft-signal |
| `agents/quality/hooks.py` | Modify: call `Evaluator.gate` for CONTENT agents |
| `agents/quality/calibration.py` | κ harness; decides mode |
| `tests/quality/*` | Tests |

---

## Task 1: EvalVerdict contract

**Files:**
- Modify: `agents/quality/contracts.py`
- Test: `tests/quality/test_eval_verdict.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/quality/test_eval_verdict.py
from agents.quality.contracts import EvalVerdict


def test_verdict_normalized_and_passed():
    v = EvalVerdict(passed=True, composite=4.0, dimension_scores={"brand_voice": 4, "clarity": 4},
                    deterministic_failures=[], critique={}, attempts=1, mode="hard_gate")
    assert v.normalized == 0.75            # (4-1)/4
    assert v.passed is True


def test_verdict_is_frozen():
    import dataclasses
    v = EvalVerdict(passed=False, composite=1.0, dimension_scores={}, deterministic_failures=["x"],
                    critique={}, attempts=2, mode="soft_signal")
    try:
        v.passed = True
        assert False
    except dataclasses.FrozenInstanceError:
        pass
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_eval_verdict.py -v`
Expected: FAIL with `ImportError: cannot import name 'EvalVerdict'`

- [ ] **Step 3: Add `EvalVerdict` to `agents/quality/contracts.py`**

Append:

```python
from typing import Literal


@dataclass(frozen=True)
class EvalVerdict:
    passed: bool
    composite: float                 # weighted mean of dimension scores (1–5 scale)
    dimension_scores: dict           # {"brand_voice": int, "clarity": int, ...}
    deterministic_failures: list     # list[str] of hard-fail check names
    critique: dict                   # routed-critique payload (see revise_loop)
    attempts: int
    mode: Literal["hard_gate", "soft_signal"]

    @property
    def normalized(self) -> float:
        """0–1 form for downstream systems: (composite - 1) / 4."""
        return (self.composite - 1) / 4
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_eval_verdict.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/quality/contracts.py tests/quality/test_eval_verdict.py
git commit -m "feat(quality): EvalVerdict contract"
```

---

## Task 2: EvaluatorConfig

**Files:**
- Create: `agents/quality/eval_config.py`
- Test: `tests/quality/test_eval_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/quality/test_eval_config.py
from agents.quality.eval_config import EvaluatorConfig


def test_defaults():
    c = EvaluatorConfig()
    assert c.enabled is False
    assert c.mode == "soft_signal"               # safe default until calibrated
    assert c.pass_threshold == 3.0
    assert c.revise_cap == 2
    assert c.judge_model_default == "claude-sonnet-4-6"
    assert set(c.weights) == {"brand_voice", "clarity", "persuasiveness", "distinctiveness"}
    assert abs(sum(c.weights.values()) - 1.0) < 1e-9
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_eval_config.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement**

```python
# agents/quality/eval_config.py
"""Evaluator configuration. Ships dormant + soft-signal until calibration (Task 8) clears κ≥0.65."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


def _default_weights() -> dict[str, float]:
    return {"brand_voice": 0.40, "clarity": 0.25, "persuasiveness": 0.25, "distinctiveness": 0.10}


@dataclass(frozen=True)
class EvaluatorConfig:
    enabled: bool = False
    mode: Literal["hard_gate", "soft_signal"] = "soft_signal"
    pass_threshold: float = 3.0            # composite < threshold → revise (hard_gate)
    revise_cap: int = 2
    judge_model_default: str = "claude-sonnet-4-6"
    judge_model_hero: str = "claude-opus-4-8"
    weights: dict[str, float] = field(default_factory=_default_weights)
    hero_agents: frozenset[str] = frozenset()   # agents whose copy uses the Opus judge
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_eval_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agents/quality/eval_config.py tests/quality/test_eval_config.py
git commit -m "feat(quality): EvaluatorConfig (dormant + soft-signal default)"
```

---

## Task 3: Deterministic gate — catalog fact-check (reuse catalog_loader)

**Files:**
- Create: `agents/quality/deterministic_gate.py`
- Test: `tests/quality/test_gate_facts.py`

- [ ] **Step 1: Confirm the reused loader**

Read `skyyrose/core/catalog_loader.py`: `read_catalog_rows()` returns `list[dict]` with columns incl. `sku`, `name`, `price`, `collection`. `get_product_with_dossier(sku)` merges row + dossier (hard-fails on missing dossier). Use `read_catalog_rows()` for the gate (no dossier needed for fact-checks).

- [ ] **Step 2: Write the failing test**

```python
# tests/quality/test_gate_facts.py
from agents.quality.deterministic_gate import check_catalog_facts


_ROWS = [
    {"sku": "br-006", "name": "Black Rose Bomber Sherpa", "price": "265", "collection": "black-rose"},
    {"sku": "lh-001", "name": "Love Hurts Tee", "price": "65", "collection": "love-hurts"},
]


def test_wrong_price_for_named_product_fails():
    text = "The Black Rose Bomber Sherpa is available now for $245."
    failures = check_catalog_facts(text, skus=["br-006"], rows=_ROWS)
    assert any(f.check == "price" for f in failures)


def test_correct_price_passes():
    text = "The Black Rose Bomber Sherpa is yours for $265."
    assert check_catalog_facts(text, skus=["br-006"], rows=_ROWS) == []


def test_no_sku_context_skips_factcheck():
    assert check_catalog_facts("generic copy with $999", skus=[], rows=_ROWS) == []
```

- [ ] **Step 3: Run to verify it fails**

Run: `python -m pytest tests/quality/test_gate_facts.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: Implement the fact-check**

```python
# agents/quality/deterministic_gate.py
"""Deterministic pre-LLM gate. All checks are pure code — un-hallucinatable.

Reuses skyyrose/core/catalog_loader for canonical product facts (catalog CSV).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GateFailure:
    check: str          # "price" | "placeholder" | "banned_phrase" | "structure" | "collection"
    detail: str
    fragment: str = ""


_PRICE_RE = re.compile(r"\$\s?(\d{2,4})(?:\.\d{2})?")


def _rows_by_sku(rows: list[dict]) -> dict[str, dict]:
    return {r["sku"]: r for r in rows}


def check_catalog_facts(text: str, skus: list[str], rows: list[dict]) -> list[GateFailure]:
    """For each SKU the draft is about, verify any mentioned price matches the catalog.

    skus: the products this copy is about (supplied by the content agent's context).
    When empty, fact-checking is skipped (global checks still run elsewhere).
    """
    if not skus:
        return []
    by_sku = _rows_by_sku(rows)
    mentioned_prices = {m.group(1) for m in _PRICE_RE.finditer(text)}
    if not mentioned_prices:
        return []
    valid_prices = set()
    failures: list[GateFailure] = []
    for sku in skus:
        row = by_sku.get(sku)
        if row:
            valid_prices.add(str(row["price"]).strip())
    # any mentioned price that matches NO targeted SKU's catalog price is a fact error
    for p in mentioned_prices:
        if p not in valid_prices:
            failures.append(GateFailure(
                check="price",
                detail=f"price ${p} does not match catalog price(s) {sorted(valid_prices)} "
                       f"for {skus}",
                fragment=f"${p}"))
    return failures
```

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest tests/quality/test_gate_facts.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add agents/quality/deterministic_gate.py tests/quality/test_gate_facts.py
git commit -m "feat(quality): deterministic catalog-fact check (reuses catalog_loader)"
```

---

## Task 4: Deterministic gate — placeholder, banned-phrase, structure, top-level runner

**Files:**
- Modify: `agents/quality/deterministic_gate.py`
- Test: `tests/quality/test_gate_rules.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/quality/test_gate_rules.py
from agents.quality.deterministic_gate import (
    check_placeholders, check_banned_phrases, check_structure, run_gate,
)

_ROWS = [{"sku": "br-006", "name": "Black Rose Bomber Sherpa", "price": "265",
          "collection": "black-rose"}]


def test_placeholder_detected():
    assert check_placeholders("great jacket TODO add cta")[0].check == "placeholder"
    assert check_placeholders("lorem ipsum dolor")[0].check == "placeholder"
    assert check_placeholders("clean copy") == []


def test_banned_cross_collection_phrase():
    # "bloodline that raised me" is Love Hurts canon only
    fails = check_banned_phrases("the bloodline that raised me", collection="black-rose")
    assert fails and fails[0].check == "banned_phrase"
    assert check_banned_phrases("the bloodline that raised me", collection="love-hurts") == []


def test_structure_min_length():
    assert check_structure("hi", content_type="pdp")[0].check == "structure"
    assert check_structure("x" * 200, content_type="pdp") == []


def test_run_gate_aggregates():
    fails = run_gate(text="TODO $245", skus=["br-006"], rows=_ROWS,
                     collection="black-rose", content_type="pdp")
    kinds = {f.check for f in fails}
    assert {"placeholder", "price", "structure"} <= kinds
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_gate_rules.py -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Append the checks + runner**

```python
# append to agents/quality/deterministic_gate.py

_PLACEHOLDER_RE = re.compile(r"\b(TODO|FIXME|lorem ipsum|lorem|XXX|TBD)\b|\{\{", re.IGNORECASE)

# Collection-specific canon phrases that must NOT appear outside their collection.
# Source of truth to expand: docs/brand/collection-stories.md
_BANNED_CROSS_COLLECTION: dict[str, str] = {
    "bloodline that raised me": "love-hurts",
}

_MIN_LENGTH = {"pdp": 120, "collection": 200, "seo": 50, "default": 80}


def check_placeholders(text: str) -> list[GateFailure]:
    m = _PLACEHOLDER_RE.search(text)
    if m:
        return [GateFailure(check="placeholder", detail=f"placeholder marker '{m.group(0)}'",
                            fragment=m.group(0))]
    return []


def check_banned_phrases(text: str, collection: str | None) -> list[GateFailure]:
    low = text.lower()
    out = []
    for phrase, owner in _BANNED_CROSS_COLLECTION.items():
        if phrase in low and (collection or "").lower() != owner:
            out.append(GateFailure(
                check="banned_phrase",
                detail=f"'{phrase}' is {owner} canon; this copy is '{collection}'",
                fragment=phrase))
    return out


def check_structure(text: str, content_type: str) -> list[GateFailure]:
    floor = _MIN_LENGTH.get(content_type, _MIN_LENGTH["default"])
    if len(text.strip()) < floor:
        return [GateFailure(check="structure",
                            detail=f"{content_type} copy below {floor}-char floor "
                                   f"({len(text.strip())} chars)")]
    return []


def run_gate(*, text: str, skus: list[str], rows: list[dict],
             collection: str | None, content_type: str) -> list[GateFailure]:
    """Run all deterministic checks; return the full failure list (empty = clean)."""
    return (check_placeholders(text)
            + check_banned_phrases(text, collection)
            + check_structure(text, content_type)
            + check_catalog_facts(text, skus, rows))
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_gate_rules.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/quality/deterministic_gate.py tests/quality/test_gate_rules.py
git commit -m "feat(quality): placeholder/banned-phrase/structure gate + run_gate"
```

---

## Task 5: LLM judge — criterion-separated, CoT, 0–5, composite

**Files:**
- Create: `agents/quality/judge.py`
- Test: `tests/quality/test_judge.py`

- [ ] **Step 1: Write the failing test (fake LLM client)**

```python
# tests/quality/test_judge.py
import json

from agents.quality.eval_config import EvaluatorConfig
from agents.quality.judge import LLMJudge


class _FakeResp:
    def __init__(self, content):
        self.content = content
        self.input_tokens = 10; self.output_tokens = 5; self.finish_reason = "stop"


class _FakeClient:
    """Returns a fixed per-dimension JSON score. Records prompts for assertions."""
    def __init__(self, score):
        self.score = score; self.prompts = []
    async def complete(self, messages, model):
        self.prompts.append(messages)
        return _FakeResp(json.dumps({"reasoning": "because", "score": self.score}))


async def test_judge_composite_weighted_mean():
    client = _FakeClient(score=4)
    judge = LLMJudge(client=client, cfg=EvaluatorConfig())
    scores, composite, usage = await judge.score(text="some luxury copy", model="claude-sonnet-4-6")
    assert set(scores) == {"brand_voice", "clarity", "persuasiveness", "distinctiveness"}
    assert composite == 4.0                       # all dims == 4
    assert usage["input_tokens"] > 0


async def test_judge_prompt_is_blind_and_anti_verbosity():
    client = _FakeClient(score=3)
    judge = LLMJudge(client=client, cfg=EvaluatorConfig())
    await judge.score(text="copy", model="claude-sonnet-4-6")
    joined = " ".join(m.content for m in client.prompts[0])
    assert "Length is not a quality signal" in joined        # anti-verbosity clause
    assert "AI-written" not in joined and "generated by" not in joined  # blind authorship


async def test_judge_handles_unparseable_score():
    class _Bad(_FakeClient):
        async def complete(self, messages, model):
            return _FakeResp("no json here")
    judge = LLMJudge(client=_Bad(0), cfg=EvaluatorConfig())
    scores, composite, _ = await judge.score(text="copy", model="claude-sonnet-4-6")
    assert composite == 1.0                       # unparseable → worst score (fail closed)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_judge.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the judge**

```python
# agents/quality/judge.py
"""Single-model judge. Criterion-separated, chain-of-thought-before-score, 0–5 integers.

Depends on an injected `llm_client` with `async complete(messages, model)` returning an
object exposing `.content`, `.input_tokens`, `.output_tokens` (matches
llm/providers/anthropic.py AnthropicClient + llm/base.py CompletionResponse).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Protocol

from llm.base import Message

from agents.quality.eval_config import EvaluatorConfig

logger = logging.getLogger(__name__)

_DIMENSION_GUIDANCE = {
    "brand_voice": "Does the copy match SkyyRose voice — Oakland-anchored, concrete, "
                   "luxury-streetwear, garment-as-protagonist? Ground judgment in specific "
                   "phrases, not vibes.",
    "clarity": "Is it immediately clear and well-structured?",
    "persuasiveness": "Does it compel without hype or urgency-timers?",
    "distinctiveness": "Is it distinctive to THIS product, not generic-luxury filler?",
}

_RUBRIC = ("Score 1-5 (integer): 1=hard fail, 2=weak, 3=acceptable, 4=good, 5=excellent. "
           "Length is not a quality signal; credit density over word count. "
           "First give 2-3 sentences of reasoning, then output strict JSON "
           '{"reasoning": "...", "score": N}.')


class _LLMClient(Protocol):
    async def complete(self, messages: list[Message], model: str) -> Any: ...


class LLMJudge:
    def __init__(self, client: _LLMClient, cfg: EvaluatorConfig) -> None:
        self._client = client
        self._cfg = cfg

    def _prompt(self, text: str, dimension: str) -> list[Message]:
        # Blind: never mention the draft is AI-written or name the generator.
        system = Message.system(
            "You are a senior brand copy editor. Evaluate ONE dimension only. " + _RUBRIC)
        user = Message.user(
            f"DIMENSION: {dimension}\nGUIDANCE: {_DIMENSION_GUIDANCE[dimension]}\n\n"
            f"COPY TO EVALUATE:\n{text}")
        return [system, user]

    @staticmethod
    def _parse(content: str) -> int:
        try:
            start = content.index("{"); end = content.rindex("}") + 1
            score = int(json.loads(content[start:end]).get("score", 1))
            return min(5, max(1, score))
        except Exception:
            logger.warning("judge score unparseable; failing closed at 1")
            return 1                       # fail closed — unparseable counts as worst

    async def score(self, text: str, model: str) -> tuple[dict[str, int], float, dict]:
        scores: dict[str, int] = {}
        in_tok = out_tok = 0
        for dim in self._cfg.weights:
            resp = await self._client.complete(self._prompt(text, dim), model=model)
            scores[dim] = self._parse(resp.content)
            in_tok += getattr(resp, "input_tokens", 0) or 0
            out_tok += getattr(resp, "output_tokens", 0) or 0
        composite = sum(scores[d] * w for d, w in self._cfg.weights.items())
        usage = {"provider": "anthropic", "model": model,
                 "input_tokens": in_tok, "output_tokens": out_tok, "finish_reason": "stop"}
        return scores, round(composite, 3), usage
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_judge.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/quality/judge.py tests/quality/test_judge.py
git commit -m "feat(quality): LLMJudge — criterion-separated CoT 0-5 scoring, blind, fail-closed"
```

---

## Task 6: Revise loop — critique builder + bounded re-invocation

**Files:**
- Create: `agents/quality/revise_loop.py`
- Test: `tests/quality/test_revise_loop.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/quality/test_revise_loop.py
from agents.quality.deterministic_gate import GateFailure
from agents.quality.revise_loop import build_critique, augmented_task


def test_build_critique_separates_facts_from_style():
    failures = [GateFailure(check="price", detail="price $245 != $265", fragment="$245")]
    style = [{"dimension": "brand_voice", "score": 2, "issue": "generic", "fragment": "elevated"}]
    crit = build_critique(failures, style, dossier_excerpt="Black Rose: armor.")
    assert crit["fact_corrections"][0]["fragment"] == "$245"
    assert crit["style_notes"][0]["dimension"] == "brand_voice"
    assert "Black Rose" in crit["dossier_context"]
    assert "praise" not in str(crit).lower()


def test_augmented_task_embeds_critique_and_original():
    crit = {"fact_corrections": [{"detail": "fix price"}], "style_notes": [], "dossier_context": ""}
    out = augmented_task("Write the PDP for br-006", crit)
    assert "Write the PDP for br-006" in out
    assert "REVISION REQUIRED" in out and "fix price" in out
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_revise_loop.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement critique builder + task augmentation**

```python
# agents/quality/revise_loop.py
"""Revise-loop helpers. The critique is specific + decomposed (research: specificity is the
highest-leverage variable). Facts (comply) are separated from style (balance). No praise."""
from __future__ import annotations

import json
from typing import Any

from agents.quality.deterministic_gate import GateFailure


def build_critique(deterministic_failures: list[GateFailure],
                   style_notes: list[dict], dossier_excerpt: str = "") -> dict[str, Any]:
    return {
        "fact_corrections": [
            {"check": f.check, "detail": f.detail, "fragment": f.fragment}
            for f in deterministic_failures
        ],
        "style_notes": style_notes,       # [{dimension, score, issue, fragment}]
        "dossier_context": dossier_excerpt,
    }


def augmented_task(original_task: str, critique: dict[str, Any]) -> str:
    """Fold the critique into the task so the originating agent regenerates correctly.
    Facts must be complied with; style is balanced against brand voice."""
    return (
        f"{original_task}\n\n"
        "=== REVISION REQUIRED — the previous draft failed evaluation ===\n"
        "FACT CORRECTIONS (mandatory — comply exactly):\n"
        f"{json.dumps(critique.get('fact_corrections', []), indent=2)}\n"
        "STYLE NOTES (balance against brand voice):\n"
        f"{json.dumps(critique.get('style_notes', []), indent=2)}\n"
        "PRODUCT DOSSIER (ground the copy in this):\n"
        f"{critique.get('dossier_context', '')}\n"
        "Regenerate the copy addressing every fact correction."
    )
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_revise_loop.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/quality/revise_loop.py tests/quality/test_revise_loop.py
git commit -m "feat(quality): revise-loop critique builder + task augmentation"
```

---

## Task 7: Evaluator.gate — orchestration (hard-gate vs soft-signal, cap 2, early-exit)

**Files:**
- Create: `agents/quality/evaluator.py`
- Test: `tests/quality/test_evaluator.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/quality/test_evaluator.py
from agents.quality.eval_config import EvaluatorConfig
from agents.quality.evaluator import Evaluator


_ROWS = [{"sku": "br-006", "name": "Black Rose Bomber Sherpa", "price": "265",
          "collection": "black-rose"}]


class _Judge:
    def __init__(self, scores_sequence):
        self._seq = list(scores_sequence); self.calls = 0
    async def score(self, text, model):
        s = self._seq[min(self.calls, len(self._seq) - 1)]; self.calls += 1
        composite = sum(s.values()) / len(s)
        return s, round(composite, 3), {"provider": "anthropic", "model": model,
                                        "input_tokens": 1, "output_tokens": 1,
                                        "finish_reason": "stop"}


class _Agent:
    core_type = "content"; name = "content_agent"
    def __init__(self, outputs): self._outputs = list(outputs); self.calls = 0
    async def execute(self, task, **kw):
        out = self._outputs[min(self.calls, len(self._outputs) - 1)]; self.calls += 1
        return out


async def test_soft_signal_attaches_verdict_never_revises():
    # failing scores, but soft_signal mode → no revision, verdict attached, original kept
    judge = _Judge([{"brand_voice": 1, "clarity": 1, "persuasiveness": 1, "distinctiveness": 1}])
    agent = _Agent([{"content": "x" * 200, "skus": ["br-006"], "collection": "black-rose",
                     "content_type": "pdp"}])
    ev = Evaluator(judge=judge, cfg=EvaluatorConfig(enabled=True, mode="soft_signal"), rows=_ROWS)
    result = {"content": "x" * 200, "skus": ["br-006"], "collection": "black-rose",
              "content_type": "pdp"}
    out = await ev.gate(agent=agent, task="t", result=result)
    assert out["_eval"]["passed"] is False
    assert out["_eval"]["mode"] == "soft_signal"
    assert agent.calls == 0                         # never re-invoked in soft mode


async def test_hard_gate_revises_then_passes_early_exit():
    # attempt 0 fails (low scores), revision 1 passes → early-exit, no 2nd revision
    judge = _Judge([
        {"brand_voice": 1, "clarity": 2, "persuasiveness": 2, "distinctiveness": 1},  # initial
        {"brand_voice": 4, "clarity": 4, "persuasiveness": 4, "distinctiveness": 4},  # revision 1
    ])
    good = {"content": "great oakland copy " * 20, "skus": ["br-006"],
            "collection": "black-rose", "content_type": "pdp"}
    agent = _Agent([good])                          # regeneration returns good copy
    ev = Evaluator(judge=judge, cfg=EvaluatorConfig(enabled=True, mode="hard_gate"), rows=_ROWS)
    initial = {"content": "weak", "skus": ["br-006"], "collection": "black-rose",
               "content_type": "pdp"}
    out = await ev.gate(agent=agent, task="Write PDP for br-006", result=initial)
    assert out["_eval"]["passed"] is True
    assert out["_eval"]["attempts"] == 1            # one revision, early-exit (cap is 2)
    assert agent.calls == 1


async def test_hard_gate_deterministic_failure_forces_revision():
    judge = _Judge([{"brand_voice": 5, "clarity": 5, "persuasiveness": 5, "distinctiveness": 5}])
    agent = _Agent([{"content": "Black Rose Bomber Sherpa for $265 " * 10, "skus": ["br-006"],
                     "collection": "black-rose", "content_type": "pdp"}])
    ev = Evaluator(judge=judge, cfg=EvaluatorConfig(enabled=True, mode="hard_gate"), rows=_ROWS)
    # initial copy has WRONG price → deterministic fail even though judge would pass
    initial = {"content": "Black Rose Bomber Sherpa for $245 " * 10, "skus": ["br-006"],
               "collection": "black-rose", "content_type": "pdp"}
    out = await ev.gate(agent=agent, task="t", result=initial)
    assert agent.calls == 1                         # forced a regeneration on the fact error
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_evaluator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the orchestrator**

```python
# agents/quality/evaluator.py
"""Evaluator orchestration: deterministic gate -> judge -> bounded revise loop.

hard_gate mode: failing drafts are regenerated (cap revise_cap, early-exit on pass),
then the best attempt is surfaced flagged.
soft_signal mode: evaluate + attach verdict, never revise (used until calibration κ≥0.65).
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any

from agents.quality.contracts import EvalVerdict
from agents.quality.deterministic_gate import run_gate
from agents.quality.eval_config import EvaluatorConfig
from agents.quality.judge import LLMJudge
from agents.quality.revise_loop import augmented_task, build_critique

logger = logging.getLogger(__name__)


class Evaluator:
    def __init__(self, judge: LLMJudge, cfg: EvaluatorConfig, rows: list[dict]) -> None:
        self._judge = judge
        self._cfg = cfg
        self._rows = rows

    @staticmethod
    def _content_of(result: Any) -> dict:
        return result if isinstance(result, dict) else {"content": str(result)}

    def _model_for(self, agent_name: str) -> str:
        return (self._cfg.judge_model_hero if agent_name in self._cfg.hero_agents
                else self._cfg.judge_model_default)

    async def _evaluate_once(self, payload: dict, model: str):
        text = payload.get("content", "")
        det = run_gate(text=text, skus=payload.get("skus", []), rows=self._rows,
                       collection=payload.get("collection"),
                       content_type=payload.get("content_type", "default"))
        scores, composite, usage = await self._judge.score(text, model=model)
        return det, scores, composite, usage

    async def gate(self, *, agent: Any, task: str, result: Any) -> Any:
        if not self._cfg.enabled:
            return result
        model = self._model_for(getattr(agent, "name", ""))
        payload = self._content_of(result)
        det, scores, composite, _ = await self._evaluate_once(payload, model)
        passed = not det and composite >= self._cfg.pass_threshold

        # soft-signal: annotate only, never revise
        if self._cfg.mode == "soft_signal":
            return self._attach(result, EvalVerdict(
                passed=passed, composite=composite, dimension_scores=scores,
                deterministic_failures=[f.check for f in det], critique={}, attempts=0,
                mode="soft_signal"))

        # hard-gate: bounded revise loop with early-exit
        best_payload, best_composite, best_scores, best_det = payload, composite, scores, det
        attempts = 0
        while (det or composite < self._cfg.pass_threshold) and attempts < self._cfg.revise_cap:
            attempts += 1
            style_notes = [{"dimension": d, "score": s} for d, s in scores.items()
                           if s < self._cfg.pass_threshold]
            critique = build_critique(det, style_notes,
                                      dossier_excerpt=payload.get("dossier", ""))
            # Re-invoke the ORIGINATING agent directly — NOT execute_safe (avoids hook recursion).
            revised = self._content_of(await agent.execute(augmented_task(task, critique)))
            det, scores, composite, _ = await self._evaluate_once(revised, model)
            payload = revised
            if composite >= best_composite and not det:
                best_payload, best_composite, best_scores, best_det = revised, composite, scores, det
            if not det and composite >= self._cfg.pass_threshold:
                best_payload, best_composite, best_scores, best_det = revised, composite, scores, det
                break  # early-exit

        passed = not best_det and best_composite >= self._cfg.pass_threshold
        verdict = EvalVerdict(passed=passed, composite=best_composite,
                              dimension_scores=best_scores,
                              deterministic_failures=[f.check for f in best_det],
                              critique={} if passed else {"flagged": True},
                              attempts=attempts, mode="hard_gate")
        out = result if best_payload is payload and isinstance(result, dict) else best_payload
        return self._attach(out, verdict)

    @staticmethod
    def _attach(result: Any, verdict: EvalVerdict) -> Any:
        if isinstance(result, dict):
            return {**result, "_eval": asdict(verdict) | {"normalized": verdict.normalized}}
        return {"content": result, "_eval": asdict(verdict)}
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_evaluator.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/quality/evaluator.py tests/quality/test_evaluator.py
git commit -m "feat(quality): Evaluator.gate orchestration (hard-gate/soft-signal, cap2, early-exit)"
```

---

## Task 8: Wire the evaluator into the hook (CONTENT agents only)

**Files:**
- Modify: `agents/quality/hooks.py`
- Test: `tests/quality/test_hook_evaluator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/quality/test_hook_evaluator.py
from agents.core.base import CoreAgentType
from agents.quality.config import ObserverConfig
from agents.quality import hooks


class _ContentAgent:
    name = "content_agent"; core_type = CoreAgentType.CONTENT; correlation_id = "c1"


class _OpsAgent:
    name = "ops_agent"; core_type = CoreAgentType.OPERATIONS; correlation_id = "c2"


async def test_content_agent_output_is_gated(monkeypatch):
    called = {}
    class _Eval:
        async def gate(self, *, agent, task, result):
            called["yes"] = True
            return {**result, "_eval": {"passed": True}}
    hooks._evaluator = _Eval()
    out = await hooks.after_execute(agent=_ContentAgent(), task="t",
                                    result={"content": "x"}, status="completed",
                                    duration_ms=1, config=ObserverConfig(enabled=True))
    assert called.get("yes") is True and out["_eval"]["passed"] is True


async def test_non_content_agent_not_gated(monkeypatch):
    class _Eval:
        async def gate(self, *, agent, task, result):
            raise AssertionError("ops agent must NOT be gated")
    hooks._evaluator = _Eval()
    out = await hooks.after_execute(agent=_OpsAgent(), task="t", result={"content": "x"},
                                    status="completed", duration_ms=1,
                                    config=ObserverConfig(enabled=True))
    assert "_eval" not in out
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_hook_evaluator.py -v`
Expected: FAIL (`hooks._evaluator` does not exist / not invoked)

- [ ] **Step 3: Extend `after_execute` to call the evaluator for CONTENT agents**

In `agents/quality/hooks.py`, add the module global and the gate call. Add near `_repo_factory`:

```python
_evaluator = None  # set at startup to an Evaluator instance (Plan 2 Task 9)
```

Then, inside `after_execute`, AFTER the record/publish block and BEFORE `return result`, insert:

```python
    # Evaluator gate — only for CONTENT-producing agents (avoids recursion: Evaluator
    # re-invokes agent.execute() directly, never execute_safe).
    try:
        from agents.core.base import CoreAgentType
        if (_evaluator is not None
                and getattr(agent, "core_type", None) == CoreAgentType.CONTENT):
            result = await _evaluator.gate(agent=agent, task=task, result=result)
    except Exception:
        logger.exception("evaluator gate failed (non-fatal)")
    return result
```

> The `return result` that previously ended the function is now after this block. Ensure there is exactly one `return result` at the end.

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_hook_evaluator.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Run Plan-1 hook tests to confirm no regression**

Run: `python -m pytest tests/quality/test_hooks.py tests/quality/test_execute_safe_hook.py -v`
Expected: PASS (observer path unaffected).

- [ ] **Step 6: Commit**

```bash
git add agents/quality/hooks.py tests/quality/test_hook_evaluator.py
git commit -m "feat(quality): gate CONTENT-agent output via Evaluator in after_execute"
```

---

## Task 9: Calibration harness (κ) + mode decision + startup wiring

**Files:**
- Create: `agents/quality/calibration.py`
- Create: `tests/fixtures/evaluator_ground_truth/README.md`
- Test: `tests/quality/test_calibration.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/quality/test_calibration.py
from agents.quality.calibration import cohen_kappa, decide_mode


def test_cohen_kappa_perfect_agreement():
    assert cohen_kappa([3, 4, 5, 2], [3, 4, 5, 2]) == 1.0


def test_cohen_kappa_no_better_than_chance():
    # constant predictions vs varied labels → kappa <= 0
    assert cohen_kappa([3, 3, 3, 3], [1, 2, 4, 5]) <= 0.0


def test_decide_mode_threshold():
    assert decide_mode(kappa=0.70) == "hard_gate"
    assert decide_mode(kappa=0.64) == "soft_signal"
    assert decide_mode(kappa=0.65) == "hard_gate"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_calibration.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement κ (no sklearn dependency) + mode decision**

```python
# agents/quality/calibration.py
"""Calibration: Cohen's kappa between judge composites (rounded) and human labels.
Decides evaluator mode — hard_gate only when kappa >= 0.65 (research-backed floor)."""
from __future__ import annotations

from collections import Counter
from typing import Literal

KAPPA_FLOOR = 0.65


def cohen_kappa(a: list[int], b: list[int]) -> float:
    """Cohen's kappa for two equal-length integer rating lists."""
    if len(a) != len(b) or not a:
        raise ValueError("rating lists must be equal length and non-empty")
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    categories = set(a) | set(b)
    pe = sum((ca.get(c, 0) / n) * (cb.get(c, 0) / n) for c in categories)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def decide_mode(kappa: float) -> Literal["hard_gate", "soft_signal"]:
    return "hard_gate" if kappa >= KAPPA_FLOOR else "soft_signal"
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_calibration.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Document the ground-truth set**

```markdown
<!-- tests/fixtures/evaluator_ground_truth/README.md -->
# Evaluator ground-truth set

~100 brand-team-labeled drafts spanning the 1–5 score range (deliberately bad → excellent).
Each entry: `{ "text": "...", "skus": ["br-006"], "collection": "black-rose",
"content_type": "pdp", "human_score": 1..5 }` in `samples.jsonl`.

Run calibration: load samples → `LLMJudge.score` each → round composite →
`cohen_kappa(judge_rounded, human_scores)` → `decide_mode(kappa)`.
If `soft_signal`, the evaluator annotates only (never blocks) until the rubric is revised
and re-validated. Re-validate monthly on 20–30 production samples.
```

- [ ] **Step 6: Wire the evaluator at startup**

Extend `agents/quality/startup.py` (from Plan 1) with an evaluator installer:

```python
# add to agents/quality/startup.py
def install_evaluator(cfg, judge, rows) -> None:
    """Point the hook's evaluator at a configured Evaluator instance."""
    from agents.quality import hooks
    from agents.quality.evaluator import Evaluator
    hooks._evaluator = Evaluator(judge=judge, cfg=cfg, rows=rows)
```

In `main_enterprise.py` lifespan (where Plan 1 installed observability), add:

```python
from agents.quality.eval_config import EvaluatorConfig
from agents.quality.judge import LLMJudge
from agents.quality.startup import install_evaluator
from skyyrose.core.catalog_loader import read_catalog_rows
from llm.providers.anthropic import AnthropicClient   # confirm constructor/api-key source

_eval_cfg = EvaluatorConfig(enabled=bool(os.getenv("EVALUATOR_ENABLED")))  # mode set by calibration
if _eval_cfg.enabled:
    _judge = LLMJudge(client=AnthropicClient(), cfg=_eval_cfg)  # confirm AnthropicClient() args
    install_evaluator(_eval_cfg, judge=_judge, rows=read_catalog_rows())
```

> **Open question (resolve here):** `AnthropicClient` constructor args / API-key source — read `llm/providers/anthropic.py` `__init__` and `llm/base.py` `BaseLLMClient.__init__`. Construct it the same way the existing agents do (there may be a factory/`LLMRouter` to reuse instead of instantiating directly).

- [ ] **Step 7: Commit**

```bash
git add agents/quality/calibration.py agents/quality/startup.py tests/quality/test_calibration.py tests/fixtures/evaluator_ground_truth/README.md main_enterprise.py
git commit -m "feat(quality): calibration kappa + mode decision + evaluator startup wiring"
```

---

## Task 10: End-to-end test + docs

**Files:**
- Create: `tests/quality/test_evaluator_e2e.py`
- Modify: `.wolf/anatomy.md`

- [ ] **Step 1: Write the end-to-end test (hook → gate → revise, fake judge)**

```python
# tests/quality/test_evaluator_e2e.py
from agents.core.base import CoreAgent, CoreAgentType
from agents.quality import hooks
from agents.quality.eval_config import EvaluatorConfig
from agents.quality.evaluator import Evaluator
from agents.quality.config import ObserverConfig


_ROWS = [{"sku": "br-006", "name": "Black Rose Bomber Sherpa", "price": "265",
          "collection": "black-rose"}]


class _Judge:
    # initial bad, revision good
    _seq = [{"brand_voice": 1, "clarity": 2, "persuasiveness": 2, "distinctiveness": 1},
            {"brand_voice": 4, "clarity": 4, "persuasiveness": 4, "distinctiveness": 4}]
    def __init__(self): self.calls = 0
    async def score(self, text, model):
        s = self._seq[min(self.calls, 1)]; self.calls += 1
        return s, sum(s.values()) / 4, {"provider": "anthropic", "model": model,
                                        "input_tokens": 1, "output_tokens": 1,
                                        "finish_reason": "stop"}


class _ContentAgent(CoreAgent):
    core_type = CoreAgentType.CONTENT
    name = "content_agent"
    def __init__(self):
        super().__init__(correlation_id="c1")
        self._n = 0
    async def execute(self, task, **kw):
        self._n += 1
        good = "Oakland-built Black Rose Bomber Sherpa, $265, concrete-cut. " * 6
        return {"content": good, "skus": ["br-006"], "collection": "black-rose",
                "content_type": "pdp"}


async def test_content_failing_draft_is_revised_then_passes(monkeypatch):
    hooks._repo_factory = None  # no DB needed for this test
    hooks._evaluator = Evaluator(
        judge=_Judge(), cfg=EvaluatorConfig(enabled=True, mode="hard_gate"), rows=_ROWS)
    agent = _ContentAgent()
    # initial weak draft goes through execute_safe -> hook -> evaluator gate
    monkeypatch.setattr(agent, "execute", agent.execute)  # keep
    out = await agent.execute_safe("Write PDP for Black Rose Bomber Sherpa")
    assert out["_eval"]["passed"] is True
    assert out["_eval"]["attempts"] >= 1
```

- [ ] **Step 2: Run to verify it passes**

Run: `python -m pytest tests/quality/test_evaluator_e2e.py -v`
Expected: PASS — proves: CONTENT agent output flows through `execute_safe` → hook → evaluator → revise loop → passing verdict attached.

- [ ] **Step 3: Run the full quality suite + lint the footprint**

Run: `python -m pytest tests/quality/ -v && ruff check agents/quality && black --check agents/quality`
Expected: all PASS / clean.

- [ ] **Step 4: Update `.wolf/anatomy.md`**

Add entries for `deterministic_gate.py`, `judge.py`, `revise_loop.py`, `evaluator.py`, `calibration.py`, `eval_config.py`, and note the evaluator gate addition to `hooks.py`.

- [ ] **Step 5: Commit**

```bash
git add tests/quality/test_evaluator_e2e.py .wolf/anatomy.md
git commit -m "test(quality): evaluator e2e (failing draft revised to pass) + docs"
```

---

## Self-review notes (run before execution)

- **Spec coverage:** deterministic gate w/ catalog facts (Tasks 3–4), Claude judge 0–5 criterion-separated CoT blind anti-verbosity (Task 5), revise loop cap-2 + early-exit + specific decomposed critique + SKU dossier grounding (Tasks 6–7), hard-gate vs soft-signal (Task 7), CONTENT-only gating via `core_type` (Task 8), calibration κ≥0.65 mode gate (Task 9), distinctiveness dimension for anti-homogenization (Task 2 weights + Task 5 guidance).
- **Recursion guard:** revise loop calls `agent.execute()` directly, never `execute_safe` (Task 7 code + comment).
- **Borderline position-swap re-check** and **score-drift monitoring** (Observer cross-link): deferred to a follow-up — noted here so they aren't lost. Position-swap is a judge enhancement; score-drift is an Observer detection rule fed by `_eval` composites.
- **Type consistency:** `EvalVerdict`, `EvaluatorConfig`, `GateFailure`, `LLMJudge.score()` signature `(text, model) -> (scores, composite, usage)`, `Evaluator.gate(agent, task, result)` are identical across Tasks 1, 2, 5, 6, 7, 8.
- **Open question:** `AnthropicClient` constructor / API-key source — resolved inline in Task 9 step 6.
