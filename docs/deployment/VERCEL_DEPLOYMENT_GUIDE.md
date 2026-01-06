# DevSkyy Frontend Vercel Deployment Guide

## Overview

This guide walks you through deploying the DevSkyy frontend dashboard to Vercel with HuggingFace Spaces integration.

**Current Status**: Project already linked to Vercel
- **Project ID**: `prj_RrA6zFQPHsJBKFd0dseViXX2mNs8`
- **Project Name**: `devskyy-dashboard`
- **Organization**: `team_BnYeL94OWrIVtidDO4gd1c4y`

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Environment Variables](#environment-variables)
4. [Deployment Process](#deployment-process)
5. [HuggingFace Spaces Configuration](#huggingface-spaces-configuration)
6. [Verification Steps](#verification-steps)
7. [Troubleshooting](#troubleshooting)
8. [Custom Domain Setup](#custom-domain-setup)

---

## Prerequisites

- [x] GitHub account with access to DevSkyy repository
- [x] Vercel account (free tier works)
- [x] HuggingFace account with deployed Spaces
- [x] Backend API deployed (e.g., Render, Railway, or self-hosted)

---

## Initial Setup

### Option A: If Project Already Linked (Current Status)

The project is already linked to Vercel. You can:

1. **Access Dashboard**:
   ```bash
   # Open Vercel dashboard
   open https://vercel.com/dashboard
   ```

2. **Navigate to Project**:
   - Go to Projects → `devskyy-dashboard`
   - Or use direct link: https://vercel.com/your-org/devskyy-dashboard

3. **Trigger Deployment**:
   ```bash
   # From frontend directory
   cd /Users/coreyfoster/DevSkyy/frontend

   # Option 1: Deploy via CLI
   npx vercel --prod

   # Option 2: Push to main branch (auto-deploy)
   git add .
   git commit -m "chore: trigger Vercel deployment"
   git push origin main
   ```

### Option B: New Vercel Project Setup

If you need to set up a new project or link a different account:

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Link Project**:
   ```bash
   cd /Users/coreyfoster/DevSkyy/frontend
   vercel link
   ```

4. **Import from GitHub** (Alternative):
   - Go to https://vercel.com/new
   - Click "Import Git Repository"
   - Select `The-Skyy-Rose-Collection-LLC/DevSkyy`
   - Configure project settings (see below)

---

## Environment Variables

### Required Environment Variables

Set these in Vercel Dashboard → Settings → Environment Variables:

#### Production Environment

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://devskyy.onrender.com` | Backend API base URL |
| `BACKEND_URL` | `https://devskyy.onrender.com` | Backend proxy URL (server-side) |
| `NEXT_PUBLIC_WORDPRESS_URL` | `https://skyyrose.com` | WordPress site URL |
| `NODE_ENV` | `production` | Node environment |

#### Optional (Authentication)

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_STACK_PROJECT_ID` | `your-project-id` | Stack Auth project ID |
| `NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY` | `pck_...` | Stack Auth client key |
| `STACK_SECRET_SERVER_KEY` | `ssk_...` | Stack Auth server key |

### Setting Environment Variables via Dashboard

1. Go to Vercel Dashboard → Project → Settings → Environment Variables
2. Click "Add New"
3. Enter Variable Name, Value
4. Select Environment: Production (and optionally Preview, Development)
5. Click "Save"

### Setting Environment Variables via CLI

```bash
# Add environment variable
vercel env add NEXT_PUBLIC_API_URL production

# Pull environment variables locally
vercel env pull .env.local
```

### Environment File Template

Create `/frontend/.env.production` locally for reference:

```bash
# Backend API
NEXT_PUBLIC_API_URL=https://devskyy.onrender.com
BACKEND_URL=https://devskyy.onrender.com

# WordPress
NEXT_PUBLIC_WORDPRESS_URL=https://skyyrose.com

# Stack Auth (if using authentication)
NEXT_PUBLIC_STACK_PROJECT_ID=your-project-id
NEXT_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY=pck_...
STACK_SECRET_SERVER_KEY=ssk_...
```

**Note**: Don't commit this file to git. It's for reference only.

---

## Deployment Process

### Automatic Deployment (Recommended)

Vercel automatically deploys when you push to GitHub:

```bash
cd /Users/coreyfoster/DevSkyy

# Make changes and commit
git add .
git commit -m "feat: update frontend"
git push origin main

# Vercel will automatically:
# 1. Detect push to main branch
# 2. Run build process
# 3. Deploy to production
# 4. Update devskyy-dashboard.vercel.app
```

### Manual Deployment via CLI

```bash
cd /Users/coreyfoster/DevSkyy/frontend

# Preview deployment (test before production)
vercel

# Production deployment
vercel --prod
```

### Build Configuration

Vercel uses these settings (already configured in `vercel.json`):

```json
{
  "framework": "nextjs",
  "regions": ["iad1"],
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install"
}
```

**Root Directory**: `frontend/` (important!)

### Build Process

Vercel will execute:

```bash
# 1. Install dependencies
npm install

# 2. Build Next.js app
npm run build

# 3. Start production server
npm run start
```

---

## HuggingFace Spaces Configuration

### Current Spaces Setup

The following 5 HuggingFace Spaces are already configured and embedded:

| Space ID | Name | URL | Category |
|----------|------|-----|----------|
| `3d-converter` | 3D Model Converter | https://huggingface.co/spaces/skyyrose/3d-converter | Conversion |
| `flux-upscaler` | Flux Upscaler | https://huggingface.co/spaces/skyyrose/flux-upscaler | Generation |
| `lora-training-monitor` | LoRA Training Monitor | https://huggingface.co/spaces/skyyrose/lora-training-monitor | Training |
| `product-analyzer` | Product Analyzer | https://huggingface.co/spaces/skyyrose/product-analyzer | Analysis |
| `product-photography` | Product Photography | https://huggingface.co/spaces/skyyrose/product-photography | Generation |

### Configuration Location

Spaces are defined in:
- `/frontend/lib/hf-spaces.ts` - Space definitions
- `/frontend/app/ai-tools/page.tsx` - Main page component
- `/frontend/components/HFSpaceCard.tsx` - Embed component

### Adding New Spaces

To add additional HuggingFace Spaces:

1. **Edit `/frontend/lib/hf-spaces.ts`**:

```typescript
export const HF_SPACES: HFSpace[] = [
  // ... existing spaces ...
  {
    id: 'new-space',
    name: 'New AI Tool',
    description: 'Description of the new tool',
    url: 'https://huggingface.co/spaces/skyyrose/new-space',
    icon: '🚀',
    category: 'generation', // or 'analysis', 'training', 'conversion'
    tags: ['AI', 'generation', 'new'],
  },
];
```

2. **Rebuild and deploy**:
```bash
npm run build
vercel --prod
```

### HuggingFace Space Requirements

Ensure your HuggingFace Spaces:
- Are publicly accessible (or have proper auth)
- Support embedding in iframes
- Have CORS configured if needed
- Use compatible Gradio/Streamlit versions

---

## Verification Steps

### Post-Deployment Checklist

After deployment completes, verify:

#### 1. Deployment Status
```bash
# Check deployment status
vercel ls

# View deployment logs
vercel logs
```

#### 2. Frontend Access
- [ ] Open deployment URL: `https://devskyy-dashboard.vercel.app`
- [ ] Verify homepage loads without errors
- [ ] Check browser console for JavaScript errors
- [ ] Test navigation between pages

#### 3. HuggingFace Spaces Page
- [ ] Navigate to `/ai-tools` page
- [ ] Verify all 5 spaces are listed in grid view
- [ ] Click on each space card to select it
- [ ] Test tab navigation between spaces
- [ ] Verify iframes load correctly
- [ ] Test fullscreen toggle button
- [ ] Test "Open in new tab" button
- [ ] Test refresh button

#### 4. Individual Space Verification

For each space, verify:

**3D Model Converter** (`/ai-tools?space=3d-converter`):
- [ ] Space loads in iframe
- [ ] Can interact with upload interface
- [ ] No CORS or loading errors

**Flux Upscaler** (`/ai-tools?space=flux-upscaler`):
- [ ] Space loads correctly
- [ ] Image upload works
- [ ] No security warnings

**LoRA Training Monitor** (`/ai-tools?space=lora-training-monitor`):
- [ ] Monitoring interface loads
- [ ] Charts/data display correctly
- [ ] Real-time updates work

**Product Analyzer** (`/ai-tools?space=product-analyzer`):
- [ ] Analysis tools load
- [ ] Input fields functional
- [ ] Results display correctly

**Product Photography** (`/ai-tools?space=product-photography`):
- [ ] Photo generation interface loads
- [ ] Upload and generation work
- [ ] Results render properly

#### 5. Backend Integration
- [ ] API calls to backend succeed
- [ ] Check `/api/v1/health` endpoint
- [ ] Verify environment variables are applied
- [ ] Test authentication (if enabled)

#### 6. Performance & UX
- [ ] Page load time < 3 seconds
- [ ] Spaces load within 5 seconds
- [ ] No layout shift issues
- [ ] Responsive design works on mobile
- [ ] Dark mode toggle works (if applicable)

#### 7. Browser Compatibility
Test in:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile browsers (iOS Safari, Chrome Mobile)

### Automated Verification Script

Run this script to check key endpoints:

```bash
#!/bin/bash
# save as verify-deployment.sh

BASE_URL="https://devskyy-dashboard.vercel.app"

echo "Verifying DevSkyy Frontend Deployment..."

# Check homepage
echo "1. Checking homepage..."
curl -s -o /dev/null -w "%{http_code}" $BASE_URL
if [ $? -eq 0 ]; then
  echo "   ✓ Homepage accessible"
else
  echo "   ✗ Homepage failed"
fi

# Check AI Tools page
echo "2. Checking AI Tools page..."
curl -s -o /dev/null -w "%{http_code}" $BASE_URL/ai-tools
if [ $? -eq 0 ]; then
  echo "   ✓ AI Tools page accessible"
else
  echo "   ✗ AI Tools page failed"
fi

# Check backend health
echo "3. Checking backend connection..."
curl -s -o /dev/null -w "%{http_code}" $BASE_URL/api/v1/health
if [ $? -eq 0 ]; then
  echo "   ✓ Backend connected"
else
  echo "   ✗ Backend connection failed"
fi

echo "Verification complete!"
```

---

## Troubleshooting

### Common Issues

#### 1. Build Failures

**Error**: `Module not found` or dependency errors

**Solution**:
```bash
# Clear dependencies and rebuild
cd /Users/coreyfoster/DevSkyy/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

**Error**: TypeScript errors

**Solution**:
```bash
# Run type check locally
npm run type-check

# Fix type errors in code
# Then redeploy
```

#### 2. HuggingFace Spaces Not Loading

**Error**: iframes show blank or "refused to connect"

**Possible Causes**:
- Space is private or requires authentication
- Space has X-Frame-Options that prevent embedding
- CORS issues

**Solution**:
- Ensure spaces are public on HuggingFace
- Check space settings for embedding permissions
- Test space URL directly in browser
- Update iframe sandbox attributes if needed

#### 3. Environment Variables Not Applied

**Error**: API calls fail or show wrong URLs

**Solution**:
```bash
# Verify environment variables in Vercel
vercel env ls

# Redeploy to apply changes
vercel --prod
```

#### 4. Backend API Connection Fails

**Error**: `/api/v1/*` endpoints return 502 or timeout

**Possible Causes**:
- Backend is down or not deployed
- Incorrect BACKEND_URL environment variable
- CORS issues

**Solution**:
```bash
# Test backend directly
curl https://devskyy.onrender.com/api/v1/health

# Verify BACKEND_URL in Vercel settings
# Check backend logs for errors
# Ensure backend allows CORS from Vercel domain
```

#### 5. Build Timeout

**Error**: Build exceeds Vercel's time limit (10 minutes free tier)

**Solution**:
- Optimize dependencies (remove unused packages)
- Use build cache
- Consider upgrading Vercel plan if needed

### Debug Mode

Enable debug logging:

1. **Add to `next.config.js`**:
```javascript
module.exports = {
  // ... existing config
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
};
```

2. **View Vercel logs**:
```bash
vercel logs --follow
```

### Get Help

- **Vercel Support**: https://vercel.com/support
- **Next.js Docs**: https://nextjs.org/docs
- **DevSkyy Issues**: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues

---

## Custom Domain Setup

### Add Custom Domain to Vercel

1. **Go to Vercel Dashboard**:
   - Project → Settings → Domains

2. **Add Domain**:
   ```
   app.skyyrose.com
   ```

3. **Configure DNS**:

   Add these records to your DNS provider (e.g., Cloudflare):

   **Option A: CNAME Record** (Recommended)
   ```
   Type: CNAME
   Name: app
   Value: cname.vercel-dns.com
   TTL: Auto
   ```

   **Option B: A Record**
   ```
   Type: A
   Name: app
   Value: 76.76.21.21
   TTL: Auto
   ```

4. **Verify Domain**:
   - Wait for DNS propagation (up to 48 hours)
   - Vercel will automatically verify
   - SSL certificate is auto-provisioned

### Redirect Rules

Set up redirects in `vercel.json` if needed:

```json
{
  "redirects": [
    {
      "source": "/old-path",
      "destination": "/new-path",
      "permanent": true
    }
  ]
}
```

---

## Performance Optimization

### Recommended Settings

1. **Enable Edge Runtime** (for faster response):
```typescript
// app/layout.tsx
export const runtime = 'edge';
```

2. **Enable Image Optimization**:
   - Already configured in `next.config.js`
   - Supports HuggingFace CDN

3. **Enable Caching**:
   - Static assets automatically cached
   - API routes can use `Cache-Control` headers

### Monitoring

Use Vercel Analytics:
1. Enable in Project Settings → Analytics
2. View performance metrics
3. Monitor Core Web Vitals

---

## Security Considerations

### Current Security Headers

Already configured in `vercel.json`:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Content Security Policy (CSP)

Add CSP headers if needed:

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; frame-src https://huggingface.co; ..."
        }
      ]
    }
  ]
}
```

### Environment Variable Security

- Never commit `.env` files
- Use Vercel's encrypted environment variables
- Rotate secrets regularly
- Limit production variable access

---

## Rollback Procedure

### Rollback to Previous Deployment

1. **Via Dashboard**:
   - Go to Deployments tab
   - Find previous successful deployment
   - Click "..." → "Promote to Production"

2. **Via CLI**:
```bash
# List deployments
vercel ls

# Rollback to specific deployment
vercel rollback <deployment-url>
```

---

## CI/CD Integration

### GitHub Actions Integration

Vercel automatically integrates with GitHub:
- Pull requests create preview deployments
- Merges to `main` trigger production deployment
- Deployment status shown in PR checks

### Custom GitHub Actions

For additional CI steps, create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Vercel

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Run tests
        working-directory: ./frontend
        run: npm test

      - name: Build
        working-directory: ./frontend
        run: npm run build

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./frontend
```

---

## Summary

### Quick Deploy Checklist

- [x] Project linked to Vercel
- [ ] Environment variables configured
- [ ] HuggingFace Spaces accessible
- [ ] Backend API deployed and reachable
- [ ] DNS configured (if using custom domain)
- [ ] All 5 spaces verified working
- [ ] Mobile responsive tested
- [ ] Performance metrics acceptable
- [ ] Security headers configured
- [ ] Monitoring enabled

### Key URLs

- **Vercel Dashboard**: https://vercel.com/dashboard
- **Project URL**: https://devskyy-dashboard.vercel.app
- **AI Tools Page**: https://devskyy-dashboard.vercel.app/ai-tools
- **Backend API**: https://devskyy.onrender.com
- **GitHub Repo**: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy

### Support Contacts

- **DevSkyy Team**: support@skyyrose.com
- **Vercel Support**: https://vercel.com/support
- **GitHub Issues**: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues

---

**Last Updated**: 2026-01-06
**Version**: 1.0.0
**Status**: Production Ready
