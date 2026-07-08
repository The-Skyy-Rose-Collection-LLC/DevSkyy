# DevSkyy Production Runbook

**Last Updated**: 2026-07-06
**Production URL**: devskyy.app (Vercel)
**WordPress**: SkyyRose Flagship theme at skyyrose.co

---

## Pre-Deployment Checklist

### Generate Security Keys (first-time setup)

```bash
# JWT secret (64+ chars)
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))"

# Encryption key (32 bytes, base64)
python -c "import secrets, base64; print('ENCRYPTION_MASTER_KEY=' + base64.b64encode(secrets.token_bytes(32)).decode())"
```

### Quality Gates

```bash
make ci                          # Full CI locally
# Or individual checks:
ruff check .                     # Lint
black --check .                  # Format
mypy . --ignore-missing-imports  # Types (904 source files)
pytest tests/ -v                 # Tests
```

### Environment Verification
- [ ] All secrets in `.env.example` are configured in `.env`
- [ ] Database is provisioned and accessible (`DATABASE_URL` set)
- [ ] Redis cache is provisioned (optional but recommended)
- [ ] At least one LLM provider API key is valid
- [ ] `.env.wordpress` has fresh SFTP credentials (rotates periodically)
- [ ] DNS records point to correct endpoints

---

## Deployment

### Frontend (Vercel)

Deployments are automatic on push to `main`. Manual deploy:

```bash
cd frontend
npm run build          # Verify build succeeds locally
git push origin main   # Triggers Vercel auto-deploy
```

- Dashboard: vercel.com/skkyroseco/devskyy
- Root directory: `frontend/` (set in Vercel project config)
- Node: 22.x, npm (NOT pnpm — causes ERR_INVALID_THIS on Node 22+)
- Preview deploys on every PR

### WordPress Theme

Single-command pipeline (build → deploy → verify):

```bash
bash scripts/deploy-pipeline.sh        # Full deploy + verify
bash scripts/deploy-pipeline.sh --dry-run  # Preview without deploying
```

Individual steps:
```bash
cd wordpress-theme && npm run deploy        # Wraps: bash ../scripts/deploy-theme.sh
cd wordpress-theme && npm run deploy:dry    # --dry-run, no server contact
bash scripts/verify-deploy.sh               # Verify pages post-deploy
WORDPRESS_URL=https://staging.skyyrose.co bash scripts/verify-deploy.sh  # Staging
```

`deploy-theme.sh` transfers via **tar + scp with an atomic hot-swap on the remote by default** (not maintenance mode). Pass `--with-maintenance` (`npm run deploy:full`) only for deploys that include DB migrations or plugin changes — that path is kept as a legacy fallback. The script already has: a concurrency lock (refuses a second concurrent deploy), retention of the last 2 `.old.*` swap directories, and **auto-rollback** if `verify_live()` fails post-swap (reverses the swap and flushes caches without human intervention). Manual `git checkout` rollback (below) is the fallback if auto-rollback itself can't recover.

Credentials required in `.env.wordpress`: `SSH_HOST`, `SSH_USER`, `SSH_PASS`, `WP_THEME_PATH`, `SFTP_HOST`, `SFTP_USER`, `SFTP_PASS`. Override the path with `ENV_FILE=<path>`.

Note: theme product imagery under `assets/images/products/` is **tracked in git**
(deploy-from-clean-tree convention) even though `.gitignore` blanket-ignores theme
webp — land new binaries with `git add -f` in the same change that references them.
Guard: `tests/test_sot_assets_tracked.py` fails CI on any SOT-referenced image that
isn't a tracked blob (bug-175). Deploy from a checkout of `main`, never from a
feature-branch working tree.

### WordPress MU-Plugins

Production MU-plugins live in `wordpress/mu-plugins/` and deploy individually
(SCP to `wp-content/mu-plugins/`, destination filename = source basename):

```bash
# Ally AJAX guard (default source) — keeps Ally out of AJAX/REST JSON responses
STOPSHOW_ACK=1 bash scripts/deploy-mu-plugin.sh

# Anonymous-cache guard — withholds WC session/cart cookies on anon GETs so the
# Atomic/Batcache edge can cache them (TTFB 1.8s → ~0.06s on edge HIT)
STOPSHOW_ACK=1 MU_SRC=wordpress/mu-plugins/skyyrose-anon-cache-guard.php \
  bash scripts/deploy-mu-plugin.sh
```

The script php-lints the plugin, uploads, flushes cache, and verifies the
CommerceKit nonce endpoint returns clean JSON. Post-deploy checks for the
anon-cache guard: anonymous `curl -sI https://skyyrose.co/` must emit **no**
`Set-Cookie`, repeat request must show `x-ac: … HIT`, and a fresh-session
add-to-cart must still populate the cart (session starts on the wc-ajax POST).

**Never trust the deploy command's exit code alone** — a broken pipe (e.g. piping deploy output through `grep`/`tail`) can report exit 0 on a failed transfer. Verify with a live-state check (`npm run deploy:verify` or a cache-busted `curl`), not just the shell exit status.

Mascot (Skyy) post-deploy checks — each catches a real shipped regression (bugs 178/189/190/193):
1. Any JS/CSS change is INERT until the `?ver=` version triple bumps — the edge caches assets by full URL.
2. `getComputedStyle(document.body).transform` must be `'none'` — any body transform (even a keyframe held by `fill-mode: forwards`) silently re-anchors every `position: fixed` overlay to the page.
3. Watch the `pageerror` channel, not just console — browser module failures (e.g. bare `'three'` import specifiers) never appear in console.error.
4. Behavioral check must SIMULATE ACTIVITY: scroll + move the mouse continuously and assert the mascot still enters. A motionless headless page structurally cannot exhibit idle-gating bugs.

### Backend (Docker)

```bash
make docker-secrets   # First time only: generates .env.docker with strong random secrets
make docker-up        # Build + start core stack (postgres/redis/app/worker/elite-worker)
make docker-logs       # Tail all services
make docker-up-monitoring  # Core stack + prometheus + grafana (--profile monitoring)
```

One image (`devskyy:local`) serves all three Python roles (API / task worker / elite-studio worker); the compose `command:` selects the role. Secrets come from `.env.docker` (never committed) — compose fails loudly (`${VAR:?...}`) if a required secret is missing, rather than booting with a placeholder. Full workflow: `docs/DOCKER.md`.

Entry point: `main_enterprise.py` — `uvicorn main_enterprise:app --host 0.0.0.0 --port 8000`

### HuggingFace Spaces

```bash
# First-time auth
pip install huggingface_hub
huggingface-cli login

# Deploy all spaces
cd hf-spaces && bash deploy-all-spaces.sh

# Deploy individual space (example: 3D Converter)
cd hf-spaces/3d-converter
huggingface-cli repo create skyyrose/3d-converter --type space -y || true
git init && git remote add origin https://huggingface.co/spaces/skyyrose/3d-converter
git add . && git commit -m "Deploy" && git push -f origin main
```

Set secrets in Space settings (`HF_TOKEN` + space-specific keys).
Verify: `curl https://huggingface.co/api/spaces/skyyrose/<space-name>`.

## Smoke Tests

```bash
# Backend + API
curl https://api.devskyy.app/health
curl https://api.devskyy.app/ready
curl https://api.devskyy.app/live
open https://api.devskyy.app/docs

# Frontend
curl -s -o /dev/null -w "%{http_code}\n" https://devskyy.app

# WordPress
curl -s -o /dev/null -w "%{http_code}\n" https://skyyrose.co
curl "https://skyyrose.co/index.php?rest_route=/wp/v2/posts&per_page=1"
curl -u "ck_xxx:cs_xxx" "https://skyyrose.co/index.php?rest_route=/wc/v3/products&per_page=1"
```

## Health Endpoints

Verified against `main_enterprise.py` (2026-07-06) — the paths below are the actual registered routes, not `/health/*` sub-paths:

| Endpoint | Purpose | Expected |
|----------|---------|----------|
| `/health` | Basic liveness (checks DB via `db.health_check()`) | `{"status": "healthy", "services": {"api": "operational", "database": "..."}}` |
| `/ready` | Readiness | `{"ready": true}` |
| `/live` | Liveness | `{"alive": true}` |
| `/api/v1/monitoring/metrics` | Application metrics (JSON, not Prometheus text) | `MonitoringMetricsResponse` — accepts `?metrics=health,performance` |

**`/metrics` at the app root does not exist.** `prometheus.yml` is configured to scrape `devskyy-app:8000/metrics`, but `main_enterprise.py` exposes no such route today — that scrape target will 404 until either a Prometheus-format `/metrics` endpoint is added (e.g. via `prometheus-client`'s ASGI app) or the scrape config is pointed at `/api/v1/monitoring/metrics` with a JSON-to-Prometheus adapter. Don't assume Prometheus metrics are flowing without checking the Prometheus targets page first.

## Monitoring

| Service | Purpose | Config |
|---------|---------|--------|
| Prometheus | Metrics collection (see gap noted above — scrape target currently unimplemented) | `prometheus.yml`, `PROMETHEUS_ENABLED=true`, `make docker-up-monitoring` |
| Sentry | Error tracking | `SENTRY_DSN` env var |
| Vercel Analytics | Frontend performance | `@vercel/analytics` |
| GitGuardian | Secret scanning | GitHub integration |

## Common Issues & Fixes

### CI/CD Pipeline Failures (All Jobs Fail Instantly)

**Symptom**: Every GitHub Actions job fails in 2-3 seconds with zero steps.
**Cause**: GitHub billing issue — account locked or minutes exhausted.
**Fix**: GitHub Settings > Billing > Update payment method or add Actions minutes.
**Rerun**: `gh run rerun <run-id>`

### Vercel Build Fails with pnpm

**Symptom**: `ERR_INVALID_THIS` during Vercel build.
**Cause**: pnpm incompatible with Node 22+.
**Fix**: Use npm. Ensure `frontend/package-lock.json` exists (not `pnpm-lock.yaml`).

### .venv-agents Import Errors

**Symptom**: `ImportError` when using Google ADK agents.
**Cause**: ADK conflicts with numpy in the main venv.
**Fix**: Always use `.venv-agents/` for ADK work. Never install ADK in `.venv`.

### WordPress REST API 404

**Symptom**: `/wp-json/` returns 404.
**Fix**: Use `index.php?rest_route=` instead of `/wp-json/`. Check permalink settings.

### Agent Context Limit Exceeded

**Symptom**: Claude/Ralph agents fail mid-task with context limit errors.
**Cause**: Too many files in scope — binaries, docs, cached artifacts.
**Fix**: Run repo cleanup. Ensure `.gitignore` covers caches, binaries, archives.

### Gemini 429 Rate Limits

**Symptom**: `429 Too Many Requests` during product generation.
**Fix**: Add `time.sleep(8)` between per-product calls. Use exponential backoff.

### WordPress Theme Upload Fails

**Symptom**: SFTP deploy hangs or fails authentication.
**Fix**: Ensure `sshpass` is installed (`brew install hudochenkov/sshpass/sshpass`). If auth still fails, the WordPress.com SFTP password has likely rotated — regenerate at WP.com Dashboard → Users → Security → SFTP/SSH credentials and update `.env.wordpress`.

### Deploy Reports Success But Site Didn't Change

**Symptom**: `deploy-theme.sh` exits 0, but the live site still shows old content.
**Cause**: Piping deploy output through `grep`/`tail` makes the pipeline's exit code that of the last command in the pipe, masking a failed transfer underneath.
**Fix**: Never wrap a deploy invocation in a pipe without checking `PIPESTATUS`/`pipefail`. Verify with a live-state check (`npm run deploy:verify`, a cache-busted `curl`, or Playwright) — never trust the exit code alone.

### Collections Page Renders Stale Template After Deploy

**Symptom**: `/collections/` (or another page) keeps rendering an old/orphan template after a hot-swap deploy, even though the new theme files are live.
**Cause**: The tar+scp hot-swap deploy replaces theme files but does not touch WordPress's `_wp_page_template` post-meta — a page still resolves to whatever template slug was saved on it, orphan or not.
**Fix**: For a specific page, force the correct template via a `template_include` filter (see `skyyrose_collections_index_template()` in the theme) rather than relying on the deploy to fix stored meta. Zero DB writes required.

### SFTP Fallback (lftp) Fails With Regex Error

**Symptom**: `lftp mirror: Invalid preceding regular expression` when the primary `scp` transfer fails and the script falls back to `lftp`.
**Cause**: The exclude list was built for rsync's glob syntax (`*.map`) but passed straight into `lftp --exclude`, which expects a regex.
**Fix**: Already patched in `deploy-theme.sh` — the exclude-building step now converts glob to regex (escape dots, `*` → `.*`, strip trailing slash) before handing it to `lftp`.

### Backend 500 Internal Server Error

**Check logs**: `docker-compose logs -f api` or `fly logs -a devskyy`.
**Common causes**:
- Missing environment variables (compare `.env` to `.env.example`)
- Database connection failed (test with `python -c "import os; from sqlalchemy import create_engine; create_engine(os.environ['DATABASE_URL']).connect()"`)

- Invalid LLM API keys (check with provider dashboard)

### CORS Errors on Frontend

**Symptom**: Browser blocks requests from `devskyy.app` to `api.devskyy.app`.
**Fix**: Verify `CORS_ORIGINS` env var includes all frontend domains:
```bash
echo $CORS_ORIGINS
# Should include: https://devskyy.app,https://skyyrose.co
```

### HuggingFace Space Not Starting

**Check space logs** in HF dashboard. Verify secrets are set. Free tier spaces sleep after inactivity — upgrade to persistent hardware or add keep-alive pings.

### Product Routing Goes to Pre-Order for Everything

**Symptom**: All product links go to `/pre-order/` instead of collection pages.
**Cause**: `skyyrose_product_url()` fallback routes to pre-order when WooCommerce doesn't have the product.
**Fix**: Verify `is_preorder` flags in `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` (the canonical catalog — `inc/product-catalog.php:28` resolves it via `get_theme_file_path('data/skyyrose-catalog.csv')`, not the root-level `data/product-catalog.csv`). The PHP theme reads this at runtime, not a hardcoded array. Non-preorder products must have `is_preorder=0` in the CSV.

## Rollback Procedures

### Vercel

```bash
# List recent deployments
vercel ls --limit 10

# Promote a previous deployment
vercel promote <deployment-url>

# Or via dashboard: Deployments > ... > Promote to Production
```

### WordPress Theme

```bash
# WordPress keeps previous theme version
# Switch back via WP Admin > Appearance > Themes
# Or restore from git:
git log --oneline wordpress-theme/ | head -5
git checkout <commit> -- wordpress-theme/skyyrose-flagship/
# Re-deploy via SFTP
```

### Backend

```bash
# Docker rollback
docker-compose down
git checkout <previous-commit>
docker-compose up -d --build

# Fly.io rollback
fly releases -a devskyy
fly deploy --image <previous-image>
```

### Database

```bash
# Alembic migration rollback
alembic downgrade -1          # One step back
alembic downgrade <revision>  # Specific revision
```

## Incident Response

1. **Assess**: Check health endpoints, Sentry, Vercel dashboard
2. **Communicate**: Update team in Slack/Discord
3. **Mitigate**: Rollback if production is affected
4. **Fix**: Apply fix on a branch, test, PR
5. **Post-mortem**: Document in `docs/archive/`

## Security Runbooks

Detailed incident response procedures are in `docs/runbooks/`:
- `api-key-leak.md` — Exposed API key response
- `data-breach.md` — Data breach protocol
- `ddos-attack.md` — DDoS mitigation
- `security-incident-response.md` — General incident response
