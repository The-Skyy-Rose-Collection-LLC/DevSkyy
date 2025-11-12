# DevSkyy Vercel Subproject

## Overview

This directory contains Vercel-specific configurations and dependencies for serverless deployment of the DevSkyy platform. The Vercel setup is optimized for fast cold starts and minimal bundle size.

## Structure

```
vercel/
├── requirements.txt          # Vercel-specific Python dependencies (isolated)
└── README.md                # This file
```

Additional Vercel-related files in root:
- `requirements.vercel.txt` (legacy - being consolidated)
- `vercel.json` (Vercel configuration)
- `vercel_startup.py` (Serverless initialization)
- `.vercelignore` (Exclude files from deployment)
- `.env.vercel` (Vercel environment template)

## Dependencies

The `requirements.txt` file contains minimal dependencies for serverless:

### Core Framework (Lightweight)
- **FastAPI**: 0.119.0
- **Uvicorn**: 0.34.0
- **Starlette**: 0.48.0
- **Pydantic**: 2.7.4

### Essential Services
- **SQLAlchemy**: 2.0.36 (database)
- **Alembic**: 1.14.0 (migrations)
- **Redis**: 5.2.1 (caching)

### AI Integration (SDK Only)
- **Anthropic**: 0.69.0 (Claude API client)
- **OpenAI**: 2.3.0 (GPT API client)

### Security & Monitoring
- **PyJWT**: 2.10.1
- **cryptography**: 46.0.2
- **structlog**: 24.4.0
- **prometheus-client**: 0.22.0

**Excluded**: Heavy ML libraries (torch, tensorflow, transformers) - reduces cold start from ~30s to ~2s

## Why Vercel?

Vercel provides:
- ✅ Automatic HTTPS and CDN
- ✅ Serverless functions (no infrastructure management)
- ✅ Edge deployment (global performance)
- ✅ Zero-config deployments
- ✅ Preview deployments for PRs
- ✅ Built-in analytics and monitoring

## Configuration

### Vercel Configuration (`vercel.json`)

```json
{
  "version": 2,
  "name": "devskyy-enterprise-platform",
  "framework": "other",
  "buildCommand": "pip install -r vercel/requirements.txt",
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb",
        "runtime": "python3.11"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "main.py"
    }
  ],
  "env": {
    "ENVIRONMENT": "production",
    "LOG_LEVEL": "INFO"
  }
}
```

### Environment Variables

Set in Vercel Dashboard or via CLI:

```bash
# Required
vercel env add ANTHROPIC_API_KEY production
vercel env add OPENAI_API_KEY production
vercel env add DATABASE_URL production

# Optional
vercel env add REDIS_URL production
vercel env add SENTRY_DSN production
```

## Deployment

### Initial Deployment

```bash
# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy to production
vercel --prod
```

### Automatic Deployments

Vercel automatically deploys on:
- Push to `main` branch → Production
- Pull requests → Preview deployments
- Push to other branches → Development deployments

### Manual Deployment

```bash
# Preview deployment
vercel

# Production deployment
vercel --prod

# Specify environment
vercel --env ENVIRONMENT=staging
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r vercel/requirements.txt

# Set environment variables
export ENVIRONMENT=development
export ANTHROPIC_API_KEY=your_key

# Run development server
vercel dev
# or
uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```

### Testing Locally

```bash
# Run tests
pytest tests/ -v

# Test with Vercel runtime
vercel dev --debug
```

## Optimization

### Bundle Size Optimization

**Heavy Dependencies Excluded:**
```python
# ❌ NOT included in vercel/requirements.txt
torch==2.9.0           # ~2GB
tensorflow==2.16.2     # ~500MB
transformers==4.57.1   # ~300MB
```

**Lightweight Alternatives:**
```python
# ✅ Use API endpoints instead
anthropic==0.69.0      # ~50KB (SDK only)
openai==2.3.0          # ~100KB (SDK only)
```

### Cold Start Optimization

**Before** (with ML libs): ~25-30 seconds
**After** (API-only): ~2-3 seconds

```python
# Use hosted ML endpoints
import anthropic

client = anthropic.Client(api_key=os.environ["ANTHROPIC_API_KEY"])
response = client.messages.create(
    model="claude-sonnet-4-5",
    messages=[{"role": "user", "content": "Analyze this product"}]
)
```

### Caching Strategy

```python
from redis import Redis

# Cache expensive operations
cache = Redis.from_url(os.environ["REDIS_URL"])

def get_recommendations(user_id: str):
    cached = cache.get(f"recs:{user_id}")
    if cached:
        return json.loads(cached)
    
    # Fetch from API
    recs = call_recommendation_api(user_id)
    cache.setex(f"recs:{user_id}", 3600, json.dumps(recs))
    return recs
```

## API Routes

### Serverless Functions

Each API route is deployed as a serverless function:

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/products")
async def get_products():
    """Serverless function for product listing"""
    return await fetch_products()

@app.post("/api/ai/generate")
async def generate_content(prompt: str):
    """Serverless AI content generation"""
    return await claude_generate(prompt)
```

### Edge Functions (Future)

```javascript
// edge-functions/middleware.js
export default function middleware(request) {
  // Run at the edge for ultra-low latency
  return new Response("Edge response");
}
```

## Monitoring

### Vercel Analytics

Built-in analytics for:
- Request counts
- Response times
- Error rates
- Bandwidth usage

### Custom Metrics

```python
from prometheus_client import Counter, Histogram

api_requests = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration'
)
```

### Logging

```python
import structlog

logger = structlog.get_logger()

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info("request_started", path=request.url.path)
    response = await call_next(request)
    logger.info("request_completed", 
                path=request.url.path,
                status=response.status_code)
    return response
```

## Security

### Security Headers

Configured in `vercel.json`:
```json
{
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {"key": "X-Content-Type-Options", "value": "nosniff"},
        {"key": "X-Frame-Options", "value": "DENY"},
        {"key": "Strict-Transport-Security", 
         "value": "max-age=31536000"}
      ]
    }
  ]
}
```

### Environment Secrets

```bash
# Never commit secrets
# Use Vercel environment variables instead

# Add secret
vercel env add SECRET_KEY production

# Use in code
import os
SECRET_KEY = os.environ.get("SECRET_KEY")
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/products")
@limiter.limit("100/minute")
async def get_products():
    return {"products": [...]}
```

## Limitations

### Vercel Serverless Constraints

- **Max execution time**: 60 seconds (Hobby), 300 seconds (Pro)
- **Max payload size**: 4.5MB (request), 4.5MB (response)
- **Max function size**: 50MB (uncompressed)
- **Cold start**: 2-5 seconds (optimized)

### Workarounds

**Long-running tasks:**
```python
# Use background jobs
import asyncio
asyncio.create_task(long_running_task())
return {"status": "processing"}
```

**Large payloads:**
```python
# Use streaming
from fastapi.responses import StreamingResponse

@app.get("/api/large-export")
async def export_data():
    async def generate():
        for chunk in data_chunks():
            yield chunk
    return StreamingResponse(generate())
```

## Best Practices

1. **Minimize Dependencies**: Use API clients, not full frameworks
2. **Cache Aggressively**: Reduce API calls and database queries
3. **Async Everything**: Use `async/await` for non-blocking I/O
4. **Environment Variables**: Never hardcode secrets
5. **Error Handling**: Graceful degradation on failures
6. **Monitoring**: Track performance and errors
7. **Security**: Validate inputs, sanitize outputs
8. **Testing**: Test locally before deploying

## Troubleshooting

### Deployment Failures

```bash
# Check build logs
vercel logs

# Deploy with debug info
vercel --debug

# Clear cache
vercel --force
```

### Runtime Errors

```bash
# Check function logs
vercel logs <deployment-url>

# Inspect specific function
vercel logs <deployment-url> --follow
```

### Performance Issues

```bash
# Check bundle size
du -sh .vercel/output/functions/*.func

# Optimize imports
# Use conditional imports for heavy modules
```

## Related Documentation

- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI on Vercel](https://vercel.com/guides/deploying-fastapi-with-vercel)
- [DevSkyy Vercel Build Config](/VERCEL_BUILD_CONFIG.md)
- [Deployment Guide](/DEPLOYMENT_GUIDE.md)

## CI/CD Integration

Vercel workflow automated via GitHub Actions:
- Workflow: `.github/workflows/vercel.yml`
- Preview deployments on PRs
- Production deployments on main
- Automatic rollbacks on failures

## Migration Path

### From Full Deployment to Vercel

1. **Identify heavy dependencies** → Move to separate services
2. **Refactor ML operations** → Use API endpoints
3. **Optimize bundle size** → Use `vercel/requirements.txt`
4. **Configure environment** → Set all required env vars
5. **Deploy to preview** → Test before production
6. **Monitor performance** → Verify cold start times
7. **Deploy to production** → Switch DNS/traffic

### Hybrid Deployment

```
┌─────────────────┐
│  Vercel (API)   │ ← Lightweight, serverless
├─────────────────┤
│  Docker (ML)    │ ← Heavy ML models, GPU
├─────────────────┤
│  MCP (Agents)   │ ← Agent orchestration
└─────────────────┘
```
