# WooCommerce + SEO Services Integration Plan
## GOD MODE 3.0 Analysis Response

**Date:** 2025-01-10
**Prepared by:** Claude Code - DevSkyy Integration Team
**Status:** AWAITING USER APPROVAL

---

## 📊 Current State Analysis

### ✅ What EXISTS (Verified in Codebase)

#### 1. **WooCommerce Services** (2 implementations)
- **`services/woocommerce_importer.py`** (Original - 300+ lines)
  - Google Sheets → WooCommerce integration
  - Batch processing with retry logic
  - Telegram notifications
  - Category mapping
  - Image handling
  - Progress tracking

- **`services/woocommerce_importer_service.py`** (New - 200+ lines)
  - Simpler REST API implementation
  - Product transformation logic
  - Connection testing

#### 2. **SEO Services** (2 implementations)
- **`services/seo_optimizer.py`** (Original - 400+ lines)
  - AI-powered (Claude Sonnet 4 + GPT-4)
  - Structured output parsing
  - Multi-provider fallback
  - Character limit validation (60/160)
  - Keyword optimization

- **`services/seo_optimizer_service.py`** (New - 300+ lines)
  - Meta title/description generation
  - URL slug generation
  - Keyword extraction
  - JSON-LD structured data

#### 3. **E-Commerce Agents**
- **`agent/ecommerce/product_manager.py`**
  - ML-powered product categorization
  - SEO metadata generation
  - Variant generation

- **`agent/ecommerce/pricing_engine.py`**
  - Dynamic pricing optimization

- **`agent/ecommerce/inventory_optimizer.py`**
  - Inventory management

#### 4. **API Endpoints (NOT INTEGRATED)**
- **`api/v1/ecommerce.py`**
  - ✅ Endpoints defined: `/import-products`, `/generate-seo`
  - ❌ Dependency injection raises `NotImplementedError`
  - ❌ Services not wired to endpoints

---

## ❌ What's MISSING (The Gap)

Based on feedback analysis:

### Critical Gaps
1. **No Unified Optimization Endpoint** - `/api/v1/ecommerce/products/optimize` doesn't exist
2. **Service Dependency Injection Broken** - `get_importer_service()` and `get_seo_service()` throw NotImplementedError
3. **No Service Integration** - WooCommerce and SEO services operate in isolation
4. **No Webhook System** - No real-time updates on inventory/price changes
5. **No Job Queue** - No async task processing (Celery/Redis)
6. **No Comprehensive Health Checks** - WooCommerce/SEO service availability not monitored

### Architecture Gaps
- No atomic transactions (WooCommerce sync + SEO optimization)
- No parallel processing for bulk operations
- No retry/circuit breaker patterns
- No SERP tracking integration
- No job status tracking (Redis/database)

---

## 🎯 Proposed Implementation (Based on Feedback)

### Model Selection: **Model B (Parallel) + Model C (Continuous)**

**Rationale:**
- Model B: Handles bulk imports efficiently (1000s of products)
- Model C: Maintains SEO freshness on inventory/price changes

---

## 📋 Implementation Roadmap

### ✅ PHASE 1: Service Integration & Dependency Injection (4-6 hours)
**Priority:** CRITICAL | **Risk:** Low

#### Task 1.1: Fix E-Commerce API Dependency Injection
**File:** `api/v1/ecommerce.py`

```python
# Replace NotImplementedError with actual service initialization

from services.woocommerce_importer import WooCommerceImporterService
from services.seo_optimizer import SEOOptimizerService
from config import settings  # Load from environment

def get_importer_service() -> WooCommerceImporterService:
    """Get WooCommerce importer service instance"""
    return WooCommerceImporterService(
        woo_url=settings.WOOCOMMERCE_URL,
        woo_consumer_key=settings.WOOCOMMERCE_CONSUMER_KEY,
        woo_consumer_secret=settings.WOOCOMMERCE_CONSUMER_SECRET,
        google_credentials=settings.GOOGLE_CREDENTIALS,
        telegram_bot_token=settings.TELEGRAM_BOT_TOKEN,
        telegram_chat_id=settings.TELEGRAM_CHAT_ID
    )

def get_seo_service() -> SEOOptimizerService:
    """Get SEO optimizer service instance"""
    return SEOOptimizerService(
        anthropic_api_key=settings.ANTHROPIC_API_KEY,
        openai_api_key=settings.OPENAI_API_KEY,
        primary_provider="anthropic",
        model="claude-sonnet-4-20250514"
    )
```

**Verification:**
- [ ] Both services instantiate without errors
- [ ] API endpoints return 200 (not 500 NotImplementedError)
- [ ] Configuration loaded from environment variables

---

### ✅ PHASE 2: Unified Optimization Endpoint (6-8 hours)
**Priority:** HIGH | **Risk:** Medium

#### Task 2.1: Create `/api/v1/ecommerce/products/optimize` Endpoint

**File:** `api/v1/ecommerce.py` (NEW ENDPOINT)

```python
class OptimizeProductsRequest(BaseModel):
    """Request for unified product optimization"""
    product_ids: List[int] = Field(..., description="Product IDs to optimize")
    woocommerce_sync: bool = Field(True, description="Sync with WooCommerce")
    seo_optimize: bool = Field(True, description="Run SEO optimization")
    update_metadata: bool = Field(True, description="Update WooCommerce meta fields")
    webhook_trigger: Optional[str] = Field(None, description="Webhook URL on completion")

class OptimizeProductsResponse(BaseModel):
    """Response from optimization job"""
    job_id: str
    status: str  # queued, processing, completed, failed
    products: List[int]
    steps: List[Dict]  # Track each step's progress
    eta_seconds: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]

@router.post("/products/optimize", response_model=OptimizeProductsResponse)
async def optimize_products(
    request: OptimizeProductsRequest,
    background_tasks: BackgroundTasks,
    importer: WooCommerceImporterService = Depends(get_importer_service),
    seo: SEOOptimizerService = Depends(get_seo_service)
):
    """
    Unified product optimization: WooCommerce sync + SEO optimization

    Executes in parallel:
    1. WooCommerce inventory/pricing sync
    2. SEO metadata generation (AI-powered)
    3. Update WooCommerce with SEO metadata
    4. Trigger webhook if specified

    Returns job ID for async tracking.
    """
    job_id = f"opt-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

    # Queue optimization job
    background_tasks.add_task(
        _execute_optimization_job,
        job_id=job_id,
        product_ids=request.product_ids,
        woocommerce_sync=request.woocommerce_sync,
        seo_optimize=request.seo_optimize,
        update_metadata=request.update_metadata,
        webhook_url=request.webhook_trigger,
        importer=importer,
        seo=seo
    )

    return OptimizeProductsResponse(
        job_id=job_id,
        status="queued",
        products=request.product_ids,
        steps=[],
        eta_seconds=len(request.product_ids) * 5,  # 5 sec/product estimate
        started_at=datetime.utcnow()
    )
```

#### Task 2.2: Implement Background Job Executor

```python
async def _execute_optimization_job(
    job_id: str,
    product_ids: List[int],
    woocommerce_sync: bool,
    seo_optimize: bool,
    update_metadata: bool,
    webhook_url: Optional[str],
    importer: WooCommerceImporterService,
    seo: SEOOptimizerService
):
    """Execute optimization job with parallel processing"""

    job_state = {
        "job_id": job_id,
        "status": "processing",
        "steps": [],
        "started_at": datetime.utcnow()
    }

    try:
        # Step 1: WooCommerce sync (parallel)
        if woocommerce_sync:
            sync_results = await asyncio.gather(
                *[importer.sync_product(pid) for pid in product_ids],
                return_exceptions=True
            )
            job_state["steps"].append({
                "step": "woocommerce_sync",
                "status": "completed",
                "products_synced": len([r for r in sync_results if not isinstance(r, Exception)])
            })

        # Step 2: SEO optimization (parallel)
        if seo_optimize:
            seo_results = await asyncio.gather(
                *[seo.generate_seo_metadata(pid) for pid in product_ids],
                return_exceptions=True
            )
            job_state["steps"].append({
                "step": "seo_optimization",
                "status": "completed",
                "seo_scores": {
                    pid: result.get("seo_score", 0)
                    for pid, result in zip(product_ids, seo_results)
                    if not isinstance(result, Exception)
                }
            })

        # Step 3: Update WooCommerce metadata
        if update_metadata and seo_optimize:
            update_results = await asyncio.gather(
                *[importer.update_product_metadata(pid, seo_results[i])
                  for i, pid in enumerate(product_ids)],
                return_exceptions=True
            )
            job_state["steps"].append({
                "step": "metadata_update",
                "status": "completed",
                "products_updated": len([r for r in update_results if not isinstance(r, Exception)])
            })

        # Step 4: Trigger webhook
        if webhook_url:
            await _trigger_webhook(webhook_url, job_state)

        job_state["status"] = "completed"
        job_state["completed_at"] = datetime.utcnow()

    except Exception as e:
        logger.error(f"Optimization job {job_id} failed: {e}")
        job_state["status"] = "failed"
        job_state["error"] = str(e)

    finally:
        # Store job state in Redis (TTL: 24h)
        await redis_client.setex(f"job:{job_id}", 86400, json.dumps(job_state, default=str))
```

**Verification:**
- [ ] Endpoint accepts bulk product IDs (tested with 10, 100, 1000 products)
- [ ] Parallel processing completes faster than sequential
- [ ] Job state persisted in Redis
- [ ] Error handling for partial failures
- [ ] Webhook triggered on completion

---

### ✅ PHASE 3: SEO Metadata Auto-Sync (3-4 hours)
**Priority:** HIGH | **Risk:** Medium

#### Task 3.1: Implement Auto-Sync on Product Creation/Update

**File:** `services/woocommerce_integration.py` (NEW)

```python
class WooCommerceIntegration:
    """Unified WooCommerce + SEO integration"""

    def __init__(self, importer: WooCommerceImporterService, seo: SEOOptimizerService):
        self.importer = importer
        self.seo = seo

    async def create_product_with_seo(self, product_data: Dict) -> Dict:
        """
        Create product in WooCommerce with auto-generated SEO metadata

        Workflow:
        1. Generate SEO metadata (AI-powered)
        2. Create product in WooCommerce
        3. Update product with SEO metadata
        4. Return complete product data
        """

        # Step 1: Generate SEO
        seo_metadata = await self.seo.generate_seo_metadata(
            ProductInfo(
                title=product_data["name"],
                category=product_data.get("category", ""),
                short_description=product_data.get("short_description", ""),
                description=product_data.get("description", ""),
                keywords=product_data.get("keywords")
            )
        )

        # Step 2: Add SEO to product data
        product_data["meta_data"] = [
            {"key": "_yoast_wpseo_title", "value": seo_metadata["metatitle"]},
            {"key": "_yoast_wpseo_metadesc", "value": seo_metadata["metadescription"]},
            {"key": "_yoast_wpseo_focuskw", "value": ",".join(seo_metadata.get("keywords", []))},
            {"key": "_yoast_wpseo_linkdex", "value": seo_metadata.get("seo_score", 0)},
            {"key": "_product_schema_markup", "value": json.dumps(seo_metadata.get("schema", {}))}
        ]

        # Step 3: Create in WooCommerce
        result = await self.importer.create_product(product_data)

        # Step 4: Return augmented result
        return {
            **result,
            "seo_metadata": seo_metadata,
            "seo_compliance": {
                "title_length_ok": 30 <= len(seo_metadata["metatitle"]) <= 60,
                "meta_desc_length_ok": 120 <= len(seo_metadata["metadescription"]) <= 160,
                "schema_markup_present": bool(seo_metadata.get("schema"))
            }
        }
```

**Verification:**
- [ ] SEO metadata generated for all new products
- [ ] Yoast SEO fields populated correctly
- [ ] Schema markup valid (JSON-LD)
- [ ] Character limits enforced (60/160)
- [ ] SEO score >= 70 for 90% of products

---

### ✅ PHASE 4: Webhook System for Real-Time Updates (6-8 hours)
**Priority:** MEDIUM | **Risk:** HIGH

#### Task 4.1: Create Webhook Registration Endpoint

**File:** `api/v1/ecommerce.py` (NEW ENDPOINTS)

```python
class WebhookRegistration(BaseModel):
    """Webhook registration request"""
    event: str = Field(..., description="Event type: product.price_changed, product.inventory_low")
    threshold: Optional[Dict] = Field(None, description="Trigger threshold")
    target_url: str = Field(..., description="Webhook delivery URL")
    actions: List[str] = Field(..., description="Actions to execute")
    retry_policy: Dict = Field(default={"max_attempts": 3, "backoff_multiplier": 2})
    secret: str = Field(..., description="HMAC secret for signature")

class WebhookResponse(BaseModel):
    """Webhook registration response"""
    webhook_id: str
    status: str
    test_result: Dict
    created_at: datetime

@router.post("/webhooks/register", response_model=WebhookResponse)
async def register_webhook(request: WebhookRegistration):
    """
    Register webhook for WooCommerce events

    Supports:
    - product.price_changed
    - product.inventory_low
    - product.updated

    Triggers:
    - seo_re_audit
    - serp_tracking_update
    - price_optimization
    """

    webhook_id = f"wh-{request.event}-{uuid.uuid4().hex[:8]}"

    # Test webhook delivery
    test_result = await _test_webhook_delivery(request.target_url, request.secret)

    # Store webhook config in database
    await db.webhooks.insert_one({
        "webhook_id": webhook_id,
        "event": request.event,
        "threshold": request.threshold,
        "target_url": request.target_url,
        "actions": request.actions,
        "retry_policy": request.retry_policy,
        "secret": request.secret,
        "status": "active" if test_result["status"] == "success" else "failed",
        "created_at": datetime.utcnow()
    })

    return WebhookResponse(
        webhook_id=webhook_id,
        status="active",
        test_result=test_result,
        created_at=datetime.utcnow()
    )

@router.post("/webhooks/handle")
async def handle_webhook(
    event_type: str,
    payload: Dict,
    signature: str = Header(..., alias="X-Webhook-Signature")
):
    """
    Handle incoming webhooks from WooCommerce

    Verifies HMAC signature (RFC 2104) and triggers actions
    """

    # Verify HMAC signature
    if not _verify_hmac_signature(payload, signature, webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Queue action based on event type
    if event_type == "product.price_changed":
        background_tasks.add_task(_handle_price_change, payload)
    elif event_type == "product.inventory_low":
        background_tasks.add_task(_handle_inventory_low, payload)

    return {"status": "accepted", "job_id": f"wh-{uuid.uuid4().hex[:8]}"}
```

**Verification:**
- [ ] HMAC-SHA256 signature verification (RFC 2104)
- [ ] Webhook test delivery succeeds
- [ ] Retry logic with exponential backoff
- [ ] Failed webhooks logged to DynamoDB/PostgreSQL
- [ ] Replay mechanism for failed deliveries

---

## 📊 Implementation Timeline

| Phase | Duration | Priority | Risk |
|-------|----------|----------|------|
| **Phase 1:** Service Integration | 4-6 hours | CRITICAL | Low |
| **Phase 2:** Unified Endpoint | 6-8 hours | HIGH | Medium |
| **Phase 3:** SEO Auto-Sync | 3-4 hours | HIGH | Medium |
| **Phase 4:** Webhook System | 6-8 hours | MEDIUM | High |
| **Testing & Documentation** | 4-6 hours | HIGH | Low |
| **TOTAL** | **23-32 hours** | | |

**Recommended Sprint:** 2 weeks (10 work days @ 3 hours/day = 30 hours)

---

## 🔍 Verification Checklist (Before Deployment)

### Phase 1 Verification
- [ ] `get_importer_service()` returns valid WooCommerceImporterService instance
- [ ] `get_seo_service()` returns valid SEOOptimizerService instance
- [ ] `/import-products` endpoint returns 200 (not 500)
- [ ] `/generate-seo` endpoint returns valid SEO metadata
- [ ] Configuration loaded from environment variables
- [ ] Health checks pass for WooCommerce and SEO services

### Phase 2 Verification
- [ ] `/products/optimize` endpoint accepts product IDs
- [ ] Parallel processing faster than sequential (benchmark: 10 products)
- [ ] Job state persisted in Redis with 24h TTL
- [ ] Error handling for partial failures (e.g., 7/10 products succeed)
- [ ] Webhook triggered on completion
- [ ] Job status queryable via `/products/optimize/{job_id}/status`

### Phase 3 Verification
- [ ] SEO metadata generated for new products
- [ ] Yoast SEO fields populated (_yoast_wpseo_title, _yoast_wpseo_metadesc)
- [ ] Schema markup valid (test with Google Rich Results Test)
- [ ] Character limits enforced (60/160)
- [ ] SEO score >= 70 for 90% of products (audit)

### Phase 4 Verification
- [ ] HMAC-SHA256 signature verification works
- [ ] Webhook test delivery succeeds
- [ ] Retry logic executes (max 3 attempts, exponential backoff)
- [ ] Failed webhooks logged to database
- [ ] Replay mechanism tested (hourly schedule)

### Security Verification
- [ ] All endpoints have JWT/OAuth2 guards
- [ ] HMAC signatures verified (RFC 2104)
- [ ] No secrets in code (environment variables only)
- [ ] Audit log records all metadata changes (GDPR)
- [ ] No TODO/FIXME in production code

---

## 🚨 Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SEO sync fails, product stuck | High | Medium | Circuit breaker: sync anyway with fallback metadata |
| Bulk optimization hits rate limits | High | High | Queue with Celery, batch 100 products/5 min |
| Duplicate metadata causes SERP penalties | High | Low | Enforce canonical URLs, monthly audit via Google Search Console API |
| Webhook delivery failures | Medium | Medium | Store failed events, replay hourly with backoff |
| SEO scores diverge from pricing | Medium | Low | Data consistency checks, audit trail |

---

## 📝 Configuration Requirements

### Environment Variables (Add to `.env`)
```bash
# WooCommerce
WOOCOMMERCE_URL=https://shop.skyyrose.co
WOOCOMMERCE_CONSUMER_KEY=ck_xxxxx
WOOCOMMERCE_CONSUMER_SECRET=cs_xxxxx

# AI Providers
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx

# Google Sheets
GOOGLE_CREDENTIALS_PATH=/path/to/credentials.json

# Telegram (optional)
TELEGRAM_BOT_TOKEN=xxxxx
TELEGRAM_CHAT_ID=xxxxx

# Redis (job queue)
REDIS_URL=redis://localhost:6379/0

# Webhook
WEBHOOK_SECRET=generate_secure_random_string
```

---

## 🎯 Deliverables

### API Endpoints
```
POST /api/v1/ecommerce/products/optimize          # Main unified endpoint
GET  /api/v1/ecommerce/products/optimize/{job_id}/status  # Job status
POST /api/v1/ecommerce/webhooks/register          # Webhook subscription
POST /api/v1/ecommerce/webhooks/handle            # Webhook handler
POST /api/v1/ecommerce/webhooks/{webhook_id}/test # Test webhook
DELETE /api/v1/ecommerce/webhooks/{webhook_id}    # Unsubscribe
GET  /api/v1/ecommerce/seo/audit/{product_id}     # View SEO score
```

### Documentation
- API reference (OpenAPI 3.0)
- 3 usage examples (bulk import, single product, webhook setup)
- Architecture diagram (WooCommerce + SEO flow)
- Troubleshooting guide

---

## 💡 Recommendations

### Recommended Approach
✅ **Implement Phases 1-3 immediately** (13-18 hours)
- Critical for production readiness
- Low-to-medium risk
- High business value

⏸️ **Defer Phase 4 (Webhooks) to Sprint 2** (6-8 hours)
- Higher complexity and risk
- Requires extensive testing
- Can operate without initially (manual triggers)

### Quick Wins (Can implement in 2-3 hours)
1. Fix dependency injection (Phase 1) → Immediate API functionality
2. Add health checks for WooCommerce/SEO services
3. Create `/products/optimize` skeleton endpoint

---

## 🤔 Questions for Confirmation

Before I proceed with implementation, please confirm:

1. **Priority:** Should I implement Phases 1-3 now and defer Phase 4 (webhooks)?
2. **Configuration:** Do you have WooCommerce API credentials and Anthropic/OpenAI keys available?
3. **Redis:** Is Redis available for job queue (or should I use FastAPI BackgroundTasks only)?
4. **Testing:** Do you want me to create test cases for each phase?
5. **Scope:** Any specific features from the feedback you want prioritized or deprioritized?

---

**AWAITING YOUR APPROVAL TO PROCEED** ✋

Once you confirm the approach, I'll begin implementation starting with Phase 1 (service integration), which will immediately unblock the existing API endpoints.
