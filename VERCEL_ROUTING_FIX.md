# Vercel Routing Issue - Required Manual Fix

## Problem

All API requests to `https://app.devskyy.app/api/*` are returning `ROUTER_EXTERNAL_TARGET_ERROR` with HTTP 502 after 120 second timeout.

## Root Cause

Vercel has **platform-level rewrite configuration** that is proxying all `/api/*` requests to the external backend URL `https://devskyy-backend.onrender.com`. This configuration:

1. **Cannot be overridden** by `vercel.json` settings
2. **Persists** even after removing rewrites from code
3. **Must be removed manually** from Vercel Dashboard

## Evidence

- Historical `vercel.json` (commit `3adfd68fb`) contained:
  ```json
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://devskyy-backend.onrender.com/:path*"
    }
  ]
  ```
- This was removed in commit `88b4918c9` but Vercel platform still uses it
- Current `vercel.json` has `"rewrites": []` but still getting ROUTER_EXTERNAL_TARGET_ERROR
- Backend is healthy (0.25s response) but Vercel proxy times out

### Intermittent Error Patterns

Testing reveals **two different errors**:

1. **HTTP 502** - `ROUTER_EXTERNAL_TARGET_ERROR` (most common)
   - Vercel platform trying to proxy to external backend
   - Confirms platform-level rewrite is active

2. **HTTP 503** - `x-render-routing: dynamic-hibernate-error-503` (occasional)
   - Request reaches application code
   - Old deployment (still live) trying to reach hibernated backend

**Why Two Errors?**: All deployments have failed for 14+ hours, so an older successful deployment is serving traffic. That deployment has backend proxy code. The intermittent behavior suggests edge cache variability or routing flapping between platform rewrite and application code.

## Solution

### Step 1: Configure Root Directory (CRITICAL)

**Issue**: Vercel is building from repository root instead of `frontend/` subdirectory

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to the `frontend` project
3. Go to **Settings** → **General**
4. Find **Root Directory** section
5. Set to: `frontend`
6. Click **Save**

### Step 2: Remove Platform-Level Rewrite

1. In same project, go to **Settings** → **Rewrites**
2. Look for any rewrite rules with:
   - Source: `/api/:path*` or `/api/*`
   - Destination: `https://devskyy-backend.onrender.com*`
3. **Delete** this rewrite rule
4. Save changes

### Step 3: Verify Configuration

1. Check that no other rewrite rules reference the backend
2. Ensure "Rewrites" section is empty or only contains non-API rules

### Step 4: Trigger Redeploy

After setting Root Directory, trigger a new deployment:

```bash
# From local machine
cd /Users/coreyfoster/DevSkyy
git commit --allow-empty -m "chore: trigger redeploy after Root Directory fix"
git push origin main
```

Or use Vercel Dashboard → Deployments → Redeploy

### Step 5: Test After Successful Deployment

Once deployment succeeds (check Dashboard), test these endpoints:

```bash
# Simple endpoint (no backend call) - should respond instantly
curl https://app.devskyy.app/api/test-simple

# Expected:
# {"status":"ok","message":"Simple test endpoint responding","timestamp":"..."}

# Health endpoint (proxies to backend) - should respond in ~1s
curl https://app.devskyy.app/api/health

# Expected:
# {"status":"healthy","timestamp":"...","agents":{"total":54}}
```

## Why Next.js Route Handlers Are Better

The current implementation uses Next.js API Route Handlers instead of Vercel platform rewrites. Benefits:

1. **Better error handling**: Route handlers can catch and handle errors gracefully
2. **Caching control**: Per-route cache strategies via Cache-Control headers
3. **Timeout management**: Can set custom timeouts per endpoint
4. **No cold start race**: Route handlers are serverless functions, not external proxies
5. **Debugging**: Full access to request/response in Next.js middleware

## Current Architecture

```
User Request → Vercel Edge → Next.js Route Handler → Render Backend
                                      ↓
                            (with retry logic,
                             error handling,
                             caching strategy)
```

## Files Reference

- `/frontend/vercel.json` - Vercel platform configuration (no rewrites)
- `/frontend/app/api/[...path]/route.ts` - Catch-all proxy handler
- `/frontend/app/api/health/route.ts` - Specific health endpoint
- `/frontend/app/api/test-simple/route.ts` - Test endpoint (no backend)
- `/frontend/lib/api-proxy.ts` - Shared proxy utility with timeout handling

## Keep-Alive Cron Job

The cron job is already configured and running:
- Endpoint: `/api/cron/keep-alive`
- Schedule: Every 10 minutes (`*/10 * * * *`)
- Purpose: Prevent Render backend hibernation

### Required: Configure CRON_SECRET

To secure the cron endpoint:

1. Generate secret:
   ```bash
   openssl rand -base64 32
   ```

2. Add to Vercel Dashboard:
   - **Settings** → **Environment Variables**
   - Name: `CRON_SECRET`
   - Value: <generated secret>
   - Environment: **Production**

3. Save and redeploy

## Next Steps

After removing the platform rewrite:

1. Wait 1-2 minutes for Vercel edge cache to clear
2. Test API endpoints (commands above)
3. If still seeing errors, check Vercel deployment logs
4. If successful, configure CRON_SECRET for cron job security

## Build Failures - Separate Critical Issue

**Status**: All deployments have failed for 14+ hours
**Impact**: Cannot deploy new code (routing fixes, keep-alive cron)
**Current State**: Old successful deployment still serving traffic

### What This Means

1. Site is accessible because an old deployment is live
2. New deployments (with routing fixes) cannot go live
3. Keep-alive cron job code is deployed but not active
4. **Both issues must be fixed**: routing AND builds

### Build Error Investigation Results

**Errors Found**:

1. **TypeScript Compilation Errors** (First 10+ failed deployments)
   - 42 TypeScript errors in root `src/app/collections/` and `src/components/collections/`
   - Broken collections code duplicated from frontend subdirectory
   - Fixed by removing 3,717 lines in commit 5c6f39214

2. **CopilotKit Dependency Conflict** (Latest deployment)
   - npm ERESOLVE error with @copilotkit/runtime-client-gql versions
   - Root `package.json` has conflicting CopilotKit dependencies
   - **Root Cause**: Vercel building from repository root, not `frontend/` subdirectory
   - **Solution**: Configure Root Directory in Dashboard (see Step 1 above)

### Priority

1. **Fix routing first** (unblocks API testing)
2. **Fix builds second** (enables deploying fixes)
3. **Test keep-alive** (after both are resolved)

Without successful builds, the routing fix in `vercel.json` (`rewrites: []`) cannot take effect.

---

**Status**: Awaiting manual intervention in Vercel Dashboard
**Priority**: HIGH - Blocking all API functionality
**Created**: 2026-01-13
**Author**: Claude Sonnet 4.5
