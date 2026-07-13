# agents/

Scoped context for the agent fleet (~218 py files). Loads on top of root. The ADK/A2A sub-agent has its
own `agents/devskyy-a2a/CLAUDE.md`.

## Two parallel hierarchies — do NOT conflate

- **Legacy domain SuperAgents:** subclasses of `EnhancedSuperAgent` (`agents/base_super_agent/agent.py`) → `BaseDevSkyyAgent` (`sdk/python/adk/base.py`, local, not pip).
- **New-core CoreAgents + Orchestrator:** subclass `CoreAgent` / `SelfHealingMixin` (`agents/core/base.py`). Wire via `agents/core/factory.py:create_orchestrator()`, which reads `_CORE_AGENT_REGISTRY` (a list of `(module_path, class_name)` tuples) and degrades gracefully on import failure.
- Don't hardcode a fleet count anywhere — the live set is whatever the registry / `grep 'class .*EnhancedSuperAgent'` yields at the time (it grows).

## Hard rules

- **New ORM tables go in `agents/models.py`** — Alembic loads that file DIRECTLY via `importlib` (`alembic/env.py:41`), bypassing the package graph. `database/db.py` (modern `DeclarativeBase`) is a SEPARATE `Base` and is invisible to `alembic autogenerate`. Tables added elsewhere silently never migrate. (`agents/models.py` uses old-style `declarative_base()` by necessity.)
- **MCP tool registration goes through the `ToolRegistry` singleton** — `ToolRegistry.get_instance()` (`core/runtime/tool_registry.py`). Tag every tool with `ToolSeverity` (`READ_ONLY` … `DESTRUCTIVE`); `DESTRUCTIVE` sets `destructiveHint=True` in the schema — the code-layer signal for STOP-AND-SHOW. Pattern: `agents/creative_agent.py:_register_tools()`.
- **`agents/__init__.py` `try/except ImportError` guards are intentional** — each export is individually guarded so a missing optional dep (WordPress, ADK) doesn't block the package. Do NOT refactor to eager imports, or the MCP server fails to start when an optional dep is absent.

## Conventions

- **Provider routing is config-driven, not inline.** `AGENT_PROVIDER_PREFERENCES` / `TASK_PROVIDER_PREFERENCES` (`agents/base_super_agent/types.py`) map agent-type / task → provider order. Round Table auto-activates when quality `< ROUND_TABLE_QUALITY_THRESHOLD (0.8)` or the task is in `HIGH_STAKES_TASK_TYPES`. Route through `LLMRouter` (`llm/router.py`) — don't duplicate routing logic.
- **`agents/base_super_agent/` is a PACKAGE, not a file** (split into `agent.py`, `types.py`, `learning_module.py`, `ml_module.py`, `prompt_module.py`, `round_table_module.py`). Import from `agents.base_super_agent` (or `agents.base_super_agent.types` for types), never a sub-file directly.
