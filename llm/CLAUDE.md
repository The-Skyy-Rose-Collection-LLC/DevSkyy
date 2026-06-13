# llm/ — Unified LLM Client Library

Canonical multi-provider LLM abstraction. Provider-agnostic `Message`/`CompletionResponse`, async clients, router with fallback, competitive evaluation (Round Table), classification helpers.

## Surface (from `__init__.py`)

| Symbol | File | Role |
|--------|------|------|
| `Message`, `MessageRole` | `base.py` | Unified chat message; class constructors `Message.system/user/assistant/tool` |
| `ToolCall`, `CallerInfo`, `CallerType` | `base.py` | PTC (Programmatic Tool Calling) — distinguishes direct vs code-execution tool calls |
| `ContainerInfo` | `base.py` | Code execution container reuse metadata |
| `CompletionResponse`, `StreamChunk` | `base.py` | Provider-agnostic response + streaming chunk |
| `BaseLLMClient` | `base.py` | Abstract async client (httpx + retry + error classification) |
| `ModelProvider` | `base.py` | Enum: `openai/anthropic/google/mistral/cohere/groq/deepseek/litellm` (8 providers) |
| `LLMRouter`, `RoutingStrategy`, `PROVIDER_CONFIGS` | `router.py` | Multi-provider router w/ fallback + cost awareness |
| `LLMRoundTable`, `RoundTableResult`, `RoundTableDatabase`, `ResponseScorer` | `round_table.py` | Tournament/A-B competition across all providers, Neon-persisted |
| `GroqFastClassifier`, `classify_intent`, `analyze_sentiment`, `detect_language` | `classification.py` | Cheap Groq-backed classification |
| `LLMError` + subclasses | `exceptions.py` | Typed error hierarchy w/ `provider`, `model`, `details` |
| Provider clients (`OpenAIClient`, `AnthropicClient`, `GoogleClient`, `MistralClient`, `CohereClient`, `GroqClient`) | `providers/` | Per-vendor async clients |

## Layout

```
llm/
├── base.py              Message, CompletionResponse, BaseLLMClient (abstract)
├── exceptions.py        LLMError hierarchy (auth/rate/quota/context/...)
├── router.py            LLMRouter + PROVIDER_CONFIGS (priority + price/1k)
├── model_ids.py         Single source of truth for model ID strings
├── unified_llm_client.py  High-level wrapper composing router + scoring
├── round_table.py       LLMRoundTable competition (4-metric scoring → A/B → judge)
├── round_table_metrics.py  Prometheus exposition for round table
├── ab_testing.py        Pairwise A/B winner selection
├── tournament.py        Bracket-style elimination scoring
├── adaptive_learning.py AdaptiveLearningEngine — weight updates from outcomes
├── creative_judge.py    LLM-as-judge scoring rubric (61k file — largest)
├── classification.py    Groq-backed fast classifiers
├── task_classifier.py   Route incoming task → recommended provider
├── evaluation_metrics.py Heuristic scoring (relevance, coherence, ...)
├── statistics.py        StatisticalAnalyzer (significance tests)
├── verification.py      Cross-provider claim verification
└── providers/
    ├── openai.py, anthropic.py, google.py, mistral.py, cohere.py, groq.py
    ├── deepseek.py, litellm_provider.py
    ├── replicate.py, stability.py, vertex_imagen.py   (image gen)
```

## Provider Priority + Pricing (router.py `PROVIDER_CONFIGS`)

Lower number = higher routing priority. Price = USD per 1K tokens.

| Provider | Priority | Default model | Input $/1K | Output $/1K |
|----------|---------:|---------------|-----------:|------------:|
| DeepSeek | 0 | deepseek-chat | 0.00014 | 0.00028 |
| Anthropic | 1 | claude-sonnet-4-20250514 | 0.003 | 0.015 |
| OpenAI | 2 | gpt-4o-mini | 0.00015 | 0.0006 |
| Google | 3 | gemini-2.0-flash | 0.000075 | 0.0003 |
| Mistral | 4 | mistral-small-latest | 0.001 | 0.003 |
| Groq | 5 | llama-3.3-70b-versatile | 0.00059 | 0.00079 |
| Cohere | 6 | command-r-08-2024 | 0.0005 | 0.0015 |

> **Model strings drift.** `PROVIDER_CONFIGS` default models are independent of `model_ids.py` — when rolling forward, update both. The canonical pipeline-role constants (`COMPOSITOR_CLAUDE_MODEL`, `GENERATION_MODEL`, `QC_MODEL`, etc.) live in `model_ids.py`.

## Canonical Pipeline Roles (`model_ids.py`)

These aliases express **intent**, not concrete models. Callers import the alias; rolls forward by editing the constant.

- **Reasoning / text-out** → `CLAUDE_OPUS_MODEL` (`claude-opus-4-7`)
- **Coding subagent / cost-efficient** → `CLAUDE_SONNET_MODEL` (`claude-sonnet-4-6`)
- **Fast classification** → `CLAUDE_HAIKU_MODEL` (`claude-haiku-4-5`)
- **Vision (read image, output text)** → `OPENAI_VISION_MODEL` (`gpt-4o`) + `GEMINI_PRO_MODEL` (`gemini-3-pro-preview`). **Never Claude — vision is a Claude weakness; dual-judge runs OpenAI + Gemini.**
- **Image generation** → `NANO_BANANA_2_MODEL` (`gemini-3.1-flash-image-preview`) + `OPENAI_IMAGE_2_MODEL` (`gpt-image-2`)
- **Security / code review** → `SECURITY_AUDIT_MODEL`, `CODE_REVIEW_MODEL` (both Sonnet until Glasswing access)

`CLAUDE_MYTHOS_PREVIEW_MODEL` is invitation-only via Anthropic's Project Glasswing — 404s without enrollment. Do not alias any pipeline role to it.

## Round Table (`round_table.py`)

Tournament where every provider competes on every task.

1. All providers generate in parallel (async fan-out).
2. Each response scored on 4 metrics (60% heuristic: relevance/coherence/specificity/safety, 40% LLM-judge).
3. Top 2 → pairwise A/B → judge model picks winner.
4. Result persisted to Neon PostgreSQL via `RoundTableDatabase`.
5. `AdaptiveLearningEngine` updates provider weights based on outcomes.

Use for **high-stakes** outputs (creative judging, brand-critical copy). Cost-prohibitive for hot-path traffic.

## Conventions

- **Async-only.** All public client methods are async coroutines or async iterators.
- **Context manager:** providers implement `__aenter__/__aexit__` — prefer `async with` to ensure httpx client closes.
- **Retry policy:** `BaseLLMClient._make_request()` retries on 429 + 5xx with exponential backoff `[1, 2, 4]`. Auth (401) and 4xx-other are not retried.
- **Errors typed:** all failures raise `LLMError` subclasses with `provider` and `model` fields populated.
- **Cost tracking:** `CompletionResponse.get_cost_estimate(input_price_per_1k, output_price_per_1k)` — pull prices from `PROVIDER_CONFIGS`.
- **No model strings in callers.** Import from `llm.model_ids` — never hardcode `"claude-opus-4-7"` inline.

## Don't

- Don't import provider-specific SDKs in agent code. Use `llm.providers.<X>Client` so swapping providers is one line.
- Don't reimplement retry / rate-limit handling — `BaseLLMClient._make_request` already does it.
- Don't add a new provider without entering it in `PROVIDER_CONFIGS` + extending `ModelProvider` enum + adding the client subclass under `providers/`.
- Don't import `round_table` at module top-level in lightweight code paths — it pulls `scipy` via `statistics.py`. Lazy-import where the heavy deps aren't needed.
- Don't conflate `orchestration/llm_clients.py` with `llm/providers/`. The orchestration shim is the older codepath kept for back-compat; new code uses `llm.providers`.

## Related

- Pipeline roles consumed by: `skyyrose/elite_studio/`, `agents/`, `services/`
- Routing strategy used by: `orchestration/llm_orchestrator.py` (older orchestration shim)
- Database persistence: Neon PostgreSQL (`DATABASE_URL`)
- Prometheus metrics: `round_table_metrics.py` exposes counters + histograms

## Recent learnings

- `llm/__init__.py` eagerly imports `round_table` → forces `scipy` on any submodule import. If you only need `Message`, import from `llm.base` directly to avoid the dep pull.
- Vision-policy migration (2026-05-04): `VISION_CLAUDE_MODEL` + `QC_CLAUDE_MODEL` removed from `model_ids.py`. Do not reintroduce.
- LiteLLM gateway support landed 2026-05-14 — provider count is **8**, not 6 as older docs claim.


