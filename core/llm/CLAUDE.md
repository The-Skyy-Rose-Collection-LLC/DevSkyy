# core/llm/ — Hexagonal LLM Layer

**Hexagonal-architecture shim over the legacy `llm/` package.** Domain ports + infrastructure factory + provider re-exports. New code MUST consume `core.llm`; old code in `llm/*` is the implementation source of truth being gradually migrated.

## Public Surface (`core/llm/__init__.py`)

| Export Group | Symbols | Source |
|--------------|---------|--------|
| Domain models | `Message`, `MessageRole`, `ModelProvider`, `CompletionResponse`, `StreamChunk`, `ToolCall`, `LLMRequest`, `LLMResponse`, `LLMCapabilities` | `domain/models.py` |
| Domain ports | `ILLMProvider`, `ILLMRouter`, `IProviderFactory` | `domain/ports.py` |
| Infrastructure | `ProviderFactory` | `infrastructure/provider_factory.py` |
| Providers (re-exported) | `AnthropicClient`, `OpenAIClient`, `GoogleClient`, `MistralClient`, `CohereClient`, `GroqClient` | `providers/__init__.py` → `llm/providers/*` |
| Services (re-exported) | `router`, `round_table`, `ab_testing` | `services/__init__.py` → `llm/*` |

## Architecture

```
core/llm/
  domain/         ← ports (ABC) + models (Pydantic) — implementation-free
  infrastructure/ ← ProviderFactory (creates concrete clients)
  providers/      ← thin re-export shim from llm/providers/*
  services/       ← thin re-export shim from llm/ (router, round_table, ab_testing)
```

## Hard Rules

- **New code imports from `core.llm`, NOT `llm.*`** — single source of truth for the hexagonal contract
- Adding a new provider:
  1. Implement `ILLMProvider` (`domain/ports.py`) in `llm/providers/<name>.py`
  2. Add re-export to `core/llm/providers/__init__.py`
  3. Register in `ProviderFactory.create_provider()` (`infrastructure/provider_factory.py`)
- `ProviderFactory.get_or_create_provider(name)` is the **process-level cache** — do not instantiate providers directly
- Six providers wired: Anthropic, OpenAI, Google, Mistral, Cohere, Groq. Adding a 7th requires factory + capabilities update
- **Re-export shims are not empty** — they delegate to `llm/providers/*` and `llm/` modules

## Consumers

- `agents/llm_roundtable/*` — multi-LLM competition via `services/round_table`
- `orchestration/*` — LangGraph nodes consume `ILLMProvider` via DI
- `api/v1/llm` — exposes capabilities + completions through `ProviderFactory`
