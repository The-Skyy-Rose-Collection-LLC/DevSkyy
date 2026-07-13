# DevSkyy Production Deployment Architecture

<!-- AUTO-GENERATED: backend-hosting facts — regenerate from fly config + main_enterprise.py -->
> **Backend hosting update (2026-07-09).** `api.devskyy.app` now resolves to a **Fly.io**
> app (`devskyy-backend`) with **Fly-managed TLS** — NOT a self-hosted server with
> `certbot`. Database is **Neon Postgres** (`DATABASE_URL` secret; `database/db.py`
> fail-loud refuses the SQLite fallback in production). Image is `Dockerfile.api` (slim,
> torch-free base; heavy ML behind the `[ml]` optional extra). Secrets are set via
> `fly secrets set`. The MCP server runs as a **separate** Fly app — confusingly named
> `devskyy-api` (`fly.toml` → `Dockerfile.mcp` → `mcp_service:app`, Python 3.12,
> ~82 tools live via `http_mount.tool_count`, bearer-auth HTTP mount at `/mcp`).
> Note the naming: `devskyy-backend` = the REST API, `devskyy-api` = the MCP. The DNS zone is
> **Vercel-managed** (`ns1/ns2.vercel-dns.com`); an explicit `api` A/AAAA record overrides
> the wildcard. The `certbot` / raw-backend-IP instructions further down are **superseded**
> by this block.
<!-- /AUTO-GENERATED -->

## Current Verified Configuration (backend hosting: Fly.io, 2026-07-09 — original diagram 2026-01-09)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GLOBAL DNS (devskyy.app)                        │
│              Domain Registrar (GoDaddy, Namecheap, etc.)                │
└─────────────────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┼────────────┬──────────────┐
        │           │            │              │
        ▼           ▼            ▼              ▼
    (A record)  (CNAME)      (A record)    (Optional)
        │           │            │              │
        │           │            │              │
    devskyy.app  app.devskyy.app  api.devskyy.app  www.devskyy.app
        │           │            │              │
        │           │            │              │
        ▼           ▼            ▼              ▼
    Redirect    Vercel       Backend      Redirect
    to app/     Edge Nodes   Server       to app/
        │           │            │              │
        └───────────┴────────┬───┴──────────────┘
                        ┌───▼──────────┐
                        │ HTTPS Layer  │
                        │ (TLS 1.3)    │
                        └───┬──────────┘
                            │
        ┌───────────────────┼────────────────────┐
        │                   │                    │
        ▼                   ▼                    ▼
   ┌─────────────┐   ┌────────────────┐   ┌──────────────┐
   │   Vercel    │   │   Backend API   │   │   Database   │
   │   (SPA)     │   │  (Python FastAPI)   │ (PostgreSQL) │
   │             │   │                │   │              │
   │ Next.js 15  │   │  Port: 443     │   │ Neon         │
   │ React       │   │  (HTTPS)       │   │ Serverless   │
   │ TypeScript  │   │                │   │              │
   │             │   │ Features:      │   │              │
   │ Dashboard   │   │ - API Routes   │   │ Connection   │
   │ 3D Viewer   │   │ - WebSocket    │   │ Pool: 20     │
   │ Collections │   │ - MCP Server   │   │              │
   │ Tools Browser   │ - Agents (54)  │   │              │
   │             │   │ - Security     │   │              │
   │ Static:     │   │ - Rate Limits  │   └──────────────┘
   │ - JS/CSS    │   │ - JWT/OAuth2   │
   │ - Assets    │   │ - CORS/CSRF    │
   │ - Images    │   │ - Encryption   │
   │             │   │ - Audit Log    │
   └────┬────────┘   └────┬───────────┘
        │                  │
        │                  │
        │ API Calls        │ Internal
        │ (HTTPS/JSON)     │ Communication
        │                  │
        └──────────┬───────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  Caching Layer      │
        │  (Redis)            │
        │                     │
        │  Upstash Redis      │
        │  (Serverless)       │
        │                     │
        │ - Sessions          │
        │ - Rate Limits       │
        │ - Cache             │
        │ - Task Queue        │
        └─────────────────────┘

```

## Service Communication Flow

### 1. Frontend to Backend (User Request)
```
User Browser (app.devskyy.app)
    │
    ├─► Next.js Page/API Route
    │
    ├─► API Rewrite (next.config.js)
    │   /api/backend/:path → https://api.devskyy.app/:path
    │
    ├─► HTTPS Request to Backend
    │   URL: https://api.devskyy.app/api/v1/...
    │   Headers: Authorization, Content-Type, CORS headers
    │
    ├─► Backend CORS Middleware (CORSMiddleware)
    │   - Validates origin: https://app.devskyy.app
    │   - Adds Access-Control-Allow-* headers
    │
    └─► FastAPI Route Handler
        - Processes request
        - Returns JSON response
        - Frontend renders result
```

### 2. Backend Internal Architecture
```
Frontend HTTPS Request
    │
    ▼
API Router (/api/v1/...)
    │
    ├─► Authentication Layer (JWT)
    │   - Validates JWT token
    │   - Checks permissions
    │
    ├─► Rate Limiting (Redis)
    │   - Checks request quota
    │   - Updates usage counter
    │
    ├─► Input Validation (Pydantic)
    │   - Type checking
    │   - Schema validation
    │
    ├─► Business Logic
    │   │
    │   ├─► Agent Selection (6 Super Agents)
    │   │   - CommerceAgent
    │   │   - CreativeAgent
    │   │   - MarketingAgent
    │   │   - SupportAgent
    │   │   - OperationsAgent
    │   │   - AnalyticsAgent
    │   │
    │   ├─► LLM Selection (6 Providers)
    │   │   - OpenAI
    │   │   - Anthropic
    │   │   - Google
    │   │   - Mistral
    │   │   - Cohere
    │   │   - Groq
    │   │
    │   ├─► Tool Execution (ToolRegistry)
    │   │   - WordPress tools
    │   │   - WooCommerce tools
    │   │   - 3D generation
    │   │   - Media creation
    │   │
    │   ├─► Database Operations (PostgreSQL)
    │   │   - ORM queries
    │   │   - Connection pooling
    │   │
    │   └─► Cache Operations (Redis)
    │       - Session storage
    │       - Data caching
    │
    ├─► Response Serialization
    │   - Convert to JSON
    │   - Add metadata
    │
    └─► Return Response
        - JSON body
        - HTTP 200/201/400/500
        - CORS headers
```

## Configuration Files and Their Purpose

### 1. Backend Configuration: `.env`
**Location**: `/Users/coreyfoster/DevSkyy/.env`
**Purpose**: Production environment variables for Python backend
<!-- AUTO-GENERATED: env names verified against main_enterprise.py + security/ + database/db.py (2026-07-09). Do not hand-edit names; regenerate from source. -->
**Key Settings** (names as read by the code — not example values):

_Security / runtime (`main_enterprise.py`):_
- `ENVIRONMENT` — `production` activates prod mode AND gates the API schema: `/docs`, `/redoc`, and `/openapi.json` all return 404 in production (`main_enterprise.py:159-165`).
- `CORS_ORIGIN_REGEX` — regex for `CORSMiddleware.allow_origin_regex` (`main_enterprise.py:201`). Unset falls back to a locked default matching only `*.devskyy.app` + the project's own Vercel deployments — **replaces the old comma-list `CORS_ORIGINS`**, which the code no longer reads. Never widen to `*.vercel.app` with credentials (bug-216).
- `ALLOWED_HOSTS` — comma-separated Host allow-list; when set, enables `TrustedHostMiddleware` (`main_enterprise.py:214-218`). Unset = middleware off (keeps Fly health checks working).
- `SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`, `SENTRY_PROFILES_SAMPLE_RATE` — Sentry init + sample rates (`main_enterprise.py:79-91`).

_Required secrets (fail-loud at startup):_
- `DATABASE_URL` — Postgres (Neon in prod). `database/db.py:328` refuses the SQLite fallback when unset in production.
- `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY`, `ENCRYPTION_MASTER_KEY` — signing / refresh / AES-256 keys via `_require_secret` (`security/jwt_oauth2_auth.py:104`, `security/infrastructure_security.py:55`).

_Other:_ `REDIS_URL`; API keys for the 6 LLM providers; 3D-generation keys (Tripo3D, Meshy, FASHN); WordPress + WooCommerce credentials; feature flags (LLM Round Table, AB Testing, etc.).
<!-- /AUTO-GENERATED -->

**Status**: ✅ Live on Fly.io + Neon (backend v3, 2026-07-09) — CORS/openapi/auth hardening deployed

### 2. Frontend Production Config: `frontend/.env.production`
**Location**: `/Users/coreyfoster/DevSkyy/frontend/.env.production`
**Purpose**: Production environment variables for Next.js frontend
**Key Settings**:
- `NEXT_PUBLIC_API_URL=https://api.devskyy.app` - API endpoint for client
- `NEXT_PUBLIC_SITE_URL=https://app.devskyy.app` - Site URL for meta tags
- `BACKEND_URL=https://api.devskyy.app` - Backend URL for server-side rewrites
- `NEXT_PUBLIC_ENABLE_3D_PIPELINE=true` - Enable 3D asset generation
- `NEXT_PUBLIC_ENABLE_ROUND_TABLE=true` - Enable LLM competition

**Status**: ✅ Configured and correct

### 3. Frontend Build Config: `frontend/next.config.js`
**Location**: `/Users/coreyfoster/DevSkyy/frontend/next.config.js`
**Purpose**: Next.js configuration for API rewrites and routing
**Key Features**:
- **Rewrites**: Maps `/api/*` to backend URL
  ```javascript
  source: '/api/:path*'
  destination: `${backendUrl}/api/:path*`
  ```
- **Environment Handling**: Uses `BACKEND_URL` env var (production-aware)
- **Fallback**: Falls back to `localhost:8000` for development
- **Remote Image Patterns**: Allows images from Google, HuggingFace, SkyyRose
- **Redirects**: Root `/` → `/dashboard`

**Status**: ✅ Configured correctly

### 4. Main Application: `main_enterprise.py`
**Location**: `/Users/coreyfoster/DevSkyy/main_enterprise.py`
**Purpose**: FastAPI application entry point
**Key Components**:
- **CORSMiddleware**: Handles CORS headers
- **Security Middleware**: CSRF, rate limiting, etc.
- **Health Endpoint**: `/health` returns service status
- **API Routers**: All agent and tool endpoints
- **WebSocket Support**: Real-time communication
- **MCP Integration**: Model Context Protocol server

**Status**: ✅ Configured and operational

## DNS Records Required

### Type: A Record (app.devskyy.app)
**Purpose**: Point frontend domain to Vercel
**Value**: Vercel provided CNAME or IP address
**TTL**: 3600 (1 hour)
**Example**:
```
Name: app
Type: CNAME
Value: your-project-name.vercel.app
```

### Type: A/AAAA Record (api.devskyy.app → Fly.io, current 2026-07-09)
**Purpose**: Point backend API at the Fly app `devskyy-backend`
**Zone**: Vercel-managed (`ns1/ns2.vercel-dns.com`) — an explicit `api` record **overrides the wildcard `*` ALIAS**, so it must be set or the API falls back to the wildcard target.
**Value**: the Fly anycast IPs from `fly ips list -a devskyy-backend` (v4 → A, v6 → AAAA)
**TTL**: 3600 (1 hour)
**Verify**: query the authoritative NS directly (`dig @ns1.vercel-dns.com api.devskyy.app`) to beat local resolver cache.
```
Name: api
Type: A     Value: <Fly v4 anycast IP from `fly ips list`>
Type: AAAA  Value: <Fly v6 anycast IP from `fly ips list`>
```
_Historical: previously an A record to a self-hosted backend server IP — no longer used._

### Type: A Record (devskyy.app - optional)
**Purpose**: Root domain handling
**Value**: Can redirect to app.devskyy.app
**TTL**: 3600 (1 hour)
**Options**:
- Option A: Set as CNAME pointing to app.devskyy.app (if using single provider)
- Option B: Set as A record and configure web server to redirect

## SSL/TLS Certificate Management

### Frontend (Vercel)
- **Provider**: Vercel (automatic)
- **Domain**: app.devskyy.app
- **Certificate**: Auto-provisioned with Let's Encrypt
- **Renewal**: Automatic (every 90 days)
- **Pinning**: Not required (Vercel managed)

### Backend (current — Fly.io, 2026-07-09)
- **Provider**: Fly.io (managed TLS via Let's Encrypt) — **supersedes the `certbot` flow below**
- **Domain**: api.devskyy.app → Fly app `devskyy-backend`
- **Configuration**:
  ```bash
  fly certs add api.devskyy.app -a devskyy-backend   # issue + auto-renew the cert
  fly certs show api.devskyy.app -a devskyy-backend   # verify issuance
  fly ips list -a devskyy-backend                      # anycast A/AAAA to point DNS at
  ```
- **Renewal**: Automatic (Fly-managed)
- _Historical (pre-2026-07-09, self-hosted — no longer used):_ `certbot certonly --standalone -d api.devskyy.app`

## Deployment Sequence

### Phase 1: Pre-Deployment (Local Verification)
1. ✅ Backend running locally (verified)
2. ✅ All configuration files exist (verified)
3. ✅ Health checks passing (verified)
4. ⏳ Frontend build test (optional locally)

### Phase 2: DNS Configuration
1. Purchase domain `devskyy.app` at registrar
2. Create DNS A/CNAME records:
   - `app.devskyy.app` → Vercel (CNAME)
   - `api.devskyy.app` → Backend IP (A)
3. Verify DNS propagation (24-48 hours)

### Phase 3: Backend Deployment
1. Prepare server with:
   - Python 3.11+
   - PostgreSQL (or Neon connection)
   - Redis (or Upstash connection)
   - SSL/TLS certificate for api.devskyy.app
2. Deploy code:
   ```bash
   git clone <repo>
   pip install -e .
   export $(cat .env | xargs)
   uvicorn main_enterprise:app --host 0.0.0.0 --port 8000 --ssl-keyfile=/path/to/key.pem --ssl-certfile=/path/to/cert.pem
   ```
3. Configure reverse proxy (nginx/Apache) if needed
4. Verify health check: `curl https://api.devskyy.app/health`

### Phase 4: Frontend Deployment
1. Connect Vercel to git repository
2. Set environment variables in Vercel dashboard:
   - `NEXT_PUBLIC_API_URL=https://api.devskyy.app`
   - `NEXT_PUBLIC_SITE_URL=https://app.devskyy.app`
   - `BACKEND_URL=https://api.devskyy.app`
3. Configure production domain in Vercel settings
4. Deploy: Vercel will auto-deploy on push to main branch
5. Verify: Visit https://app.devskyy.app

### Phase 5: Post-Deployment Verification
1. Health checks:
   - Backend: `curl https://api.devskyy.app/health`
   - Frontend: Browse to https://app.devskyy.app
2. API testing: Make request from frontend to backend
3. Certificate validation: Check SSL in browser dev tools
4. Performance: Monitor response times and error rates
5. Security: Verify HTTPS enforcement, headers, etc.

## Scaling Considerations

### Frontend (Vercel)
- **Auto-scaling**: Managed by Vercel
- **CDN**: Global edge network
- **Limits**: Handle unlimited concurrent users
- **Cost**: Pay-per-use (compute) + transfer

### Backend
- **Current**: Single instance
- **For scaling**:
  - Add load balancer (HAProxy, nginx)
  - Multiple backend instances behind load balancer
  - Database connection pooling (already configured)
  - Redis cluster for distributed caching
  - Consider Kubernetes for orchestration

### Database
- **Current**: PostgreSQL with connection pool (20)
- **Neon**: Serverless Postgres auto-scales
- **Max Connections**: Increase pool size if needed
- **Read Replicas**: Add if read traffic is high

### Cache
- **Current**: Redis with 50 connections
- **Upstash**: Serverless Redis auto-scales
- **TTL**: Configure per use case
- **Eviction**: LRU policy for memory management

## Monitoring and Observability

### Health Checks
```bash
# Backend health
curl https://api.devskyy.app/health

# Response:
{
  "status": "healthy",
  "version": "1.0.1",
  "environment": "production",
  "services": {
    "api": "operational",
    "auth": "operational",
    "encryption": "operational",
    "mcp_server": "operational",
    "agents": "operational"
  }
}
```

### Metrics to Monitor
- Response time (p50, p95, p99)
- Error rate by endpoint
- Database query performance
- Cache hit rate
- Agent execution time
- LLM token usage and cost
- API rate limit violations

### Logs to Collect
- All HTTP requests/responses
- Authentication attempts
- Database queries (slow queries)
- Error stack traces
- Security events (rate limits, CORS violations)
- Agent execution logs

## Disaster Recovery

### Backup Strategy
- **Database**: Daily automated backups to cloud storage
- **Configuration**: Version controlled in git
- **Secrets**: Managed in secure secrets manager
- **Media**: Backup WordPress uploads regularly

### Failover Procedure
1. If backend goes down:
   - Frontend shows maintenance page
   - Requests queue in Redis
   - Deploy to new instance
   - Verify health checks

2. If database goes down:
   - Restore from latest backup
   - Verify data integrity
   - Restart backend
   - Clear cache to refresh data

3. If frontend goes down:
   - Vercel auto-redeploys from git
   - DNS failover to backup CDN if configured

## Security Hardening Checklist

- [ ] ✅ HTTPS enforced on both frontend and backend
- [ ] ✅ CORS properly configured (verified with app.devskyy.app)
- [ ] ✅ JWT secret key is cryptographically secure
- [ ] ✅ Encryption master key is securely stored
- [ ] ✅ Rate limiting enabled and tuned
- [ ] ✅ CSRF protection enabled
- [ ] ✅ Security headers configured (X-Frame-Options, etc.)
- [ ] ✅ Input validation on all endpoints (Pydantic)
- [ ] ✅ SQL injection prevention (ORM usage)
- [ ] ✅ SSRF protection enabled
- [ ] ✅ Audit logging enabled
- [ ] ✅ MFA support implemented
- [ ] ✅ PII protection enabled
- [ ] ✅ Dependencies audited for vulnerabilities

## Cost Estimation

### Monthly Costs (Estimated)
- **Vercel Frontend**: $20-100 (usage-based)
- **Backend Server**: $100-500 (VPS or cloud instance)
- **Database (Neon)**: $15-50 (serverless, usage-based)
- **Cache (Upstash)**: $5-20 (serverless, usage-based)
- **Domain**: $12-15 (annual, ~$1-1.50/month)
- **SSL Certificate**: $0 (Let's Encrypt, free)
- **LLM API Calls**: $50-500+ (OpenAI, Anthropic, etc.)
- **Storage/CDN**: $10-50 (Google Cloud, etc.)

**Total**: $200-1,000+ per month depending on usage

---

**Generated**: 2026-01-09
**Status**: Production Ready
**Last Verified**: Domain Verification Script (Phase 4)
