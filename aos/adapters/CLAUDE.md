# aos/adapters/ — Duck-typed wrappers around existing SuperAgents

Non-invasive bridge between the AOS kernel and pre-existing `EnhancedSuperAgent` classes. The adapter never imports `agents/` — it relies entirely on structural typing so the agents directory and the AOS directory stay independently importable.

## Key files

- `superagent_adapter.py` — `SuperAgentAdapter`: wraps any object that exposes `.agent_type`, `.execute()`, and optionally `._heal_journal`, `._consecutive_failures`, `._circuit_state`. Reads heal-journal entries via duck-typing so the kernel can surface circuit-breaker state without `agents/` knowing AOS exists. Also exports `HealJournalEntry` and `AdapterRun`.

## Conventions

- No imports from `agents/`. The adapter contract is pure structural typing — any object meeting the shape works. This is what lets `agents/` boot without AOS and vice versa.
- One adapter per wrapping target. To support a new wrapped type (e.g., ClaudeSDK), add a sibling file (`claude_sdk_adapter.py`) — don't extend `SuperAgentAdapter`.
- Adapters are stateless. They read mutable state (`._heal_journal`, `._consecutive_failures`, `._circuit_state`) from the wrapped agent on every call rather than caching.
- Optional attributes use `getattr(agent, "_heal_journal", default)` — never assume presence.

## Don't

- Don't `from agents import ...` here. The import-graph isolation is load-bearing — breaking it creates a cycle through `aos/kernel/` and re-couples the two subtrees.
- Don't store wrapped-agent state on the adapter instance. State lives on the agent; the adapter is a view.
- Don't bypass the adapter from kernel code. Even when the kernel has direct reference to an `EnhancedSuperAgent`, it must call through `SuperAgentAdapter` so heal-journal observation stays uniform.
- Don't extend `SuperAgentAdapter` with type-specific branches. A new wrapped type means a new sibling adapter.

## Related

- `aos/kernel/` — wraps agents through `SuperAgentAdapter` at spawn time
- `agents/enhanced_base.py` — the duck-typed contract target (read by adapter, never imported)
- `aos/healing/circuit_breaker.py` — reads `_circuit_state` / `_consecutive_failures` surfaced by this adapter
- `aos/CLAUDE.md` — parent kernel doc
