---
layout: default
title: API Reference
permalink: /docs/api-reference/
---

# API Reference

Complete documentation for The Skyy Rose Collection DevSkyy Platform API.

## Base URL

```
Local Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

Most endpoints require API key authentication:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://your-domain.com/api/endpoint
```

## Core Endpoints

### Dashboard & Health

#### GET /health
Check system health and status.

**Response:**
```json
{
  "status": "healthy",
  "agents": {
    "inventory": "operational",
    "financial": "operational",
    "ecommerce": "operational",
    "wordpress": "operational",
    "webdev": "operational",
    "communication": "operational",
    "brand_intelligence": "operational"
  },
  "timestamp": "2024-01-20T12:00:00Z"
}
```

#### GET /dashboard
Get comprehensive business overview.

**Response:**
```json
{
  "summary": {
    "total_revenue": 125000,
    "conversion_rate": 8.5,
    "active_orders": 45,
    "agent_health": 95.2
  },
  "agents": [...],
  "recent_activities": [...]
}
```

### Agent Workflow

#### POST /run
Execute the complete DevSkyy agent workflow.

**Request:**
```json
{
  "target_url": "https://example.com",
  "agents": ["inventory", "wordpress", "webdev"],
  "auto_commit": true
}
```

**Response:**
```json
{
  "workflow_id": "wf_123456",
  "status": "running",
  "agents_triggered": 3,
  "estimated_completion": "2024-01-20T12:30:00Z"
}
```

## Agent-Specific Endpoints

### Inventory Management

#### POST /inventory/scan
Scan and analyze digital assets.

**Request:**
```json
{
  "scan_type": "full",
  "target_directories": ["/assets", "/uploads"],
  "detect_duplicates": true
}
```

#### GET /inventory/report
Get inventory analysis report.

**Response:**
```json
{
  "total_assets": 1250,
  "duplicates_found": 15,
  "optimization_suggestions": [...],
  "storage_usage": "2.4GB"
}
```

### Financial Operations

#### POST /payments/process
Process payment transaction.

**Request:**
```json
{
  "amount": 99.99,
  "currency": "USD",
  "customer_id": "cust_123",
  "payment_method": "stripe_card_456"
}
```

#### GET /financial/dashboard
Get financial analytics dashboard.

**Response:**
```json
{
  "revenue": {
    "today": 5420.50,
    "month": 125000.00,
    "year": 750000.00
  },
  "transactions": {
    "processed": 145,
    "pending": 3,
    "failed": 2
  }
}
```

### E-commerce Intelligence

#### POST /orders/create
Create new order.

**Request:**
```json
{
  "customer_id": "cust_123",
  "items": [
    {
      "product_id": "prod_456",
      "quantity": 2,
      "price": 49.99
    }
  ],
  "shipping_address": {...}
}
```

#### GET /analytics/report
Get e-commerce analytics.

**Response:**
```json
{
  "sales_metrics": {
    "conversion_rate": 8.5,
    "average_order_value": 125.50,
    "customer_lifetime_value": 450.75
  },
  "top_products": [...],
  "customer_insights": [...]
}
```

### WordPress Optimization

#### POST /wordpress/analyze-layout
Analyze WordPress/Divi layout performance.

**Request:**
```json
{
  "page_url": "https://yoursite.com/page",
  "analyze_seo": true,
  "check_performance": true
}
```

#### POST /wordpress/optimize
Optimize WordPress site performance.

**Request:**
```json
{
  "optimizations": [
    "compress_images",
    "minify_css",
    "cache_optimization",
    "database_cleanup"
  ]
}
```

### Web Development

#### POST /webdev/analyze-code
Analyze code for issues and improvements.

**Request:**
```json
{
  "repository_url": "https://github.com/user/repo",
  "file_patterns": ["*.js", "*.css", "*.php"],
  "check_security": true
}
```

#### POST /webdev/fix-code
Automatically fix code issues.

**Request:**
```json
{
  "issues": ["syntax_errors", "security_vulnerabilities"],
  "auto_commit": true,
  "commit_message": "Auto-fix: DevSkyy code optimization"
}
```

### Brand Intelligence

#### GET /brand/intelligence
Get brand analysis and insights.

**Response:**
```json
{
  "brand_confidence": 95.2,
  "visual_consistency": 88.5,
  "content_alignment": 92.1,
  "competitor_analysis": [...],
  "improvement_suggestions": [...]
}
```

#### POST /brand/evolution
Track brand evolution and learning.

**Request:**
```json
{
  "learning_sources": [
    "website_content",
    "social_media",
    "customer_feedback"
  ],
  "competitor_brands": [
    "Supreme",
    "Off-White",
    "Fear of God"
  ]
}
```

## Theme Deployment

#### POST /themes/deploy
Deploy luxury WordPress theme.

**Request:**
```json
{
  "theme_id": "luxury_streetwear_homepage",
  "brand_assets": {
    "primary_logo": "https://...",
    "color_scheme": "rose_gold_luxury",
    "typography": "playfair_inter"
  },
  "target_site": "https://yoursite.com"
}
```

## WebHooks

### WordPress Events
```
POST /webhooks/wordpress
```

### Payment Events
```
POST /webhooks/payments
```

### Order Events
```
POST /webhooks/orders
```

## Rate Limits

- **Free Tier**: 100 requests/hour
- **Pro Tier**: 1000 requests/hour
- **Enterprise**: Unlimited

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Error |

## SDKs and Libraries

### Python
```python
from devskyy import DevSkyyClient

client = DevSkyyClient(api_key="your_key")
result = client.run_workflow(agents=["inventory", "wordpress"])
```

### JavaScript
```javascript
import { DevSkyyAPI } from '@skyy-rose/devskyy-js';

const api = new DevSkyyAPI('your_key');
const result = await api.runWorkflow(['inventory', 'wordpress']);
```

### cURL Examples

```bash
# Health check
curl https://api.skyyrose.co/health

# Run workflow
curl -X POST https://api.skyyrose.co/run \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"agents": ["inventory", "wordpress"]}'

# Get dashboard
curl https://api.skyyrose.co/dashboard \
  -H "Authorization: Bearer YOUR_KEY"
```

## Support

Need help with the API?
- 📚 [View Examples](https://github.com/SkyyRoseLLC/DevSkyy/tree/main/examples)
- 🐛 [Report Issues](https://github.com/SkyyRoseLLC/DevSkyy/issues)
- 💬 [Join Discord](https://discord.gg/skyyrose)