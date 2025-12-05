# DevSkyy Agents Directory - MCP Resource
**Purpose:** Structured agent intelligence for MCP tool routing and LLM consumption
**Last Updated:** Auto-generated from agent registry
**Version:** 2.0.0

---

## Quick Reference: Agent Routing by Intent

Use this mapping to route user requests to optimal agents:

```yaml
CODE_QUALITY:
  intents: ["scan", "analyze", "fix", "debug", "security audit"]
  agents: ["scanner_v2", "fixer_v2", "security_agent"]

COMMERCE:
  intents: ["product", "inventory", "pricing", "order", "customer"]
  agents: ["product_manager", "inventory_optimizer", "pricing_engine", "order_manager"]

MARKETING:
  intents: ["campaign", "email", "social", "seo", "content"]
  agents: ["marketing_campaign", "email_marketing", "social_media", "seo_optimizer"]

ML_ANALYTICS:
  intents: ["predict", "forecast", "analyze", "trend", "sentiment"]
  agents: ["ml_trend_prediction", "demand_forecasting", "sentiment_analysis"]

CONTENT:
  intents: ["write", "generate", "blog", "copywriting"]
  agents: ["content_generation", "seo_copywriting", "brand_voice"]

WORDPRESS:
  intents: ["theme", "divi", "elementor", "page", "website"]
  agents: ["wordpress_divi_elementor", "wordpress_theme_builder"]

SYSTEM:
  intents: ["monitor", "health", "performance", "heal"]
  agents: ["self_healing_system", "performance_monitor", "system_health"]
```

---

## Agent Catalog (54 Total)

### 🏗️ Infrastructure & System Agents (8 agents)

#### 1. Scanner V2 (`scanner_v2`)
**Capabilities:** Code analysis, bug detection, security scanning, quality checks
**Input:** `code_path`, `scan_type`, `severity_threshold`
**Output:** Issues list with severity, recommendations
**API:** `POST /api/v1/agents/scanner/scan`
**Use When:** "scan my code", "find bugs", "security audit"

#### 2. Fixer V2 (`fixer_v2`)
**Capabilities:** Automated bug fixing, code formatting, optimization
**Input:** `code_path`, `issues` (from scanner), `fix_mode`
**Output:** Fixed code, changelog, test results
**API:** `POST /api/v1/agents/fixer/fix`
**Use When:** "fix bugs", "auto-repair", "format code"
**Dependencies:** Requires scanner_v2 output

#### 3. Security Agent (`security_agent`)
**Capabilities:** JWT validation, encryption, RBAC, audit logging
**Input:** `operation`, `resource`, `user_context`
**Output:** Auth decision, security violations, audit trail
**API:** `POST /api/v1/agents/security/validate`
**Use When:** "check permissions", "audit security", "validate access"

#### 4. Performance Monitor (`performance_monitor`)
**Capabilities:** Metrics collection, P50/P95/P99 latency tracking, bottleneck detection
**Input:** `metric_type`, `time_range`, `filters`
**Output:** Performance metrics, recommendations
**API:** `GET /api/v1/agents/performance/metrics`
**Use When:** "performance stats", "slow endpoints", "bottlenecks"

#### 5. Self-Healing System (`self_healing_system`)
**Capabilities:** Auto-detect issues, self-repair, rollback, health monitoring
**Input:** `action` ("scan" | "heal" | "status"), `auto_fix`
**Output:** Health status, fixes applied, recommendations
**API:** `POST /api/v1/agents/self-healing/execute`
**Use When:** "fix system", "health check", "auto-repair"

#### 6. System Health Monitor (`system_health_monitor`)
**Capabilities:** Component health checks, uptime tracking, dependency status
**Input:** `components`, `depth`
**Output:** Health report, failing components, alerts
**API:** `GET /api/v1/agents/health/status`
**Use When:** "system status", "is platform healthy"

#### 7. Backup & Recovery (`backup_recovery`)
**Capabilities:** Automated backups, disaster recovery, data restoration
**Input:** `action`, `backup_id`, `restore_point`
**Output:** Backup status, restore results
**API:** `POST /api/v1/agents/backup/execute`
**Use When:** "backup data", "restore system"

#### 8. Configuration Manager (`config_manager`)
**Capabilities:** Environment config, secrets management, feature flags
**Input:** `config_key`, `environment`
**Output:** Configuration values, validation status
**API:** `GET /api/v1/agents/config/get`
**Use When:** "get config", "update settings"

---

### 🤖 AI & Intelligence Agents (7 agents)

#### 9. Claude Sonnet (`claude_sonnet_agent`)
**Capabilities:** Advanced reasoning, text generation, analysis, coding assistance
**Input:** `prompt`, `context`, `temperature`, `max_tokens`
**Output:** Generated text, analysis, recommendations
**API:** `POST /api/v1/agents/claude/generate`
**Use When:** Complex reasoning, code generation, content creation

#### 10. OpenAI GPT (`openai_agent`)
**Capabilities:** Text completion, embeddings, moderation
**Input:** `prompt`, `model`, `parameters`
**Output:** Completion, embeddings, moderation results
**API:** `POST /api/v1/agents/openai/complete`
**Use When:** Fast completions, embeddings, moderation

#### 11. Multi-Model Orchestrator (`multi_model_orchestrator`)
**Capabilities:** Route to best model, fallback handling, cost optimization
**Input:** `task_type`, `priority`, `budget`
**Output:** Optimal model selection, execution result
**API:** `POST /api/v1/agents/multi-model/execute`
**Use When:** "best model for task", automatic model selection

#### 12. Sentiment Analysis (`sentiment_analysis`)
**Capabilities:** Customer feedback analysis, emotion detection, review scoring
**Input:** `text`, `source_type`
**Output:** Sentiment score (-1 to 1), emotions, summary
**API:** `POST /api/v1/agents/sentiment/analyze`
**Use When:** "analyze reviews", "customer sentiment"

#### 13. NLP Processor (`nlp_processor`)
**Capabilities:** Entity extraction, intent classification, language detection
**Input:** `text`, `operations`
**Output:** Entities, intent, language, keywords
**API:** `POST /api/v1/agents/nlp/process`
**Use When:** "extract entities", "detect intent"

#### 14. Translation Agent (`translation_agent`)
**Capabilities:** Multi-language translation, locale detection
**Input:** `text`, `target_language`, `source_language`
**Output:** Translated text, confidence score
**API:** `POST /api/v1/agents/translation/translate`
**Use When:** "translate to Spanish", "multi-language support"

#### 15. Content Moderation (`content_moderation`)
**Capabilities:** Harmful content detection, NSFW filtering, compliance checks
**Input:** `content`, `content_type`, `strictness`
**Output:** Moderation result, violations, confidence
**API:** `POST /api/v1/agents/moderation/check`
**Use When:** "check content safety", "filter NSFW"

---

### 🛒 E-Commerce Agents (9 agents)

#### 16. Product Manager (`product_manager`)
**Capabilities:** CRUD products, variant management, catalog organization
**Input:** `action`, `product_data`, `filters`
**Output:** Product info, operation status
**API:** `POST /api/v1/agents/ecommerce/products`
**Use When:** "create product", "update inventory", "list products"

#### 17. Pricing Engine (`pricing_engine`)
**Capabilities:** Dynamic pricing, competitive analysis, A/B testing
**Input:** `product_id`, `strategy`, `constraints`
**Output:** Optimized price, expected revenue, rationale
**API:** `POST /api/v1/agents/ecommerce/pricing/optimize`
**Use When:** "optimize price", "competitive pricing"

#### 18. Inventory Optimizer (`inventory_optimizer`)
**Capabilities:** Stock forecasting, reorder points, warehouse optimization
**Input:** `product_id`, `warehouse`, `forecast_period`
**Output:** Reorder recommendations, stock levels, alerts
**API:** `POST /api/v1/agents/ecommerce/inventory/optimize`
**Use When:** "stock forecast", "reorder alerts"

#### 19. Order Manager (`order_manager`)
**Capabilities:** Order processing, fulfillment, tracking, returns
**Input:** `order_id`, `action`, `parameters`
**Output:** Order status, tracking info, updates
**API:** `POST /api/v1/agents/ecommerce/orders/manage`
**Use When:** "process order", "track shipment"

#### 20. Customer Manager (`customer_manager`)
**Capabilities:** Customer profiles, segmentation, lifetime value, behavior analysis
**Input:** `customer_id`, `action`, `segment_criteria`
**Output:** Customer data, segments, recommendations
**API:** `POST /api/v1/agents/ecommerce/customers/manage`
**Use When:** "customer segments", "CLV analysis"

#### 21. Cart Optimizer (`cart_optimizer`)
**Capabilities:** Cart abandonment prevention, upsell suggestions
**Input:** `cart_id`, `optimization_type`
**Output:** Recommendations, discount suggestions
**API:** `POST /api/v1/agents/ecommerce/cart/optimize`
**Use When:** "reduce cart abandonment", "upsell products"

#### 22. Shipping Calculator (`shipping_calculator`)
**Capabilities:** Real-time rates, carrier selection, zone pricing
**Input:** `origin`, `destination`, `package_details`
**Output:** Shipping options, rates, estimated delivery
**API:** `POST /api/v1/agents/ecommerce/shipping/calculate`
**Use When:** "shipping costs", "carrier options"

#### 23. Payment Processor (`payment_processor`)
**Capabilities:** Payment gateway integration, fraud detection
**Input:** `payment_data`, `gateway`, `amount`
**Output:** Transaction result, fraud score
**API:** `POST /api/v1/agents/ecommerce/payment/process`
**Use When:** "process payment", "fraud check"

#### 24. Returns Manager (`returns_manager`)
**Capabilities:** Return requests, refunds, restocking
**Input:** `order_id`, `return_reason`, `items`
**Output:** Return authorization, refund status
**API:** `POST /api/v1/agents/ecommerce/returns/process`
**Use When:** "process return", "issue refund"

---

### 📊 ML & Analytics Agents (6 agents)

#### 25. ML Trend Prediction (`ml_trend_prediction`)
**Capabilities:** Fashion trend forecasting, demand prediction, seasonality analysis
**Input:** `category`, `timeframe`, `historical_data`
**Output:** Trend predictions, confidence scores, recommendations
**API:** `POST /api/v1/agents/ml/predict-trends`
**Use When:** "fashion trends", "demand forecast"

#### 26. Customer Segmentation (`customer_segmentation`)
**Capabilities:** RFM analysis, behavioral clustering, persona generation
**Input:** `customer_data`, `segmentation_method`, `num_segments`
**Output:** Customer segments, characteristics, sizes
**API:** `POST /api/v1/agents/ml/segment-customers`
**Use When:** "customer segments", "RFM analysis"

#### 27. Demand Forecasting (`demand_forecasting`)
**Capabilities:** Sales forecasting, inventory planning, seasonal patterns
**Input:** `product_id`, `forecast_horizon`, `historical_sales`
**Output:** Forecast values, confidence intervals, insights
**API:** `POST /api/v1/agents/ml/forecast-demand`
**Use When:** "sales forecast", "inventory planning"

#### 28. Dynamic Pricing ML (`dynamic_pricing_ml`)
**Capabilities:** ML-powered price optimization, elasticity modeling
**Input:** `product_id`, `market_conditions`, `objectives`
**Output:** Optimal prices, revenue projections
**API:** `POST /api/v1/agents/ml/optimize-pricing`
**Use When:** "AI pricing", "price optimization"

#### 29. Churn Prediction (`churn_prediction`)
**Capabilities:** Customer churn forecasting, retention strategies
**Input:** `customer_cohort`, `prediction_window`
**Output:** Churn probabilities, at-risk customers, interventions
**API:** `POST /api/v1/agents/ml/predict-churn`
**Use When:** "churn risk", "retention strategy"

#### 30. Recommendation Engine (`recommendation_engine`)
**Capabilities:** Product recommendations, collaborative filtering, content-based
**Input:** `customer_id`, `context`, `num_recommendations`
**Output:** Recommended products, scores, reasoning
**API:** `POST /api/v1/agents/ml/recommend`
**Use When:** "product recommendations", "personalization"

---

### 📝 Marketing & Content Agents (11 agents)

#### 31. Marketing Campaign Manager (`marketing_campaign_manager`)
**Capabilities:** Multi-channel campaigns, A/B testing, performance tracking
**Input:** `campaign_type`, `target_audience`, `channels`, `budget`
**Output:** Campaign plan, execution status, metrics
**API:** `POST /api/v1/agents/marketing/campaign/create`
**Use When:** "create campaign", "launch promotion"

#### 32. Email Marketing (`email_marketing_agent`)
**Capabilities:** Email campaigns, templates, segmentation, automation
**Input:** `template`, `recipients`, `schedule`
**Output:** Campaign ID, delivery status, metrics
**API:** `POST /api/v1/agents/marketing/email/send`
**Use When:** "email campaign", "newsletter"

#### 33. Social Media Manager (`social_media_manager`)
**Capabilities:** Multi-platform posting, scheduling, engagement tracking
**Input:** `content`, `platforms`, `schedule`, `targeting`
**Output:** Post IDs, engagement metrics, insights
**API:** `POST /api/v1/agents/marketing/social/post`
**Use When:** "post to Instagram", "schedule social"

#### 34. SEO Optimizer (`seo_optimizer`)
**Capabilities:** Keyword research, on-page SEO, meta optimization, sitemap generation
**Input:** `content`, `target_keywords`, `competitors`
**Output:** SEO score, recommendations, optimized content
**API:** `POST /api/v1/agents/marketing/seo/optimize`
**Use When:** "SEO optimization", "keyword research"

#### 35. Content Generator (`content_generator`)
**Capabilities:** Blog posts, product descriptions, ad copy
**Input:** `content_type`, `topic`, `tone`, `length`
**Output:** Generated content, variants, metadata
**API:** `POST /api/v1/agents/marketing/content/generate`
**Use When:** "write blog post", "product description"

#### 36. Brand Voice Analyzer (`brand_voice_analyzer`)
**Capabilities:** Brand consistency checking, tone analysis
**Input:** `content`, `brand_guidelines`
**Output:** Consistency score, violations, suggestions
**API:** `POST /api/v1/agents/marketing/brand/analyze`
**Use When:** "check brand consistency", "tone analysis"

#### 37. Copywriting Agent (`copywriting_agent`)
**Capabilities:** Sales copy, headlines, CTAs, ad variations
**Input:** `purpose`, `product`, `audience`, `platform`
**Output:** Copy variants, A/B test suggestions
**API:** `POST /api/v1/agents/marketing/copy/generate`
**Use When:** "write ad copy", "create CTA"

#### 38. SMS Marketing (`sms_marketing_agent`)
**Capabilities:** SMS campaigns, short codes, compliance
**Input:** `message`, `recipients`, `schedule`
**Output:** Campaign ID, delivery stats
**API:** `POST /api/v1/agents/marketing/sms/send`
**Use When:** "SMS campaign", "text promotion"

#### 39. Influencer Marketing (`influencer_marketing`)
**Capabilities:** Influencer discovery, campaign management, ROI tracking
**Input:** `niche`, `audience_size`, `budget`
**Output:** Influencer matches, campaign proposals
**API:** `POST /api/v1/agents/marketing/influencer/find`
**Use When:** "find influencers", "influencer campaign"

#### 40. Ad Campaign Manager (`ad_campaign_manager`)
**Capabilities:** Google/Meta ads, bid optimization, A/B testing
**Input:** `platform`, `ad_creative`, `targeting`, `budget`
**Output:** Campaign ID, performance metrics
**API:** `POST /api/v1/agents/marketing/ads/create`
**Use When:** "Google Ads", "Facebook ads"

#### 41. Analytics Reporter (`analytics_reporter`)
**Capabilities:** Marketing analytics, attribution, ROI calculation
**Input:** `metrics`, `date_range`, `campaigns`
**Output:** Report, insights, recommendations
**API:** `GET /api/v1/agents/marketing/analytics/report`
**Use When:** "marketing ROI", "campaign analytics"

---

### 🎨 WordPress & Frontend Agents (5 agents)

#### 42. WordPress Theme Builder (`wordpress_theme_builder`)
**Capabilities:** Custom theme generation, responsive design, plugin integration
**Input:** `design_preferences`, `features`, `brand_colors`
**Output:** Theme files, installation guide
**API:** `POST /api/v1/agents/wordpress/theme/generate`
**Use When:** "create WordPress theme", "custom design"

#### 43. WordPress Divi/Elementor (`wordpress_divi_elementor`)
**Capabilities:** Page builder integration, module creation, layout generation
**Input:** `builder_type`, `layout_structure`, `content`
**Output:** Builder JSON, import instructions
**API:** `POST /api/v1/agents/wordpress/builder/generate`
**Use When:** "Divi layout", "Elementor page"

#### 44. Design Automation (`design_automation_agent`)
**Capabilities:** UI/UX design, color schemes, typography, layout generation
**Input:** `design_type`, `brand_guidelines`, `content`
**Output:** Design mockups, CSS, assets
**API:** `POST /api/v1/agents/frontend/design/generate`
**Use When:** "design UI", "color scheme"

#### 45. Landing Page Generator (`landing_page_generator`)
**Capabilities:** High-converting landing pages, A/B variants
**Input:** `goal`, `product`, `target_audience`
**Output:** HTML/CSS/JS, variants, analytics code
**API:** `POST /api/v1/agents/frontend/landing/generate`
**Use When:** "create landing page", "conversion optimization"

#### 46. Fashion Computer Vision (`fashion_computer_vision`)
**Capabilities:** Style classification, product recognition, visual search
**Input:** `image`, `task_type`
**Output:** Classifications, tags, similar products
**API:** `POST /api/v1/agents/frontend/vision/analyze`
**Use When:** "analyze fashion image", "visual search"

---

### 🔧 Integration & Advanced Agents (8 agents)

#### 47. Integration Manager (`integration_manager`)
**Capabilities:** Third-party API integration, OAuth, webhooks
**Input:** `service`, `action`, `credentials`
**Output:** Integration status, data sync results
**API:** `POST /api/v1/agents/integration/execute`
**Use When:** "connect Shopify", "Stripe integration"

#### 48. Webhook Manager (`webhook_manager`)
**Capabilities:** Webhook subscription, event delivery, retry logic
**Input:** `event_type`, `url`, `secret`
**Output:** Subscription ID, delivery status
**API:** `POST /api/v1/agents/integration/webhook/subscribe`
**Use When:** "setup webhook", "event notifications"

#### 49. API Rate Limiter (`api_rate_limiter`)
**Capabilities:** Rate limiting, quota management, throttling
**Input:** `client_id`, `endpoint`, `limit`
**Output:** Rate limit status, remaining quota
**API:** `GET /api/v1/agents/integration/rate-limit/status`
**Use When:** "check rate limits", "throttle requests"

#### 50. Data Transformer (`data_transformer`)
**Capabilities:** ETL pipelines, format conversion, data validation
**Input:** `source_format`, `target_format`, `data`
**Output:** Transformed data, validation results
**API:** `POST /api/v1/agents/integration/transform`
**Use When:** "convert data format", "ETL pipeline"

#### 51. Blockchain NFT (`blockchain_nft_luxury_assets`)
**Capabilities:** NFT minting, authenticity certificates, blockchain tracking
**Input:** `asset_data`, `blockchain`, `operation`
**Output:** Transaction hash, NFT metadata
**API:** `POST /api/v1/agents/blockchain/nft/mint`
**Use When:** "mint NFT", "blockchain certificate"
**Status:** ⚠️ Partial - needs Web3 integration

#### 52. Voice Agent (`voice_agent`)
**Capabilities:** Text-to-speech, speech-to-text, voice commands
**Input:** `text`, `voice_model`, `language`
**Output:** Audio file, transcript
**API:** `POST /api/v1/agents/voice/synthesize`
**Use When:** "text to speech", "voice generation"

#### 53. Image Generator (`image_generator`)
**Capabilities:** AI image generation, style transfer, upscaling
**Input:** `prompt`, `style`, `dimensions`
**Output:** Generated images, variants
**API:** `POST /api/v1/agents/image/generate`
**Use When:** "generate product image", "AI art"

#### 54. Predictive Automation (`predictive_automation_system`)
**Capabilities:** Task automation, workflow prediction, smart scheduling
**Input:** `task_pattern`, `context`, `automation_rules`
**Output:** Automation recommendations, scheduled tasks
**API:** `POST /api/v1/agents/automation/predict`
**Use When:** "automate workflow", "smart scheduling"

---

## Agent Dependencies & Workflows

### Common Workflows

#### 1. Product Launch Workflow
```
1. product_manager (create product)
2. ml_trend_prediction (forecast demand)
3. pricing_engine (optimize price)
4. marketing_campaign_manager (create campaign)
5. social_media_manager (announce launch)
```

#### 2. Code Quality Workflow
```
1. scanner_v2 (scan codebase)
2. fixer_v2 (auto-fix issues)
3. security_agent (security audit)
4. performance_monitor (benchmark)
```

#### 3. Content Marketing Workflow
```
1. seo_optimizer (keyword research)
2. content_generator (write blog)
3. brand_voice_analyzer (check consistency)
4. email_marketing_agent (newsletter)
5. analytics_reporter (track performance)
```

#### 4. E-Commerce Optimization Workflow
```
1. inventory_optimizer (stock forecast)
2. demand_forecasting (sales prediction)
3. dynamic_pricing_ml (price optimization)
4. recommendation_engine (product suggestions)
5. cart_optimizer (reduce abandonment)
```

---

## API Endpoint Patterns

All agents follow consistent REST patterns:

```
# Execution
POST /api/v1/agents/{agent_name}/execute
Body: { "parameters": {...}, "options": {...} }

# Status
GET /api/v1/agents/{agent_name}/status

# Capabilities
GET /api/v1/agents/{agent_name}/capabilities

# Batch Execution
POST /api/v1/orchestrator/execute
Body: { "workflow": "name", "steps": [...] }
```

---

## Error Handling

All agents return structured errors:

```json
{
  "status": "error",
  "error_code": "AGENT_ERROR_CODE",
  "message": "Human-readable error",
  "details": {...},
  "retry_after": 5000,
  "suggestions": ["Try X", "Check Y"]
}
```

Common error codes:
- `INVALID_INPUT`: Parameter validation failed
- `AGENT_UNAVAILABLE`: Agent offline or degraded
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `DEPENDENCY_FAILED`: Required agent failed
- `INSUFFICIENT_PERMISSIONS`: Auth/RBAC failure

---

## Performance Guidelines

**Response Time SLAs:**
- Query/Status agents: <50ms
- Light processing: <200ms
- ML predictions: <2s
- Content generation: <5s
- Batch workflows: <30s

**Rate Limits (per agent):**
- Default: 100 req/min per user
- ML agents: 20 req/min per user
- Batch operations: 10 req/min per user

**Caching Strategy:**
- Agent list: 1 hour TTL
- Health status: 30 sec TTL
- ML predictions: 5 min TTL
- Content: No cache (dynamic)

---

## Usage Examples for MCP

### Example 1: Route user intent to agent
```python
user_query = "I need to scan my code for security issues"

# Intent classification
if "scan" in user_query and "security" in user_query:
    agent = "scanner_v2"
    parameters = {"scan_type": "security", "severity": "high"}
```

### Example 2: Execute workflow
```python
workflow = "product_launch"
agents_needed = [
    "product_manager",
    "ml_trend_prediction",
    "pricing_engine",
    "marketing_campaign_manager"
]
```

### Example 3: Handle dependencies
```python
# Fixer requires Scanner output
scanner_result = await execute_agent("scanner_v2", params)
fixer_params = {"issues": scanner_result["issues"]}
fixer_result = await execute_agent("fixer_v2", fixer_params)
```

---

## MCP Integration Notes

This document is designed to be:
1. **Loaded as MCP Resource:** `devskyy://agents/directory`
2. **Cached aggressively:** Updates hourly from registry
3. **Token-optimized:** Structured YAML/JSON > verbose prose
4. **Intent-routable:** Quick lookup tables for LLM decision-making

**For MCP Server:**
```python
@mcp.resource("devskyy://agents/directory")
def get_agents_directory() -> str:
    """Return this entire AGENTS_PROMPT.md file."""
    return Path("AGENTS_PROMPT.md").read_text()

@mcp.resource("devskyy://agents/{category}")
def get_agents_by_category(category: str) -> str:
    """Return filtered agent list by category."""
    # Parse AGENTS_PROMPT.md and filter by category
    pass
```

---

**End of AGENTS_PROMPT.md**
*This file is auto-maintained by the agent registry system*
*For programmatic access, use: `GET /api/v1/agents/registry/list`*
