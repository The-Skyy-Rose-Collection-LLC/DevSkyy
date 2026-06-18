# Metrics Foundation + Observability Agent — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Instrument the orphaned `agent_executions` table at the `execute_safe` seam (OTel-GenAI-named fields, split tokens, computed cost), then detect anomalies (dead/looping agents, retry storms, per-conversation cost runaway, spend/latency trends) and emit alert+recommend signals.

**Architecture:** A single framework hook (`agents/quality/hooks.py::after_execute`) is called from `CoreAgent.execute_safe` (`agents/core/base.py:670`). It writes one `AgentExecution` row per execution and publishes an `AgentExecEvent` on the existing in-process `EventBus`. Detection logic operates on a `MetricsRepository` interface (unit-tested with an in-memory fake; integration-tested against the DB) so it has no DB dependency. The observer never auto-acts — it produces `AgentAlert`s.

**Tech Stack:** Python 3.11+, SQLAlchemy (async, `database/db.py`), Alembic, pytest (`asyncio_mode=auto`). Reuses `llm/router.py` pricing, `core/events/event_bus.py`, `database/db.py`.

**Companion spec:** `docs/superpowers/specs/2026-06-16-evaluator-observability-agents-design.html`

---

## Deviations from spec (grounded in code reads)

| Spec said | Plan does | Why |
|---|---|---|
| New `PricingTable` in `agents/quality/cost.py` | Reuse `llm/router.py` `PROVIDER_CONFIGS` + a thin `cost_usd()` wrapper | Pricing table already exists (per-1K USD); DRY |
| Token counts captured at seam | v1 reads token/cost from an optional `result["_usage"]` envelope; nullable otherwise | `execute()` returns untyped dict; `CompletionResponse` tokens are swallowed (`llm/base.py:246`). Fleet-wide capture = phase 2 |
| Detection reads `agent_executions` directly | Detection reads a `MetricsRepository` interface | `AgentExecution` uses PG-only types (`PG_UUID`, `JSONB`, `uuid_generate_v4()`) → can't unit-test on SQLite; repository lets logic be DB-free |

---

## File structure

| File | Responsibility |
|---|---|
| `agents/quality/__init__.py` | Package marker (required — no implicit namespace packages) |
| `agents/quality/contracts.py` | Frozen dataclasses: `AgentMetrics`, `AgentExecEvent`, `AgentAlert`, `Severity` |
| `agents/quality/config.py` | `ObserverConfig` (thresholds, intervals, warm-up) |
| `agents/quality/cost.py` | `cost_usd(provider, input_tokens, output_tokens)` — wraps `llm/router` pricing |
| `agents/quality/repository.py` | `MetricsRepository` (Protocol) + `SqlMetricsRepository` + `InMemoryMetricsRepository` |
| `agents/quality/hooks.py` | `after_execute(...)` — builds `AgentMetrics`, writes row, publishes event; `usage_envelope()` helper |
| `agents/quality/detection_rules.py` | Pure functions: one per detection rule, operating on `AgentMetrics` lists |
| `agents/quality/alerts.py` | `AlertSink` — dedup/hysteresis + EventBus publish + in-memory store for API |
| `agents/quality/observer.py` | `Observer` — `record()`, `scan()`, EventBus subscriber, warm-up gating |
| `agents/models.py:201` | Modify: add OTel-aligned columns to `AgentExecution` |
| `alembic/versions/004_agent_execution_observability.py` | Create: migration adding the columns |
| `agents/core/base.py:670` | Modify: call `after_execute` hook in `execute_safe` |
| `tests/quality/*` | Tests |

---

## Task 1: Package + contracts

**Files:**
- Create: `agents/quality/__init__.py`
- Create: `agents/quality/contracts.py`
- Test: `tests/quality/test_contracts.py`

- [ ] **Step 1: Create the package marker**

```python
# agents/quality/__init__.py
"""Cross-cutting quality agents: observability + evaluator interceptors."""
```

- [ ] **Step 2: Write the failing test**

```python
# tests/quality/test_contracts.py
from agents.quality.contracts import AgentMetrics, AgentExecEvent, AgentAlert, Severity


def test_agent_metrics_is_frozen_and_computes_total_tokens():
    m = AgentMetrics(
        execution_id="e1", agent_name="content", status="completed",
        duration_ms=120, conversation_id="c1",
        input_tokens=100, output_tokens=50, cost_usd=0.0,
        provider_name="anthropic", request_model="claude-sonnet-4-6",
        finish_reason="stop", error_type=None, retry_attempt=0,
    )
    assert m.total_tokens == 150
    import dataclasses
    try:
        m.status = "failed"  # frozen → should raise
        assert False, "expected FrozenInstanceError"
    except dataclasses.FrozenInstanceError:
        pass


def test_alert_severity_ordering():
    assert Severity.PAGE > Severity.TICKET > Severity.DASHBOARD


def test_exec_event_has_event_type():
    ev = AgentExecEvent(agent_name="x", status="completed", conversation_id="c1",
                        cost_usd=0.0, duration_ms=10, error_type=None)
    assert ev.event_type == "agent.execution"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/quality/test_contracts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agents.quality.contracts'`

- [ ] **Step 4: Implement the contracts**

```python
# agents/quality/contracts.py
"""Frozen data contracts shared by the observability + evaluator interceptors.

Field names align to OpenTelemetry GenAI semantic conventions where applicable
(input_tokens/output_tokens, provider_name, request_model, finish_reason, error_type).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class Severity(IntEnum):
    """Ordered so PAGE > TICKET > DASHBOARD for comparison."""
    DASHBOARD = 1
    TICKET = 2
    PAGE = 3


@dataclass(frozen=True)
class AgentMetrics:
    """One agent execution. Maps 1:1 to an `agent_executions` row."""
    execution_id: str
    agent_name: str
    status: str                      # "completed" | "failed"
    duration_ms: int
    conversation_id: str | None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    provider_name: str | None = None
    request_model: str | None = None
    finish_reason: str | None = None
    error_type: str | None = None
    retry_attempt: int = 0

    @property
    def total_tokens(self) -> int:
        return (self.input_tokens or 0) + (self.output_tokens or 0)


@dataclass(frozen=True)
class AgentExecEvent:
    """Published on the EventBus after each execution (real-time channel)."""
    agent_name: str
    status: str
    conversation_id: str | None
    cost_usd: float | None
    duration_ms: int
    error_type: str | None
    event_type: str = "agent.execution"


@dataclass(frozen=True)
class AgentAlert:
    """Observer output. Alert + recommend; never an action."""
    severity: Severity
    kind: str                        # "retry_storm" | "dead_agent" | "conversation_cost" | ...
    agent_name: str
    evidence: dict = field(default_factory=dict)
    recommendation: str = ""
    conversation_id: str | None = None

    def key(self) -> str:
        """Stable identity for hysteresis (alert once per open condition)."""
        return f"{self.kind}:{self.agent_name}:{self.conversation_id or '-'}"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/quality/test_contracts.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add agents/quality/__init__.py agents/quality/contracts.py tests/quality/test_contracts.py
git commit -m "feat(quality): data contracts for observability interceptor"
```

---

## Task 2: Cost helper (reuse existing pricing)

**Files:**
- Create: `agents/quality/cost.py`
- Test: `tests/quality/test_cost.py`

- [ ] **Step 1: Confirm the reused pricing source**

Read `llm/router.py:62-109` (`PROVIDER_CONFIGS`) and `llm/router.py:560-573` (`estimate_cost`). Prices are **per 1K tokens USD**. Confirm `ModelProvider` enum members include `ANTHROPIC`, `OPENAI`, `GOOGLE`.

- [ ] **Step 2: Write the failing test**

```python
# tests/quality/test_cost.py
from agents.quality.cost import cost_usd


def test_cost_anthropic_matches_per_1k_pricing():
    # anthropic: input 0.003/1k, output 0.015/1k  (llm/router.py)
    c = cost_usd("anthropic", input_tokens=1000, output_tokens=1000)
    assert round(c, 6) == round(0.003 + 0.015, 6)


def test_cost_unknown_provider_returns_zero():
    assert cost_usd("nonesuch", 1000, 1000) == 0.0


def test_cost_handles_none_tokens():
    assert cost_usd("anthropic", None, None) == 0.0
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/quality/test_cost.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: Implement, delegating to the existing pricing table**

```python
# agents/quality/cost.py
"""Cost computation. Reuses the per-1K pricing table in llm/router.py — no new table."""
from __future__ import annotations

from llm.router import PROVIDER_CONFIGS, ModelProvider


def cost_usd(provider_name: str | None, input_tokens: int | None,
             output_tokens: int | None) -> float:
    """USD cost from token counts using llm/router pricing. 0.0 on unknown provider."""
    if not provider_name:
        return 0.0
    try:
        provider = ModelProvider(provider_name.lower())
    except ValueError:
        return 0.0
    config = PROVIDER_CONFIGS.get(provider)
    if config is None:
        return 0.0
    inp = (input_tokens or 0) / 1000 * config.input_price
    out = (output_tokens or 0) / 1000 * config.output_price
    return inp + out
```

> If `ModelProvider(provider_name.lower())` does not resolve the string values, adjust to map by `.value`. Confirm enum values during step 1.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/quality/test_cost.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add agents/quality/cost.py tests/quality/test_cost.py
git commit -m "feat(quality): cost_usd helper reusing llm/router pricing"
```

---

## Task 3: Config

**Files:**
- Create: `agents/quality/config.py`
- Test: `tests/quality/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/quality/test_config.py
from agents.quality.config import ObserverConfig


def test_defaults():
    c = ObserverConfig()
    assert c.enabled is False               # ships dormant
    assert c.scan_interval_s == 300
    assert c.warmup_days == 14
    assert c.retry_storm_count == 5
    assert c.retry_storm_window_s == 60
    assert c.per_conversation_cost_ceiling_usd == 5.0
    assert c.dead_agent_window_s == 600


def test_override():
    c = ObserverConfig(enabled=True, per_conversation_cost_ceiling_usd=1.0)
    assert c.enabled is True
    assert c.per_conversation_cost_ceiling_usd == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/quality/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement**

```python
# agents/quality/config.py
"""Observer configuration. Ships dormant (enabled=False)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ObserverConfig:
    enabled: bool = False
    scan_interval_s: int = 300
    warmup_days: int = 14
    settling_window_s: int = 600
    # static (no warm-up)
    retry_storm_count: int = 5
    retry_storm_window_s: int = 60
    dead_agent_window_s: int = 600
    per_conversation_cost_ceiling_usd: float = 5.0
    workflow_ttl_s: int = 1800
    tool_failure_rate: float = 0.20
    tool_failure_window_s: int = 300
    # warm-up gated (trend)
    token_spike_multiplier: float = 3.0
    token_spike_circuit_multiplier: float = 10.0
    latency_p95_bound_ms: int = 30000
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/quality/test_config.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/quality/config.py tests/quality/test_config.py
git commit -m "feat(quality): observer config (ships dormant)"
```

---

## Task 4: MetricsRepository (interface + in-memory fake)

**Files:**
- Create: `agents/quality/repository.py`
- Test: `tests/quality/test_repository.py`

- [ ] **Step 1: Write the failing test (in-memory repo only — DB repo tested in Task 6)**

```python
# tests/quality/test_repository.py
from agents.quality.contracts import AgentMetrics
from agents.quality.repository import InMemoryMetricsRepository


def _m(**kw):
    base = dict(execution_id="e", agent_name="a", status="completed",
                duration_ms=10, conversation_id="c1", cost_usd=1.0)
    base.update(kw)
    return AgentMetrics(**base)


async def test_save_and_recent():
    repo = InMemoryMetricsRepository()
    await repo.save(_m(execution_id="e1"))
    await repo.save(_m(execution_id="e2", agent_name="b"))
    recent = await repo.recent(window_s=3600)
    assert {m.execution_id for m in recent} == {"e1", "e2"}


async def test_conversation_cost_sums():
    repo = InMemoryMetricsRepository()
    await repo.save(_m(execution_id="e1", conversation_id="c1", cost_usd=2.0))
    await repo.save(_m(execution_id="e2", conversation_id="c1", cost_usd=3.5))
    await repo.save(_m(execution_id="e3", conversation_id="c2", cost_usd=1.0))
    costs = await repo.conversation_cost_totals(window_s=3600)
    assert costs["c1"] == 5.5
    assert costs["c2"] == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/quality/test_repository.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the Protocol + in-memory fake**

```python
# agents/quality/repository.py
"""Metrics persistence + read aggregates behind an interface.

Detection logic depends on this Protocol, never on the DB directly — so it is
unit-testable with InMemoryMetricsRepository. SqlMetricsRepository (Task 6)
is the production implementation.
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Protocol, runtime_checkable

from agents.quality.contracts import AgentMetrics


@runtime_checkable
class MetricsRepository(Protocol):
    async def save(self, m: AgentMetrics) -> None: ...
    async def recent(self, window_s: int) -> list[AgentMetrics]: ...
    async def conversation_cost_totals(self, window_s: int) -> dict[str, float]: ...


class InMemoryMetricsRepository:
    """Test/dev implementation. Stores (monotonic_ts, metrics)."""

    def __init__(self) -> None:
        self._rows: list[tuple[float, AgentMetrics]] = []

    async def save(self, m: AgentMetrics) -> None:
        self._rows.append((time.monotonic(), m))

    async def recent(self, window_s: int) -> list[AgentMetrics]:
        cutoff = time.monotonic() - window_s
        return [m for ts, m in self._rows if ts >= cutoff]

    async def conversation_cost_totals(self, window_s: int) -> dict[str, float]:
        totals: dict[str, float] = defaultdict(float)
        for m in await self.recent(window_s):
            if m.conversation_id:
                totals[m.conversation_id] += m.cost_usd or 0.0
        return dict(totals)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/quality/test_repository.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/quality/repository.py tests/quality/test_repository.py
git commit -m "feat(quality): MetricsRepository protocol + in-memory impl"
```

---

## Task 5: Extend the AgentExecution model + migration 004

**Files:**
- Modify: `agents/models.py:201-235`
- Create: `alembic/versions/004_agent_execution_observability.py`
- Test: `tests/quality/test_model_columns.py`

- [ ] **Step 1: Write the failing test (columns exist on the model)**

```python
# tests/quality/test_model_columns.py
from agents.models import AgentExecution


def test_observability_columns_present():
    cols = set(AgentExecution.__table__.columns.keys())
    for c in ("input_tokens", "output_tokens", "cache_read_tokens", "cost_usd",
              "provider_name", "request_model", "finish_reason", "error_type",
              "conversation_id", "trace_id", "retry_attempt"):
        assert c in cols, f"missing column {c}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/quality/test_model_columns.py -v`
Expected: FAIL — missing column `input_tokens`

- [ ] **Step 3: Add columns to the model (match existing `Column()` style exactly)**

In `agents/models.py`, inside `class AgentExecution`, after the `extra_data` line (`:235`), add:

```python
    # --- Observability (migration 004), OTel GenAI semconv aligned ---
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cache_read_tokens = Column(Integer)
    cost_usd = Column(DECIMAL(10, 6))
    provider_name = Column(String(50))
    request_model = Column(String(100))
    finish_reason = Column(String(50))
    error_type = Column(String(100))
    conversation_id = Column(String(100), index=True)
    trace_id = Column(String(100))
    retry_attempt = Column(Integer, server_default=text("0"))
```

`DECIMAL`, `Integer`, `String`, `text` are already imported at `agents/models.py:1-20`. No new imports needed.

- [ ] **Step 4: Run the model test to verify it passes**

Run: `python -m pytest tests/quality/test_model_columns.py -v`
Expected: PASS

- [ ] **Step 5: Write the Alembic migration (down_revision = "003" — current head)**

```python
# alembic/versions/004_agent_execution_observability.py
"""agent execution observability columns

Revision ID: 004
Revises: 003
Create Date: 2026-06-16

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("agent_executions", sa.Column("input_tokens", sa.Integer(), nullable=True))
    op.add_column("agent_executions", sa.Column("output_tokens", sa.Integer(), nullable=True))
    op.add_column("agent_executions", sa.Column("cache_read_tokens", sa.Integer(), nullable=True))
    op.add_column("agent_executions", sa.Column("cost_usd", sa.DECIMAL(10, 6), nullable=True))
    op.add_column("agent_executions", sa.Column("provider_name", sa.String(50), nullable=True))
    op.add_column("agent_executions", sa.Column("request_model", sa.String(100), nullable=True))
    op.add_column("agent_executions", sa.Column("finish_reason", sa.String(50), nullable=True))
    op.add_column("agent_executions", sa.Column("error_type", sa.String(100), nullable=True))
    op.add_column("agent_executions", sa.Column("conversation_id", sa.String(100), nullable=True))
    op.add_column("agent_executions", sa.Column("trace_id", sa.String(100), nullable=True))
    op.add_column("agent_executions",
                  sa.Column("retry_attempt", sa.Integer(), server_default=sa.text("0")))
    op.create_index("ix_agent_executions_conversation_id", "agent_executions", ["conversation_id"])
    op.create_index("ix_agent_executions_created_status", "agent_executions",
                    ["created_at", "status"])


def downgrade() -> None:
    op.drop_index("ix_agent_executions_created_status")
    op.drop_index("ix_agent_executions_conversation_id")
    for col in ("retry_attempt", "trace_id", "conversation_id", "error_type", "finish_reason",
                "request_model", "provider_name", "cost_usd", "cache_read_tokens",
                "output_tokens", "input_tokens"):
        op.drop_column("agent_executions", col)
```

- [ ] **Step 6: Verify the migration imports cleanly (offline check)**

Run: `python -c "import importlib.util,glob; f=glob.glob('alembic/versions/004_*.py')[0]; importlib.util.spec_from_file_location('m',f); print('ok', f)"`
Expected: `ok alembic/versions/004_...py`
(Applying against a live Postgres — `alembic upgrade head` — is an integration step done at deploy time, not in unit tests.)

- [ ] **Step 7: Commit**

```bash
git add agents/models.py alembic/versions/004_agent_execution_observability.py tests/quality/test_model_columns.py
git commit -m "feat(db): add OTel-aligned observability columns to agent_executions (004)"
```

---

## Task 6: SqlMetricsRepository (production write/read)

**Files:**
- Modify: `agents/quality/repository.py`
- Test: `tests/quality/test_repository_sql.py` (marked `integration`)

- [ ] **Step 1: Write the failing integration test**

```python
# tests/quality/test_repository_sql.py
import pytest

from agents.quality.contracts import AgentMetrics

pytestmark = pytest.mark.integration  # excluded by default; needs a Postgres test DB


@pytest.fixture
async def pg_session():
    from database.db import DatabaseConfig, DatabaseManager
    mgr = DatabaseManager()
    await mgr.initialize(DatabaseConfig(url="postgresql+asyncpg://localhost/devskyy_test"))
    async with mgr.session() as s:
        yield s
    await mgr.close()


async def test_save_then_recent_roundtrip(pg_session):
    from agents.quality.repository import SqlMetricsRepository
    repo = SqlMetricsRepository(session=pg_session)
    await repo.save(AgentMetrics(
        execution_id="it-e1", agent_name="content", status="completed",
        duration_ms=42, conversation_id="it-c1", input_tokens=10, output_tokens=5,
        cost_usd=0.001, provider_name="anthropic", request_model="claude-sonnet-4-6",
        finish_reason="stop", error_type=None, retry_attempt=0,
    ))
    recent = await repo.recent(window_s=60)
    assert any(m.execution_id == "it-e1" for m in recent)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_repository_sql.py -v -m integration`
Expected: FAIL with `ImportError: cannot import name 'SqlMetricsRepository'`

- [ ] **Step 3: Implement `SqlMetricsRepository`**

Append to `agents/quality/repository.py`:

```python
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.models import AgentExecution


class SqlMetricsRepository:
    """Production impl backed by the agent_executions table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, m: AgentMetrics) -> None:
        self._session.add(AgentExecution(
            execution_id=m.execution_id,
            agent_name=m.agent_name,
            prompt="",  # prompt captured separately by callers if needed
            status=m.status,
            tokens_used=m.total_tokens or None,
            duration_ms=m.duration_ms,
            input_tokens=m.input_tokens,
            output_tokens=m.output_tokens,
            cost_usd=m.cost_usd,
            provider_name=m.provider_name,
            request_model=m.request_model,
            finish_reason=m.finish_reason,
            error_type=m.error_type,
            conversation_id=m.conversation_id,
            retry_attempt=m.retry_attempt,
        ))
        await self._session.flush()

    async def recent(self, window_s: int) -> list[AgentMetrics]:
        cutoff = datetime.now(UTC) - timedelta(seconds=window_s)
        rows = (await self._session.execute(
            select(AgentExecution).where(AgentExecution.created_at >= cutoff)
        )).scalars().all()
        return [self._to_metrics(r) for r in rows]

    async def conversation_cost_totals(self, window_s: int) -> dict[str, float]:
        totals: dict[str, float] = {}
        for m in await self.recent(window_s):
            if m.conversation_id:
                totals[m.conversation_id] = totals.get(m.conversation_id, 0.0) + (m.cost_usd or 0.0)
        return totals

    @staticmethod
    def _to_metrics(r: AgentExecution) -> AgentMetrics:
        return AgentMetrics(
            execution_id=r.execution_id, agent_name=r.agent_name, status=r.status or "",
            duration_ms=r.duration_ms or 0, conversation_id=r.conversation_id,
            input_tokens=r.input_tokens, output_tokens=r.output_tokens,
            cost_usd=float(r.cost_usd) if r.cost_usd is not None else None,
            provider_name=r.provider_name, request_model=r.request_model,
            finish_reason=r.finish_reason, error_type=r.error_type,
            retry_attempt=r.retry_attempt or 0,
        )
```

- [ ] **Step 4: Run the integration test (requires a Postgres test DB + migration applied)**

Run: `alembic upgrade head && python -m pytest tests/quality/test_repository_sql.py -v -m integration`
Expected: PASS. If no Postgres test DB is available in the environment, document the skip and run in CI/deploy.

- [ ] **Step 5: Commit**

```bash
git add agents/quality/repository.py tests/quality/test_repository_sql.py
git commit -m "feat(quality): SqlMetricsRepository over agent_executions"
```

---

## Task 7: Hook — build metrics, write, publish

**Files:**
- Create: `agents/quality/hooks.py`
- Test: `tests/quality/test_hooks.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/quality/test_hooks.py
from agents.quality.config import ObserverConfig
from agents.quality.contracts import AgentExecEvent
from agents.quality.hooks import after_execute, usage_envelope


class _Agent:
    name = "content"
    core_type = "content"
    correlation_id = "conv-1"


async def test_after_execute_records_and_publishes(monkeypatch):
    from agents.quality import hooks
    saved, published = [], []

    class _Repo:
        async def save(self, m): saved.append(m)

    async def _publish(ev): published.append(ev)

    hooks._repo_factory = lambda: _Repo()
    monkeypatch.setattr(hooks.event_bus, "publish", _publish)

    result = {"ok": True, "_usage": usage_envelope(
        provider="anthropic", model="claude-sonnet-4-6",
        input_tokens=100, output_tokens=50, finish_reason="stop")}

    out = await after_execute(agent=_Agent(), task="t", result=result,
                              status="completed", duration_ms=33,
                              config=ObserverConfig(enabled=True))
    assert out is result                       # hook returns result unchanged (observer is passive)
    assert len(saved) == 1
    assert saved[0].agent_name == "content"
    assert saved[0].input_tokens == 100
    assert saved[0].cost_usd > 0
    assert isinstance(published[0], AgentExecEvent)


async def test_after_execute_noop_when_disabled():
    out = await after_execute(agent=_Agent(), task="t", result={"ok": True},
                              status="completed", duration_ms=1,
                              config=ObserverConfig(enabled=False))
    assert out == {"ok": True}
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_hooks.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the hook**

```python
# agents/quality/hooks.py
"""The single framework interception point, called from CoreAgent.execute_safe.

v1 responsibility: build AgentMetrics, persist a row, publish an AgentExecEvent.
The evaluator gate (Plan 2) extends this hook; it is absent here by design.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from core.events.event_bus import event_bus

from agents.quality.config import ObserverConfig
from agents.quality.contracts import AgentExecEvent, AgentMetrics
from agents.quality.cost import cost_usd

logger = logging.getLogger(__name__)

# Indirection so tests can inject a fake repo without a DB.
_repo_factory = None  # set at startup (Task 11) to a callable returning a MetricsRepository


def usage_envelope(*, provider: str, model: str, input_tokens: int,
                   output_tokens: int, finish_reason: str = "",
                   cache_read_tokens: int | None = None) -> dict[str, Any]:
    """Agents that call an LLM put this under result['_usage'] so the hook can
    record exact token/cost. See llm/base.py CompletionResponse for the fields."""
    return {
        "provider": provider, "model": model,
        "input_tokens": input_tokens, "output_tokens": output_tokens,
        "cache_read_tokens": cache_read_tokens, "finish_reason": finish_reason,
    }


def _metrics_from(agent: Any, result: Any, status: str, duration_ms: int,
                  retry_attempt: int) -> AgentMetrics:
    usage = result.get("_usage") if isinstance(result, dict) else None
    provider = usage.get("provider") if usage else None
    return AgentMetrics(
        execution_id=str(uuid.uuid4()),
        agent_name=getattr(agent, "name", "unknown"),
        status=status,
        duration_ms=duration_ms,
        conversation_id=getattr(agent, "correlation_id", None),
        input_tokens=usage.get("input_tokens") if usage else None,
        output_tokens=usage.get("output_tokens") if usage else None,
        cost_usd=cost_usd(provider, usage.get("input_tokens"), usage.get("output_tokens"))
            if usage else None,
        provider_name=provider,
        request_model=usage.get("model") if usage else None,
        finish_reason=usage.get("finish_reason") if usage else None,
        error_type=(result.get("error_type") if isinstance(result, dict) else None),
        retry_attempt=retry_attempt,
    )


async def after_execute(*, agent: Any, task: str, result: Any, status: str,
                        duration_ms: int, config: ObserverConfig | None = None,
                        retry_attempt: int = 0) -> Any:
    """Record one execution. Returns `result` unchanged (observer is passive).
    No-op (and never raises) when disabled — must never break the agent path."""
    config = config or ObserverConfig()
    if not config.enabled:
        return result
    try:
        metrics = _metrics_from(agent, result, status, duration_ms, retry_attempt)
        if _repo_factory is not None:
            repo = _repo_factory()
            await repo.save(metrics)
        await event_bus.publish(AgentExecEvent(
            agent_name=metrics.agent_name, status=metrics.status,
            conversation_id=metrics.conversation_id, cost_usd=metrics.cost_usd,
            duration_ms=metrics.duration_ms, error_type=metrics.error_type,
        ))
    except Exception:  # observability must never break execution
        logger.exception("quality.after_execute failed (non-fatal)")
    return result
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_hooks.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/quality/hooks.py tests/quality/test_hooks.py
git commit -m "feat(quality): after_execute hook — record + publish, fail-safe"
```

---

## Task 8: Wire the hook into execute_safe

**Files:**
- Modify: `agents/core/base.py:670-716`
- Test: `tests/quality/test_execute_safe_hook.py`

- [ ] **Step 1: Write the failing test (hook fires on success AND failure)**

```python
# tests/quality/test_execute_safe_hook.py
import agents.quality.hooks as hooks
from agents.core.base import CoreAgent, CoreAgentType


class _Ok(CoreAgent):
    core_type = CoreAgentType.OPERATIONS
    name = "ok_agent"
    async def execute(self, task, **kw):
        return {"success": True}


class _Boom(CoreAgent):
    core_type = CoreAgentType.OPERATIONS
    name = "boom_agent"
    async def heal(self, diagnosis):  # force no-heal so it returns the failure dict
        class _H:  # minimal heal result
            success = False; escalation_needed = True; history = []
        return _H()
    async def execute(self, task, **kw):
        raise RuntimeError("nope")


async def test_hook_called_on_success(monkeypatch):
    calls = []
    async def _spy(**kw): calls.append(kw); return kw["result"]
    monkeypatch.setattr(hooks, "after_execute", _spy)
    await _Ok().execute_safe("t")
    assert calls and calls[0]["status"] == "completed"


async def test_hook_called_on_failure(monkeypatch):
    calls = []
    async def _spy(**kw): calls.append(kw); return kw["result"]
    monkeypatch.setattr(hooks, "after_execute", _spy)
    await _Boom().execute_safe("t")
    assert calls and calls[0]["status"] == "failed"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_execute_safe_hook.py -v`
Expected: FAIL (hook not wired — `calls` empty)

- [ ] **Step 3: Modify `execute_safe` to call the hook on every return path**

Replace the body of `execute_safe` (`agents/core/base.py:670-716`) with the version below. It preserves the existing circuit-breaker + heal logic and adds timing + the hook on success and terminal-failure paths.

```python
    async def execute_safe(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """Execute with circuit breaker + self-healing wrapper, then the quality hook."""
        from time import monotonic

        from agents.quality import hooks
        from agents.quality.config import ObserverConfig

        cfg = getattr(self, "_observer_config", None) or ObserverConfig()

        if not self.circuit_breaker_allows():
            return {"success": False,
                    "error": f"Circuit breaker OPEN for {self.name}",
                    "escalation_needed": True}

        started = monotonic()
        try:
            result = await self.execute(task, **kwargs)
            self._record_success()
            return await hooks.after_execute(
                agent=self, task=task, result=result, status="completed",
                duration_ms=int((monotonic() - started) * 1000), config=cfg)
        except Exception as exc:
            diagnosis = self.diagnose(exc)
            heal_result = await self.heal(diagnosis)
            if heal_result.success:
                try:
                    result = await self.execute(task, **kwargs)
                    self._record_success()
                    return await hooks.after_execute(
                        agent=self, task=task, result=result, status="completed",
                        duration_ms=int((monotonic() - started) * 1000),
                        config=cfg, retry_attempt=1)
                except Exception as retry_exc:
                    self._record_failure()
                    fail = {"success": False, "error": str(retry_exc),
                            "heal_attempted": True, "escalation_needed": True,
                            "error_type": type(retry_exc).__name__}
                    return await hooks.after_execute(
                        agent=self, task=task, result=fail, status="failed",
                        duration_ms=int((monotonic() - started) * 1000),
                        config=cfg, retry_attempt=1)
            self._record_failure()
            fail = {"success": False, "error": str(exc), "heal_attempted": True,
                    "heal_history": [{"success": h.success, "message": h.message}
                                     for h in heal_result.history],
                    "escalation_needed": heal_result.escalation_needed,
                    "error_type": type(exc).__name__}
            return await hooks.after_execute(
                agent=self, task=task, result=fail, status="failed",
                duration_ms=int((monotonic() - started) * 1000), config=cfg)
```

> The `from agents.quality import hooks` import is inside the method to avoid an import cycle at module load (`agents.quality.hooks` imports nothing from `agents.core.base`, but the lazy import is defensive and cheap).

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_execute_safe_hook.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Run the broader base-agent tests to confirm no regression**

Run: `python -m pytest tests/ -k "core_agent or execute_safe or self_heal" -v`
Expected: PASS (existing behavior preserved)

- [ ] **Step 6: Commit**

```bash
git add agents/core/base.py tests/quality/test_execute_safe_hook.py
git commit -m "feat(quality): wire after_execute hook into execute_safe (success + failure)"
```

---

## Task 9: Detection rules — static (dead agent, retry storm, conversation cost, TTL, tool-failure)

**Files:**
- Create: `agents/quality/detection_rules.py`
- Test: `tests/quality/test_detection_static.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/quality/test_detection_static.py
from agents.quality.config import ObserverConfig
from agents.quality.contracts import AgentMetrics, Severity
from agents.quality import detection_rules as dr


def _m(**kw):
    base = dict(execution_id="e", agent_name="a", status="completed",
                duration_ms=10, conversation_id="c1", cost_usd=0.0)
    base.update(kw); return AgentMetrics(**base)


def test_retry_storm_fires_at_threshold():
    cfg = ObserverConfig(retry_storm_count=5)
    fails = [_m(status="failed", agent_name="a") for _ in range(5)]
    alerts = dr.retry_storm(fails, cfg)
    assert len(alerts) == 1 and alerts[0].kind == "retry_storm"
    assert alerts[0].severity == Severity.PAGE


def test_retry_storm_quiet_below_threshold():
    cfg = ObserverConfig(retry_storm_count=5)
    assert dr.retry_storm([_m(status="failed") for _ in range(4)], cfg) == []


def test_conversation_cost_ceiling():
    cfg = ObserverConfig(per_conversation_cost_ceiling_usd=5.0)
    totals = {"c1": 6.5, "c2": 1.0}
    alerts = dr.conversation_cost(totals, cfg)
    assert len(alerts) == 1
    assert alerts[0].conversation_id == "c1" and alerts[0].kind == "conversation_cost"


def test_dead_agent_when_expected_agent_silent():
    cfg = ObserverConfig()
    alerts = dr.dead_agents(recent=[_m(agent_name="a")], expected={"a", "b"}, cfg=cfg)
    assert [x.agent_name for x in alerts] == ["b"]
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_detection_static.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the static rules (pure functions)**

```python
# agents/quality/detection_rules.py
"""Detection rules: pure functions over metrics. No DB, no I/O — unit-testable.

Each returns a list[AgentAlert]. Static rules need no warm-up; trend rules
(Task 10) are gated by the caller during the warm-up window.
"""
from __future__ import annotations

from collections import defaultdict

from agents.quality.config import ObserverConfig
from agents.quality.contracts import AgentAlert, AgentMetrics, Severity


def retry_storm(recent: list[AgentMetrics], cfg: ObserverConfig) -> list[AgentAlert]:
    """≥ N failures for one agent within the window the `recent` list represents."""
    fails: dict[str, int] = defaultdict(int)
    for m in recent:
        if m.status == "failed":
            fails[m.agent_name] += 1
    out = []
    for agent, n in fails.items():
        if n >= cfg.retry_storm_count:
            out.append(AgentAlert(
                severity=Severity.PAGE, kind="retry_storm", agent_name=agent,
                evidence={"failures": n, "window_s": cfg.retry_storm_window_s},
                recommendation=f"Inspect {agent}'s dependency; consider circuit-break."))
    return out


def conversation_cost(totals: dict[str, float], cfg: ObserverConfig) -> list[AgentAlert]:
    """Per-conversation cumulative cost over ceiling — the $47K-loop guard."""
    out = []
    for conv, total in totals.items():
        if total > cfg.per_conversation_cost_ceiling_usd:
            out.append(AgentAlert(
                severity=Severity.PAGE, kind="conversation_cost", agent_name="(conversation)",
                conversation_id=conv,
                evidence={"cost_usd": round(total, 4),
                          "ceiling_usd": cfg.per_conversation_cost_ceiling_usd},
                recommendation=f"Conversation {conv} exceeded cost ceiling — likely a loop; "
                               f"recommend terminating it."))
    return out


def dead_agents(recent: list[AgentMetrics], expected: set[str],
                cfg: ObserverConfig) -> list[AgentAlert]:
    """Expected agents with zero executions in the window."""
    seen = {m.agent_name for m in recent}
    return [AgentAlert(severity=Severity.TICKET, kind="dead_agent", agent_name=a,
                       evidence={"window_s": cfg.dead_agent_window_s},
                       recommendation=f"{a} produced no executions in window; check liveness.")
            for a in sorted(expected - seen)]


def tool_failure_rate(recent: list[AgentMetrics], cfg: ObserverConfig) -> list[AgentAlert]:
    """Per-agent failure ratio over threshold."""
    by_agent: dict[str, list[AgentMetrics]] = defaultdict(list)
    for m in recent:
        by_agent[m.agent_name].append(m)
    out = []
    for agent, rows in by_agent.items():
        if len(rows) < 5:  # need minimum volume to compute a meaningful rate
            continue
        rate = sum(1 for r in rows if r.status == "failed") / len(rows)
        if rate > cfg.tool_failure_rate:
            out.append(AgentAlert(
                severity=Severity.TICKET, kind="tool_failure_rate", agent_name=agent,
                evidence={"rate": round(rate, 3), "n": len(rows)},
                recommendation=f"{agent} failure rate {rate:.0%} > {cfg.tool_failure_rate:.0%}."))
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_detection_static.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/quality/detection_rules.py tests/quality/test_detection_static.py
git commit -m "feat(quality): static detection rules incl. per-conversation cost guard"
```

---

## Task 10: Detection rules — trend (token spike EWMA, latency p95)

**Files:**
- Modify: `agents/quality/detection_rules.py`
- Test: `tests/quality/test_detection_trend.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/quality/test_detection_trend.py
from agents.quality.config import ObserverConfig
from agents.quality.contracts import AgentMetrics
from agents.quality import detection_rules as dr


def _m(tokens, dur=10, agent="a"):
    return AgentMetrics(execution_id="e", agent_name=agent, status="completed",
                        duration_ms=dur, conversation_id="c", input_tokens=tokens,
                        output_tokens=0, cost_usd=0.0)


def test_token_spike_fires_above_multiplier():
    cfg = ObserverConfig(token_spike_multiplier=3.0)
    baseline = [_m(100) for _ in range(10)]
    spike = _m(500)  # 5x baseline
    alerts = dr.token_spike(recent=baseline + [spike], baseline_ewma=100.0, cfg=cfg)
    assert any(x.kind == "token_spike" for x in alerts)


def test_token_spike_quiet_within_band():
    cfg = ObserverConfig(token_spike_multiplier=3.0)
    alerts = dr.token_spike(recent=[_m(120)], baseline_ewma=100.0, cfg=cfg)
    assert alerts == []


def test_latency_p95_over_bound():
    cfg = ObserverConfig(latency_p95_bound_ms=100)
    rows = [_m(10, dur=d) for d in [10, 20, 30, 40, 50, 60, 70, 80, 90, 500]]
    alerts = dr.latency_regression(rows, cfg)
    assert any(x.kind == "latency_regression" for x in alerts)


def test_ewma_helper():
    assert dr.ewma([100, 100, 100], alpha=0.3) == 100.0
    assert dr.ewma([], alpha=0.3) is None
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_detection_trend.py -v`
Expected: FAIL with `AttributeError: module ... has no attribute 'token_spike'`

- [ ] **Step 3: Append the trend rules + EWMA + percentile helpers**

```python
# append to agents/quality/detection_rules.py

def ewma(values: list[float], alpha: float = 0.3) -> float | None:
    """Exponentially weighted moving average. None on empty input."""
    if not values:
        return None
    acc = values[0]
    for v in values[1:]:
        acc = alpha * v + (1 - alpha) * acc
    return acc


def _percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * pct
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def token_spike(recent: list[AgentMetrics], baseline_ewma: float | None,
                cfg: ObserverConfig) -> list[AgentAlert]:
    """Latest total-token usage > multiplier × baseline EWMA. Warm-up gated by caller
    (baseline_ewma is None during warm-up → no alert)."""
    if baseline_ewma is None or baseline_ewma <= 0 or not recent:
        return []
    latest = recent[-1].total_tokens
    ratio = latest / baseline_ewma
    if ratio < cfg.token_spike_multiplier:
        return []
    sev = (Severity.PAGE if ratio >= cfg.token_spike_circuit_multiplier else Severity.TICKET)
    rec = (f"{recent[-1].agent_name} token usage {ratio:.1f}× baseline."
           + (" Recommend circuit-break." if sev == Severity.PAGE else ""))
    return [AgentAlert(severity=sev, kind="token_spike", agent_name=recent[-1].agent_name,
                       evidence={"latest_tokens": latest, "baseline": round(baseline_ewma, 1),
                                 "ratio": round(ratio, 2)}, recommendation=rec)]


def latency_regression(recent: list[AgentMetrics], cfg: ObserverConfig) -> list[AgentAlert]:
    """p95 duration over the static SLO bound. (MWMBR burn-rate layering = phase 2.)"""
    durs = sorted(float(m.duration_ms) for m in recent if m.duration_ms is not None)
    if len(durs) < 5:
        return []
    p95 = _percentile(durs, 0.95)
    if p95 <= cfg.latency_p95_bound_ms:
        return []
    return [AgentAlert(severity=Severity.TICKET, kind="latency_regression",
                       agent_name="(fleet)",
                       evidence={"p95_ms": round(p95), "bound_ms": cfg.latency_p95_bound_ms},
                       recommendation=f"p95 latency {round(p95)}ms over "
                                      f"{cfg.latency_p95_bound_ms}ms bound.")]
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_detection_trend.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/quality/detection_rules.py tests/quality/test_detection_trend.py
git commit -m "feat(quality): trend detection (token-spike EWMA, latency p95)"
```

---

## Task 11: AlertSink with hysteresis

**Files:**
- Create: `agents/quality/alerts.py`
- Test: `tests/quality/test_alerts.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/quality/test_alerts.py
from agents.quality.alerts import AlertSink
from agents.quality.contracts import AgentAlert, Severity


async def test_emits_once_then_suppresses_until_cleared(monkeypatch):
    import agents.quality.alerts as a
    published = []
    async def _pub(ev): published.append(ev)
    monkeypatch.setattr(a.event_bus, "publish", _pub)

    sink = AlertSink()
    alert = AgentAlert(severity=Severity.PAGE, kind="retry_storm", agent_name="x")
    await sink.emit([alert])
    await sink.emit([alert])                  # same open condition → suppressed
    assert len(published) == 1
    assert len(sink.active()) == 1

    sink.clear(alert.key())                    # condition resolved
    await sink.emit([alert])                    # may fire again
    assert len(published) == 2
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_alerts.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the sink**

```python
# agents/quality/alerts.py
"""Alert emission with hysteresis: fire once per open condition, expose active set
for an API endpoint, publish to the EventBus. Never auto-acts."""
from __future__ import annotations

import logging

from core.events.event_bus import event_bus

from agents.quality.contracts import AgentAlert

logger = logging.getLogger(__name__)


class AlertSink:
    def __init__(self) -> None:
        self._active: dict[str, AgentAlert] = {}

    async def emit(self, alerts: list[AgentAlert]) -> None:
        for alert in alerts:
            k = alert.key()
            if k in self._active:                 # already open → suppress (hysteresis)
                continue
            self._active[k] = alert
            logger.warning("AGENT ALERT [%s] %s: %s", alert.severity.name, alert.kind,
                           alert.recommendation)
            try:
                await event_bus.publish(alert)
            except Exception:
                logger.exception("alert publish failed (non-fatal)")

    def clear(self, key: str) -> None:
        self._active.pop(key, None)

    def active(self) -> list[AgentAlert]:
        return list(self._active.values())
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_alerts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agents/quality/alerts.py tests/quality/test_alerts.py
git commit -m "feat(quality): AlertSink with hysteresis + EventBus publish"
```

---

## Task 12: Observer — orchestrates scan + warm-up gating + EventBus subscription

**Files:**
- Create: `agents/quality/observer.py`
- Test: `tests/quality/test_observer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/quality/test_observer.py
import time

from agents.quality.config import ObserverConfig
from agents.quality.contracts import AgentMetrics
from agents.quality.observer import Observer
from agents.quality.repository import InMemoryMetricsRepository


def _m(**kw):
    base = dict(execution_id="e", agent_name="a", status="completed",
                duration_ms=10, conversation_id="c1", cost_usd=0.0)
    base.update(kw); return AgentMetrics(**base)


async def test_scan_fires_static_rules_even_during_warmup():
    repo = InMemoryMetricsRepository()
    for _ in range(6):
        await repo.save(_m(status="failed"))
    obs = Observer(repo=repo, cfg=ObserverConfig(enabled=True, retry_storm_count=5),
                   expected_agents={"a"}, started_monotonic=time.monotonic())
    alerts = await obs.scan()
    kinds = {a.kind for a in alerts}
    assert "retry_storm" in kinds              # static rule fires day-zero
    assert "token_spike" not in kinds          # trend rule dormant during warm-up


async def test_scan_enables_trend_rules_after_warmup():
    repo = InMemoryMetricsRepository()
    for _ in range(12):
        await repo.save(_m(input_tokens=100, output_tokens=0))
    await repo.save(_m(input_tokens=600, output_tokens=0))   # spike
    warmed_start = time.monotonic() - (15 * 86400)           # 15 days ago > 14d warm-up
    obs = Observer(repo=repo, cfg=ObserverConfig(enabled=True), expected_agents=set(),
                   started_monotonic=warmed_start)
    alerts = await obs.scan()
    assert any(a.kind == "token_spike" for a in alerts)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_observer.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the Observer**

```python
# agents/quality/observer.py
"""The observability agent: scheduled scan + EventBus subscription. Alert+recommend only."""
from __future__ import annotations

import logging
import time

from agents.quality import detection_rules as dr
from agents.quality.alerts import AlertSink
from agents.quality.config import ObserverConfig
from agents.quality.contracts import AgentExecEvent
from agents.quality.repository import MetricsRepository

logger = logging.getLogger(__name__)


class Observer:
    def __init__(self, repo: MetricsRepository, cfg: ObserverConfig,
                 expected_agents: set[str], started_monotonic: float | None = None,
                 sink: AlertSink | None = None) -> None:
        self._repo = repo
        self._cfg = cfg
        self._expected = expected_agents
        self._started = started_monotonic if started_monotonic is not None else time.monotonic()
        self._sink = sink or AlertSink()

    def _warmed_up(self) -> bool:
        return (time.monotonic() - self._started) >= self._cfg.warmup_days * 86400

    async def scan(self) -> list:
        """Run all rules over recent metrics. Returns the alerts produced this scan."""
        cfg = self._cfg
        window = max(cfg.retry_storm_window_s, cfg.dead_agent_window_s,
                     cfg.tool_failure_window_s, 3600)
        recent = await self._repo.recent(window_s=window)
        alerts = []
        # static rules — always
        alerts += dr.retry_storm(recent, cfg)
        alerts += dr.dead_agents(recent, self._expected, cfg)
        alerts += dr.tool_failure_rate(recent, cfg)
        alerts += dr.conversation_cost(
            await self._repo.conversation_cost_totals(window_s=window), cfg)
        # trend rules — only after warm-up
        if self._warmed_up():
            tokens = [m.total_tokens for m in recent if m.total_tokens]
            baseline = dr.ewma([float(t) for t in tokens[:-1]]) if len(tokens) > 1 else None
            alerts += dr.token_spike(recent, baseline, cfg)
            alerts += dr.latency_regression(recent, cfg)
        else:
            logger.info("Observer warm-up: trend rules dormant (%d/%d days)",
                        int((time.monotonic() - self._started) / 86400), cfg.warmup_days)
        await self._sink.emit(alerts)
        return alerts

    async def on_event(self, event) -> None:
        """Real-time EventBus handler. Reacts to failures for fast retry-storm detection."""
        if isinstance(event, AgentExecEvent) and event.status == "failed":
            recent = await self._repo.recent(window_s=self._cfg.retry_storm_window_s)
            await self._sink.emit(dr.retry_storm(recent, self._cfg))

    def active_alerts(self) -> list:
        return self._sink.active()
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_observer.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/quality/observer.py tests/quality/test_observer.py
git commit -m "feat(quality): Observer scan + warm-up gating + event handler"
```

---

## Task 13: Startup wiring — repo factory, EventBus subscribe, scan loop

**Files:**
- Create: `agents/quality/startup.py`
- Test: `tests/quality/test_startup.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/quality/test_startup.py
from agents.quality.config import ObserverConfig
from agents.quality.repository import InMemoryMetricsRepository
from agents.quality import startup, hooks
from core.events.event_bus import event_bus


def test_install_sets_repo_factory_and_subscribes(monkeypatch):
    before = len(event_bus._handlers)
    repo = InMemoryMetricsRepository()
    obs = startup.install_observability(
        cfg=ObserverConfig(enabled=True), repo=repo, expected_agents={"a"})
    assert hooks._repo_factory() is repo            # hook now writes to our repo
    assert len(event_bus._handlers) == before + 1   # observer subscribed
    assert obs.active_alerts() == []
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/quality/test_startup.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement the installer**

```python
# agents/quality/startup.py
"""Install observability at app startup: point the hook at a repo, subscribe the
Observer to the EventBus, and (in production) launch the periodic scan loop.

Call install_observability(...) from the FastAPI lifespan in main_enterprise.py.
"""
from __future__ import annotations

import asyncio
import logging

from agents.quality import hooks
from agents.quality.config import ObserverConfig
from agents.quality.observer import Observer
from agents.quality.repository import MetricsRepository
from core.events.event_bus import event_bus

logger = logging.getLogger(__name__)


def install_observability(cfg: ObserverConfig, repo: MetricsRepository,
                          expected_agents: set[str]) -> Observer:
    """Wire the hook + subscribe the observer. Returns the Observer (for the API/scan loop)."""
    hooks._repo_factory = lambda: repo
    observer = Observer(repo=repo, cfg=cfg, expected_agents=expected_agents)
    event_bus.subscribe(observer.on_event)
    logger.info("Observability installed (enabled=%s)", cfg.enabled)
    return observer


async def run_scan_loop(observer: Observer, cfg: ObserverConfig) -> None:
    """Background task: periodic scan. Launch via asyncio.create_task in lifespan."""
    while True:
        try:
            await observer.scan()
        except Exception:
            logger.exception("observer scan failed (non-fatal)")
        await asyncio.sleep(cfg.scan_interval_s)
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/quality/test_startup.py -v`
Expected: PASS

- [ ] **Step 5: Wire into the app lifespan**

In `main_enterprise.py`, find the FastAPI lifespan/startup. Add (production repo built from a session — confirm the session-acquisition pattern matches `database/db.py:db_manager`):

```python
# in the lifespan startup block of main_enterprise.py
from agents.quality.config import ObserverConfig
from agents.quality.repository import SqlMetricsRepository
from agents.quality.startup import install_observability, run_scan_loop
from database.db import db_manager

_obs_cfg = ObserverConfig(enabled=bool(os.getenv("OBSERVABILITY_ENABLED")))
if _obs_cfg.enabled:
    # SqlMetricsRepository takes a session; build a short-lived repo per write via a factory.
    def _repo_factory():
        # db_manager.session() is an async context manager; SqlMetricsRepository
        # is constructed per-write inside after_execute. Provide a session-bound repo.
        ...  # confirm exact per-write session handling here (open question O1)
    observer = install_observability(_obs_cfg, repo=_repo_factory(), expected_agents=set())
    app.state.observer = observer
    app.state.observer_task = asyncio.create_task(run_scan_loop(observer, _obs_cfg))
```

> **Open question O1 (resolve here):** `after_execute` calls `repo.save()` once per execution, but `SqlMetricsRepository` holds a single `AsyncSession`. Production needs a fresh session per write. Decide between: (a) `_repo_factory` opens `async with db_manager.session()` per call and returns a session-bound repo, or (b) `SqlMetricsRepository.save()` internally opens its own `db_manager.session()`. Option (b) keeps `after_execute` simple — recommended. If you pick (b), refactor `SqlMetricsRepository.__init__` to take no session and open one inside each method.

- [ ] **Step 6: Commit**

```bash
git add agents/quality/startup.py tests/quality/test_startup.py main_enterprise.py
git commit -m "feat(quality): startup wiring (hook repo, event subscribe, scan loop)"
```

---

## Task 14: Alerts API endpoint

**Files:**
- Create: `api/v1/observability.py` (or follow the existing router pattern in `api/v1/`)
- Test: `tests/quality/test_observability_api.py`

- [ ] **Step 1: Confirm the router registration pattern**

Read one existing router in `api/v1/` and how it's included in `main_enterprise.py` (`app.include_router(...)`). Match it.

- [ ] **Step 2: Write the failing test**

```python
# tests/quality/test_observability_api.py
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from agents.quality.alerts import AlertSink
from agents.quality.contracts import AgentAlert, Severity
from api.v1.observability import build_router


async def test_alerts_endpoint_returns_active():
    sink = AlertSink()
    await sink.emit([AgentAlert(severity=Severity.PAGE, kind="retry_storm", agent_name="x",
                                recommendation="check x")])
    app = FastAPI(); app.include_router(build_router(lambda: sink.active()))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/api/v1/observability/alerts")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1 and body["alerts"][0]["kind"] == "retry_storm"
```

- [ ] **Step 3: Run to verify it fails**

Run: `python -m pytest tests/quality/test_observability_api.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 4: Implement the router**

```python
# api/v1/observability.py
"""Read-only observability API: surface active alerts for the dashboard."""
from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter

from agents.quality.contracts import AgentAlert


def build_router(get_active: Callable[[], list[AgentAlert]]) -> APIRouter:
    router = APIRouter(prefix="/api/v1/observability", tags=["observability"])

    @router.get("/alerts")
    async def alerts() -> dict:
        active = get_active()
        return {"count": len(active),
                "alerts": [{"severity": a.severity.name, "kind": a.kind,
                            "agent_name": a.agent_name, "conversation_id": a.conversation_id,
                            "evidence": a.evidence, "recommendation": a.recommendation}
                           for a in active]}
    return router
```

- [ ] **Step 5: Run to verify it passes**

Run: `python -m pytest tests/quality/test_observability_api.py -v`
Expected: PASS

- [ ] **Step 6: Register the router in `main_enterprise.py`**

```python
from api.v1.observability import build_router as build_observability_router
# after the observer is created in lifespan / app setup:
app.include_router(build_observability_router(lambda: app.state.observer.active_alerts()))
```

- [ ] **Step 7: Commit**

```bash
git add api/v1/observability.py tests/quality/test_observability_api.py main_enterprise.py
git commit -m "feat(api): read-only observability alerts endpoint"
```

---

## Task 15: End-to-end integration test + docs

**Files:**
- Create: `tests/quality/test_observability_e2e.py`
- Modify: `.wolf/anatomy.md`, `docs/model-routing.md` (or a new `docs/observability.md`)

- [ ] **Step 1: Write the end-to-end test (fake repo, real hook + observer + sink)**

```python
# tests/quality/test_observability_e2e.py
from agents.core.base import CoreAgent, CoreAgentType
from agents.quality.config import ObserverConfig
from agents.quality.repository import InMemoryMetricsRepository
from agents.quality.startup import install_observability


class _Agent(CoreAgent):
    core_type = CoreAgentType.OPERATIONS
    name = "loop_agent"
    def __init__(self):
        super().__init__(correlation_id="conv-loop")
    async def execute(self, task, **kw):
        from agents.quality.hooks import usage_envelope
        return {"ok": True, "_usage": usage_envelope(
            provider="anthropic", model="claude-sonnet-4-6",
            input_tokens=200000, output_tokens=50000, finish_reason="stop")}


async def test_runaway_conversation_triggers_cost_alert():
    repo = InMemoryMetricsRepository()
    observer = install_observability(
        ObserverConfig(enabled=True, per_conversation_cost_ceiling_usd=1.0),
        repo=repo, expected_agents=set())
    agent = _Agent()
    for _ in range(3):                      # 3 expensive calls in one conversation
        await agent.execute_safe("do work")
    alerts = await observer.scan()
    assert any(a.kind == "conversation_cost" and a.conversation_id == "conv-loop"
               for a in alerts)
```

- [ ] **Step 2: Run to verify it passes (full chain wired)**

Run: `python -m pytest tests/quality/test_observability_e2e.py -v`
Expected: PASS — proves: hook fires from `execute_safe` → row saved with cost → scan detects the per-conversation runaway.

- [ ] **Step 3: Run the whole quality suite + lint the footprint**

Run: `python -m pytest tests/quality/ -v && ruff check agents/quality api/v1/observability.py && black --check agents/quality`
Expected: all PASS / clean.

- [ ] **Step 4: Update `.wolf/anatomy.md`**

Add entries for each new file in `agents/quality/` (one line + token estimate each) and note the `execute_safe` hook + migration 004.

- [ ] **Step 5: Commit**

```bash
git add tests/quality/test_observability_e2e.py .wolf/anatomy.md docs/
git commit -m "test(quality): observability e2e (runaway-conversation cost alert) + docs"
```

---

## Self-review notes (run before execution)

- **Spec coverage:** instrument-write (Tasks 5–8), OTel field names (Task 5), cost from reused pricing (Task 2), EventBus + scheduled scan (Tasks 12–13), all v1 detection rules incl. per-conversation cost (Tasks 9–10), warm-up gating (Task 12), alert+recommend + hysteresis + severity tiers (Tasks 11–12), API surface (Task 14). Score-drift rule depends on the evaluator → lives in Plan 2.
- **Deferred (named in spec):** SuperAgent-tier, OTel span emission, duplicate-tool-call hash, context-growth, MWMBR burn-rate layering — all phase 2.
- **Open question O1** (per-write session) resolved inline in Task 13.
- **Type consistency:** `AgentMetrics`, `AgentExecEvent`, `AgentAlert`, `Severity`, `ObserverConfig` field/method names are identical across Tasks 1, 4, 7, 9–14.
