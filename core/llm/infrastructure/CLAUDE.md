# core/llm/infrastructure/ — Provider Factory

**Creates and caches LLM provider clients.** The seam between domain ports and concrete SDK implementations.

## Public Surface (`core/llm/infrastructure/__init__.py`)

- `ProviderFactory` — implements `IProviderFactory`:
  - `create_provider(name)` — instantiate fresh
  - `get_or_create_provider(name)` — process-level cache (preferred)
  - `get_capabilities(name)` → `LLMCapabilities`
  - `list_providers()` → six provider slugs

## Hard Rules

- **All provider instantiation MUST go through `ProviderFactory`** — never `AnthropicClient()` directly. The factory:
  - Reads provider config from env vars
  - Caches client instances per process (avoids redundant SDK init)
  - Exposes uniform error handling via `core.errors.LLMProviderError`
- Six providers wired: `anthropic`, `openai`, `google`, `mistral`, `cohere`, `groq`. Adding a 7th requires:
  1. Add `ILLMProvider` impl to `llm/providers/<name>.py`
  2. Re-export from `core/llm/providers/__init__.py`
  3. Add branch in `ProviderFactory.create_provider()`
  4. Declare capabilities in `get_capabilities()`
- Capability reads are cheap (in-memory). Use `get_capabilities()` before routing — never assume a model supports vision/tools/streaming
- Process-level cache means **provider clients survive across requests**. Tests MUST clear the factory or mock at the port level

## Consumers

- `agents/llm_roundtable/*` — pulls all 6 providers for parallel queries
- `orchestration/*` — LangGraph nodes get providers via factory
- `api/v1/llm` — capability listing endpoint


<claude-mem-context>

</claude-mem-context>