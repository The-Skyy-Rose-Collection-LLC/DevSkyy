# monitoring/ — DevSkyy MCP observability stack

Prometheus + Grafana monitoring for all MCP servers, tools, and Elite Studio pipeline health. Includes an AB comparison runner, a stream processor, and a metrics server that exposes the `/metrics` endpoint scraped by Prometheus.

## Key files

- `metrics_server.py` — FastAPI server exposing `/metrics` (Prometheus format) and `/health`. Import `prometheus_metrics.py` — do not instantiate a second `Counter`/`Gauge` here.
- `prometheus_metrics.py` — All Prometheus metric definitions (`Counter`, `Gauge`, `Histogram`, `Summary`). Single source of truth for metric names. Import and call `record_*` helpers from other modules; never define metrics elsewhere.
- `ab_comparison.py` — A/B test harness for comparing model outputs: records latency, cost, and quality score per variant. Outputs to `grafana/elite_studio_dashboard.json` for visualization.
- `elite_studio_metrics.py` — Elite Studio-specific business metrics: render success rate, FASHN tryon cost-per-session, Tripo generation latency. Consumed by `prometheus_metrics.py`.
- `stream_processor.py` — Streams log events from the MCP message bus into Prometheus counters. Runs as a background task alongside the MCP server.
- `grafana/devskyy_dashboard.json` — DevSkyy system-level Grafana dashboard (API latency, error rates, agent invocations).
- `grafana/elite_studio_dashboard.json` — Elite Studio pipeline Grafana dashboard (render stages, cost, quality scores).

## Conventions

- All metric names use the `devskyy_` prefix — never bare names (avoids collision with Prometheus defaults).
- Add new metrics only to `prometheus_metrics.py` — import the metric object wherever you need to record it.
- Grafana dashboard JSON is source-controlled; export from Grafana UI → replace the JSON file → commit. Don't hand-edit the JSON.
- `ab_comparison.py` writes results to a CSV in `renders/output/ab/` (gitignored) — never to a database.

## Don't

- Don't define `Counter`/`Gauge`/`Histogram` outside `prometheus_metrics.py` — duplicate metric names crash the Prometheus client.
- Don't call `metrics_server.py` endpoints in production request paths — they are observability-only, not business logic.
- Don't commit Grafana dashboard JSON with hardcoded `localhost` datasource UIDs — use the templated variable `${DS_PROMETHEUS}`.

## Related

- `core/events.py` — event bus that `stream_processor.py` subscribes to
- `api/v1/health.py` — production health endpoint (separate from the metrics server's `/health`)
- `skyyrose/elite_studio/` — primary source of Elite Studio metrics events
