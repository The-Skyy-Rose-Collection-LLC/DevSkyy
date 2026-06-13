# core/llm/domain/ — LLM Domain Layer

**Implementation-free domain layer.** Models (Pydantic DTOs) and ports (ABCs) only. No provider SDK imports, no I/O, no business logic.

## Public Surface (`core/llm/domain/__init__.py`)

| Symbol | Kind | Source |
|--------|------|--------|
| `Message`, `MessageRole` | DTO + Enum | `models.py` |
| `ModelProvider` | Enum | `models.py` |
| `CompletionResponse`, `StreamChunk`, `ToolCall` | DTOs | `models.py` |
| `LLMRequest`, `LLMResponse`, `LLMCapabilities` (31 fields) | Pydantic | `models.py` |
| `ILLMProvider` | ABC — `complete`, `stream`, `connect`, `close` + 5 more | `ports.py` |
| `ILLMRouter` | ABC | `ports.py` |
| `IProviderFactory` | ABC | `ports.py` |

## Hard Rules

- **No SDK imports here.** Domain layer cannot depend on `anthropic`, `openai`, `google.genai`, etc. Those live in `llm/providers/*`
- Models are Pydantic v2 — use `model_config = ConfigDict(frozen=True)` for immutable DTOs
- Adding a new port: write the ABC here, implement in `core/llm/infrastructure/` or `llm/providers/*`
- `LLMCapabilities` has 31 fields — when adding a capability, update all 6 provider implementations or the factory will misroute requests
- `ILLMProvider.complete()` is the canonical sync-completion contract. `stream()` returns `AsyncIterator[StreamChunk]`

## Consumers

- `core/llm/infrastructure/provider_factory.py` — depends on `ILLMProvider`, `IProviderFactory`
- `agents/llm_roundtable/*` — typed against `ILLMProvider` for swappability
- Tests — mock `ILLMProvider` for unit tests of consumers


