# core/agents/ — Agent Interfaces

**Implementation-free agent contracts.** Three ABCs that every agent in `agents/` (and consumers in `api/`, `orchestration/`) types against.

## Public Surface (`core/agents/__init__.py`)

| Symbol | Methods | Source |
|--------|---------|--------|
| `IAgent` | `execute`, `initialize`, `get_capabilities`, `execute_auto` + 5 more | `interfaces.py` |
| `ISuperAgent` | extends `IAgent` with multi-tool orchestration | `interfaces.py` |
| `IAgentOrchestrator` | manages a fleet of agents (dispatch, lifecycle) | `interfaces.py` |

## Hard Rules

- **All agents implement `IAgent` or `ISuperAgent`** — never define a free-standing agent class without a port
- `agents/base_super_agent/agent.py:EnhancedSuperAgent` is the canonical `ISuperAgent` implementation. Subclass it; do not re-implement the port from scratch
- Agent capabilities are declared via `get_capabilities()` — orchestrator dispatch reads this, lying breaks routing
- This module MUST NOT import from `agents/`, `services/`, `api/`. Pure contract layer

## Consumers

- `agents/base_super_agent/agent.py` — `EnhancedSuperAgent` implements `ISuperAgent`
- `agents/core/**/*` — all domain agents (commerce, marketing, content, creative, operations, web_builder) inherit from `EnhancedSuperAgent`
- `orchestration/*` — LangGraph / CrewAI nodes type against `IAgent` for swappability
- `api/v1/agents` — endpoint surface types against `IAgentOrchestrator`

## Anti-Patterns (Do Not Repeat)

- Do NOT create `agents/base_super_agent.py` as a flat file — the package directory `agents/base_super_agent/` already exists. Python silently ignores the `.py` if the package is present (Cerebrum entry)
