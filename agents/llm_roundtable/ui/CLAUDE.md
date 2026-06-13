# agents/llm_roundtable/ui/ — LLM Round-Table React visualization

React visualization component for the devskyy-dashboard. Shows model roster, ELO leaderboard, and active battles in read-only display. This is NOT the TypeScript consensus engine — that lives in `agents/llm_roundtable/agent.ts`.

## Key files

- `LLMRoundtable.tsx` — `@ts-nocheck` React component. Color constants defined at top of file (not from design tokens — intentionally self-contained). Contains three hardcoded seed arrays: `MODELS` (8 entries: claude-opus-4-7, claude-sonnet-4-6, gpt-4o, gpt-4o-mini, gemini-2.5-pro, gemini-flash, deepseek-r1, llama-405b), `LEADERBOARD` (8 ELO entries), `BATTLES` (active battle slots). Uses React `useState`, `useEffect`, `useRef`, `useCallback`.

## Conventions

- `@ts-nocheck` is intentional — the component uses dynamic data shapes from the round-table engine that aren't fully typed yet. Do not remove it without adding proper types first.
- `MODELS`, `LEADERBOARD`, and `BATTLES` are visualization seed data, not live state — the component renders what the round-table engine reports, it does not fetch or compute results itself.
- This component is consumed by `frontend/` Next.js dashboard — import path resolves through the monorepo workspace alias, not a relative path.
- Color constants at the top of the file (not `var(--skyyrose-*)` tokens) — this component renders in a dashboard context with a different design system than the WP theme.

## Don't

- Don't add LLM API calls, WebSocket connections, or data-fetching logic to this file — it is a pure visualization layer. Actual battle execution runs in `agents/llm_roundtable/agent.ts`.
- Don't import this component from Python code — it is a React/TypeScript asset only. Python access to round-table results goes through `base_super_agent/round_table_module.py`.
- Don't add Klaviyo or WooCommerce side effects — this is display only.

## Related

- `agents/llm_roundtable/agent.ts` — TypeScript `LLMRoundtable` class that runs actual battles
- `agents/llm_roundtable/CLAUDE.md` — full round-table system documentation (engine, adaptive weighting, circuit breaker)
- `frontend/` — Next.js dashboard that imports and renders this component
- `agents/base_super_agent/round_table_module.py` — Python subprocess bridge for battle results
