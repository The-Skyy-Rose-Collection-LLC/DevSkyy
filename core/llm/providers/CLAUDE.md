# core/llm/providers/ — Backward-compat re-export shim for legacy `llm/providers/`

Migration facade. Forwards the six provider clients from their canonical home at `llm/providers/*` under the newer `core/llm/` namespace so older imports keep working while consumers cut over. No provider logic lives here.

## Key files

- `__init__.py` — Re-exports `AnthropicClient`, `CohereClient`, `GoogleClient`, `GroqClient`, `MistralClient`, `OpenAIClient` from `llm.providers.{anthropic,cohere,google,groq,mistral,openai}`. The entire surface of this directory.

## Conventions

- New code imports from `llm.providers.<vendor>` directly. The shim exists for migration, not for new dependencies.
- When a provider gains capabilities (new model class, new auth path), update `llm/providers/<vendor>.py` and let the shim forward automatically — do not duplicate.
- The shim is acceptable to import in legacy paths under audit; treat any *new* import of `core.llm.providers` as a code-review flag.

## Don't

- Don't add provider implementation logic in this directory. Logic lives in `llm/providers/<vendor>.py`.
- Don't add a new vendor here. New vendors land under `llm/providers/`, then the shim picks them up via an explicit re-export line.
- Don't deprecate the shim before confirming downstream cutover. A grep for `from core.llm.providers` must return zero hits first.
- Don't import from this shim in `core/`, `services/`, or `agents/` greenfield code — those should target `llm.providers.*` directly.

## Related

- `llm/providers/` — canonical home for the six vendor clients
- `core/llm/CLAUDE.md` — parent hexagonal layer; declares the shim role
- `core/llm/services/CLAUDE.md` — sibling shim for `router`, `round_table`, `ab_testing`
- `core/CLAUDE.md` — grandparent foundation layer
