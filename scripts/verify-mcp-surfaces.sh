#!/usr/bin/env bash
# scripts/verify-mcp-surfaces.sh -- Read-only E2E verifier for the DevSkyy MCP
# streamable-HTTP surface (mcp_service.py / mcp_tools/http_mount.py).
#
# Mirrors the request sequence in wordpress-theme/skyyrose-flagship/inc/mcp-bridge.php
# (skyyrose_mcp_request()): initialize -> notifications/initialized -> tools/list,
# carrying Mcp-Session-Id across all three requests. Read-only -- never calls
# tools/call, never mutates anything.
#
# Usage:
#   export MCP_URL=https://devskyy-api.fly.dev/mcp/
#   export MCP_SERVICE_TOKEN=<token>            # never hardcode; from fly secrets / .env
#   bash scripts/verify-mcp-surfaces.sh
#
# CI-safe: if either env var is unset, prints SKIPPED and exits 0.
#
# Asserts:
#   1. initialize returns HTTP 200 with a non-empty Mcp-Session-Id response header.
#   2. tools/list returns >= 40 tools.
#   3. A request to MCP_URL with no Authorization header returns HTTP 401.

set -euo pipefail

MCP_URL="${MCP_URL:-}"
MCP_SERVICE_TOKEN="${MCP_SERVICE_TOKEN:-}"
PROTOCOL_VERSION="2025-06-18"
MIN_TOOLS=40

if [ -z "$MCP_URL" ] || [ -z "$MCP_SERVICE_TOKEN" ]; then
  echo "SKIPPED: MCP_URL and/or MCP_SERVICE_TOKEN not set in environment."
  echo "  Set both to run this verifier against a live /mcp endpoint, e.g.:"
  echo "    export MCP_URL=https://devskyy-api.fly.dev/mcp/"
  echo "    export MCP_SERVICE_TOKEN=<token from fly secrets / .env.wordpress>"
  echo "    bash scripts/verify-mcp-surfaces.sh"
  exit 0
fi

INIT_HEADERS="$(mktemp)"
INIT_BODY="$(mktemp)"
LIST_HEADERS="$(mktemp)"
LIST_BODY="$(mktemp)"
# shellcheck disable=SC2329 # invoked indirectly via `trap cleanup EXIT` below
cleanup() { rm -f "$INIT_HEADERS" "$INIT_BODY" "$LIST_HEADERS" "$LIST_BODY"; }
trap cleanup EXIT

echo "== MCP surface verification: ${MCP_URL} =="
FAIL=0

# --- 1. initialize -----------------------------------------------------
init_status=$(curl -sS -o "$INIT_BODY" -D "$INIT_HEADERS" -w '%{http_code}' \
  -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer ${MCP_SERVICE_TOKEN}" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"${PROTOCOL_VERSION}\",\"capabilities\":{},\"clientInfo\":{\"name\":\"devskyy-verify-mcp-surfaces\",\"version\":\"1.0.0\"}}}")

session_id="$(grep -i '^mcp-session-id:' "$INIT_HEADERS" | tr -d '\r' | awk '{print $2}' || true)"

if [ "$init_status" != "200" ]; then
  echo "FAIL: initialize returned HTTP ${init_status} (expected 200)"
  FAIL=1
elif [ -z "$session_id" ]; then
  echo "FAIL: initialize returned 200 but no Mcp-Session-Id header"
  FAIL=1
else
  echo "PASS: initialize -> 200, session=${session_id}"
fi

if [ "$FAIL" -eq 1 ]; then
  echo "== MCP surface verification FAILED =="
  exit 1
fi

# --- 2. notifications/initialized (fire-and-forget notification) -------
curl -sS -o /dev/null -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer ${MCP_SERVICE_TOKEN}" \
  -H "Mcp-Session-Id: ${session_id}" \
  -H "MCP-Protocol-Version: ${PROTOCOL_VERSION}" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}' || true

# --- 3. tools/list -------------------------------------------------------
list_status=$(curl -sS -o "$LIST_BODY" -D "$LIST_HEADERS" -w '%{http_code}' \
  -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer ${MCP_SERVICE_TOKEN}" \
  -H "Mcp-Session-Id: ${session_id}" \
  -H "MCP-Protocol-Version: ${PROTOCOL_VERSION}" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}')

list_json="$(sed -n 's/^data: //p' "$LIST_BODY")"
if [ -z "$list_json" ]; then
  list_json="$(cat "$LIST_BODY")"
fi

tool_count="$(printf '%s' "$list_json" | jq -r '.result.tools | length' 2>/dev/null || echo "")"

if [ "$list_status" != "200" ]; then
  echo "FAIL: tools/list returned HTTP ${list_status} (expected 200)"
  FAIL=1
elif [ -z "$tool_count" ] || ! [ "$tool_count" -eq "$tool_count" ] 2>/dev/null; then
  echo "FAIL: tools/list response did not parse to a tool count"
  FAIL=1
elif [ "$tool_count" -lt "$MIN_TOOLS" ]; then
  echo "FAIL: tools/list returned ${tool_count} tools (expected >= ${MIN_TOOLS})"
  FAIL=1
else
  echo "PASS: tools/list -> ${tool_count} tools (>= ${MIN_TOOLS})"
fi

# best-effort session teardown, mirrors skyyrose_mcp_terminate()
curl -sS -o /dev/null -X DELETE "$MCP_URL" \
  -H "Authorization: Bearer ${MCP_SERVICE_TOKEN}" \
  -H "Mcp-Session-Id: ${session_id}" \
  -H "MCP-Protocol-Version: ${PROTOCOL_VERSION}" || true

# --- 4. 401 without token ------------------------------------------------
noauth_status=$(curl -sS -o /dev/null -w '%{http_code}' \
  -X POST "$MCP_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"${PROTOCOL_VERSION}\",\"capabilities\":{},\"clientInfo\":{\"name\":\"devskyy-verify-mcp-surfaces-noauth\",\"version\":\"1.0.0\"}}}")

if [ "$noauth_status" != "401" ]; then
  echo "FAIL: unauthenticated request returned HTTP ${noauth_status} (expected 401)"
  FAIL=1
else
  echo "PASS: unauthenticated request -> 401"
fi

if [ "$FAIL" -eq 1 ]; then
  echo "== MCP surface verification FAILED =="
  exit 1
fi

echo "== MCP surface verification PASSED =="
exit 0
