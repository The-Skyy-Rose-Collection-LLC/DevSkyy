# DevSkyy Vercel Quick Start Guide

**🚀 Deploy in 5 Minutes**

---

## Prerequisites Check

```bash
# Verify you're in the right directory
cd /Users/coreyfoster/DevSkyy/frontend

# Check Node.js version (requires v18+)
node --version

# Verify git status
git status
```

---

## Step 1: Environment Variables (2 minutes)

### Option A: Via Vercel Dashboard

1. Go to: https://vercel.com/dashboard
2. Click on `devskyy-dashboard` project
3. Go to **Settings** → **Environment Variables**
4. Add these variables:

| Variable Name | Value | Environment |
|--------------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://devskyy.onrender.com` | Production |
| `BACKEND_URL` | `https://devskyy.onrender.com` | Production |
| `NEXT_PUBLIC_WORDPRESS_URL` | `https://skyyrose.com` | Production |

5. Click **Save**

### Option B: Via CLI

```bash
# Install Vercel CLI if needed
npm install -g vercel

# Login
vercel login

# Add environment variables
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://devskyy.onrender.com

vercel env add BACKEND_URL production
# Enter: https://devskyy.onrender.com

vercel env add NEXT_PUBLIC_WORDPRESS_URL production
# Enter: https://skyyrose.com
```

---

## Step 2: Deploy (1 minute)

### Option A: Automatic Deploy (Recommended)

```bash
# Commit and push to trigger auto-deployment
git add .
git commit -m "chore: deploy to Vercel"
git push origin main

# Vercel will automatically deploy
# Watch progress at: https://vercel.com/dashboard
```

### Option B: Manual Deploy via CLI

```bash
# Production deployment
npx vercel --prod

# Preview deployment (test first)
npx vercel
```

---

## Step 3: Verify Deployment (2 minutes)

### A. Check Deployment Status

```bash
# View recent deployments
npx vercel ls

# View logs
npx vercel logs
```

### B. Test Frontend

1. **Open deployment URL**:
   ```
   https://devskyy-dashboard.vercel.app
   ```

2. **Check homepage loads**
   - No errors in browser console
   - Navigation works
   - Branding appears correctly

### C. Test HuggingFace Spaces

1. **Navigate to AI Tools**:
   ```
   https://devskyy-dashboard.vercel.app/ai-tools
   ```

2. **Verify all 5 spaces load**:
   - [ ] 🎲 3D Model Converter
   - [ ] 🔍 Flux Upscaler
   - [ ] 📊 LoRA Training Monitor
   - [ ] 🔬 Product Analyzer
   - [ ] 📸 Product Photography

3. **Test functionality**:
   - Click on each space card
   - Verify iframe loads
   - Test fullscreen toggle
   - Test "Open in new tab" button

### D. Test Backend Connection

```bash
# Check API health
curl https://devskyy-dashboard.vercel.app/api/v1/health

# Should return 200 OK
```

---

## Quick Verification Checklist

```bash
# Run this script to verify deployment
#!/bin/bash
BASE_URL="https://devskyy-dashboard.vercel.app"

echo "🔍 Checking homepage..."
curl -sI $BASE_URL | grep "200 OK" && echo "✅ Homepage OK" || echo "❌ Homepage failed"

echo "🔍 Checking AI Tools page..."
curl -sI $BASE_URL/ai-tools | grep "200" && echo "✅ AI Tools OK" || echo "❌ AI Tools failed"

echo "🔍 Checking backend..."
curl -sI $BASE_URL/api/v1/health | grep "200" && echo "✅ Backend OK" || echo "❌ Backend failed"

echo "✅ Deployment verification complete!"
```

---

## Troubleshooting

### Issue: Build Failed

**Solution**:
```bash
# Test build locally first
cd /Users/coreyfoster/DevSkyy/frontend
npm run build

# If successful, redeploy
vercel --prod
```

### Issue: Spaces Not Loading

**Check**:
1. Are spaces public on HuggingFace?
2. Do space URLs work directly in browser?
3. Check browser console for CORS errors

**Fix**:
- Verify space URLs in `/frontend/lib/hf-spaces.ts`
- Ensure spaces allow iframe embedding
- Check HuggingFace space settings

### Issue: Backend Connection Failed

**Check**:
```bash
# Test backend directly
curl https://devskyy.onrender.com/api/v1/health

# Check environment variables
vercel env ls
```

**Fix**:
- Verify `BACKEND_URL` in Vercel settings
- Ensure backend is deployed and running
- Check backend CORS configuration

### Issue: Environment Variables Not Applied

**Solution**:
```bash
# Trigger redeployment to apply env vars
vercel --prod --force

# Or via dashboard: Deployments → Redeploy
```

---

## Next Steps

### 1. Custom Domain (Optional)

```bash
# Add domain via CLI
vercel domains add app.skyyrose.com

# Or via dashboard: Settings → Domains
```

### 2. Enable Analytics

1. Go to Vercel Dashboard → Analytics
2. Enable Web Analytics
3. Monitor Core Web Vitals

### 3. Set Up Monitoring

1. Enable Vercel Speed Insights
2. Set up error tracking (Sentry, etc.)
3. Configure uptime monitoring

---

## Rollback

If deployment has issues:

```bash
# List deployments
vercel ls

# Promote previous deployment to production
# Via dashboard: Deployments → ... → Promote to Production
```

---

## Key URLs

- **Vercel Dashboard**: https://vercel.com/dashboard
- **Production URL**: https://devskyy-dashboard.vercel.app
- **AI Tools**: https://devskyy-dashboard.vercel.app/ai-tools
- **GitHub Repo**: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy

---

## Support

- **Detailed Guide**: See `VERCEL_DEPLOYMENT_GUIDE.md`
- **Issues**: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues
- **Email**: support@skyyrose.com

---

**Status**: ✅ Ready to Deploy
**Last Updated**: 2026-01-06
