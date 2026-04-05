# DevSkyy Production Runbook

**Last Updated**: 2026-04-05
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

Single-command pipeline (build → rsync → maintenance mode → verify):

```bash
bash scripts/deploy-pipeline.sh        # Full deploy + verify
bash scripts/deploy-pipeline.sh --dry-run  # Preview without deploying
```

Individual steps:
```bash
bash scripts/deploy-theme.sh           # Transfer theme files only
bash scripts/verify-deploy.sh          # Verify 11 pages post-deploy
WORDPRESS_URL=https://staging.skyyrose.co bash scripts/verify-deploy.sh  # Staging
```

Pages verified (11 total): Homepage, REST API, Collections ×3, About, Immersive ×3, Pre-Order Gateway, Experiences Hub.

Credentials required in `.env.wordpress`: `SSH_HOST`, `SSH_USER`, `SSH_PASS`, `WP_THEME_PATH`, `SFTP_HOST`, `SFTP_USER`, `SFTP_PASS`.

Note: Binary assets in `assets/images/` are gitignored — rsync uploads them from local disk each deploy.

### Backend (Docker)

```bash
docker-compose up -d                    # Local
docker-compose -f docker-compose.staging.yml up -d  # Staging
```

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
curl https://api.devskyy.app/metrics
open https://api.devskyy.app/docs

# Frontend
curl -s -o /dev/null -w "%{http_code}\n" https://devskyy.app

# WordPress
curl -s -o /dev/null -w "%{http_code}\n" https://skyyrose.co
curl "https://skyyrose.co/index.php?rest_route=/wp/v2/posts&per_page=1"
curl -u "ck_xxx:cs_xxx" "https://skyyrose.co/index.php?rest_route=/wc/v3/products&per_page=1"
```

## Health Endpoints

| Endpoint | Purpose | Expected |
|----------|---------|----------|
| `/health` | Basic liveness | `{"status": "healthy"}` |
| `/health/ready` | Readiness (DB, cache) | `{"status": "ready"}` |
| `/health/live` | Kubernetes liveness | `{"status": "live"}` |
| `/metrics` | Prometheus metrics | Prometheus text format |

## Monitoring

| Service | Purpose | Config |
|---------|---------|--------|
| Prometheus | Metrics collection | `prometheus.yml`, `PROMETHEUS_ENABLED=true` |
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

### Backend 500 Internal Server Error

**Check logs**: `docker-compose logs -f api` or `fly logs -a devskyy`.
**Common causes**:
- Missing environment variables (compare `.env` to `.env.example`)
- Database connection failed (test with `python -c "from sqlalchemy import create_engine; create_engine(os.environ['DATABASE_URL']).connect()"`)
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
**Fix**: Verify `is_preorder` flags in `data/product-catalog.csv` (canonical source). The PHP theme reads this at runtime; `inc/product-catalog.php` is now a CSV reader, not a hardcoded array. Non-preorder products must have `is_preorder=0` in the CSV.

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
