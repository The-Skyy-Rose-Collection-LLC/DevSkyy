# Vercel Deployment Guide

Complete guide for deploying DevSkyy to Vercel.

---

## Deployment Options

### Option 1: Frontend Only (Recommended for Vercel)

Deploy the React frontend to Vercel and host the backend elsewhere (Railway, Render, Fly.io, or AWS).

### Option 2: Full Stack (Experimental)

Deploy both frontend and serverless Python functions to Vercel.

---

## Prerequisites

1. **Vercel Account:** Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI:** Install globally
   ```bash
   npm install -g vercel
   ```
3. **GitHub Repository:** Push code to GitHub for automatic deployments

---

## Option 1: Frontend Only Deployment (Recommended)

### Step 1: Deploy Backend Separately

**Recommended Backend Hosts:**

**Railway (Easiest):**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and initialize
railway login
railway init

# Deploy
railway up
```

**Render:**
1. Go to [render.com](https://render.com)
2. Connect GitHub repository
3. Select "Web Service"
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Fly.io:**
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Deploy
flyctl launch
flyctl deploy
```

### Step 2: Configure Environment Variables

Create `.env.production` in frontend directory:

```env
VITE_API_URL=https://your-backend-url.railway.app
VITE_APP_NAME=DevSkyy
VITE_APP_VERSION=1.0.0
```

### Step 3: Deploy Frontend to Vercel

**Via CLI:**
```bash
# From project root
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name: devskyy
# - Directory: ./
# - Override settings? No
```

**Via GitHub (Recommended):**

1. Push code to GitHub
2. Go to [vercel.com/new](https://vercel.com/new)
3. Import your repository
4. Configure:
   - **Framework Preset:** Vite
   - **Build Command:** `cd frontend && npm run build`
   - **Output Directory:** `frontend/dist`
   - **Install Command:** `cd frontend && npm install`
5. Add environment variables (see below)
6. Click **Deploy**

### Step 4: Add Environment Variables in Vercel

Go to Project Settings → Environment Variables:

**Production Variables:**
```
API_URL = https://your-backend-url.railway.app
NODE_VERSION = 20.x
VITE_API_URL = https://your-backend-url.railway.app
```

**Preview & Development:**
- Copy same variables to Preview and Development environments
- Use localhost for Development: `VITE_API_URL = http://localhost:8000`

---

## Option 2: Full Stack Deployment (Experimental)

### Step 1: Create Serverless Functions

Create `api/` directory for serverless endpoints:

```bash
mkdir -p api
```

**Example: `api/health.py`**
```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def health():
    return JSONResponse({
        "status": "healthy",
        "service": "DevSkyy API",
        "deployed_on": "vercel"
    })
```

**Note:** Vercel serverless functions have limitations:
- 10-second timeout (Hobby plan)
- 50MB deployment size limit
- Cold start latency
- Not ideal for AI agents with long processing times

### Step 2: Configure Vercel

The included `vercel.json` is pre-configured for full stack deployment.

### Step 3: Deploy

```bash
vercel --prod
```

---

## Environment Variables

### Required for Frontend

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://api.devskyy.com` |
| `NODE_VERSION` | Node.js version | `20.x` |

### Required for Backend (if using Vercel functions)

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | `sk-...` |
| `DATABASE_URL` | Database connection | `postgresql://...` or `sqlite+aiosqlite:///./devskyy.db` |
| `SECRET_KEY` | FastAPI secret | Random 32+ char string |
| `ENVIRONMENT` | Environment name | `production` |

### Optional

| Variable | Description |
|----------|-------------|
| `META_ACCESS_TOKEN` | Facebook/Instagram API |
| `ELEVENLABS_API_KEY` | Voice synthesis |
| `WORDPRESS_URL` | WordPress integration |

---

## Database Options for Production

### Option 1: Neon (Serverless PostgreSQL) - Recommended

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy connection string
4. Add to Vercel: `DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname`

**Pros:**
- Serverless (auto-scales)
- Free tier: 512MB storage
- Low latency
- Built-in connection pooling

### Option 2: Supabase (PostgreSQL + Real-time)

1. Sign up at [supabase.com](https://supabase.com)
2. Create project
3. Get connection string from Settings → Database
4. Add to Vercel: `SUPABASE_DATABASE_URL=postgresql+asyncpg://...`

**Pros:**
- Real-time subscriptions
- Built-in auth
- Storage + functions
- Generous free tier

### Option 3: PlanetScale (MySQL)

1. Sign up at [planetscale.com](https://planetscale.com)
2. Create database
3. Get connection string
4. Add to Vercel: `PLANETSCALE_DATABASE_URL=mysql+aiomysql://...`

**Pros:**
- Branching for databases
- Built-in connection pooling
- Horizontal scaling

### Option 4: Railway PostgreSQL

```bash
railway add --database postgresql
railway variables
```

Copy `DATABASE_URL` to Vercel environment variables.

---

## Deployment Workflow

### Automatic Deployments

Vercel automatically deploys on:
- **Production:** Push to `main` branch
- **Preview:** Pull requests and pushes to other branches

### Manual Deployments

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod

# Check deployment status
vercel ls

# View logs
vercel logs
```

---

## Custom Domains

### Add Custom Domain

1. Go to Project Settings → Domains
2. Add your domain: `www.devskyy.com`
3. Configure DNS:
   ```
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```
4. Vercel auto-provisions SSL certificate

### Recommended DNS Records

```
A     @       76.76.21.21
CNAME www     cname.vercel-dns.com
CNAME api     your-backend-host.railway.app
```

---

## Performance Optimization

### 1. Enable Edge Caching

Already configured in `vercel.json`:
- Static assets: 1 year cache
- API routes: No cache (dynamic)

### 2. Enable Compression

Vercel automatically compresses:
- Brotli for modern browsers
- Gzip fallback

### 3. Image Optimization

Use Vercel Image Optimization:

```tsx
import { Image } from '@vercel/image'

<Image
  src="/product.jpg"
  width={800}
  height={600}
  alt="Product"
/>
```

### 4. Edge Functions

For ultra-low latency, convert API routes to Edge Functions:

```typescript
export const config = {
  runtime: 'edge',
}
```

---

## Monitoring & Analytics

### Built-in Analytics

Enable in Project Settings → Analytics:
- Page views
- Top pages
- Traffic sources
- Real User Monitoring (RUM)

### Custom Logging

Add to `vercel.json`:
```json
{
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.11",
      "maxDuration": 10
    }
  }
}
```

View logs:
```bash
vercel logs
vercel logs --follow  # Live tail
```

---

## Troubleshooting

### Build Fails: "Module not found"

**Solution:** Ensure `package.json` is in the correct location:
```json
{
  "buildCommand": "cd frontend && npm install && npm run build",
  "installCommand": "cd frontend && npm install"
}
```

### API Routes Not Working

**Check:**
1. API routes are in `api/` directory
2. Functions are exported correctly
3. Environment variables are set
4. Check logs: `vercel logs`

### Database Connection Fails

**Solutions:**
- Verify `DATABASE_URL` format includes `+asyncpg` or `+aiomysql`
- Check SSL requirements (most cloud DBs require SSL in prod)
- Whitelist Vercel IPs (if database has firewall)
- Use connection pooling

### Cold Start Latency

**Solutions:**
- Use Edge Functions (instant)
- Add warmup function (ping every 5 minutes)
- Use smaller dependencies
- Consider dedicated backend hosting (Railway, Render)

### Environment Variables Not Updating

**Solution:**
1. Update in Vercel Dashboard
2. Trigger new deployment:
   ```bash
   vercel --prod --force
   ```

---

## Security Best Practices

### 1. Secure Environment Variables

- ✅ Use Vercel environment variables (encrypted)
- ❌ Never commit `.env` files
- ✅ Rotate API keys regularly
- ✅ Use different keys for prod/preview

### 2. Enable Security Headers

Already configured in `vercel.json`:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin

### 3. Configure CORS

Update backend CORS to allow Vercel domains:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://devskyy.vercel.app",
        "https://www.devskyy.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Rate Limiting

Add rate limiting to API routes:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/endpoint")
@limiter.limit("10/minute")
async def endpoint():
    return {"status": "ok"}
```

---

## Cost Estimation

### Vercel Pricing

**Hobby (Free):**
- Unlimited deployments
- 100GB bandwidth/month
- Serverless function executions: 100 hours/month
- **Best for:** Development, small projects

**Pro ($20/month):**
- 1TB bandwidth/month
- Serverless functions: 1000 hours/month
- Team collaboration
- Custom domains (100)
- **Best for:** Production apps, small teams

**Enterprise (Custom):**
- Unlimited everything
- SLA guarantees
- Dedicated support

### Backend Hosting (if separate)

**Railway:**
- Free: $5 credit/month (~100 hours)
- Pro: $20/month base + usage

**Render:**
- Free tier available
- Starter: $7/month (512MB RAM)
- Standard: $25/month (2GB RAM)

**Fly.io:**
- Free: 2,340 hours/month
- Pay-as-you-go after free tier

---

## CI/CD Integration

### GitHub Actions + Vercel

Create `.github/workflows/vercel.yml`:

```yaml
name: Vercel Deployment

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Vercel CLI
        run: npm install -g vercel

      - name: Pull Vercel Environment
        run: vercel pull --yes --environment=production --token=${{ secrets.VERCEL_TOKEN }}

      - name: Build Project
        run: vercel build --prod --token=${{ secrets.VERCEL_TOKEN }}

      - name: Deploy to Vercel
        run: vercel deploy --prebuilt --prod --token=${{ secrets.VERCEL_TOKEN }}
```

Add `VERCEL_TOKEN` to GitHub Secrets:
1. Generate token: https://vercel.com/account/tokens
2. Add to repository secrets

---

## Quick Start

**Deploy in 60 seconds:**

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Deploy
cd /path/to/DevSkyy
vercel

# 3. Add environment variables (via Vercel Dashboard)
# 4. Deploy to production
vercel --prod
```

---

## Support & Resources

- **Vercel Docs:** https://vercel.com/docs
- **Vercel Support:** https://vercel.com/support
- **DevSkyy Docs:** See `CLAUDE.md` and `README.md`
- **Community:** GitHub Discussions

---

**Last Updated:** 2025-10-12
**Maintained By:** DevSkyy Team
