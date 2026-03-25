# Vercel Project Configuration

## ✅ Project Link Verified

**Project Name:** `devskyy`
**Project ID:** `prj_8xfdmzkns13XDOq0hKuju3CdEpWn`
**Organization:** `skkyroseco` (Team ID: `team_BnYeL94OWrIVtidDO4gd1c4y`)

---

## 🔗 Project Configuration

### vercel.json

```json
{
  "name": "devskyy",
  "framework": "nextjs",
  "buildCommand": "pnpm build",
  "devCommand": "pnpm dev",
  "installCommand": "pnpm install",
  "outputDirectory": ".next",
  "regions": ["iad1"]
}
```

### .vercel/project.json

```json
{
  "projectId": "prj_8xfdmzkns13XDOq0hKuju3CdEpWn",
  "orgId": "team_BnYeL94OWrIVtidDO4gd1c4y",
  "projectName": "devskyy"
}
```

---

## 🚀 Deployment Commands

All deployments now target the **devskyy** project:

### Quick Deploy

```bash
# Preview deployment to devskyy
pnpm deploy
# or
vercel

# Production deployment to devskyy
pnpm deploy:prod
# or
vercel --prod
```

### Automated Deploy (with checks)

```bash
# Preview with pre-checks
pnpm deploy:auto

# Production with pre-checks, build, and smoke tests
pnpm deploy:auto:prod
```

### Environment Variables

```bash
# Pull env vars from devskyy project
pnpm vercel:env:pull

# Push env vars to devskyy project
pnpm vercel:env:push

# List all env vars for devskyy
vercel env ls
```

---

## 🔄 Re-linking (if needed)

If you ever need to re-link to the devskyy project:

### Method 1: Automated Script

```bash
pnpm vercel:link:auto
# or
./scripts/link-vercel-project.sh
```

### Method 2: Direct CLI

```bash
pnpm vercel:link
# or
vercel link --project=devskyy
```

### Method 3: Manual

```bash
vercel link
# Then select:
# - Team: skkyroseco
# - Project: devskyy
```

---

## 📋 Verification

### Check Current Link

```bash
cat .vercel/project.json
```

Expected output:
```json
{
  "projectId": "prj_8xfdmzkns13XDOq0hKuju3CdEpWn",
  "orgId": "team_BnYeL94OWrIVtidDO4gd1c4y",
  "projectName": "devskyy"
}
```

### Check Vercel Dashboard

Visit: https://vercel.com/skkyroseco/devskyy

---

## 🌍 Deployment URLs

### Production

**Primary:** https://devskyy.vercel.app
**Custom domains:** (Configure in Vercel dashboard)

### Preview

Every push to non-production branches gets a preview URL:
- Format: `https://devskyy-<branch>-<team>.vercel.app`
- Or: `https://devskyy-<git-sha>-<team>.vercel.app`

---

## 📊 Available Scripts

```json
{
  "deploy": "vercel",
  "deploy:prod": "vercel --prod",
  "deploy:auto": "tsx scripts/deploy.ts",
  "deploy:auto:prod": "tsx scripts/deploy.ts --prod",
  "vercel:link": "vercel link --project=devskyy",
  "vercel:link:auto": "./scripts/link-vercel-project.sh",
  "vercel:env:pull": "vercel env pull .env.local",
  "vercel:env:push": "vercel env push .env.production",
  "vercel:logs": "vercel logs",
  "vercel:inspect": "vercel inspect",
  "vercel:project": "vercel project ls"
}
```

---

## 🔐 Environment Variables Downloaded

The following variables are now available in `.env.local`:

- ✅ API Keys: Anthropic, Cohere, Groq, Mistral, OpenAI, etc.
- ✅ Service Tokens: HuggingFace, LangChain, Context7
- ✅ DevSkyy Config: API URLs, feature flags
- ✅ 3D Services: Meshy, Fashn
- ✅ Vercel OIDC Token

---

## 🎯 Deployment Workflow

### 1. Develop Locally

```bash
pnpm dev
# Runs on http://localhost:3000
```

### 2. Test Build

```bash
pnpm build
# Ensures production build works
```

### 3. Deploy Preview

```bash
pnpm deploy
# Creates preview deployment
# URL: https://devskyy-<unique-id>.vercel.app
```

### 4. Test Preview

Visit the preview URL, verify everything works.

### 5. Deploy Production

```bash
pnpm deploy:prod
# Deploys to https://devskyy.vercel.app
```

### 6. Monitor

```bash
# View logs
pnpm vercel:logs

# View deployment details
pnpm vercel:inspect <deployment-url>
```

---

## 🛠 Automated Deployment Features

The automated deployment script (`pnpm deploy:auto:prod`) includes:

1. **Pre-deployment Checks**
   - ✅ Vercel CLI installed
   - ✅ Project linked to "devskyy"
   - ✅ Environment files present
   - ✅ Configuration validated

2. **Build Process**
   - ✅ Full TypeScript compilation
   - ✅ Next.js production build
   - ✅ Error detection

3. **Deployment**
   - ✅ Deploy to devskyy project
   - ✅ URL extraction
   - ✅ Progress monitoring

4. **Post-deployment**
   - ✅ Wait for deployment to be ready
   - ✅ Smoke tests (production only)
   - ✅ Deployment logging

---

## 🔧 Troubleshooting

### "Project not linked" Error

```bash
pnpm vercel:link
```

### "Wrong project" Warning

If deploying to wrong project:

```bash
# Remove old link
rm -rf .vercel

# Re-link to devskyy
pnpm vercel:link
```

### Environment Variables Missing

```bash
# Pull latest from Vercel
pnpm vercel:env:pull

# This updates .env.local with all devskyy project vars
```

### Build Fails on Vercel

```bash
# Test build locally first
pnpm build

# If it works locally but fails on Vercel:
# 1. Check Vercel build logs
# 2. Verify environment variables set correctly
# 3. Check Node.js version matches (package.json engines)
```

---

## 📱 Dashboard Access

**Vercel Dashboard:** https://vercel.com/skkyroseco/devskyy

From here you can:
- View all deployments
- Manage environment variables
- Configure custom domains
- View analytics
- Monitor performance
- Configure build settings
- Set up webhooks

---

## ✅ Current Status

- ✅ Project linked to **devskyy**
- ✅ Environment variables synced
- ✅ Build configuration set
- ✅ Deployment scripts ready
- ✅ Automated deployment available
- ✅ Pre-deployment checks enabled

**Ready to deploy!** 🚀

---

## 🎯 Next Steps

1. **Deploy to Preview:**
   ```bash
   pnpm deploy:auto
   ```

2. **Verify Preview Works:**
   - Visit the preview URL
   - Test all features
   - Check analytics integration

3. **Deploy to Production:**
   ```bash
   pnpm deploy:auto:prod
   ```

4. **Monitor Deployment:**
   ```bash
   pnpm vercel:logs
   ```

5. **Configure Custom Domain (Optional):**
   - Visit Vercel dashboard
   - Go to Settings → Domains
   - Add your custom domain

---

**Last Updated:** 2026-02-19
**Project:** devskyy
**Organization:** skkyroseco
