# DevSkyy Production Runbook

**Last Updated**: 2026-03-09
**Production URL**: devskyy.app (Vercel)
**WordPress**: SkyyRose Flagship theme

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

```bash
cd wordpress-theme/skyyrose-flagship
bash scripts/wp-deploy-theme.sh   # SFTP sync + WP-CLI config
```

Or manual SFTP upload of `wordpress-theme/skyyrose-flagship/` to `/wp-content/themes/skyyrose-flagship/`.

### Backend (Docker)

```bash
docker-compose up -d                    # Local
docker-compose -f docker-compose.staging.yml up -d  # Staging
```

Entry point: `main_enterprise.py` — `uvicorn main_enterprise:app --host 0.0.0.0 --port 8000`

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
**Fix**: Ensure `sshpass` is installed (`brew install hudochenkov/sshpass/sshpass`).

### Product Routing Goes to Pre-Order for Everything

**Symptom**: All product links go to `/pre-order/` instead of collection pages.
**Cause**: `skyyrose_product_url()` fallback routes to pre-order when WooCommerce doesn't have the product.
**Fix**: Verify `is_preorder` flags in `inc/product-catalog.php`. Non-preorder products should have `'is_preorder' => false`. The function checks this flag before routing.

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
