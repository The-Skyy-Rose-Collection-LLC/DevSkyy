# Programmatic Tool Calling (PTC) — Full-Platform Integration Spec

- **Date:** 2026-07-12
- **Status:** Design approved (brainstorm) → pending written-spec review → writing-plans
- **Author:** DevSkyy engineering agent (with founder Corey Foster)
- **Scope:** Complete DevSkyy's partially-built PTC integration into a full-platform capability: a central driver, the ~80-tool MCP surface exposed under a **controlled-autonomy gate**, a rollout flag, and an eval harness.

---

## 1. Problem / Goal

PTC collapses multi-tool / batch workflows from N round-trips into ~1: the model writes code once that calls `allowed_callers`-marked tools inside Anthropic's code-execution sandbox; only the *final* result returns to context, not each intermediate payload.

DevSkyy has the **entire PTC kit built and unit-tested but unwired** — `core/runtime/code_execution_tool.py` defines `CODE_EXECUTION_TOOL` and **nothing imports it**. Goal: plug it in, platform-wide, with a safety model that fits this project's money/production constraints.

---

## 2. Current state (verified 2026-07-12)

| Layer | State | Evidence |
|---|---|---|
| PTC data models | ✅ built + tested | `llm/base.py` — `CallerType.CODE_EXECUTION="code_execution_20250825"`, `CallerInfo`, container/response models; `tests/test_ptc_models.py` |
| Provider support | ✅ built + tested | `llm/providers/anthropic.py` — beta header `advanced-tool-use-2025-11-20`, container reuse, caller/container parsing; `tests/test_anthropic_ptc.py` |
| Tool registry | ✅ `allowed_callers` field + serialization | `core/runtime/tool_registry.py`; `tests/test_tool_registry.py` |
| Server tool spec | ✅ defined, ❌ **unimported** | `core/runtime/code_execution_tool.py` `CODE_EXECUTION_TOOL` — 0 production importers |
| Tool marks | ⚠️ partial + risky | `tools/commerce_tools.py` — batch WC **write** create/update marked PTC (631/686 — production writes, see §3), read-only auto-PTC (727) |
| MCP constant | ✅ | `mcp_tools/server.py:55` `PTC_CALLER` |
| **End-to-end driver** | ❌ **MISSING** | nothing assembles `CODE_EXECUTION_TOOL` + marked tools, calls the provider, and loops on `code_execution` result blocks |

**The gap is the cheap part** (a driver); the hard parts (container/caller parsing, beta header) are done.

---

## 3. Governing policy — the Controlled-Autonomy Gate

**Founder decision 2026-07-12:** the absolute STOP-AND-SHOW gate is *softened for the PTC context only* — some paid/production tool calls MAY run autonomously inside a PTC run, under strict rules enforced at the container gate. This is a deliberate amendment to `CLAUDE.md`'s STOP-AND-SHOW; it applies **only** to tool calls made from inside a PTC sandbox run, never to normal operation.

**Why the container gate is the enforcement point:** the sandbox runs the model's code but holds no DevSkyy credentials — it only *emits* tool-call requests that the driver (§4) fulfills. Every call funnels through one DevSkyy chokepoint. The model cannot bypass it.

**The strict rules (all enforced in the driver's tool-fulfillment step):**

1. **Per-run spend budget.** Each PTC run carries a hard USD ceiling (reuse the `scripts/oai_render/cost.py` `SpendTracker` pattern). Paid tool calls decrement it; reaching the ceiling **aborts the run** — never overspends. **Default: $25 / run** (founder-set 2026-07-12); raise later per surface.
2. **Per-tool policy** (a registry field extending `ToolSpec`):
   ```
   ptc: { autonomy: "auto" | "gated" | "forbidden",
          cost_cap_usd: float | null,      # per-call ceiling for "auto" paid tools
          dry_run_required: bool,
          rate_limit_per_run: int | null }
   ```
   - **read-only / idempotent / non-paid** → `auto`.
   - **bounded paid** (e.g. a single render under its `cost_cap_usd`) → `auto`, capped per call AND by the run budget.
   - **high blast radius** (deploy, bulk production writes, media upload) → `gated` (driver denies + returns `requires_approval`; the call is never executed inside the run, it's surfaced for a separate gated step) or `forbidden` (never code-callable).
3. **Escalate, never silently proceed.** A call over budget / over `cost_cap_usd` / not `auto` → the driver **denies** it and returns a structured `requires_approval` result to the sandbox; the model surfaces it and the run continues without that call. It never executes past a limit. (A live mid-run human pause is possible but **deferred** — it risks the container timing out; deny-and-surface is the P1 mechanism.)
4. **Audit every autonomous paid/write call** — tool name, args hash, cost, cumulative run spend, run id — to an audit sink. A PTC run's spend is fully reconstructable after the fact.
5. **Guard test (CI):** assert no `forbidden` tool ever carries a `code_execution` caller, and every paid tool with `autonomy:"auto"` has a non-null `cost_cap_usd`. Mis-marking a mutating/paid tool is a test failure, not a production incident.

**🔴 Reconcile:** `commerce_tools.py` currently marks batch WC **write** create/update as PTC. Under this policy those are `gated` (or route through a dry-run/staging variant), not silent `auto`. P3 fixes this.

---

## 4. Central driver (`llm/unified_llm_client.py`)

The founder chose the central seam. Add a PTC path to the unified client:

1. **Eligibility:** request carries ≥1 tool with a `code_execution` caller AND the rollout flag (§6) is on for this surface.
2. **Assemble:** inject `CODE_EXECUTION_TOOL`, set the beta header (already wired in the provider), call `provider.complete()`.
3. **Loop:** while the response contains `code_execution`/sandbox tool-call requests — fulfill each **through the Controlled-Autonomy Gate (§3)**, reuse the `container_id`, feed results back — until `stop_reason == end_turn`.
4. **Return:** final `LLMResponse` + PTC metadata (container id, run spend, round-trips saved, tokens saved vs a classic-tool-use estimate).

Isolated + testable: the gate is a pure function `(tool_call, run_budget, policy) -> allow | deny | escalate` so its rules unit-test without a live API.

---

## 5. MCP-surface exposure (`mcp_tools/tools/*`)

Data-driven `ptc` policy (§3) on the ~80 tools, held in one **policy registry** (not scattered literals). `tool_registry` already serializes `allowed_callers`, so external MCP clients (Claude Code) that do their own PTC benefit too — the marks are the single source of truth for both the internal driver and external callers.

**Founder decision 2026-07-12:** the full registry (every tool tagged `auto` / `gated` / `forbidden` + `cost_cap_usd`) is **drafted for founder tool-by-tool review; NO tool goes `auto` until explicitly approved.** Until then every paid/mutating tool defaults to `gated`.

---

## 6. Rollout flag

Env/config gate, **global + per-surface**, default **off**. Enables dark-launch: build, measure, then turn on per surface once the eval (§7) validates savings and the gate holds.

---

## 7. Eval harness

Per representative workflow, run **PTC vs classic tool-use** and report: input/output tokens, round-trips, latency, **correctness (identical result)**, and USD spend. Also asserts the gate held (no over-budget breach, all paid calls audited). Gemini/Claude-class judge for correctness where output isn't byte-exact. Gate rollout on this.

---

## 8. Version currency

DevSkyy uses `code_execution_20250825` + beta `advanced-tool-use-2025-11-20`. Context7 confirms the SDK now exposes `code_execution_20260120` / `20260521`. **Founder decision 2026-07-12: upgrade to `code_execution_20260521` in P1.** Because a mismatched tool-version ↔ beta-header pairing means the response blocks won't parse, P1 **first verifies the exact `20260521` header string against Anthropic docs (Context7/live)** — do not hardcode a guessed beta-header — then upgrades `llm/base.py`, `anthropic.py`, and the tests together.

---

## 9. Phasing

- **P1 — Foundation:** verify + **upgrade to `code_execution_20260521`** (§8) → driver + Controlled-Autonomy Gate (§3, §4) with the **$25/run** budget → policy registry seed → wire **read-only + one bounded-paid** tool → integration test (E2E loop + gate-denies-over-budget + savings measured). Ships NO silent write/deploy autonomy.
- **P2 — Breadth:** `ptc` policy across the ~80 MCP tools (§5) + the eval harness (§7) + the CI guard test (§3.5).
- **P3 — Rollout:** flag (§6) → dark-launch → measure → enable per surface; reconcile the `commerce_tools` write marks (§3) to `gated`/dry-run; add the STOP-AND-SHOW PTC-carve-out clause to `CLAUDE.md`.

---

## 10. Success criteria / verification

- [ ] Driver runs a real PTC loop E2E; a read-only + bounded-paid workflow completes in ~1 turn, container reused.
- [ ] **Gate proven:** an over-budget / over-cap / non-`auto` call is denied or escalated, never executed; audit records every paid call with cumulative spend.
- [ ] Eval shows token + round-trip savings vs classic tool-use, correctness preserved.
- [ ] CI guard test green (no `forbidden` tool code-callable; every `auto` paid tool has a cost cap).
- [ ] Flag defaults off; enabling is per-surface and reversible.

---

## 11. Risks

- **Softened money/production gate** — the core risk. Mitigated by: run budget hard-cap, per-tool `cost_cap_usd`, escalate-never-silent, full audit, CI guard test. The gate is airtight because DevSkyy fulfills every sandbox call.
- **Sandbox tool-auth:** creds live in the driver, not the sandbox; the sandbox only emits requests. Scope creds to the run's policy.
- **Container lifecycle / leaks:** reuse `container_id` within a run; expire per Anthropic's `expires_at`.
- **Mis-marking a tool** (paid/mutating as `auto`): the CI guard test is the backstop.

---

## 12. Decisions (founder, 2026-07-12) + remaining

Resolved at spec review:
1. **Run budget:** **$25 / run** hard cap (§3.1).
2. **Version:** **upgrade to `code_execution_20260521`** in P1, header verified first (§8).
3. **Allowlist:** founder reviews **tool-by-tool** — I draft the full ~80-tool policy registry (`auto`/`gated`/`forbidden` + `cost_cap_usd`); nothing goes `auto` until approved; paid/mutating defaults to `gated` until then (§5).

Remaining (produced during the plan, for founder sign-off before P2 enablement):
- The **drafted policy registry** itself (per-tool tags + caps).
- Per-tool `cost_cap_usd` values for whichever paid tools the founder promotes to `auto`.
