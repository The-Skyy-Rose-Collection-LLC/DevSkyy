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

## Solution

### Step 1: Remove Platform-Level Rewrite

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Navigate to the `frontend` project
3. Go to **Settings** → **Rewrites**
4. Look for any rewrite rules with:
   - Source: `/api/:path*` or `/api/*`
   - Destination: `https://devskyy-backend.onrender.com*`
5. **Delete** this rewrite rule
6. Save changes

### Step 2: Verify Configuration

1. Check that no other rewrite rules reference the backend
2. Ensure "Rewrites" section is empty or only contains non-API rules

### Step 3: Test After Changes

Once the platform rewrite is removed, test these endpoints:

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

## Build Failures Note

All deployments from the past 14+ hours show "Error" status, but the site is still accessible. This suggests:

1. An older successful deployment is still serving traffic
2. Recent build failures are a separate issue from the routing problem
3. Check build logs in Vercel Dashboard for specific error messages

The routing fix should be prioritized first, as it's blocking API functionality.

---

**Status**: Awaiting manual intervention in Vercel Dashboard
**Priority**: HIGH - Blocking all API functionality
**Created**: 2026-01-13
**Author**: Claude Sonnet 4.5
