# DevSkyy Dashboard Operations Runbook

> **Last Updated:** 2026-02-20 | **On-Call:** 24/7 Monitoring

Production operations guide for DevSkyy Enterprise AI Platform.

---

## Table of Contents

- [System Overview](#system-overview)
- [Deployment Procedures](#deployment-procedures)
- [Monitoring & Alerts](#monitoring--alerts)
- [Common Issues & Fixes](#common-issues--fixes)
- [Rollback Procedures](#rollback-procedures)
- [Emergency Contacts](#emergency-contacts)

---

## System Overview

### Architecture

```
┌─────────────────┐
│   Vercel CDN    │  ← https://www.devskyy.app
└────────┬────────┘
         │
┌────────▼────────┐
│  Next.js App    │  ← Frontend (React 19 + TypeScript)
│  (iad1 region)  │
└────────┬────────┘
         │
┌────────▼────────┐
│   API Routes    │  ← /api/*
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│ Vercel│ │WordPress│
│  KV   │ │ Backend │
└───────┘ └─────────┘
```

### Infrastructure

- **Hosting:** Vercel (skkyroseco organization)
- **Project:** devskyy
- **Region:** iad1 (Washington, D.C., USA East)
- **Build Machine:** 8 cores, 16 GB RAM
- **Framework:** Next.js 16 with Turbopack
- **Runtime:** Node.js 24.x

### URLs

| Environment | URL | Purpose |
|-------------|-----|---------|
| Production | https://www.devskyy.app | Public-facing dashboard |
| Preview | https://devskyy-*.vercel.app | PR previews |
| API Health | https://www.devskyy.app/api/monitoring/health | Health check endpoint |
| API Metrics | https://www.devskyy.app/api/monitoring/metrics | Prometheus metrics |

---

## Deployment Procedures

### Pre-Deployment Checklist

- [ ] All tests passing (`pnpm test:e2e`)
- [ ] Build succeeds locally (`pnpm build`)
- [ ] No TypeScript errors
- [ ] No console.log statements
- [ ] Environment variables configured in Vercel
- [ ] PR approved and merged to main
- [ ] Changelog updated
- [ ] Stakeholders notified

### Standard Deployment

**Automated (Recommended):**
```bash
cd /Users/coreyfoster/DevSkyy/frontend

# Preview deployment with pre-checks
pnpm deploy:auto

# Production deployment with full checks + smoke tests
pnpm deploy:auto:prod
```

**Manual:**
```bash
# Option 1: Direct from frontend directory
cd /Users/coreyfoster/DevSkyy/frontend
pnpm deploy:prod

# Option 2: Pre-built deployment (faster, more reliable)
cd /Users/coreyfoster/DevSkyy
vercel build --prod --yes
vercel --prod --yes --prebuilt
```

### Deployment Steps (Automated)

1. **Pre-deployment Checks** (1-2 min)
   - Vercel CLI installed
   - Project linked to "devskyy"
   - Environment files present
   - Configuration validated

2. **Build Process** (30-40s)
   - TypeScript compilation
   - Next.js production build
   - Asset optimization
   - Source map generation

3. **Deployment** (20-30s)
   - Upload to Vercel
   - Build on Vercel infrastructure
   - Deploy to iad1 region
   - Alias to production URL

4. **Post-Deployment** (10-20s)
   - Wait for deployment ready
   - Smoke tests (production only)
   - Log deployment
   - Update status

**Total Time:** ~2-3 minutes for full deployment

### Deployment Verification

```bash
# Check deployment status
vercel ls

# View logs
pnpm vercel:logs

# Inspect specific deployment
vercel inspect <deployment-url>

# Test health endpoint
curl https://www.devskyy.app/api/monitoring/health
```

**Expected Health Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-20T00:00:00Z",
  "version": "1.0.0",
  "uptime": 123456
}
```

### Post-Deployment Checklist

- [ ] Health check returns 200
- [ ] Main dashboard loads (`/admin`)
- [ ] Settings page loads (`/admin/settings`)
- [ ] Monitoring page loads (`/admin/monitoring`)
- [ ] No console errors
- [ ] Analytics tracking
- [ ] Vercel Analytics showing traffic
- [ ] Response times < 500ms

---

## Monitoring & Alerts

### Health Checks

**Endpoints:**
- `GET /api/monitoring/health` - System health status
- `GET /api/monitoring/metrics` - Prometheus metrics

**Monitor:**
```bash
# Automated health check (every 5 minutes)
*/5 * * * * curl -f https://www.devskyy.app/api/monitoring/health || echo "Health check failed"
```

### Vercel Dashboard

**Access:** https://vercel.com/skkyroseco/devskyy

**Key Metrics:**
- Deployment status
- Build duration
- Response times
- Error rates
- Bandwidth usage
- Visitor analytics

### System Monitoring (`/admin/monitoring`)

**Real-time Metrics:**
- Service health (WordPress API, Vercel API, Round Table, Database)
- Circuit breaker status
- System metrics (API req/min, success rate, avg response time)
- Activity logs

**Alert Thresholds:**
- Response time > 1s → Warning
- Response time > 3s → Critical
- Error rate > 5% → Warning
- Error rate > 10% → Critical
- Uptime < 99.5% → Warning
- Uptime < 99% → Critical

### Vercel Analytics

**Metrics Tracked:**
- Page views
- Unique visitors
- Geographic distribution
- Device types
- Core Web Vitals (LCP, FID, CLS)

### Logs

```bash
# View recent logs
pnpm vercel:logs

# Tail logs (real-time)
vercel logs --follow

# Filter by deployment
vercel logs <deployment-url>

# Export logs
vercel logs > deployment-logs.txt
```

---

## Common Issues & Fixes

### Build Failures

**Issue:** Build fails with TypeScript errors

**Fix:**
```bash
# Check for type errors locally
cd frontend
pnpm build

# If errors found, fix them and test
pnpm lint
pnpm test:e2e
```

**Issue:** Build fails with missing dependencies

**Fix:**
```bash
# Clear cache and reinstall
rm -rf node_modules .next
pnpm install
pnpm build
```

**Issue:** Build timeout on Vercel

**Fix:**
- Optimize build process
- Remove large dependencies
- Use dynamic imports for heavy components
- Contact Vercel support to increase timeout

### Deployment Failures

**Issue:** "Project not linked" error

**Fix:**
```bash
# Re-link project
pnpm vercel:link

# Verify link
cat .vercel/project.json
```

**Issue:** Environment variables missing

**Fix:**
```bash
# Pull from Vercel
pnpm vercel:env:pull

# Or set in Vercel dashboard
# Settings → Environment Variables → Add
```

**Issue:** Wrong Vercel project

**Fix:**
```bash
# Remove old link
rm -rf .vercel

# Re-link to correct project
pnpm vercel:link
# Select: skkyroseco → devskyy
```

### Runtime Issues

**Issue:** 404 errors on routes

**Fix:**
- Verify page exists in `app/` directory
- Check Next.js routing configuration
- Clear browser cache
- Redeploy

**Issue:** API routes failing

**Fix:**
```bash
# Check API health
curl https://www.devskyy.app/api/monitoring/health

# View logs
pnpm vercel:logs

# Check environment variables
vercel env ls
```

**Issue:** Slow page loads (LCP > 4s)

**Fix:**
- Check Vercel Analytics for bottlenecks
- Optimize images (use next/image)
- Enable code splitting
- Lazy load heavy components
- Review bundle size

**Issue:** White screen / React hydration error

**Fix:**
- Check browser console for errors
- Verify server/client rendering match
- Clear cache: `rm -rf .next`
- Rebuild: `pnpm build`

### Environment Variable Issues

**Issue:** "Invalid API_URL configuration" warning

**Status:** Non-blocking (runtime warning)

**Fix:**
```bash
# Set proper API_URL in Vercel dashboard
# Settings → Environment Variables → Production
NEXT_PUBLIC_API_URL=https://api.devskyy.app
```

**Issue:** Missing secrets in production

**Fix:**
```bash
# Add to Vercel dashboard
# Settings → Environment Variables → Add Variable
# Select: Production, Preview, Development

# Common missing vars:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_AI_API_KEY=...
```

### Performance Issues

**Issue:** Circuit breaker open

**Location:** `/admin/monitoring` → Circuit Breaker Status

**Fix:**
- Wait for timeout (60s default)
- Check service health
- If persistent, investigate service failures
- Increase circuit breaker threshold in `/admin/settings`

**Issue:** High latency (>1s)

**Fix:**
```bash
# Check Vercel region
vercel inspect <deployment-url>

# Verify database connection
# Check WordPress API response time
curl -w "@curl-format.txt" -o /dev/null -s https://your-wordpress-site.com

# Enable caching
# Update environment variables:
RESPONSE_CACHE_TTL=300
VECTOR_SEARCH_CACHE_TTL=300
```

---

## Rollback Procedures

### Immediate Rollback (< 5 minutes)

**Option 1: Vercel Dashboard (Fastest)**
1. Go to https://vercel.com/skkyroseco/devskyy
2. Click "Deployments"
3. Find previous stable deployment
4. Click "..." → "Promote to Production"
5. Confirm promotion

**Option 2: CLI**
```bash
# List recent deployments
vercel ls

# Rollback to previous deployment
vercel rollback
```

**Option 3: Git Revert**
```bash
# Revert last commit
git revert HEAD
git push origin main

# Vercel will auto-deploy the revert
```

### Partial Rollback (Feature Flags)

**Disable Feature via Environment Variable:**
```bash
# In Vercel Dashboard:
# Settings → Environment Variables → Production

# Example: Disable auto-sync
NEXT_PUBLIC_ENABLE_AUTO_SYNC=false

# Redeploy to apply
vercel --prod
```

### Database Rollback

**If database changes were deployed:**

1. Stop all writes to database
2. Restore from backup (if available)
3. Run migration rollback:
```bash
# If using Alembic/Prisma migrations
pnpm db:rollback
```
4. Verify data integrity
5. Resume traffic

### Emergency Rollback

**Criteria for emergency rollback:**
- Critical security vulnerability
- Data loss risk
- Complete service outage
- Database corruption

**Procedure:**
1. **Immediate:** Use Vercel Dashboard to rollback (fastest)
2. **Notify:** Alert team in #devskyy-incidents Slack
3. **Investigate:** Check logs, metrics, errors
4. **Fix:** Apply fix in new branch
5. **Test:** Thoroughly test before redeploying
6. **Deploy:** Once verified, deploy fix
7. **Post-mortem:** Document incident and learnings

---

## Emergency Contacts

### On-Call Rotation

| Role | Contact | Escalation |
|------|---------|------------|
| Primary On-Call | TBD | Slack: @devskyy-oncall |
| Backend Lead | TBD | Email: backend@skyyrose.com |
| DevOps Lead | TBD | Email: devops@skyyrose.com |
| CTO | TBD | Phone: (415) XXX-XXXX |

### External Contacts

| Service | Support | URL |
|---------|---------|-----|
| Vercel | support@vercel.com | https://vercel.com/support |
| OpenAI | support@openai.com | https://help.openai.com |
| Anthropic | support@anthropic.com | https://console.anthropic.com |
| WordPress | N/A | Self-hosted |

### Incident Response Channels

- **Slack:** #devskyy-incidents (urgent)
- **Email:** incidents@skyyrose.com
- **PagerDuty:** (if configured)

---

## Runbook Maintenance

### Update Schedule

- **After every major deployment:** Update deployment procedures
- **Monthly:** Review and update common issues
- **Quarterly:** Full runbook audit and cleanup
- **On incident:** Document new issues and fixes immediately

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-20 | Initial runbook creation |

---

## Appendix

### Useful Commands Reference

```bash
# Deployment
pnpm deploy:auto:prod          # Full automated production deploy
vercel --prod --yes --prebuilt # Pre-built production deploy
vercel rollback                # Rollback to previous deployment

# Monitoring
pnpm vercel:logs               # View deployment logs
vercel inspect <url>           # Inspect deployment details
curl <url>/api/monitoring/health # Health check

# Environment
pnpm vercel:env:pull           # Pull env vars from Vercel
pnpm vercel:env:push           # Push env vars to Vercel
vercel env ls                  # List all env vars

# Project
pnpm vercel:link               # Link to devskyy project
vercel project ls              # List all projects
cat .vercel/project.json       # Show current link

# Build
pnpm build                     # Build locally
pnpm lint                      # Check code quality
pnpm test:e2e                  # Run E2E tests
```

### Deployment Checklist (Printable)

```
□ Pre-Deployment
  □ Tests passing
  □ Build succeeds
  □ No TypeScript errors
  □ PR approved
  □ Changelog updated

□ Deployment
  □ Run: pnpm deploy:auto:prod
  □ Monitor build logs
  □ Wait for completion (2-3 min)

□ Verification
  □ Health check: curl <url>/api/monitoring/health
  □ Main dashboard loads
  □ Settings page loads
  □ No console errors
  □ Analytics tracking

□ Post-Deployment
  □ Monitor for 15 minutes
  □ Check error rates
  □ Verify response times
  □ Update team
```

---

**Runbook Version:** 1.0.0
**Last Reviewed:** 2026-02-20
**Next Review:** 2026-03-20
**Maintained By:** DevSkyy Platform Team
