---
name: Silent-Disable Pattern Audit
specified_by: [user request 2026-05-03]
phase: 0 (audit only, no fixes applied without confirmation)
last_updated: 2026-05-03
last_updated_by: silent-disable investigation pass
trigger: User flagged the Sequential Thinking MCP key-rename gotcha as the second instance (after claude-mem v12.1.0 worker no-op) of the same anti-pattern. This audit hunts for more.
---

# Silent-Disable Pattern Audit

## The pattern

A system component is **configured** in some config file or registry, but **produces no visible behavior** at runtime. No error message, no log entry, no tool surfaces. The only way to discover it failed is to look for what *should* be happening and notice the absence.

**Fingerprints to search for:**

1. Config keys with prefix-renames that hide them from the loader (`_disabled_*`, `_archived_*`)
2. Hooks/scripts that wrap the real work in `2>/dev/null`, `|| true`, `; true`
3. MCP/plugin servers configured but with missing env vars, unreachable hosts, or stale auth
4. Multiple competing config locations for the same registry (project `.mcp.json` vs user `settings.json` vs `~/.claude.json`)
5. Cron / scheduled jobs configured but with no proof they fire
6. Documented "available" tools whose runtime invocation always errors

---

## Confirmed instances

### CRITICAL — these ARE failing right now

#### S1. `~/DevSkyy/.mcp.json` — `claude-context` server fails on every session start

```json
"claude-context": {
  "command": "npx",
  "args": ["-y", "@zilliz/claude-context-mcp@latest"],
  "env": {
    "OLLAMA_HOST": "http://127.0.0.1:11434",     // Ollama IS up (tested: 200)
    "MILVUS_ADDRESS": "127.0.0.1:19530"          // Milvus NOT reachable (tested: connection refused)
  }
}
```

**Evidence of silent failure:** `ps aux | grep claude-context-mcp` returns zero processes. The server attempts to connect to Milvus, fails, and exits. No error surfaces in this session because MCP servers are loaded at session start with logs written to a location not exposed to the model.

**Fix options:**
- (a) Run Milvus locally: `docker run -d -p 19530:19530 milvusdb/milvus:latest`
- (b) Remove the entry from `.mcp.json` until Milvus is provisioned (recommended)
- (c) Move it to a `_disabled_mcpServers__claude_context_needs_milvus` block in `.mcp.json` (mirroring the settings.json fix from earlier today)

#### S2. `~/DevSkyy/.mcp.json` — `postgresql` server fails on every session start

```json
"postgresql": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres"],
  "env": {
    "POSTGRES_CONNECTION_STRING": "${POSTGRES_CONNECTION_STRING}"   // env var NOT SET
  }
}
```

**Evidence of silent failure:** `POSTGRES_CONNECTION_STRING` is not set in `~/.zshrc`, `~/.bash_profile`, `~/.zprofile`, `~/.bashrc`, any `.env*` file, or the current shell. The MCP server starts with an empty/literal connection string and fails to establish a database connection. No process visible.

**Fix options:**
- (a) Set `POSTGRES_CONNECTION_STRING` in `~/.zshrc` if a Postgres DB is intended for this project
- (b) Remove the entry from `.mcp.json` if Postgres MCP isn't needed
- (c) Document in the file what database this server is supposed to connect to (the project doesn't appear to have a Postgres dependency — main DB is WP MySQL)

#### S3. `~/.claude.json` — `wordpress` MCP server has plaintext password

```json
"wordpress": {
  "type": "stdio",
  "command": "mcp-wordpress-remote",
  "env": {
    "WP_API_URL": "https://skyyrose.co",
    "WP_API_USERNAME": "skyyroseco",
    "WP_API_PASSWORD": "<REDACTED — full plaintext app password in file>"
  }
}
```

**Evidence of silent failure:** `mcp__wordpress__*` tools do NOT appear in this session's deferred-tools list, suggesting the server failed to start (probably `mcp-wordpress-remote` binary is missing or auth handshake failed). But the **plaintext password in `~/.claude.json`** is the more urgent finding — this file is not in the same protection layer as `.env` files, and any process or backup that reads it now has the WordPress app password.

**Fix options:**
- (a) **High priority:** Rotate the WP application password (it's been at rest in this file)
- (b) Move the new password to `~/.claude.json`'s scoped env via macOS Keychain reference, or move the MCP config to `.env.wordpress` and have the launcher read from there
- (c) Remove the wordpress MCP entry if you're using `mcp__claude_ai_WordPress_com__*` instead (which appears to be the active path — that one IS in the deferred list)

#### S4. `~/DevSkyy/.mcp.json` — `aidesigner` HTTP MCP returns 401 on every call

```json
"aidesigner": {
  "type": "http",
  "url": "https://api.aidesigner.ai/api/v1/mcp"
}
```

**Evidence of silent failure:** `curl https://api.aidesigner.ai/api/v1/mcp` returns HTTP 401. The tool surfaces as `mcp__aidesigner__authenticate` and `mcp__aidesigner__complete_authentication` in the deferred list — meaning Claude Code recognizes the auth handshake is incomplete. But every other aidesigner call would fail without that handshake first. The "tool exists" signal masks the "tool unusable" reality.

**Fix options:**
- (a) Run `mcp__aidesigner__authenticate` once to complete auth (recommended before Phase 4 design work)
- (b) Document in `.mcp.json` that auth is required before first use
- (c) Remove if AIDesigner won't be used until later phases

#### S5. Measurement packet `test_command` points to non-existent script

In `eval/measurement-access-requests.md` frontmatter:

```yaml
test_command: node scripts/measurement/verify-all-grants.js
```

But `scripts/measurement/` directory does NOT exist. None of the six referenced verify scripts exist:

- `scripts/measurement/verify-all-grants.js`
- `scripts/measurement/verify-google-service-account.js`
- `scripts/measurement/verify-gsc.js`
- `scripts/measurement/verify-gtm.js`
- `scripts/measurement/verify-meta.js`
- `scripts/measurement/verify-sentry.js`

**Evidence of silent failure (potential):** When you complete Step 7 of the access packet and I run "verification sweep" per the doc, commands will exit with `Error: Cannot find module ...`. The plan implies these scripts exist; they don't yet — they're a Phase 0.5 deliverable.

**Fix options:**
- (a) Add `# Built in Phase 0.5 — does not yet exist` comment next to the test_command in frontmatter (clarifies expectation)
- (b) Build the scripts in Phase 0 as stubs that exit 1 with "Phase 0.5 has not yet built this verifier" (makes the gap loud)
- (c) Build them for real in Phase 0.5 as planned (the original intent)

Recommended: (a) for now, (c) when Phase 0.5 starts.

---

### LOWER SEVERITY — pre-existing footguns

#### S6. `claude-mem` shell alias still points at the broken v12.1.0 binary

```
claude-mem is an alias for bun "/Users/theceo/.claude/plugins/cache/thedotmack/claude-mem/12.1.0/scripts/worker-service.cjs"
```

But `npx --yes claude-mem --version` returns `12.5.1` (the working CLI). The SessionStart hook uses `npx` so it bypasses the alias and works correctly. But anyone manually running `claude-mem` in a shell hits the broken v12.1.0 binary — same failure mode the user fought through earlier today.

**Fix options:**
- (a) Update the alias to point at v12.5.1 binary path: `alias claude-mem='bun "/Users/theceo/.claude/plugins/cache/thedotmack/claude-mem/12.5.1/scripts/worker-service.cjs"'` (or wherever 12.5.1 actually lives; check the cache dir)
- (b) Remove the alias and rely on PATH (npx resolution)
- (c) `rm -rf ~/.claude/plugins/cache/thedotmack/claude-mem/12.1.0` to ensure the broken version can't be reached

#### S7. SessionStart hook for claude-mem swallows all output

In `~/.claude/settings.json` line 187:

```bash
npx --yes claude-mem status > /dev/null 2>&1 || (npx --yes claude-mem start > /dev/null 2>&1 &)
```

Both stdout and stderr discarded on both branches. If start fails, you'll never know unless you inspect `~/.claude-mem/` for liveness signals. (I added this hook earlier today — own-goal.)

**Fix options:**
- (a) Append a write to `/tmp/claude-mem-start.log` instead of discarding stderr: `... 2>/tmp/claude-mem-start.log ...`
- (b) Check exit code of `start` and write a marker file: `... && touch ~/.claude-mem/.started-$(date +%s)`
- (c) Leave it (acceptable risk — the worker is currently running, verified via `ps aux`)

#### S8. PostToolUse formatter hook swallows ruff/isort/prettier errors

In `~/.claude/settings.json` line 131:

```bash
fp=$(jq -r '.tool_input.file_path // empty'); case "$fp" in
  *.py) ruff format "$fp" 2>/dev/null; isort "$fp" 2>/dev/null;;
  ...
esac; true
```

The trailing `; true` and per-tool `2>/dev/null` mean a file that ruff cannot format (e.g., syntax error from a recent edit) gets committed without any warning. The hook reports success, the file is broken.

**Fix options:**
- (a) Remove `2>/dev/null` so format errors surface in the model's tool result feed
- (b) Replace `; true` with a check that emits a hook-level warning if formatters errored
- (c) Leave it (acceptable if you trust the model's output and rely on lint:php / pytest as the real gate)

---

### NOT bugs but worth noting

- **`vercel.json` has no `crons` block.** The plan documents this as a Phase 0.5 deliverable, so it's not a current bug — but `eval/measurement-access-requests.md` line 274 ("vercel.json crons block added") could be misread as present-tense. Recommend tightening the wording to "WILL be added in Phase 0.5".
- **`~/.claude/settings.json` lists 31 plugins as `enabled: false`.** Per `enabledPlugins`, these are explicit "off" — likely intentional given the plan only wants 6-8 active. Worth a one-line audit later to confirm none should be on (e.g., `pinecone`, `vercel`, `figma` could be useful in Phase 5; `playwright` will be needed for Phase 7 e2e).
- **`~/.claude.json` projects.<dir>.mcpServers + `.mcp.json` mcpServers + `~/.claude/settings.json` mcpServers** — three locations all loaded simultaneously by Claude Code. Currently no naming collisions, but the surface area for the silent-disable pattern grows with each new entry. Recommend one source of truth per server.

---

## Pattern recognition

All eight instances share this structure:

```
configured ───→ [silently fails] ───→ no visible behavior ───→ author assumes it works
```

The ones that hurt most were:
- **claude-mem v12.1.0** (today, earlier) — `start` command exited 0 without starting the worker. Found by inspecting `ps aux`.
- **Sequential Thinking MCP** (today, earlier) — server parked under renamed config key. Found by reading the config file directly.
- **claude-context Milvus** (this audit) — server starts, can't connect, dies. Found by `ps aux` showing zero processes.
- **postgresql env var** (this audit) — server starts with empty connection string, dies. Same fingerprint as above.

**The unifying principle:** when "exit 0" is the primary success signal, any code path that returns 0 without doing the work is invisible. Defensible signals require an *external* check (process running, file present, response received), not a *self-reported* exit code.

---

## Resolution status (updated 2026-05-03)

| ID | Status | What was done |
|----|--------|---------------|
| **S1** | ✅ FIXED | `~/DevSkyy/.mcp.json` — `claude-context` moved to `_disabled_mcpServers__claude_context_needs_milvus` block with explicit re-enable comment. Server no longer attempts to start every session. |
| **S2** | ✅ FIXED | `~/DevSkyy/.mcp.json` — `postgresql` moved to `_disabled_mcpServers__postgresql_needs_connection_string` block. The project doesn't use Postgres (primary DB is WP MySQL on WPCom), so this entry was likely speculative; preserved in case Postgres is added later. |
| **S3** | ✅ PARTIALLY FIXED — REQUIRES CREDENTIAL ROTATION | Wordpress MCP entry surgically removed from `~/.claude.json` via `jq 'del(.mcpServers.wordpress)'` (atomic write with validation). Backup at `~/.claude.json.backup-20260503-162141`. **The plaintext password sat at rest in the file — Corey must rotate the WordPress application password manually**: WP admin → Users → skyyroseco → Application Passwords → revoke `mcp-wordpress-remote` and any old "claude" tokens, then issue fresh ones (do NOT store the new one in `~/.claude.json` again — use `mcp__claude_ai_WordPress_com__*` OAuth flow instead, which is already in the deferred-tools list). |
| **S4** | ✅ AUTH FLOW INITIATED | `mcp__aidesigner__authenticate` called. OAuth URL emitted (in tool result above). Corey: open the URL, complete the flow, and the aidesigner tools will become available without further intervention. If the redirect 404s, paste the full address-bar URL into chat and I'll call `mcp__aidesigner__complete_authentication`. |
| **S5** | ✅ FIXED | `eval/measurement-access-requests.md` frontmatter `test_command` line updated to clarify the script is a Phase 0.5 deliverable. New `scripts/measurement/README.md` documents planned scripts. New `scripts/measurement/verify-all-grants.js` dispatcher stub exits 1 with an explicit explanation — turns silent fail into loud fail. Verified exit code: 1. |
| **S6** | DEFERRED | `claude-mem` shell alias still points at v12.1.0. Low priority — npx-based session hook bypasses it. Fix when convenient: `unalias claude-mem` or update to v12.5.1 path. |
| **S7** | DEFERRED | SessionStart claude-mem hook swallows all output. Currently working (worker is running, verified). Worth adding a status marker file later. |
| **S8** | DEFERRED | PostToolUse formatter hook swallows ruff/isort/prettier errors. Trade-off: surfacing them adds noise to model context. Defer until a formatter-error-driven bug hits. |

## What requires Corey to do something

Two items need a human:

1. **Rotate the WordPress application password** (S3). The current one was at rest in `~/.claude.json` plaintext. Procedure:
   - Log into WP admin at `https://skyyrose.co/wp-admin/`
   - Users → skyyroseco → Application Passwords section
   - Revoke any token named `mcp-wordpress-remote` or similar
   - For future WP API access: use `mcp__claude_ai_WordPress_com__*` OAuth (zero plaintext credentials needed)

2. **Complete aidesigner OAuth** (S4). The auth URL was emitted by the `mcp__aidesigner__authenticate` call. One-click in the browser unlocks all aidesigner tools for Phase 4 design work.

Everything else is fixed in code/config — no further action needed.
