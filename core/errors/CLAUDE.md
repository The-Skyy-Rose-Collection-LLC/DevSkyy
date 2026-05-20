# core/errors/ — Production error taxonomy with correlation IDs

The DevSkyy error hierarchy. One base class, 20 specialized subclasses, severity + error-code enums, correlation-ID propagation, and an HTTP-shaped response builder. Consumed by 18 modules across `services/`, `agents/`, and `pipelines/`.

## Key files

- `production_errors.py` — `DevSkyError` base class. 20 subclasses including `LLMProviderError`, `ToolExecutionError`, `AgentExecutionError`, `ValidationError`, `RAGError`, `ConfigurationError`. `DevSkyErrorSeverity` enum (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). `DevSkyErrorCode` enum (`DEVSKYY-1xxx` through `DEVSKYY-7xxx` — one band per subsystem). `error_handler` decorator wraps service / API entry points. `classify_error(exc)` maps arbitrary exceptions onto the taxonomy. `create_error_response(exc)` returns an `ErrorResponse` Pydantic model safe to ship to clients.
- `__init__.py` — Re-exports the 27 public symbols (base class, 20 subclasses, two enums, four utilities).

## Conventions

- Raise the most specific subclass. `LLMProviderError` for provider failures, `ToolExecutionError` for `core.runtime` failures, `AgentExecutionError` for SuperAgent failures, `ValidationError` at system boundaries.
- Assign a correlation ID at the request boundary and pass it through the error chain via the `correlation_id` constructor arg. Tracing collapses without it.
- Wrap API + service entry points with `@error_handler`. The decorator catches `DevSkyError`, logs with severity, and produces a client-safe response.
- Use `create_error_response(exc)` — never `str(exc)` — when returning errors to HTTP clients. The response model strips internal context and stack frames.
- One `DevSkyErrorCode` value belongs to exactly one subclass. Reuse means correlation logs lie about which subsystem failed.

## Don't

- Don't catch `DevSkyError` to silence it. If a layer can recover, it raises a different subclass; if not, it lets the decorator handle it.
- Don't introduce a new `DevSkyErrorSeverity` above `CRITICAL`. The severity ladder maps to alerting thresholds in `core/telemetry/`; widening breaks the contract.
- Don't reuse a `DevSkyErrorCode` across subclasses. The code is the join key in logs.
- Don't return raw exception messages to clients. Internal context belongs only in server logs.

## Related

- `core/CLAUDE.md` — parent foundation layer; declares `DevSkyError` as the mandatory base for all `core/` failures
- `core/runtime/CLAUDE.md` — raises `ToolExecutionError`
- 18 downstream consumers including `services/analytics/`, `services/ml/`, `services/storage/`, `services/three_d/`, `agents/visual_generation/conversation_editor.py`
- `core/telemetry/` — severity feeds alerting thresholds
