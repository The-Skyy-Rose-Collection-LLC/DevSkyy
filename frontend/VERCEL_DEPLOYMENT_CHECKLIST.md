# Vercel Deployment Checklist

**Status**: ✅ PRODUCTION READY (Frontend + Backend Configured)
**Date**: 2026-01-12
**Backend URL**: `https://api.devskyy.app` (Render - Ready to Deploy)
**Frontend URL**: `https://app.devskyy.app` (Vercel - Ready to Deploy)

> **Note**: Backend configuration complete! See `/RENDER_DEPLOYMENT_CHECKLIST.md` for backend deployment guide.

---

## ✅ Configuration Complete

### 1. Backend URL Standardization
- ✅ **vercel.json**: Rewrites to `https://api.devskyy.app`
- ✅ **next.config.js**: Uses `process.env.BACKEND_URL` (defaults to `https://api.devskyy.app`)
- ✅ **.env.production**: `BACKEND_URL=https://api.devskyy.app`
- ✅ **.env.production.example**: Updated with all required vars
- ✅ **BACKEND_CONNECTION.md**: Updated to reflect correct URLs

### 2. Environment Variables
**.env.production** contains:
```bash
# API URLs
NEXT_PUBLIC_API_URL=https://api.devskyy.app
NEXT_PUBLIC_WS_URL=wss://api.devskyy.app
BACKEND_URL=https://api.devskyy.app

# Site URL
NEXT_PUBLIC_SITE_URL=https://app.devskyy.app

# Feature Flags
NEXT_PUBLIC_ENABLE_3D_PIPELINE=true
NEXT_PUBLIC_ENABLE_ROUND_TABLE=true

# Stack Auth (configure in Vercel dashboard)
# NEXT_PUBLIC_STACK_PROJECT_ID=your-project-id
# NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY=pck_...
# STACK_SECRET_SERVER_KEY=ssk_...
```

**Vercel Dashboard Setup Required:**
1. Go to: https://vercel.com/skyyroseco/frontend/settings/environment-variables
2. Add all `NEXT_PUBLIC_*` variables from `.env.production`
3. Add Stack Auth credentials (if using)

### 3. Production Pages Validated (12 pages)
All pages exist, compile successfully, and have correct routing:

1. ✅ **Dashboard** (`/`) - 6.49 kB
   - Metrics cards, agent grid, round table viewer
   - Links: AgentCard → `/agents/{type}`, `/agents/{type}/chat`

2. ✅ **Agents List** (`/agents`) - 1.4 kB
   - Agent directory
   - Links: Individual agent pages

3. ✅ **Individual Agent** (`/agents/[agent]`) - 6.34 kB (dynamic)
   - Agent details and controls
   - Links: Chat page

4. ✅ **Agent Chat** (`/agents/[agent]/chat`) - 753 B (dynamic)
   - Real-time agent interaction
   - Links: Back to `/agents`

5. ✅ **3D Pipeline** (`/3d-pipeline`) - 4.23 kB
   - 3D asset generation interface

6. ✅ **Round Table** (`/round-table`) - 2.87 kB
   - LLM competition viewer
   - Links: History page

7. ✅ **Round Table History** (`/round-table/history`) - 3.69 kB
   - Past competitions archive

8. ✅ **A/B Testing** (`/ab-testing`) - 2.9 kB
   - Model comparison tool

9. ✅ **Tools** (`/tools`) - 4.42 kB
   - Tool registry viewer

10. ✅ **Settings** (`/settings`) - 3.99 kB
    - Settings hub (newly created!)
    - Links: `/settings/brand`

11. ✅ **HF Spaces** (`/hf-spaces`) - 3.77 kB
    - HuggingFace Space embeds

12. ✅ **WordPress** (`/wordpress`) - New!
    - WordPress & WooCommerce management
    - Pages, products, media, sync status
    - Links: External links to WordPress site

### 4. Navigation
**Main Navigation** (in `layout.tsx`):
- ✅ `/` → Dashboard
- ✅ `/agents` → Agents
- ✅ `/3d-pipeline` → 3D Pipeline
- ✅ `/round-table` → Round Table
- ✅ `/ab-testing` → A/B Testing
- ✅ `/tools` → Tools
- ✅ `/wordpress` → WordPress
- ✅ `/settings` → Settings

**All links validated** - no 404s!

### 5. vercel.json Configuration
**File Location**: `/Users/coreyfoster/DevSkyy/vercel.json` (repository root)

**Valid Properties** (updated 2026-01-12):
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "regions": ["iad1"],
  "functions": {
    "app/api/**/*.ts": {
      "maxDuration": 60
    }
  },
  "headers": [...],
  "rewrites": [...]
}
```

**What's Configured**:
- ✅ **Regions**: Deploy to `iad1` (Virginia, USA)
- ✅ **Functions**: API routes timeout after 60 seconds
- ✅ **Headers**: CORS, security headers (see below)
- ✅ **Rewrites**: Proxy `/api/*` to `https://api.devskyy.app`

**What's NOT in vercel.json** (configure in dashboard):
- ❌ `rootDirectory` - Set in Vercel Dashboard → General → Root Directory
- ❌ `buildCommand` - Use dashboard default (`npm run build`)
- ❌ `framework` - Auto-detected (Next.js)

### 6. CORS Configuration
**vercel.json** headers:
```json
{
  "source": "/api/(.*)",
  "headers": [
    { "key": "Access-Control-Allow-Credentials", "value": "true" },
    { "key": "Access-Control-Allow-Origin", "value": "*" },
    { "key": "Access-Control-Allow-Methods", "value": "GET,POST,PUT,DELETE,OPTIONS" },
    { "key": "Access-Control-Allow-Headers", "value": "X-Requested-With, Content-Type, Authorization" }
  ]
}
```

**next.config.js** headers (same as above) ✅

### 7. Build Status
```bash
✓ Compiled successfully in 6.8s
✓ Generating static pages (25/25)
✓ Finalizing page optimization

Build Output:
- 12 production pages (25 total including non-production)
- 0 build errors
- 4 ESLint warnings (non-blocking, related to collections/test/wordpress pages)
- Total First Load JS: 102 kB (shared)
- Largest page: 264 kB (Dashboard with charts)
```

### 8. Linting
```bash
npm run lint
✅ Passed with 4 warnings (non-blocking)
- collections/layout.tsx: Font loading warning
- test/layout.tsx: Font loading warning
- wordpress/page.tsx: useEffect dependency warning
- ProductModal.tsx: useEffect dependency warning
```

---

## 📋 Pre-Deployment Checklist

### Backend Readiness
- [x] **Backend configured** for Render deployment (see `/RENDER_DEPLOYMENT_CHECKLIST.md`)
- [x] **Health check endpoints** implemented: `/health`, `/ready`, `/live`
- [x] **CORS configured** to allow `https://app.devskyy.app`
- [x] **WebSocket** endpoint available: `wss://api.devskyy.app/ws/*`
- [x] **Gunicorn + Uvicorn** production server configured
- [x] **Database pooling** configured (PostgreSQL + Redis)
- [ ] **Backend deployed** to Render at `https://api.devskyy.app`

### Frontend Deployment
- [x] **Build succeeds** locally (`npm run build`)
- [x] **Environment variables** documented in `.env.production`
- [x] **All pages** compile without errors
- [x] **Navigation links** validated
- [ ] **Vercel environment variables** configured in dashboard

### Testing (Post-Deployment)
After deploying to Vercel, test:

1. **Health Check**
   ```bash
   curl https://app.devskyy.app
   # Should return 200 OK
   ```

2. **API Proxy**
   ```bash
   curl https://app.devskyy.app/api/v1/agents
   # Should proxy to https://api.devskyy.app/api/v1/agents
   ```

3. **WebSocket Connection**
   - Open browser DevTools → Network → WS
   - Navigate to Dashboard
   - Verify WebSocket connections to `wss://api.devskyy.app/ws/agents`

4. **Page Navigation**
   - [ ] Dashboard loads
   - [ ] Click "Agents" → loads agents list
   - [ ] Click an agent → loads agent detail
   - [ ] Click "Chat" → loads chat page
   - [ ] Click "Round Table" → loads competition
   - [ ] Click "Settings" → loads settings hub
   - [ ] All other nav items load correctly

5. **API Integration**
   - [ ] Dashboard metrics load from backend
   - [ ] Agent list populates from API
   - [ ] Round Table data displays
   - [ ] Real-time updates via WebSocket

---

## 🚀 Deployment Commands

### STEP 1: Configure Vercel Dashboard (REQUIRED)

**CRITICAL**: Configure project settings in Vercel Dashboard BEFORE deploying:

1. Go to: https://vercel.com/skyyroseco/devskyy-dashboard/settings/general

2. **Configure Root Directory**:
   - **Root Directory**: `frontend` ← **MUST BE SET**
   - Framework Preset: Next.js (auto-detected)
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)
   - Install Command: `npm install` (default)

3. Click **Save**

**Why This Is Required**:
- The `rootDirectory` property is NOT valid in `vercel.json` (causes deployment errors)
- Must be configured in the Vercel dashboard instead
- Without this, Vercel will try to build from repository root instead of `frontend/` directory

### STEP 2: Deploy to Vercel
```bash
# From repository root (/Users/coreyfoster/DevSkyy)
cd frontend

# Install Vercel CLI (if not installed)
npm i -g vercel

# Login to Vercel
vercel login

# Link to existing project (if not already linked)
vercel link

# Deploy to production
vercel --prod
```

**Expected Output**:
```
✓ Linked to skyyroseco/devskyy-dashboard
✓ Inspecting 12 Serverless Functions
✓ Building Production Bundle
✓ Generating static pages (25/25)
✓ Deployment Ready
https://app.devskyy.app
```

### Environment Variables in Vercel Dashboard
After deployment, verify in Vercel Dashboard:

1. Go to: **Project Settings** → **Environment Variables**
2. Add/verify for **Production** environment:
   ```
   NEXT_PUBLIC_API_URL=https://api.devskyy.app
   NEXT_PUBLIC_WS_URL=wss://api.devskyy.app
   NEXT_PUBLIC_SITE_URL=https://app.devskyy.app
   NEXT_PUBLIC_ENABLE_3D_PIPELINE=true
   NEXT_PUBLIC_ENABLE_ROUND_TABLE=true
   BACKEND_URL=https://api.devskyy.app
   ```

3. Add Stack Auth credentials (if using):
   ```
   NEXT_PUBLIC_STACK_PROJECT_ID=<your-project-id>
   NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY=<your-key>
   STACK_SECRET_SERVER_KEY=<your-secret>
   ```

---

## 🔧 Troubleshooting

### Issue: "Invalid vercel.json - should NOT have additional property 'rootDirectory'"
**Solution**:
1. This error means `vercel.json` contains properties that should be in the dashboard
2. Configure Root Directory in Vercel Dashboard (see STEP 1 above)
3. The `vercel.json` file should only contain: `regions`, `functions`, `headers`, `rewrites`
4. Fixed in commit `f639207de` - ensure you have the latest version

### Issue: Build fails with "Cannot find module" errors
**Solution**:
1. Verify Root Directory is set to `frontend` in Vercel Dashboard
2. Ensure `package.json` exists in `frontend/` directory
3. Check that `npm install` runs successfully locally
4. Redeploy after verifying configuration

### Issue: Pages return 404
**Solution**: Redeploy after fixing navigation. All pages now exist.

### Issue: API calls fail with CORS error
**Solution**:
1. Verify backend has CORS headers allowing `https://app.devskyy.app`
2. Check `vercel.json` and `next.config.js` have correct headers
3. Verify `NEXT_PUBLIC_API_URL` is set in Vercel dashboard

### Issue: WebSocket connections fail
**Solution**:
1. Verify `NEXT_PUBLIC_WS_URL=wss://api.devskyy.app` in Vercel
2. Check backend WebSocket endpoint is accessible
3. Verify no proxy/firewall blocking WSS connections

### Issue: Environment variables not working
**Solution**:
1. Verify variables are set in Vercel Dashboard for **Production** environment
2. Redeploy after adding/changing variables
3. Check variable names start with `NEXT_PUBLIC_` for client-side access

### Issue: Build fails in Vercel
**Solution**:
1. Check build logs in Vercel dashboard
2. Verify `npm run build` succeeds locally
3. Ensure all dependencies in `package.json`

---

## 📊 Performance Metrics

### Build Stats
- **Total Pages**: 25 (12 production, 13 additional)
- **Largest Page**: 264 kB (Dashboard)
- **Smallest Page**: 753 B (Agent Chat)
- **Shared JS**: 102 kB
- **Build Time**: ~6.8 seconds

### Production Pages Sizes
| Page | Size | First Load JS |
|------|------|---------------|
| Dashboard | 6.49 kB | 264 kB |
| Individual Agent | 6.34 kB | 258 kB |
| Round Table | 2.87 kB | 261 kB |
| A/B Testing | 2.9 kB | 250 kB |
| Tools | 4.42 kB | 131 kB |
| Settings | 3.99 kB | 124 kB |
| WordPress | 5.61 kB | 122 kB |
| 3D Pipeline | 4.23 kB | 106 kB |
| HF Spaces | 3.77 kB | 106 kB |
| RT History | 3.69 kB | 134 kB |
| Agents List | 1.4 kB | 149 kB |
| Agent Chat | 753 B | 148 kB |

---

## ✅ Completion Status

**Vercel Configuration**: PRODUCTION READY ✅

**What's Ready:**
- ✅ 12 production pages compile and load (including WordPress)
- ✅ Backend URL standardized to `https://api.devskyy.app`
- ✅ Environment variables configured
- ✅ CORS headers set correctly
- ✅ All navigation links validated
- ✅ Build succeeds with 0 errors
- ✅ TypeScript compilation clean
- ✅ Linting passed (4 non-blocking warnings)
- ✅ vercel.json fixed (removed invalid `rootDirectory` property)
- ✅ WordPress integration complete (12 API endpoints)

**What's Next:**
1. ✅ **Backend configured** - See `/RENDER_DEPLOYMENT_CHECKLIST.md` for deployment
2. ✅ **vercel.json fixed** - Invalid properties removed (commit `f639207de`)
3. **REQUIRED**: Configure Root Directory in Vercel Dashboard (see STEP 1 above)
4. Deploy backend to Render at `https://api.devskyy.app`
5. Configure Vercel environment variables in dashboard
6. Run `vercel --prod` to deploy frontend to `https://app.devskyy.app`
7. Test full-stack integration:
   - All 12 pages load correctly (including WordPress)
   - API connections work (Dashboard metrics, Agent list, WordPress sync)
   - WebSocket connections establish
   - Navigation links function
   - Real-time features work
8. Monitor production metrics (Prometheus)

**Deployment URLs:**
- Frontend: `https://app.devskyy.app` (Vercel - Ready)
- Backend: `https://api.devskyy.app` (Render - Ready)

---

**Last Updated**: 2026-01-12 (WordPress Integration + vercel.json Fix)
**Validated By**: Ralph Loop Production Configuration (Frontend + Backend)
**Recent Changes**:
- Added WordPress management page (12th production page)
- Fixed vercel.json (removed invalid `rootDirectory` property)
- Updated deployment instructions with Vercel Dashboard configuration steps
