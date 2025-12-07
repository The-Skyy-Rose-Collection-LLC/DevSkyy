# Vercel Deployment Guide

## ✅ Ready to Deploy

Your DevSkyy Enterprise Platform is fully configured for Vercel deployment.

## Quick Deploy

### Option 1: Deploy via GitHub (Recommended)

1. **Connect Repository to Vercel**:
   - Go to [vercel.com](https://vercel.com/)
   - Click "Add New Project"
   - Import your GitHub repository: `The-Skyy-Rose-Collection-LLC/DevSkyy`

2. **Configure Project**:
   - **Framework Preset**: Other
   - **Build Command**: Auto-detected from `vercel.json`
   - **Output Directory**: `.` (current directory)
   - **Install Command**: Auto-detected from `vercel.json`

3. **Environment Variables** (Required):
   Set these in Vercel Dashboard > Settings > Environment Variables:

   ```bash
   # Core Configuration
   PYTHONPATH=.
   ENVIRONMENT=production
   LOG_LEVEL=INFO

   # API Keys (Add your actual keys)
   ANTHROPIC_API_KEY=your_anthropic_key_here
   OPENAI_API_KEY=your_openai_key_here

   # Database (Optional - Vercel uses SQLite by default)
   DATABASE_URL=sqlite:///./devskyy.db

   # Security (Generate secure random strings)
   JWT_SECRET=your_secure_jwt_secret_here
   SECRET_KEY=your_secure_secret_key_here
   ```

4. **Deploy**:
   - Click "Deploy"
   - Vercel will automatically deploy on every push to main branch

### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy to production
vercel --prod

# Or deploy preview
vercel
```

## Configuration Files

### ✅ `vercel.json` (Already Configured)
- Python 3.11 runtime
- FastAPI application
- Security headers
- 50MB max bundle size
- 30s function timeout
- 1024MB memory

### ✅ `requirements.vercel.txt` (Already Created)
- Minimal production dependencies
- Optimized for Vercel bundle size limits
- Security-hardened packages
- Essential APIs only (Claude, OpenAI)

### ✅ `.vercelignore` (Already Configured)
- Excludes test files
- Excludes documentation
- Excludes development tools
- Keeps bundle size minimal

## Build Process

When you deploy, Vercel will:

1. **Install Python 3.11**
2. **Install dependencies** from `requirements.vercel.txt`
3. **Build the application**
4. **Create serverless function** from `main.py`
5. **Deploy to edge network**

## Deployment URLs

After deployment, you'll get:

- **Production**: `https://devskyy.vercel.app`
- **Preview**: `https://devskyy-{git-branch}.vercel.app`
- **API Docs**: `https://devskyy.vercel.app/api/v1/docs`
- **Health Check**: `https://devskyy.vercel.app/health`

## Features Included in Vercel Deployment

### ✅ Included (Lightweight)
- ✅ FastAPI REST API
- ✅ Authentication & JWT
- ✅ SQLite database
- ✅ Claude API integration
- ✅ OpenAI API integration
- ✅ Security middleware
- ✅ Rate limiting
- ✅ Logging

### ⚠️ Excluded (Bundle Size Limits)
- ❌ PyTorch / ML models (use API calls instead)
- ❌ Computer vision libraries (use external services)
- ❌ Video processing (use external services)
- ❌ Web automation (Selenium/Playwright)
- ❌ Heavy data science libraries

**For full feature set**, use Docker deployment instead.

## Environment Variables Reference

### Required
```bash
ANTHROPIC_API_KEY=sk-ant-...        # Claude API key
OPENAI_API_KEY=sk-...               # OpenAI API key
JWT_SECRET=random-secret-string     # JWT signing key
SECRET_KEY=another-random-string    # Application secret
```

### Optional
```bash
# Database
DATABASE_URL=sqlite:///./devskyy.db
POSTGRES_URL=postgresql://...       # For Neon/Supabase

# Monitoring
SENTRY_DSN=https://...              # Error tracking
DATADOG_API_KEY=...                 # APM monitoring

# Features
ENABLE_CORS=true
CORS_ORIGINS=https://yourdomain.com
MAX_UPLOAD_SIZE=10485760           # 10MB default
```

## Post-Deployment Verification

1. **Check Health Endpoint**:
   ```bash
   curl https://devskyy.vercel.app/health
   ```

2. **Test API Documentation**:
   - Visit: `https://devskyy.vercel.app/api/v1/docs`
   - Verify all endpoints load

3. **Test Authentication**:
   ```bash
   curl -X POST https://devskyy.vercel.app/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"your_password"}'
   ```

4. **Monitor Logs**:
   - Go to Vercel Dashboard > Your Project > Logs
   - Check for errors or warnings

## Automatic Deployments

Configured in `vercel.json`:

- ✅ **Auto-deploy on push to main** - Production deployment
- ✅ **Auto-deploy on PR** - Preview deployment
- ✅ **Auto-cancel previous builds** - Save build minutes

## Performance & Limits

### Vercel Hobby (Free) Limits:
- **Bandwidth**: 100 GB/month
- **Serverless Function Execution**: 100 GB-hours
- **Build Time**: 6000 minutes/month
- **Max Function Duration**: 10s (Hobby) / 30s (Pro)
- **Max Function Size**: 50MB

### Vercel Pro Limits:
- **Bandwidth**: 1 TB/month
- **Serverless Function Execution**: 1000 GB-hours
- **Build Time**: Unlimited
- **Max Function Duration**: 300s
- **Max Function Size**: 50MB

## Troubleshooting

### Build Fails - Bundle Too Large
**Solution**: Check `requirements.vercel.txt` only includes essential packages

### Function Timeout
**Solution**:
- Optimize slow database queries
- Use caching (Redis via Vercel KV)
- Consider upgrading to Pro plan (300s timeout)

### Database Connection Issues
**Solution**:
- Vercel serverless functions are stateless
- Use Neon/Supabase for PostgreSQL
- Or Vercel Postgres (built-in)

### Missing Environment Variables
**Solution**:
- Add in Vercel Dashboard > Settings > Environment Variables
- Redeploy after adding variables

## Migration from Other Platforms

### From Cloudflare Pages:
- ✅ Already configured for Vercel
- ✅ Remove any Cloudflare-specific files (already done)
- ✅ Update DNS to point to Vercel

### From Heroku:
- ✅ Export environment variables from Heroku
- ✅ Import to Vercel dashboard
- ✅ Update `DATABASE_URL` if using Heroku Postgres

## Security Best Practices

1. **Never commit secrets**:
   - ✅ Use Vercel Environment Variables
   - ✅ Keep `.env` in `.gitignore`

2. **Enable security headers**:
   - ✅ Already configured in `vercel.json`
   - ✅ HSTS, X-Frame-Options, CSP, etc.

3. **Use HTTPS only**:
   - ✅ Vercel enforces HTTPS by default

4. **Rate limiting**:
   - ✅ Configured via `slowapi` middleware

## Custom Domain Setup

1. Go to Vercel Dashboard > Your Project > Settings > Domains
2. Add your custom domain (e.g., `api.skyy-rose.com`)
3. Update DNS records as instructed by Vercel
4. SSL certificate auto-provisioned

## Monitoring & Analytics

### Built-in Vercel Analytics:
- Go to Dashboard > Analytics
- View request count, response times, errors

### External Monitoring (Optional):
- **Sentry**: Error tracking
- **Datadog**: APM monitoring
- **LogDNA**: Log aggregation

## Support & Resources

- **Vercel Docs**: https://vercel.com/docs
- **FastAPI Deployment**: https://vercel.com/guides/deploying-fastapi-with-vercel
- **Python on Vercel**: https://vercel.com/docs/functions/serverless-functions/runtimes/python
- **Project Issues**: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues

---

## Quick Reference

```bash
# Deploy to production
vercel --prod

# Deploy preview
vercel

# View logs
vercel logs

# List deployments
vercel ls

# Environment variables
vercel env add
vercel env ls

# Pull environment variables locally
vercel env pull
```

---

**Status**: ✅ Ready for Vercel Deployment
**Configuration**: Complete
**Last Updated**: 2025-11-19
**Version**: 5.2.0-enterprise
