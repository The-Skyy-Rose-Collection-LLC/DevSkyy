# core/telemetry/ — OpenTelemetry tracer with NoOp fallback

Boots the OpenTelemetry tracer provider at process startup and hands out tracer instances at module-import time. Falls through to a NoOp implementation when the OTel SDK is absent or `OTEL_ENABLED` is off, so consumers can call `tracer.start_as_current_span(...)` unconditionally.

## Key files

- `tracer.py` — `init_telemetry(service_name)`: boots a `TracerProvider`. Uses the OTLP exporter when `OTEL_EXPORTER_OTLP_ENDPOINT` is set, otherwise `ConsoleSpanExporter`. `get_tracer(name)`: returns the OTel `Tracer` or `_NoOpTracer`. `_NoOpTracer` and `_NoOpSpan` are import-time fallbacks used when the OTel SDK is not installed or telemetry is disabled.
- `__init__.py` — Re-exports `init_telemetry` and `get_tracer`. The full public surface.

## Conventions

- `init_telemetry()` runs exactly once at process startup. The boot site is `main_enterprise.py:66`. A second call would overwrite the global `TracerProvider` and silently drop in-flight spans.
- Consumers call `get_tracer(__name__)` at module import time and bind it to a module-level `_tracer` (see `llm/router.py:38`, `core/events/event_store.py:39`, `skyyrose/elite_studio/gemini_rest.py:17`).
- Span usage is the standard OTel context manager: `with tracer.start_as_current_span("name"):`. The NoOp fallback supports the same call shape so consumer code never branches on telemetry availability.
- Env vars: `OTEL_ENABLED` (off by default), `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `ENVIRONMENT`. All read inside `init_telemetry` — no module-level env reads.

## Don't

- Don't call `init_telemetry()` more than once per process. The TracerProvider is a global.
- Don't import OTel SDK types in consumer code. Always go through `get_tracer` so the NoOp fallback stays seamless when the SDK is absent.
- Don't enable OTLP without confirming the collector endpoint is reachable. A misconfigured exporter blocks span flushes on shutdown.
- Don't add module-level env reads here. All env-var lookups happen inside `init_telemetry` so process-startup ordering is controllable.

## Related

- `core/CLAUDE.md` — parent foundation layer; `telemetry/` is row tier-2 in the public surface table
- `main_enterprise.py:66` — boot site for `init_telemetry`
- `llm/router.py`, `core/events/event_store.py`, `skyyrose/elite_studio/gemini_rest.py` — current consumers binding module-level tracers
- `tests/unit/test_telemetry.py` — full coverage including NoOp fallback paths
