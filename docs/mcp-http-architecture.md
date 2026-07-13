# MCP over HTTP — Architecture

The DevSkyy MCP server (agents, WooCommerce, imagery, RAG, code analysis, and
more — tool count is computed at runtime via `mcp.list_tools()`, never
hand-typed; see `mcp_service.py`'s `/health` `tool_count` field and the
Slim-service pivot rationale section below for the full/slim split) is
exposed over authenticated **streamable HTTP**, live at
`https://devskyy-api.fly.dev/mcp/`. This lets the Next.js dashboard (AI
console) and the skyyrose.co WordPress admin both consume the same tool set
over the network, instead of each client needing local stdio access to the
MCP process.

## Slim-service pivot rationale

The MCP server is served by a **standalone slim FastAPI app**
(`mcp_service.py` + `Dockerfile.mcp`), not by the full `main_enterprise`
router monolith. Per `mcp_service.py`'s own module docstring:

> "Serves ONLY the DevSkyy MCP server over streamable HTTP at `/mcp` —
> without the heavy `main_enterprise` router monolith (no torch / ML
> stack)."

The full `main_enterprise` image is a ~6-10GB torch monolith with a broken
Dockerfile and an unsatisfiable `[all]` extras dependency graph — it cannot
be deployed as-is to a lightweight Fly machine. `Dockerfile.mcp` builds from
a minimal `requirements-mcp.txt` (FastAPI + `mcp` SDK + `httpx` +
`structlog`; no torch, no OpenAI/Anthropic/Google SDKs baked into the image)
so the slim image boots without the ML stack. Tool modules that need an
optional heavy dependency lazy-import it inside their handler; the resilient
loader in `mcp_tools/tools` skips registering a tool module whose optional
dependency is absent on this slim image rather than failing the whole
service — `tools/list` still enumerates every tool, but a tool that proxies
to the full `main_enterprise` backend (not deployed alongside this slim
service) returns a runtime error only if actually invoked.

**Full vs. slim tool count (verified via `mcp.list_tools()`):** the full
backend registers **89** tools. The slim Fly image (`MCP_SLIM_IMAGE=1`, set
in `Dockerfile.mcp`) registers **82** — 2 modules are *deliberately* excluded
there (`oai_render`, `lora_generation`; see
`mcp_tools/tools/__init__.py`'s `SLIM_EXCLUDED_MODULES`) because their heavy
optional deps (`scripts.oai_render`, `imagery.*`) are never shipped to the
slim image. `Dockerfile.mcp` was previously pinned to `python:3.11-slim`
(below this project's `>=3.12` floor per `pyproject.toml`), which caused an
*undeclared* third module — `external_mcp` (17 tools) — to silently drop as
well: `core/errors/production_errors.py` uses PEP-695 generic-function syntax
(`def error_handler[T](`), a `SyntaxError` on Python <3.12, which propagated
past the `except ImportError` handler that only catches declared-missing
modules. That left the slim image at 65 tools instead of 82. Fixed by
bumping the base image to `python:3.12-slim` (matching the main `Dockerfile`)
and copying `core/errors/` (stdlib+pydantic only, safe for the slim image)
alongside the existing slim COPY set.

## Mount and auth

`mcp_tools/http_mount.py` builds the FastMCP streamable-HTTP ASGI app:

- `build_mcp_app()` calls `mcp.streamable_http_app()` (which also
  constructs `mcp.session_manager`), sets `mcp.settings.streamable_http_path
  = "/"` so mounting at `MCP_MOUNT_PATH = "/mcp"` doesn't double the path to
  `/mcp/mcp`, and wraps the result in `BearerAuthMiddleware`.
- **`BearerAuthMiddleware`** (`http_mount.py:47-91`) enforces the shared
  service token from the `MCP_SERVICE_TOKEN` env var. When the token is set,
  every request must carry `Authorization: Bearer <token>` or the middleware
  returns `401` with body
  `{"error":"unauthorized","detail":"MCP requires Authorization: Bearer <MCP_SERVICE_TOKEN>"}`.
  When unset in a non-`development` `ENVIRONMENT`, construction logs a
  `mcp_endpoint_unauthenticated` warning so a reachable-but-open `/mcp`
  cannot ship silently.
- A **host allowlist** (`_DEFAULT_ALLOWED_HOSTS`: `api.devskyy.app`,
  `devskyy-api.fly.dev`, `127.0.0.1`, `localhost`, extendable via
  `MCP_ALLOWED_HOSTS`) is passed into FastMCP's `TransportSecuritySettings`
  to keep DNS-rebinding protection on while allowing the public Fly-proxied
  Host header through — FastMCP otherwise auto-scopes that protection to
  `localhost` and returns `421 Invalid Host header` behind a proxy.

`mcp_service.py` wraps this mount in a standalone FastAPI app with `/health`
and `/ready` liveness/readiness probes (for the Fly health check) and a
`lifespan` that runs `mcp_session_manager().run()` for the app's lifetime.
The mount happens at import time (`app.mount(MCP_MOUNT_PATH,
build_mcp_app())`), before the lifespan starts, because `build_mcp_app()` is
what constructs `mcp.session_manager` in the first place.

## Protocol handshake

Both consumer surfaces implement the same stateful sequence:

1. `initialize` — `protocolVersion: "2025-06-18"`, `capabilities: {}`,
   `clientInfo`. The response carries an `Mcp-Session-Id` header that must
   be captured and replayed on every subsequent request.
2. `notifications/initialized` — a fire-and-forget JSON-RPC notification
   (no `id`, no response body expected), carrying the session id and
   `MCP-Protocol-Version` header.
3. `tools/list` or `tools/call` — carries the session id; the response may
   arrive as plain `application/json` or as an SSE `text/event-stream` with
   `data:`-framed JSON-RPC messages, depending on the `Accept` header
   negotiation.
4. Optional `DELETE` — best-effort session teardown.

This is **stateful** — a session lives in the serving process's memory —
which is why the Fly deployment is pinned to exactly **one always-on
machine** (`fly.toml`: `min_machines_running = 1`, `auto_stop_machines =
false`, comment: "MCP sessions live in process memory — never suspend/stop
mid-session"). Scaling past one machine would break session affinity for any
in-flight handshake.

## Consumer surface 1 — Dashboard (Next.js)

`frontend/app/api/mcp/route.ts` is a NextAuth-session-gated `POST` route
handler (`action: 'list' | 'call'`) that:

- Returns `401` if there is no authenticated dashboard session
  (`getServerSession(authOptions)`), before ever touching the MCP token —
  per the route.ts comment, "the proxy holds `MCP_SERVICE_TOKEN`
  server-side, so an open route would expose the full tool set" (the live
  count is now served at runtime by `/health`'s `tool_count` field — see
  above — rather than hand-typed in a comment).
- Uses the official `@modelcontextprotocol/sdk` `Client` +
  `StreamableHTTPClientTransport`, constructing the transport with the
  Bearer header baked into `requestInit` when `MCP_TOKEN` is set, and races
  the call against a ~20s timeout (matching the WordPress bridge's timeout
  below) since the transport has no native `AbortSignal` hook — see the
  in-code comment in `route.ts` for why.
- Reads `process.env.MCP_URL` and `process.env.MCP_SERVICE_TOKEN`
  server-side only — never sent to the browser, never exposed via
  `NEXT_PUBLIC_*`.
- Wraps MCP client errors as `502` responses to the dashboard frontend.

The UI lives at `frontend/app/admin/mcp/page.tsx` (the AI console that lists
and invokes tools through this proxy).

## Consumer surface 2 — WordPress bridge

`wordpress-theme/skyyrose-flagship/inc/mcp-bridge.php` implements the raw
JSON-RPC/SSE handshake directly against the `/mcp/` endpoint using
`wp_remote_post` / `wp_remote_request`:

- `skyyrose_mcp_request()` runs the full `initialize` ->
  `notifications/initialized` -> `tools/list`|`tools/call` sequence,
  carrying `Mcp-Session-Id` and `MCP-Protocol-Version` headers, and always
  calls `skyyrose_mcp_terminate()` for best-effort teardown regardless of
  outcome.
- `skyyrose_mcp_parse_message()` decodes either a bare JSON body or an SSE
  body (splitting on blank-line-separated events, concatenating each
  event's `data:` lines, and returning the first frame that decodes to a
  JSON-RPC message).
- Every outbound URL is SSRF-guarded via `skyyrose_see_is_safe_url()` before
  any request is sent — an unsafe URL returns a `skyyrose_mcp_unsafe_url`
  `WP_Error` instead of making the request.
- **Config precedence** (`mcp-bridge.php:13-17`):
  - URL: option `skyyrose_mcp_url` > const `SKYYROSE_MCP_URL` > env
    `SKYYROSE_MCP_URL` > default `https://api.devskyy.app/mcp/`.
  - Token: const `SKYYROSE_MCP_TOKEN` > env `MCP_SERVICE_TOKEN` > option
    `skyyrose_mcp_token` — code/env intentionally outrank the database
    option so the secret never has to live in `wp_options` when the host
    can inject it via `wp-config.php` or environment.
- The admin console is registered at **Tools -> DevSkyy MCP**
  (`manage_options` capability required), rendered by
  `skyyrose_mcp_render_admin_page()`, and driven by
  `assets/js/admin-mcp-console.js` — DOM built with `createElement` /
  `textContent` only (no `innerHTML`), relayed through a nonce-gated
  (`check_ajax_referer('skyyrose_mcp', 'nonce')`),
  `manage_options`-gated `wp_ajax_skyyrose_mcp_invoke` AJAX action.

WooCommerce catalog/order reads are already covered by the MCP tool layer
itself (`wc_get_products` / `wc_get_product` / `wc_get_orders` in
`mcp_tools/tools/wc_client.py`) — no redundant WP-side REST client was
built for that purpose.

## Env var matrix (names only — no values)

| Surface | Var | Where set | Notes |
|---|---|---|---|
| Fly backend | `MCP_SERVICE_TOKEN` | `fly secrets set -a devskyy-api` | Gates `BearerAuthMiddleware`; every non-dev environment must set it. |
| Fly backend | `WC_CONSUMER_KEY`, `WC_CONSUMER_SECRET` (aliases: `WOOCOMMERCE_KEY`, `WOOCOMMERCE_SECRET`) | `fly secrets set -a devskyy-api` | Makes the WooCommerce tools callable (`skyyrose/integrations/wc_safe_client.py`). Without these, WC tools still list but raise `KeyError` when invoked. |
| Fly backend (optional) | `MCP_ALLOWED_HOSTS` | `fly secrets set -a devskyy-api` | Comma-separated extension/override of the default DNS-rebinding host allowlist. |
| Dashboard (Vercel) | `MCP_URL`, `MCP_SERVICE_TOKEN` | Vercel Production environment | Server-only — never prefixed `NEXT_PUBLIC_*`, never sent to the browser. |
| WordPress | `SKYYROSE_MCP_URL`, `SKYYROSE_MCP_TOKEN` | `wp-config.php` constant (preferred) or `wp_options` (`skyyrose_mcp_url` / `skyyrose_mcp_token`) via wp-admin | Constants baked into `wp-config.php` need no theme deploy to take effect; changing the PHP bridge code itself does. |

## Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| `401 unauthorized` | Missing or wrong `Authorization: Bearer <token>` header | Confirm the caller sends the exact token configured in `MCP_SERVICE_TOKEN` / `SKYYROSE_MCP_TOKEN`. |
| `421 Invalid Host header` | Request's `Host` header isn't in the DNS-rebinding allowlist | Add the host via `MCP_ALLOWED_HOSTS`, or point traffic at an already-allowlisted host (`api.devskyy.app`, `devskyy-api.fly.dev`). |
| `skyyrose_mcp_no_session` (WP_Error) | `initialize` returned 200 but no `Mcp-Session-Id` response header | Usually a proxy/CDN stripping the header — check for an intermediary between WordPress and Fly. |
| `skyyrose_mcp_bad_response` (WP_Error) | Response body didn't parse as JSON or a valid SSE `data:` frame | Check `Accept` header negotiation and confirm the endpoint is actually the streamable-HTTP mount, not a redirect/error page. |
| `skyyrose_mcp_unsafe_url` (WP_Error) | Configured MCP URL failed `skyyrose_see_is_safe_url()` (SSRF guard) | Fix the configured `skyyrose_mcp_url` / `SKYYROSE_MCP_URL` to a safe, expected host. |
| Tool listed but errors on invoke | Tool proxies to the full `main_enterprise` backend, which isn't deployed alongside this slim service, or a WC credential env var is missing | Expected for backend-proxy tools on the slim deployment; for WC tools, set `WC_CONSUMER_KEY`/`WC_CONSUMER_SECRET`. |
| Dropped in-flight session after a Fly deploy/secrets change | `fly secrets set` restarts the machine; sessions live in process memory only | Re-`initialize` — sessions are not expected to survive a machine restart. |

## Verification

`scripts/verify-mcp-surfaces.sh` is a read-only E2E verifier that exercises
the exact `initialize` -> `notifications/initialized` -> `tools/list`
sequence documented above against a live `/mcp` endpoint, then asserts:

1. `initialize` returns HTTP 200 with a non-empty `Mcp-Session-Id` header.
2. `tools/list` returns at least `MIN_TOOLS` tools (currently 70 — a
   conservative floor below the slim image's verified 82; see
   `scripts/verify-mcp-surfaces.sh`'s inline comment for the derivation).
3. A request with no `Authorization` header returns HTTP 401.

It never calls `tools/call`, so it cannot mutate any state. It is CI-safe:
when `MCP_URL` and `MCP_SERVICE_TOKEN` are not both set in the environment,
it prints a `SKIPPED` message and exits `0` rather than failing a build that
has no live credentials.

## Relationship to `docs/MCP_ARCHITECTURE.md`

`docs/MCP_ARCHITECTURE.md` predates this HTTP mount/pivot and describes
stdio-based clients (Claude Desktop, ChatGPT Desktop) talking to the MCP
server directly. This document is the authoritative reference for the
streamable-HTTP surface described in `tasks/todo.md`'s "MCP over HTTP"
workstream.
