# core/llm/services/ — Backward-compat re-export shim for legacy `llm/` services

Migration facade. Forwards `router`, `round_table`, and `ab_testing` modules from the canonical `llm/` package under the newer `core/llm/` namespace. No service logic lives here.

## Key files

- `__init__.py` — Re-exports `router` (task-based LLM routing), `round_table` (multi-LLM competition / synthesis), `ab_testing` (statistical A/B harness) from the top-level `llm/` package. The entire surface of this directory.

## Conventions

- New code imports `from llm import router` (or `round_table` / `ab_testing`) directly. The shim exists only to keep the older `core.llm.services` import path alive.
- Service additions happen in `llm/<module>.py`. The shim auto-forwards; do not duplicate behavior here.
- Pair with `core/llm/providers/` — the two shims form a coherent migration surface for the `core/llm/` namespace.

## Don't

- Don't extend service logic in this directory. Behavior belongs in `llm/<module>.py`.
- Don't add new modules to the shim — new service-tier modules go under `llm/`, then get a single re-export line here only if legacy callers need them.
- Don't import this shim path from greenfield code in `core/`, `services/`, `orchestration/`, or `agents/`. Target `llm/` directly.
- Don't remove the shim before grep confirms zero `from core.llm.services` imports remain.

## Related

- `llm/` — canonical home for `router`, `round_table`, `ab_testing`
- `core/llm/CLAUDE.md` — parent hexagonal layer; declares the shim role
- `core/llm/providers/CLAUDE.md` — sibling shim for the six vendor clients
- `core/CLAUDE.md` — grandparent foundation layer
