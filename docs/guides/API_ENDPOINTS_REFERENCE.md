# DevSkyy API Endpoints Quick Reference

**Version:** 5.2.0
**Last Updated:** 2025-11-20

## Available Health Check Endpoints

### 1. Main Application Health Check
```
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "version": "5.2.0",
  "environment": "development|staging|production",
  "timestamp": "2025-11-20T12:00:00",
  "uptime_seconds": 123.45
}
```
**Usage:** Simple health check, no authentication required
**Docker:** ✅ Works in containers

### 2. Monitoring API Health Check
```
GET /api/v1/monitoring/health
```
**Response:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "message": "System status message",
  "checks": {
    "database": {...},
    "redis": {...},
    "services": {...}
  }
}
```
**Usage:** Comprehensive health check with detailed service status
**Docker:** ✅ Now fixed - correct routing

### 3. Detailed Health Check (Admin Only)
```
GET /api/v1/monitoring/health/detailed
```
**Auth Required:** Yes (JWT token with admin role)
**Response:** Extended health info with system metrics
**Docker:** ✅ Available

### 4. System Status
```
GET /status
```
**Response:**
```json
{
  "status": "operational",
  "version": "5.1.0-enterprise",
  "environment": "...",
  "modules": {
    "core_modules": true,
    "security_modules": true,
    "ai_services": true,
    ...
  },
  "issues": [],
  "agent_cache_size": 0
}
```
**Usage:** Comprehensive system status including all modules
**Docker:** ✅ Available

## Testing the Endpoints

### Using curl

```bash
# Test main health endpoint
curl http://localhost:8000/health

# Test monitoring health endpoint
curl http://localhost:8000/api/v1/monitoring/health

# Test system status
curl http://localhost:8000/status
```

### Using Docker

```bash
# If running in Docker
docker-compose -f docker-compose.dev.yml exec api curl http://localhost:8000/health

# From host machine (if port is exposed)
curl http://localhost:8000/health
```

### Using httpie

```bash
# Install httpie
pip install httpie

# Test endpoints
http :8000/health
http :8000/api/v1/monitoring/health
http :8000/status
```

## API Router Prefixes

All API endpoints follow this structure:

```
/api/v1/{router}/{endpoint}
```

**Available Routers:**
- `/api/v1/agents` - Agent management
- `/api/v1/auth` - Authentication
- `/api/v1/webhooks` - Webhook management
- `/api/v1/monitoring` - Monitoring & health checks ✅ FIXED
- `/api/v1/gdpr` - GDPR compliance
- `/api/v1/ml` - Machine learning operations
- `/api/v1/codex` - Code operations
- `/api/v1/dashboard` - Dashboard APIs
- `/api/v1/orchestration` - Agent orchestration
- `/api/v1/luxury-automation` - Luxury fashion automation
- `/api/v1/enterprise/auth` - Enterprise authentication
- `/api/v1/enterprise/webhooks` - Enterprise webhooks
- `/api/v1/enterprise/monitoring` - Enterprise monitoring

## Prometheus Metrics

```
GET /metrics
```
**Response:** Prometheus-formatted metrics
**Content-Type:** text/plain
**Usage:** For Prometheus scraping
**Docker:** ✅ Configured in prometheus.yml

## MCP Server Endpoint

```
GET /mcp/sse
```
**Protocol:** Server-Sent Events (SSE)
**Usage:** Model Context Protocol integration
**Tools Exposed:**
- brand_intelligence_reviewer
- seo_marketing_reviewer
- security_compliance_reviewer
- post_categorizer
- product_seo_optimizer

## API Documentation

### Development/Staging
```
GET /docs        # Swagger UI
GET /redoc       # ReDoc
GET /openapi.json  # OpenAPI spec
```

### Production
⚠️ Disabled for security (returns 404)

## Common Issues & Solutions

### Issue: "this route does not exist"
**Cause:** Incorrect URL or routing misconfiguration
**Solution:**
1. Use `/health` instead of `/api/v1/monitoring/health` for simple checks
2. Ensure Docker containers are properly networked
3. Check if service is running: `docker-compose ps`

### Issue: 404 Not Found
**Cause:** Route doesn't exist or typo in URL
**Solution:**
1. Check available routes: `curl http://localhost:8000/docs`
2. Verify the exact path from the router configuration
3. Check if the router is properly included in `main.py`

### Issue: Container Health Check Failing
**Cause:** Health endpoint not responding
**Solution:**
1. Check logs: `docker-compose logs api`
2. Verify port is exposed: `docker-compose ps`
3. Test from inside container: `docker-compose exec api curl localhost:8000/health`

### Issue: Connection Refused
**Cause:** Service not running or port not accessible
**Solution:**
1. Check service status: `docker-compose ps`
2. Restart service: `docker-compose restart api`
3. Check firewall rules
4. Verify port mapping in docker-compose.yml

## Environment-Specific Endpoints

### Development (`docker-compose.dev.yml`)
- All endpoints available
- API docs enabled at `/docs`
- Debug endpoints at `/debug/*`
- Adminer (DB UI) at http://localhost:8080
- Redis Commander at http://localhost:8081

### Staging (`docker-compose.staging.yml`)
- All endpoints available
- API docs enabled
- Monitoring at http://localhost:9090 (Prometheus)
- Dashboards at http://localhost:3000 (Grafana)

### Production (`docker-compose.prod.yml`)
- API docs disabled (security)
- `/health` and `/api/v1/monitoring/health` available
- Monitoring behind Nginx reverse proxy
- Grafana at https://your-domain.com/grafana

## Need Help?

1. **Check API docs:** http://localhost:8000/docs
2. **View system status:** http://localhost:8000/status
3. **Check logs:** `docker-compose logs -f api`
4. **Health check:** `curl http://localhost:8000/health`

---

**Last Updated:** 2025-11-20 | **Version:** 5.2.0
