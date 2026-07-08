# devskyy-backend Go-Live Manifest

STOP-AND-SHOW gated runbook for standing up the `devskyy-backend` Fly app
(main_enterprise FastAPI backend). Every claim below traces to a `file:line`
read in the `ws/fly-backend-20260707-4` workstream session on 2026-07-07.
**No command in this file has been executed.** Deploys are founder-gated per
`CLAUDE.md` STOP-AND-SHOW protocol — this document is the checklist, not the
execution.

## Preconditions

- WS1 (ml-extra) merged to `main`.
- WS2 (dockerfile-api) merged to `main` — creates `Dockerfile.api`. As of this
  session, `Dockerfile.api` does **not** exist yet (`ls Dockerfile.api` → No
  such file or directory). `fly.backend.toml`'s `build.dockerfile =
  "Dockerfile.api"` is a valid forward reference; it will not build until WS2
  lands. Per `tasks/todo.md:338-343` a real `docker build -f Dockerfile.api
  -t devskyy-backend:test .` proof is deferred to "Post-merge: main thread" —
  do not attempt that build from this workstream, and do not run BLOCK 3 below
  until that proof exists.
- This workstream (WS3, fly-backend) merged to `main` — ships `fly.backend.toml`
  and the CORS/Sentry env wiring in `main_enterprise.py`.

## BLOCK 1 — Create the Fly app

```
fly apps create devskyy-backend --org <org-slug>
```

Confirm the org slug against `fly orgs list` before running — do not guess it.

```
STOP — Confirm before proceeding:

Action : fly apps create
App    : devskyy-backend
Org    : <org-slug>  (confirm via `fly orgs list` first)
Cost   : new Fly app (no machine cost until BLOCK 3 deploys)

Proceed? [y/N]
```

## BLOCK 2 — Set secrets (NAMES ONLY — never real values in this file or in chat)

```
fly secrets set -a devskyy-backend \
  DATABASE_URL=<PLACEHOLDER> \
  REDIS_URL=<PLACEHOLDER> \
  JWT_SECRET_KEY=<PLACEHOLDER> \
  ENCRYPTION_MASTER_KEY=<PLACEHOLDER> \
  SENTRY_DSN=<PLACEHOLDER>
```

Optional, only if the deployed routes need them:

```
fly secrets set -a devskyy-backend \
  OPENAI_API_KEY=<PLACEHOLDER> \
  ANTHROPIC_API_KEY=<PLACEHOLDER>
```

```
STOP — Confirm before proceeding:

Action : fly secrets set
App    : devskyy-backend
Names  : DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, ENCRYPTION_MASTER_KEY,
         SENTRY_DSN (+ optional OPENAI_API_KEY, ANTHROPIC_API_KEY)
Values : supplied out-of-band by the founder, never pasted into chat/logs

Proceed? [y/N]
```

## BLOCK 3 — Deploy

Precondition: `Dockerfile.api` exists on `main` AND a real
`docker build -f Dockerfile.api -t devskyy-backend:test .` has succeeded
(main-thread proof per `tasks/todo.md:342` — link/cite it here before running
this block).

```
fly deploy -c fly.backend.toml -a devskyy-backend
```

```
STOP — Confirm before proceeding:

Action : fly deploy
App    : devskyy-backend
Config : fly.backend.toml
Cost   : 1 always-on shared-cpu-1x/1gb machine (min_machines_running=1) —
         see "Cost note" below for the scale-to-zero alternative

Proceed? [y/N]
```

## BLOCK 4 — Post-deploy curl proofs (read-only, no gate needed)

```
curl -sS -o /dev/null -w "%{http_code}\n" https://devskyy-backend.fly.dev/health   # expect 200
curl -sS -o /dev/null -w "%{http_code}\n" https://devskyy-backend.fly.dev/ready    # expect 200
curl -sS https://devskyy-backend.fly.dev/health                                    # expect {"status":"healthy",...}
```

Record the actual output in this file's run-log (append a dated section below)
before proceeding to BLOCK 5. Session baseline (2026-07-07, pre-deploy):
`curl https://devskyy-backend.fly.dev/health` → `Could not resolve host` (app
does not exist yet — expected).

## BLOCK 5 — DNS repoint of api.devskyy.app

Precondition: BLOCK 4 proofs are green (both `/health` and `/ready` return 200
on `devskyy-backend.fly.dev`).

Session baseline (2026-07-07): `curl -o /dev/null -w "%{http_code}" \
https://api.devskyy.app/health` → `404`. This session confirmed the HTTP
response is a Vercel 404 but did **not** confirm which provider owns the
`devskyy.app` DNS zone — confirm the zone/registrar/provider before touching
any record. `frontend/vercel.json:11-12` already sets `NEXT_PUBLIC_API_URL` /
`NEXT_PUBLIC_WS_URL` to `https://api.devskyy.app` — no Vercel env change is
needed once the backend is live and DNS is repointed, only the DNS/cert step
below.

Sub-steps:
1. Record the CURRENT DNS record for `api.devskyy.app` verbatim (whatever the
   zone owner shows) — this is the rollback target.
2. `fly certs add api.devskyy.app -a devskyy-backend`
3. Update the DNS record per flyctl's certs-add output (CNAME or A/AAAA as
   instructed by that command's own output — do not guess the record type).
4. Poll `fly certs show api.devskyy.app -a devskyy-backend` until issued.

```
STOP — Confirm before proceeding:

Action : DNS repoint + cert issuance
Domain : api.devskyy.app
From   : <current DNS target — record it in step 1 above before this gate>
To     : devskyy-backend.fly.dev (via fly certs add)
Precondition: BLOCK 4 curl proofs both returned 200

Proceed? [y/N]
```

## BLOCK 6 — Post-DNS curl proof (read-only)

```
curl -sS -o /dev/null -w "%{http_code}\n" https://api.devskyy.app/health   # expect 200
```

Confirms cert + DNS propagated end-to-end. Record actual output in the run-log.

## Trusted-host note

`main_enterprise.py` has no `TrustedHostMiddleware` / `ALLOWED_HOSTS`
enforcement (grep for both across `main_enterprise.py`, `core/`, `api/` —
0 matches, this session). `api.devskyy.app` will be accepted at the app layer
without any additional allowlist configuration — no code change needed for
this repoint.

## Cost note — min_machines_running

`fly.backend.toml` sets `min_machines_running = 1` (dashboard-facing traffic,
no cold-start latency). The alternative, `min_machines_running = 0`, scales
to zero between requests, trading roughly 1-3s cold-start latency on the
first request after idle for lower machine-hour cost. Exact $/mo was **not
sourced from a live pricing page in this session** — pull current
shared-cpu-1x / 1gb pricing from fly.io/pricing before founder cost sign-off
if this tradeoff matters for budget approval.

## Rollback

- Cert/DNS: `fly certs remove api.devskyy.app -a devskyy-backend`; restore the
  DNS record captured in BLOCK 5 step 1.
- Bad release: `fly releases -a devskyy-backend` to list releases, then
  `fly deploy --image <previous-release-image> -a devskyy-backend` to revert.
- Abandon the app entirely: `fly apps destroy devskyy-backend` — STOP-AND-SHOW,
  irreversible, only if abandoning the app.

## Run log

_(Append dated entries here as each BLOCK is actually executed, with the real
command output pasted — this section stays empty until execution begins.)_
