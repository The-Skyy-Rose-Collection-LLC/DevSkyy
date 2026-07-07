# MCP-over-HTTP Go-Live Manifest — STOP AND SHOW

The backend is **already live** at `https://devskyy-api.fly.dev/mcp/` (Fly
app `devskyy-api`, 1 always-on machine, `MCP_SERVICE_TOKEN` set). Everything
below is what remains to wire the two consumer surfaces (dashboard, WordPress)
and the WooCommerce tools to that live backend.

Per `CLAUDE.md`'s STOP AND SHOW protocol, every block below touches
production (Vercel prod env / Fly secrets / skyyrose.co) and **requires
explicit "y"/"yes" confirmation before execution** — this document is the
manifest to show, not an instruction to run any of it autonomously. No real
secret values are pasted anywhere in this file; every token/secret is a
placeholder in `<value-from-...>` form pointing at where the real value
lives (`.env.wordpress`, `fly secrets list`, etc.).

Full architecture reference: `docs/mcp-http-architecture.md`.
Read-only post-verify tool used throughout: `scripts/verify-mcp-surfaces.sh`.

---

## Block 1 — Vercel production env (dashboard surface)

```
STOP — Confirm before proceeding:

Action : Set Vercel Production environment variables + redeploy
Vars   : MCP_URL=https://devskyy-api.fly.dev/mcp/
         MCP_SERVICE_TOKEN=<value-from-fly-secrets:MCP_SERVICE_TOKEN>
Cost   : $0 (no paid API call) — but redeploys the live dashboard
Proceed? [y/N]
```

Commands (only after "y"):

```bash
cd frontend
vercel env add MCP_URL production
# paste: https://devskyy-api.fly.dev/mcp/
vercel env add MCP_SERVICE_TOKEN production
# paste: <value-from-fly-secrets:MCP_SERVICE_TOKEN> (see `fly secrets list -a devskyy-api`,
# value itself lives in .env.wordpress or the Fly dashboard — never print it)
npm run deploy
```

**Post-verify:**

```bash
MCP_URL=https://devskyy-api.fly.dev/mcp/ \
MCP_SERVICE_TOKEN=<value-from-fly-secrets:MCP_SERVICE_TOKEN> \
bash scripts/verify-mcp-surfaces.sh
```

This confirms the backend itself is healthy and the token is valid — it does
not test Vercel's wiring. Follow with a manual browser check: sign in to the
deployed dashboard, open `/admin/mcp`, click "list tools", confirm >= 40
tools render.

---

## Block 2 — Fly WooCommerce secrets

```
STOP — Confirm before proceeding:

Action : fly secrets set (restarts the devskyy-api machine)
Vars   : WC_CONSUMER_KEY=<value-from-.env.wordpress:WC_CONSUMER_KEY>
         WC_CONSUMER_SECRET=<value-from-.env.wordpress:WC_CONSUMER_SECRET>
App    : devskyy-api
Cost   : $0 — but drops any in-flight MCP session (single-machine session
         affinity; `fly secrets set` triggers a machine restart)
Proceed? [y/N]
```

Command (only after "y"):

```bash
fly secrets set \
  WC_CONSUMER_KEY=<value-from-.env.wordpress:WC_CONSUMER_KEY> \
  WC_CONSUMER_SECRET=<value-from-.env.wordpress:WC_CONSUMER_SECRET> \
  -a devskyy-api
```

**Post-verify:**

```bash
MCP_URL=https://devskyy-api.fly.dev/mcp/ \
MCP_SERVICE_TOKEN=<value-from-fly-secrets:MCP_SERVICE_TOKEN> \
bash scripts/verify-mcp-surfaces.sh
```

Then (manual, founder-run, read-only): call the `wc_get_products` tool via
the dashboard console with a small `per_page` to confirm the WC credentials
resolve end-to-end (`skyyrose/integrations/wc_safe_client.py` raises
`KeyError` at call time if either var is still missing).

---

## Block 3 — WordPress bridge config + theme deploy

```
STOP — Confirm before proceeding:

Action : Set wp-config.php constants (or wp_options via wp-admin), then
         optionally redeploy the theme
Vars   : SKYYROSE_MCP_URL=https://devskyy-api.fly.dev/mcp/
         SKYYROSE_MCP_TOKEN=<value-from-fly-secrets:MCP_SERVICE_TOKEN>
Cost   : $0 — but a theme deploy touches production (skyyrose.co)
Proceed? [y/N]
```

Add to `wp-config.php` (via wp-admin hosting file manager, or WP.com MCP
site-editing tools — configuring `wp-config.php` is out of this
workstream's scope to execute, only to specify):

```php
define( 'SKYYROSE_MCP_URL', 'https://devskyy-api.fly.dev/mcp/' );
define( 'SKYYROSE_MCP_TOKEN', '<value-from-fly-secrets:MCP_SERVICE_TOKEN>' );
```

(Or, if consts aren't practical on the host, set the equivalent `wp_options`
— `skyyrose_mcp_url` / `skyyrose_mcp_token` — via wp-admin; per
`mcp-bridge.php`'s precedence, the const wins if both are set.)

`inc/mcp-bridge.php` is presumed already deployed as part of the theme (its
own history should be checked with `git log -- wordpress-theme/skyyrose-flagship/inc/mcp-bridge.php`
against the live theme version before assuming a deploy is needed). If only
the wp-config constants change, **no theme deploy is required** — constants
take effect immediately. Only run the deploy below if the theme itself has
unshipped code changes:

```bash
STOPSHOW_ACK=1 bash scripts/deploy-theme.sh
```

**Post-verify:**

```bash
MCP_URL=https://devskyy-api.fly.dev/mcp/ \
MCP_SERVICE_TOKEN=<value-from-fly-secrets:MCP_SERVICE_TOKEN> \
bash scripts/verify-mcp-surfaces.sh
```

This is a backend-side sanity check only. Follow with a manual browser check
of wp-admin **Tools -> DevSkyy MCP**: click "Load tools", confirm the tool
list renders with no `skyyrose_mcp_unsafe_url` or `skyyrose_mcp_no_session`
errors.

---

## Block 4 — Optional DNS cutover (api.devskyy.app)

```
STOP — Confirm before proceeding:

Action : fly certs add + DNS record(s) at the domain registrar/DNS provider
Domain : api.devskyy.app
Cost   : $0 — adds a TLS cert + DNS record, no data write, but DNS changes
         propagate publicly and are not instantly reversible
Proceed? [y/N]
```

Lower risk than Blocks 1-3 (no application data write), but still shown here
because DNS propagation is not instantaneous and a misconfigured record is
publicly visible. Command (only after "y"):

```bash
fly certs add api.devskyy.app -a devskyy-api
```

`flyctl`'s exact `certs add` flag surface can drift between versions — run
`flyctl help certs add` immediately before this command to confirm current
syntax rather than trusting this document verbatim. `flyctl` will print the
DNS record(s) to add (typically an A/AAAA or CNAME); add those at the DNS
provider for `devskyy.app`. Once the certificate issues, both surfaces'
*default* URLs (the WP bridge's baked-in `https://api.devskyy.app/mcp/`
default, and any per-surface override) resolve without needing an explicit
`MCP_URL` / `SKYYROSE_MCP_URL` override.

**Post-verify:**

```bash
MCP_URL=https://api.devskyy.app/mcp/ \
MCP_SERVICE_TOKEN=<value-from-fly-secrets:MCP_SERVICE_TOKEN> \
bash scripts/verify-mcp-surfaces.sh
```

---

## Summary checklist

- [ ] Block 1 — Vercel `MCP_URL` + `MCP_SERVICE_TOKEN` (Production) + redeploy — confirmed? ______
- [ ] Block 2 — Fly `WC_CONSUMER_KEY` / `WC_CONSUMER_SECRET` — confirmed? ______
- [ ] Block 3 — WordPress `SKYYROSE_MCP_URL` / `SKYYROSE_MCP_TOKEN` (+ theme deploy if needed) — confirmed? ______
- [ ] Block 4 (optional) — `api.devskyy.app` cert + DNS — confirmed? ______

Every block's post-verify step is `bash scripts/verify-mcp-surfaces.sh` with
`MCP_URL` / `MCP_SERVICE_TOKEN` exported — it is read-only, cannot mutate
site state, and is safe to re-run after every step above.
