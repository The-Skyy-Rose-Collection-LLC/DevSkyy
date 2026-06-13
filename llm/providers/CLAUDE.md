# llm/providers/ — Per-vendor async LLM clients

Concrete `BaseLLMClient` subclasses, one per vendor. Each implements `_get_headers()`, `complete()`, `stream()` against vendor REST API via `httpx.AsyncClient`.

## Surface (from `__init__.py`)

| Client | File | Vendor API | Default model |
|--------|------|-----------|---------------|
| `OpenAIClient` | `openai.py` | `api.openai.com/v1` | gpt-4o-mini |
| `AnthropicClient` | `anthropic.py` | `api.anthropic.com/v1` | claude-sonnet-4-20250514 |
| `GoogleClient` | `google.py` | `generativelanguage.googleapis.com` | gemini-2.0-flash |
| `MistralClient` | `mistral.py` | `api.mistral.ai/v1` | mistral-small-latest |
| `CohereClient` | `cohere.py` | `api.cohere.com/v1` | command-r-08-2024 |
| `GroqClient` | `groq.py` | `api.groq.com/openai/v1` | llama-3.3-70b-versatile |
| `DeepSeekClient` | `deepseek.py` | `api.deepseek.com/v1` | deepseek-chat |
| `LiteLLMProvider` | `litellm_provider.py` | LiteLLM gateway (multi-vendor) | provider-specified |
| `StabilityClient` | `stability.py` | Stability AI REST | SDXL/SD3/Core/Ultra |
| `VertexImagenClient` | `vertex_imagen.py` | GCP Vertex AI | Imagen 3 |
| `ReplicateClient` | `replicate.py` | `api.replicate.com` | varies per model |

## Subclass contract

Each provider client MUST implement:

```python
class FooClient(BaseLLMClient):
    provider = "foo"               # ModelProvider enum value
    default_model = "foo-flagship"

    def _get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def complete(self, messages: list[Message], model=None, **kw) -> CompletionResponse:
        ...

    async def stream(self, messages, model=None, **kw) -> AsyncIterator[StreamChunk]:
        ...
```

`BaseLLMClient` provides: httpx lifecycle (`connect/close`), `_make_request` (retry + error classification), `_messages_to_list` (Message → dict), `_calculate_latency`.

## Conventions

- **API keys via env vars only.** Never accept `api_key` in agent calls. Pull from `os.environ` in the client `__init__` or accept `None` and default to env lookup.
  - `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` / `MISTRAL_API_KEY` / `COHERE_API_KEY` / `GROQ_API_KEY` / `DEEPSEEK_API_KEY`
- **Map vendor errors to `LLMError` subclasses.** Don't re-raise raw `httpx.HTTPStatusError`. The base `_make_request` handles 401/429/5xx; provider-specific 400-class errors map to `InvalidRequestError` / `ContentFilterError` / `ContextLengthError`.
- **Token usage in `CompletionResponse`.** Vendor responses ship token counts in different fields — normalize to `input_tokens` / `output_tokens` / `total_tokens`. Don't leave at 0.
- **Tool calling shape.** Each vendor's tool format differs; serialize to `CompletionResponse.tool_calls: list[ToolCall]` using the unified shape.
- **Streaming:** yield `StreamChunk(delta_content=..., index=N)` per server-sent event. Final chunk sets `finish_reason`.

## Don't

- Don't synchronously call vendor SDK constructors at module import. Lazy-init the SDK inside `complete()` or `__init__`. Avoids forcing every consumer to install all vendor packages.
- Don't hardcode model strings. Caller supplies `model` parameter; default to `self.default_model` (pulled from `PROVIDER_CONFIGS` in the router).
- Don't bypass `_make_request` for the main completion call. Helpers can use raw httpx, but the primary call MUST go through the retry/error-classification pipeline.
- Don't add a new provider without adding it to:
  1. `ModelProvider` enum in `llm/base.py`
  2. `PROVIDER_CONFIGS` dict in `llm/router.py` (priority + pricing)
  3. `llm/providers/__init__.py` re-export
  4. Per-provider tests under `tests/llm/providers/`

## Image-gen providers

`StabilityClient`, `VertexImagenClient`, `ReplicateClient` don't fit the text-completion `Message → CompletionResponse` shape. They expose their own typed methods (`generate_image()`, `inpaint()`, etc.). Kept in `providers/` for API-key + retry-policy consistency, not because they inherit `BaseLLMClient`.

## Related

- Base contract: `llm/base.py` `BaseLLMClient`
- Routing: `llm/router.py` — composes these clients
- Errors: `llm/exceptions.py` `LLMError` hierarchy
- Model IDs: `llm/model_ids.py` — single source of truth


