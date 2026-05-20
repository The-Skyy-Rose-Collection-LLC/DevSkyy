# agents/llm_roundtable/ — TypeScript LLM competition arena

**TypeScript** Round Table implementation — separate runtime from the Python `llm/round_table.py`. Multi-model battles, Elo ratings, technique A/B testing. Distributed as `@devskyy/llm-roundtable` npm package (v1.0.0).

## Why two Round Tables?

Per cmem #478 (2026-04-15) and #5160 (2026-05-15) — there are multiple Round Table implementations in the codebase. Canonical map:

| Implementation | Path | Use when |
|----------------|------|----------|
| **TS Round Table (this)** | `agents/llm_roundtable/` | Web frontend, browser/Node Round Table runs, MCP server context |
| Python text Round Table | `llm/round_table.py` + `llm/round_table_metrics.py` | Python agent backend, Neon-persisted, Prometheus metrics |
| 3D Round Table | `orchestration/threed_round_table.py` | Multi-judge 3D quality vote (different from text Round Table) |
| RoundTableInterface | `agents/base_super_agent/round_table_module.py` | Bridge from SuperAgents into the Python Round Table |

This directory is the **TypeScript** path — separate codebase, separate dependencies, separate package.

## Files

```
agents/llm_roundtable/
├── package.json           @devskyy/llm-roundtable v1.0.0 — type: module
├── tsconfig.json          TS compiler config
├── index.ts               Public API — re-exports engine + adaptive surface
├── engine.ts              roundtableServer — main competition engine
├── adapter.ts (adaptive.ts)  Adaptive learning: routing weights, Elo, circuit breakers
├── agent.ts               Agent definition for SDK integration
├── schemas.ts             Zod schemas for input/output validation
├── utils.ts               Helpers
└── ui/                    Browser UI for live Round Table viewing — see ui/CLAUDE.md
```

## Public API (from `index.ts`)

```typescript
// Engine entry
import { roundtableServer } from "@devskyy/llm-roundtable"

// Adaptive layer — learning + routing
import {
  recordLearning,
  updateRoutingWeights,
  getLearnedRoute,
  isModelDisabled,
  recordFailure,
  recordSuccess,
  getFallbackModel,
  withRetry,
  isAnomalousScore,
  isTechniqueUnderperforming,
  checkEloHealth,
  getHealthReport,
  getRecentCorrections,
} from "@devskyy/llm-roundtable"

// Types
import type {
  LearningRecord,
  RoutingWeight,
  CircuitBreaker,
  CorrectionRecord,
} from "@devskyy/llm-roundtable"
```

## Dependencies (`package.json`)

```json
{
  "@anthropic-ai/claude-agent-sdk": "^0.1.72",
  "@anthropic-ai/sdk": "^0.52.0",
  "zod": "^3.24.0"
}
```

Built with `tsx` (dev) and `tsc` (build). Module type `"module"` (ESM only — `.js` imports use the `.js` extension even when importing `.ts` source per ESM resolution rules).

## Commands

```bash
cd agents/llm_roundtable
npm install
npm run battle      # tsx engine.ts — live competition
npm run agent       # tsx agent.ts — SDK-integrated agent
npm run build       # tsc — compile to .js
npm run typecheck   # tsc --noEmit
```

## Adaptive learning surface

The `adaptive.ts` module provides:

- **`recordLearning(record)`** — every Round Table outcome → routing weight update
- **`updateRoutingWeights()`** — recompute weights from accumulated records
- **`getLearnedRoute(task)`** — recommend model for a task type
- **`isModelDisabled(model)`** — circuit-breaker check
- **`recordFailure(model, error)` / `recordSuccess(model)`** — feed the circuit breaker
- **`getFallbackModel(primary)`** — return next-best when primary is disabled
- **`withRetry(fn, opts)`** — exponential backoff wrapper
- **`isAnomalousScore(score, ...)`** — outlier detection (e.g. judge unanimous 1.0 vs typical 0.85)
- **`isTechniqueUnderperforming(technique, ...)`** — prompt technique A/B health check
- **`checkEloHealth()`** — Elo rating sanity check across models
- **`getHealthReport()`** — aggregate dashboard health export
- **`getRecentCorrections(window)`** — operator corrections feed for proposal review

## Conventions

- **TypeScript strict mode + Zod for validation.** `LearningRecord`, `RoutingWeight`, `CircuitBreaker`, `CorrectionRecord` are exported types — use them across the boundary.
- **Imports use `.js` extension even for `.ts` files** — ESM resolution requires it. Don't omit the extension.
- **No `any`.** Use `unknown` + narrowing for untrusted input.
- **Errors via narrowing.** `error instanceof Error ? error.message : 'Unexpected error'` — never `any`.
- **Brand context per project memory.** When this Round Table generates brand-facing copy, pull from `SKYYROSE_BRAND_DNA` (Python side) via the MCP boundary; TS-side does not duplicate the brand canon.

## Don't

- Don't duplicate this in Python or vice versa. The boundary is intentional — TS for browser/Node UI surfaces, Python for backend agents. Cross-language → MCP message bus, not parallel code.
- Don't bypass the adaptive layer for "manual" routing decisions. Adaptive weights are the production routing surface; manual overrides go through `recordLearning` so the system learns.
- Don't add a fourth Round Table implementation. There are already too many (cmem #5160). Add features to one of the existing ones.
- Don't import `@anthropic-ai/sdk` directly elsewhere in this dir — use `@anthropic-ai/claude-agent-sdk` so tool use + thinking are wired consistently.
- Don't run `npm install` outside this dir. The `node_modules/` here is local — there's no monorepo-shared install.

## Related

- Sibling Python Round Table: `llm/round_table.py`
- 3D Round Table (separate concern): `orchestration/threed_round_table.py`
- Live UI: `agents/llm_roundtable/ui/`
- MCP boundary for cross-language: agents/wordpress_bridge/ pattern (analogous, Python side)
- Brand canon source: `knowledge-base/seed/from-interview.md`, `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`

## Recent learnings

- Four parallel Round Table implementations exist (cmem #478, 2026-04-15) — TS, Python text, Python 3D, SuperAgent bridge.
- Stays in TypeScript intentionally — browser UI consumers + Node-based MCP scenarios need a native TS path.
- Adaptive learning surface is comprehensive — Elo, circuit breakers, anomaly detection, technique A/B, fallback selection — don't reinvent on the Python side; bridge via MCP if needed.
