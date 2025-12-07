# Implementation Guide: 35 New API Endpoints

**Date:** 2025-11-18
**Version:** 1.0.0
**Status:** Ready for Implementation

---

## Quick Start

This guide provides step-by-step instructions for implementing the 35 new API endpoints across 4 business domains.

## Files Created

### 1. Design Documentation
- **Location:** `/home/user/DevSkyy/docs/NEW_ENDPOINTS_DESIGN.md`
- **Purpose:** Comprehensive design specifications for all 35 endpoints
- **Content:**
  - Full endpoint specifications (method, path, auth, request, response)
  - Database schema designs
  - RBAC requirements
  - Rate limiting strategy
  - Webhook events
  - Integration architecture
  - Test scenarios
  - Performance SLOs

### 2. Database Models
- **Location:** `/home/user/DevSkyy/models/new_business_domains.py`
- **Purpose:** SQLAlchemy ORM models for all new tables
- **Content:**
  - 15 new database tables
  - Social Media models (4 tables)
  - Email Marketing models (5 tables)
  - Customer Service models (5 tables)
  - Payment, Notification, File Storage models (3 tables)

### 3. Pydantic Schemas
- **Location:** `/home/user/DevSkyy/api/schemas/new_domains_schemas.py`
- **Purpose:** Request/response validation models
- **Content:**
  - 70+ Pydantic models
  - Input validation with security checks
  - SQL injection prevention
  - XSS prevention
  - Field-level validators

### 4. Example Router Implementation
- **Location:** `/home/user/DevSkyy/api/v1/social_media.py`
- **Purpose:** Complete example of social media endpoint implementation
- **Content:**
  - 6 working endpoints
  - RBAC integration
  - Rate limiting hooks
  - Webhook triggers
  - AI agent integration
  - Database operations
  - Error handling

---

## Implementation Phases

### Phase 1: Database Setup (Week 1)

**Tasks:**
1. Review SQLAlchemy models in `/home/user/DevSkyy/models/new_business_domains.py`
2. Create database migration using Alembic
3. Run migrations in development environment
4. Verify all tables created correctly
5. Add indexes and constraints
6. Test database performance

**Commands:**
```bash
# Create migration
alembic revision --autogenerate -m "Add new business domain tables"

# Review migration file
cat alembic/versions/XXXX_add_new_business_domain_tables.py

# Apply migration
alembic upgrade head

# Verify tables
psql -h localhost -U postgres -d devskyy -c "\dt"
```

**Validation:**
```sql
-- Verify all tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'social_%'
   OR table_name LIKE 'email_%'
   OR table_name LIKE 'support_%'
   OR table_name LIKE 'payment_%'
   OR table_name LIKE 'chat_%'
   OR table_name LIKE 'kb_%';

-- Should return 15 tables
```

---

### Phase 2: Social Media APIs (Week 2)

**Tasks:**
1. Complete social media router implementation
2. Integrate with platform APIs (Facebook, Instagram, Twitter, LinkedIn)
3. Implement AI content optimization
4. Add rate limiting
5. Configure webhooks
6. Write unit tests
7. Write integration tests

**Implementation Checklist:**
- [ ] Create `/api/v1/social_media.py` router (example provided)
- [ ] Implement platform API integrations:
  - [ ] Facebook Graph API
  - [ ] Instagram Graph API
  - [ ] Twitter API v2
  - [ ] LinkedIn API
  - [ ] TikTok API (optional)
  - [ ] Pinterest API (optional)
- [ ] Create service layer: `/services/social_media_service.py`
- [ ] Add rate limiting middleware
- [ ] Configure webhook events
- [ ] Write tests: `/tests/api/test_social_media.py`

**Test Coverage Target:** ≥90%

**Example Test:**
```python
@pytest.mark.asyncio
async def test_create_social_post(client: AsyncClient, auth_token: str):
    response = await client.post(
        "/api/v1/social/posts",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "content": "New luxury collection! #Fashion",
            "platforms": ["instagram", "facebook"],
            "ai_optimize": True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "post_id" in data
    assert len(data["platform_results"]) == 2
```

---

### Phase 3: Email Marketing APIs (Week 3)

**Tasks:**
1. Implement email marketing router
2. Integrate with email providers (SendGrid, SES, Mailgun)
3. Set up SPF/DKIM validation
4. Implement template engine
5. Add automation workflows
6. Configure deliverability monitoring
7. Write tests

**Implementation Checklist:**
- [ ] Create `/api/v1/email_marketing.py` router
- [ ] Integrate email providers:
  - [ ] SendGrid SDK
  - [ ] Amazon SES SDK
  - [ ] Mailgun SDK (optional)
- [ ] Implement template rendering engine
- [ ] Set up automation scheduler
- [ ] Add bounce/complaint handling
- [ ] Configure DNS records (SPF, DKIM, DMARC)
- [ ] Write tests: `/tests/api/test_email_marketing.py`

**Email Provider Configuration:**
```python
# config/email_providers.py

EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "sendgrid")

SENDGRID_CONFIG = {
    "api_key": os.getenv("SENDGRID_API_KEY"),
    "default_from": os.getenv("EMAIL_DEFAULT_FROM"),
}

SES_CONFIG = {
    "aws_access_key": os.getenv("AWS_ACCESS_KEY_ID"),
    "aws_secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "region": os.getenv("AWS_REGION", "us-east-1"),
}
```

---

### Phase 4: Customer Service APIs (Week 4)

**Tasks:**
1. Implement support ticket system
2. Build live chat with WebSocket
3. Create knowledge base search
4. Integrate AI assistant
5. Add SLA tracking
6. Implement analytics dashboard
7. Write tests

**Implementation Checklist:**
- [ ] Create `/api/v1/customer_service.py` router
- [ ] Implement WebSocket for live chat
- [ ] Build ticket assignment logic
- [ ] Create KB search with full-text indexing
- [ ] Integrate AI support assistant
- [ ] Add SLA tracking and alerts
- [ ] Build agent performance analytics
- [ ] Write tests: `/tests/api/test_customer_service.py`

**WebSocket Implementation:**
```python
# api/v1/customer_service.py

from fastapi import WebSocket, WebSocketDisconnect

@router.websocket("/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()

            # Process message
            response = await process_chat_message(session_id, data)

            # Send response
            await websocket.send_json(response)

    except WebSocketDisconnect:
        logger.info(f"Chat session {session_id} disconnected")
```

---

### Phase 5: Additional Business APIs (Week 5)

**Tasks:**
1. Implement payment processing
2. Build notification system
3. Create file upload/storage
4. Add analytics/reporting
5. Implement data export
6. Write tests

**Implementation Checklist:**
- [ ] Create `/api/v1/payments.py` router
- [ ] Integrate payment gateways:
  - [ ] Stripe SDK
  - [ ] Square SDK (optional)
  - [ ] PayPal SDK (optional)
- [ ] Implement PCI DSS compliance
- [ ] Create `/api/v1/notifications.py` router
- [ ] Build multi-channel notification service
- [ ] Create `/api/v1/files.py` router
- [ ] Set up S3/CloudFlare R2 for file storage
- [ ] Write tests for all endpoints

**Payment Security:**
```python
# security/payment_encryption.py

from cryptography.fernet import Fernet

class PaymentEncryption:
    def __init__(self):
        self.key = os.getenv("PAYMENT_ENCRYPTION_KEY").encode()
        self.cipher = Fernet(self.key)

    def encrypt_card_data(self, card_data: dict) -> str:
        """Encrypt sensitive payment data"""
        json_data = json.dumps(card_data)
        encrypted = self.cipher.encrypt(json_data.encode())
        return encrypted.decode()

    def decrypt_card_data(self, encrypted_data: str) -> dict:
        """Decrypt payment data"""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return json.loads(decrypted.decode())
```

---

### Phase 6: Integration & Testing (Week 6)

**Tasks:**
1. Integrate all endpoints with main.py
2. Run comprehensive test suite
3. Perform security audit
4. Load testing
5. Fix bugs and optimize
6. Update documentation

**Integration Steps:**

**1. Register routers in main.py:**
```python
# main.py

from api.v1.social_media import router as social_router
from api.v1.email_marketing import router as email_router
from api.v1.customer_service import router as support_router
from api.v1.payments import router as payments_router
from api.v1.notifications import router as notifications_router

# Register routers
app.include_router(social_router, prefix="/api/v1/social", tags=["social-media"])
app.include_router(email_router, prefix="/api/v1/email", tags=["email-marketing"])
app.include_router(support_router, prefix="/api/v1/support", tags=["customer-service"])
app.include_router(payments_router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["notifications"])
```

**2. Run test suite:**
```bash
# Run all tests
pytest tests/ -v --cov=api --cov-report=html

# Run specific domain tests
pytest tests/api/test_social_media.py -v
pytest tests/api/test_email_marketing.py -v
pytest tests/api/test_customer_service.py -v

# Check coverage
open htmlcov/index.html
```

**3. Security audit:**
```bash
# Run Bandit security scan
bandit -r api/ -ll

# Run Safety check
safety check --json

# Run pip-audit
pip-audit

# Run OWASP dependency check
dependency-check --project devskyy --scan .
```

**4. Load testing:**
```bash
# Install autocannon
npm install -g autocannon

# Test social media endpoint
autocannon -c 100 -d 60 -m POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -b '{"content":"Test","platforms":["twitter"]}' \
  http://localhost:8000/api/v1/social/posts

# Test email endpoint
autocannon -c 50 -d 30 -m POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/email/send
```

---

### Phase 7: Deployment (Week 7)

**Tasks:**
1. Deploy to staging environment
2. Run UAT (User Acceptance Testing)
3. Configure production environment
4. Set up monitoring and alerts
5. Deploy to production
6. Monitor error rates and performance

**Deployment Checklist:**

**Staging Deployment:**
- [ ] Update staging database schema
- [ ] Deploy new endpoints to staging
- [ ] Configure staging environment variables
- [ ] Run smoke tests
- [ ] Perform UAT with stakeholders
- [ ] Document any issues

**Production Deployment:**
- [ ] Create production database backup
- [ ] Run database migrations in production
- [ ] Deploy application to production
- [ ] Configure production environment variables:
  - [ ] `SOCIAL_PLATFORM_CREDENTIALS` (encrypted)
  - [ ] `EMAIL_PROVIDER_API_KEYS` (encrypted)
  - [ ] `PAYMENT_GATEWAY_CREDENTIALS` (encrypted)
  - [ ] `ENCRYPTION_KEYS`
  - [ ] `WEBHOOK_SECRET_KEYS`
- [ ] Enable monitoring dashboards
- [ ] Set up alerts for error rates, latency, etc.
- [ ] Smoke test production endpoints
- [ ] Monitor for 24 hours

**Monitoring Setup:**
```yaml
# prometheus/alerts.yml

groups:
  - name: api_endpoints
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: SlowResponseTime
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency exceeds 200ms"
```

---

## Environment Variables

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/devskyy

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=<strong-secret-key>
JWT_SECRET_KEY=<jwt-secret-key>
ENCRYPTION_KEY=<encryption-key>

# Social Media Platforms
FACEBOOK_APP_ID=<app-id>
FACEBOOK_APP_SECRET=<app-secret>
INSTAGRAM_APP_ID=<app-id>
INSTAGRAM_APP_SECRET=<app-secret>
TWITTER_API_KEY=<api-key>
TWITTER_API_SECRET=<api-secret>
LINKEDIN_CLIENT_ID=<client-id>
LINKEDIN_CLIENT_SECRET=<client-secret>

# Email Providers
EMAIL_PROVIDER=sendgrid  # or ses, mailgun
SENDGRID_API_KEY=<api-key>
EMAIL_DEFAULT_FROM=noreply@devskyy.com
AWS_ACCESS_KEY_ID=<access-key>
AWS_SECRET_ACCESS_KEY=<secret-key>
AWS_REGION=us-east-1

# Payment Gateways
STRIPE_SECRET_KEY=<secret-key>
STRIPE_PUBLISHABLE_KEY=<publishable-key>
STRIPE_WEBHOOK_SECRET=<webhook-secret>

# File Storage
S3_BUCKET_NAME=devskyy-files
S3_ACCESS_KEY=<access-key>
S3_SECRET_KEY=<secret-key>
CDN_URL=https://cdn.devskyy.com

# Webhooks
WEBHOOK_SECRET_KEY=<secret-key>

# Monitoring
LOGFIRE_TOKEN=<token>
PROMETHEUS_ENABLED=true
```

---

## Testing Strategy

### Unit Tests (Target: ≥90% coverage)

```python
# tests/api/test_social_media.py

class TestSocialMediaEndpoints:
    @pytest.mark.asyncio
    async def test_create_post_success(self, client, auth_token):
        """Test successful post creation"""
        response = await client.post(
            "/api/v1/social/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "content": "Test post",
                "platforms": ["twitter"]
            }
        )
        assert response.status_code == 200
        assert response.json()["success"] == True

    @pytest.mark.asyncio
    async def test_create_post_invalid_platform(self, client, auth_token):
        """Test post creation with invalid platform"""
        response = await client.post(
            "/api/v1/social/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "content": "Test",
                "platforms": ["invalid"]
            }
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_post_sql_injection(self, client, auth_token):
        """Test SQL injection prevention"""
        response = await client.post(
            "/api/v1/social/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "content": "Test'; DROP TABLE social_posts; --",
                "platforms": ["twitter"]
            }
        )
        assert response.status_code == 422
```

### Integration Tests

```python
# tests/integration/test_social_media_flow.py

class TestSocialMediaIntegration:
    @pytest.mark.asyncio
    async def test_complete_post_workflow(self, client, auth_token):
        """Test complete social media posting workflow"""

        # 1. Create post
        create_response = await client.post(
            "/api/v1/social/posts",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "content": "Integration test post",
                "platforms": ["twitter"],
                "ai_optimize": True
            }
        )
        assert create_response.status_code == 200
        post_id = create_response.json()["post_id"]

        # 2. Retrieve post
        get_response = await client.get(
            f"/api/v1/social/posts/{post_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 200

        # 3. Check analytics
        analytics_response = await client.get(
            "/api/v1/social/analytics",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={
                "date_from": datetime.utcnow().isoformat(),
                "date_to": datetime.utcnow().isoformat()
            }
        )
        assert analytics_response.status_code == 200
```

---

## Performance Benchmarks

### Target SLOs

| Metric | Target | Monitoring |
|--------|--------|------------|
| API Response Time (P95) | < 200ms | Prometheus |
| API Response Time (P99) | < 500ms | Prometheus |
| Error Rate | < 0.5% | Logfire |
| Uptime | > 99.9% | StatusPage |
| Database Query Time (P95) | < 50ms | PostgreSQL |

### Load Testing Results Template

```markdown
## Load Test Results - Social Media APIs

**Date:** 2025-11-18
**Tool:** Autocannon
**Duration:** 60 seconds
**Concurrency:** 100

### POST /api/v1/social/posts

| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| Requests/sec | 850 | > 500 | ✅ |
| P95 Latency | 180ms | < 200ms | ✅ |
| P99 Latency | 420ms | < 500ms | ✅ |
| Error Rate | 0.2% | < 0.5% | ✅ |
| Throughput | 2.1 MB/s | > 1 MB/s | ✅ |
```

---

## Troubleshooting

### Common Issues

**Issue: Database connection errors**
```bash
# Check PostgreSQL status
systemctl status postgresql

# Test connection
psql -h localhost -U postgres -d devskyy -c "SELECT 1"

# Check connection pool
# In main.py, increase pool size if needed
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Increase from default 10
    max_overflow=40
)
```

**Issue: Rate limiting too strict**
```python
# Adjust rate limits in config
RATE_LIMITS = {
    "social.posts.create": "200/hour",  # Increased from 100
}
```

**Issue: Webhook delivery failures**
```python
# Check webhook logs
logger.info("Webhook delivery status", extra={
    "event_type": event_type,
    "delivery_status": status,
    "retry_count": retry_count
})

# Implement retry logic
async def deliver_webhook_with_retry(
    webhook_url: str,
    payload: dict,
    max_retries: int = 3
):
    for attempt in range(max_retries):
        try:
            response = await httpx.post(webhook_url, json=payload)
            if response.status_code == 200:
                return True
        except Exception as e:
            logger.error(f"Webhook delivery attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

    return False
```

---

## Next Steps

1. **Review Design Document:** Read `/home/user/DevSkyy/docs/NEW_ENDPOINTS_DESIGN.md`
2. **Set Up Database:** Create migrations for new tables
3. **Begin Phase 1:** Start with Social Media APIs implementation
4. **Test Continuously:** Write tests as you implement each endpoint
5. **Monitor Progress:** Use project management tools to track completion
6. **Deploy Incrementally:** Deploy each domain as completed to staging

---

## Support & Resources

- **Design Document:** `/home/user/DevSkyy/docs/NEW_ENDPOINTS_DESIGN.md`
- **Database Models:** `/home/user/DevSkyy/models/new_business_domains.py`
- **Pydantic Schemas:** `/home/user/DevSkyy/api/schemas/new_domains_schemas.py`
- **Example Router:** `/home/user/DevSkyy/api/v1/social_media.py`
- **CLAUDE.md:** Truth Protocol and DevSkyy standards

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-18
**Next Review:** Start of Phase 1 Implementation
