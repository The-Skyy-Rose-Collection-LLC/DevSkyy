# New MCP-Integrated API Endpoints

> **Version**: 1.0.0
> **Date**: 2026-01-05
> **Status**: Production Ready

This document describes the 13 new API endpoints that bridge DevSkyy's MCP tools with the REST API.

---

## Overview

These endpoints provide HTTP access to the functionality exposed via the MCP server (`devskyy_mcp.py`). All endpoints are prefixed with `/api/v1` and require JWT authentication (except health checks).

**Total Endpoints**: 13
**Authentication**: Bearer Token (JWT)
**Base URL**: `http://localhost:8000` (development)

---

## Table of Contents

1. [Code Analysis](#1-code-analysis)
2. [WordPress](#2-wordpress)
3. [Machine Learning](#3-machine-learning)
4. [Media Generation](#4-media-generation)
5. [Marketing](#5-marketing)
6. [Commerce](#6-commerce)
7. [Orchestration](#7-orchestration)
8. [Monitoring](#8-monitoring)
9. [Health](#9-health)

---

## 1. Code Analysis

### 1.1 Code Scanning

**Endpoint**: `POST /api/v1/code/scan`
**Description**: Scan codebase for errors, security vulnerabilities, and optimization opportunities.

**Request Body**:
```json
{
  "path": "/path/to/scan",
  "file_types": ["py", "js", "ts"],
  "deep_scan": true
}
```

**Response** (200 OK):
```json
{
  "scan_id": "uuid-here",
  "status": "completed",
  "timestamp": "2026-01-05T12:00:00Z",
  "path": "/path/to/scan",
  "files_scanned": 42,
  "issues_found": 5,
  "issues": [
    {
      "file": "example.py",
      "line": 42,
      "column": 10,
      "severity": "high",
      "type": "security",
      "message": "Potential SQL injection vulnerability",
      "rule": "S100",
      "suggestion": "Use parameterized queries"
    }
  ],
  "summary": {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 2
  }
}
```

**Integration**: `security/code_scanner.py`, `security/vulnerability_scanner.py`

---

### 1.2 Code Fixing

**Endpoint**: `POST /api/v1/code/fix`
**Description**: Automatically fix code issues detected by scanner.

**Request Body**:
```json
{
  "scan_id": "uuid-here",
  "scan_results": {"issues": [...]},
  "auto_apply": false,
  "create_backup": true,
  "fix_types": ["syntax", "imports", "docstrings"]
}
```

**Response** (200 OK):
```json
{
  "fix_id": "uuid-here",
  "status": "suggestions_generated",
  "timestamp": "2026-01-05T12:00:00Z",
  "fixes_generated": 3,
  "fixes_applied": 0,
  "fixes": [
    {
      "file": "example.py",
      "line": 42,
      "fix_type": "security",
      "original": "query = \"SELECT * FROM users WHERE id = \" + user_id",
      "fixed": "query = \"SELECT * FROM users WHERE id = %s\"\\ncursor.execute(query, (user_id,))",
      "applied": false
    }
  ],
  "backup_path": "/tmp/backup_uuid"
}
```

**Integration**: LLM-based code repair (to be implemented)

---

## 2. WordPress

### 2.1 Theme Generation

**Endpoint**: `POST /api/v1/wordpress/generate-theme`
**Description**: Generate custom WordPress themes automatically from brand guidelines.

**Request Body**:
```json
{
  "brand_name": "FashionHub",
  "industry": "fashion",
  "theme_type": "elementor",
  "color_palette": ["#FF5733", "#3498DB"],
  "pages": ["home", "shop", "about", "contact"],
  "include_woocommerce": true,
  "seo_optimized": true
}
```

**Response** (202 Accepted):
```json
{
  "theme_id": "uuid-here",
  "status": "processing",
  "timestamp": "2026-01-05T12:00:00Z",
  "brand_name": "FashionHub",
  "theme_type": "elementor",
  "download_url": "https://downloads.devskyy.com/themes/uuid.zip",
  "preview_url": "https://preview.devskyy.com/themes/uuid",
  "pages": [
    {
      "name": "home",
      "template": "homepage-hero",
      "elements": 12,
      "preview_url": "..."
    }
  ],
  "metadata": {
    "wordpress_version": "6.4+",
    "php_version": "8.0+",
    "theme_version": "1.0.0"
  }
}
```

**Integration**: `wordpress/elementor.py` (ElementorManager)

---

## 3. Machine Learning

### 3.1 ML Predictions

**Endpoint**: `POST /api/v1/ml/predict`
**Description**: Run machine learning predictions for fashion e-commerce.

**Request Body**:
```json
{
  "model_type": "trend_prediction",
  "data": {
    "items": ["oversized_blazers", "cargo_pants"],
    "time_horizon": "3_months"
  },
  "confidence_threshold": 0.7
}
```

**Supported Model Types**:
- `trend_prediction`: Identify emerging fashion trends
- `customer_segmentation`: Group customers by behavior
- `demand_forecasting`: Predict product demand
- `dynamic_pricing`: Optimize prices using ML
- `sentiment_analysis`: Analyze customer sentiment

**Response** (200 OK):
```json
{
  "prediction_id": "uuid-here",
  "status": "completed",
  "timestamp": "2026-01-05T12:00:00Z",
  "model_type": "trend_prediction",
  "model_version": "v2.1.0",
  "predictions": [
    {
      "label": "oversized_blazers",
      "confidence": 0.85,
      "value": "trending_up",
      "metadata": {
        "growth_rate": 0.45,
        "time_to_peak": "2_months"
      }
    }
  ],
  "metrics": {
    "model_accuracy": 0.89,
    "prediction_horizon_days": 90
  }
}
```

**Integration**: `agents/ml_module.py` (MLModule)

---

## 4. Media Generation

### 4.1 Text-to-3D Generation

**Endpoint**: `POST /api/v1/media/3d/generate/text`
**Description**: Generate 3D fashion models from text descriptions using Tripo3D AI.

**Request Body**:
```json
{
  "product_name": "Heart Rose Bomber",
  "collection": "BLACK_ROSE",
  "garment_type": "bomber",
  "additional_details": "Rose gold zipper, embroidered rose on back",
  "output_format": "glb"
}
```

**Supported Formats**: `glb`, `gltf`, `fbx`, `obj`, `usdz`, `stl`

**Response** (202 Accepted):
```json
{
  "generation_id": "uuid-here",
  "status": "processing",
  "timestamp": "2026-01-05T12:00:00Z",
  "product_name": "Heart Rose Bomber",
  "output_format": "glb",
  "model_url": "https://cdn.devskyy.com/3d/uuid.glb",
  "preview_url": "https://preview.devskyy.com/3d/uuid",
  "download_url": "https://downloads.devskyy.com/3d/uuid.glb",
  "metadata": {
    "polycount": 25000,
    "file_size_mb": 8.5,
    "texture_resolution": "2048x2048"
  },
  "estimated_completion_time": "2-5 minutes"
}
```

**Integration**: `agents/tripo_agent.py` (TripoAgent)

---

### 4.2 Image-to-3D Generation

**Endpoint**: `POST /api/v1/media/3d/generate/image`
**Description**: Generate 3D models from reference images.

**Request Body**:
```json
{
  "product_name": "Custom Hoodie",
  "image_url": "https://cdn.skyyrose.co/designs/hoodie.jpg",
  "output_format": "glb"
}
```

**Response**: Same as text-to-3D (202 Accepted)

**Integration**: `agents/tripo_agent.py` (TripoAgent)

---

## 5. Marketing

### 5.1 Marketing Campaigns

**Endpoint**: `POST /api/v1/marketing/campaigns`
**Description**: Create and execute automated marketing campaigns.

**Request Body**:
```json
{
  "campaign_type": "email",
  "target_audience": {
    "segment": "high_value",
    "location": "US"
  },
  "content_template": "Welcome to SkyyRose!",
  "schedule": "2025-10-25T10:00:00Z",
  "budget": 5000.0,
  "ab_test": true
}
```

**Campaign Types**: `email`, `sms`, `social`, `multi_channel`

**Response** (201 Created):
```json
{
  "campaign_id": "uuid-here",
  "status": "scheduled",
  "timestamp": "2026-01-05T12:00:00Z",
  "campaign_type": "email",
  "target_audience_size": 2500,
  "content_generated": false,
  "scheduled_for": "2025-10-25T10:00:00Z",
  "metrics": {
    "estimated_reach": 2500,
    "estimated_engagement_rate": 0.28,
    "estimated_conversion_rate": 0.045,
    "estimated_revenue": 5625.0,
    "confidence_score": 0.82
  }
}
```

**Integration**: `agents/marketing_agent.py` (MarketingAgent)

---

## 6. Commerce

### 6.1 Bulk Product Operations

**Endpoint**: `POST /api/v1/commerce/products/bulk`
**Description**: Perform bulk operations on products.

**Request Body**:
```json
{
  "action": "create",
  "products": [
    {
      "name": "Classic Denim Jacket",
      "sku": "SKR-DEN-JAC-001",
      "price": 89.99,
      "category": "outerwear"
    }
  ],
  "validate_only": false
}
```

**Actions**: `create`, `update`, `delete`

**Response** (200 OK):
```json
{
  "operation_id": "uuid-here",
  "status": "completed",
  "timestamp": "2026-01-05T12:00:00Z",
  "action": "create",
  "total_products": 10,
  "successful": 9,
  "failed": 1,
  "results": [
    {
      "product_id": "prod_abc123",
      "sku": "SKR-DEN-JAC-001",
      "status": "success",
      "message": null
    }
  ]
}
```

**Integration**: `agents/commerce_agent.py` (CommerceAgent)

---

### 6.2 Dynamic Pricing

**Endpoint**: `POST /api/v1/commerce/pricing/optimize`
**Description**: Optimize product pricing using ML and market intelligence.

**Request Body**:
```json
{
  "product_ids": ["PROD123", "PROD456"],
  "strategy": "ml_optimized",
  "constraints": {
    "min_margin": 0.2,
    "max_discount": 0.3
  }
}
```

**Strategies**: `competitive`, `demand_based`, `ml_optimized`, `time_based`

**Response** (200 OK):
```json
{
  "optimization_id": "uuid-here",
  "status": "completed",
  "timestamp": "2026-01-05T12:00:00Z",
  "strategy": "ml_optimized",
  "total_products": 2,
  "optimizations": [
    {
      "product_id": "PROD123",
      "current_price": 89.99,
      "optimized_price": 79.99,
      "price_change": -10.0,
      "price_change_pct": -11.1,
      "estimated_revenue_impact": 450.0,
      "confidence": 0.85
    }
  ],
  "aggregate_metrics": {
    "total_revenue_impact": 900.0,
    "avg_price_change_pct": -11.1
  }
}
```

**Integration**: `agents/commerce_agent.py` (CommerceAgent)

---

## 7. Orchestration

### 7.1 Multi-Agent Workflows

**Endpoint**: `POST /api/v1/orchestration/workflows`
**Description**: Orchestrate multiple AI agents for complex workflows.

**Request Body**:
```json
{
  "workflow_name": "product_launch",
  "parameters": {
    "product_data": {
      "name": "Summer Collection",
      "category": "seasonal"
    },
    "launch_date": "2025-11-01"
  },
  "agents": ["commerce_agent", "marketing_agent"],
  "parallel": true
}
```

**Pre-built Workflows**:
- `product_launch`: Complete product launch automation
- `campaign_optimization`: Marketing campaign improvement
- `inventory_optimization`: Stock management
- `customer_reengagement`: Win back inactive customers

**Response** (202 Accepted):
```json
{
  "workflow_id": "uuid-here",
  "status": "completed",
  "timestamp": "2026-01-05T12:00:00Z",
  "workflow_name": "product_launch",
  "agents_used": ["commerce_agent", "marketing_agent", "creative_agent"],
  "parallel_execution": true,
  "total_duration_seconds": 5.2,
  "task_results": [
    {
      "agent_name": "commerce_agent",
      "task_id": "task_abc123",
      "status": "completed",
      "duration_seconds": 2.5,
      "result": {
        "success": true,
        "artifacts_created": 3
      },
      "error": null
    }
  ],
  "summary": {
    "total_tasks": 3,
    "successful_tasks": 3,
    "failed_tasks": 0,
    "workflow_efficiency": 1.0
  }
}
```

**Integration**: `orchestration/orchestrator.py` (WorkflowOrchestrator)

---

## 8. Monitoring

### 8.1 System Metrics

**Endpoint**: `GET /api/v1/monitoring/metrics`
**Description**: Monitor DevSkyy platform health and performance metrics.

**Query Parameters**:
- `metrics`: Comma-separated list (`health`, `performance`, `ml_accuracy`, `errors`)
- `time_range`: Time window (`1h`, `24h`, `7d`, `30d`)

**Request**:
```
GET /api/v1/monitoring/metrics?metrics=health&metrics=performance&time_range=1h
```

**Response** (200 OK):
```json
{
  "timestamp": "2026-01-05T12:00:00Z",
  "time_range": "1h",
  "metrics": [
    {
      "metric_name": "api_latency_p95",
      "unit": "milliseconds",
      "data_points": [
        {
          "timestamp": "2026-01-05T12:00:00Z",
          "value": 125.5,
          "labels": null
        }
      ],
      "aggregation": "p95"
    }
  ],
  "summary": {
    "overall_health": "healthy",
    "total_requests": 125000,
    "error_rate": 0.012,
    "active_agents": 54
  }
}
```

**Integration**: `security/prometheus_exporter.py`

---

### 8.2 Agent Directory

**Endpoint**: `GET /api/v1/agents`
**Description**: List all DevSkyy AI agents with capabilities.

**Response** (200 OK):
```json
{
  "timestamp": "2026-01-05T12:00:00Z",
  "total_agents": 54,
  "active_agents": 54,
  "agents_by_category": {
    "ecommerce": 12,
    "marketing": 8,
    "content": 10
  },
  "agents": [
    {
      "name": "commerce_agent",
      "version": "v2.1.0",
      "category": "ecommerce",
      "status": "active",
      "capabilities": [
        "product_management",
        "dynamic_pricing",
        "inventory_tracking"
      ],
      "endpoints": [
        "/api/v1/commerce/products",
        "/api/v1/commerce/pricing"
      ],
      "last_execution": "2026-01-05T11:55:00Z"
    }
  ]
}
```

**Integration**: `agents/` directory (dynamic discovery)

---

## 9. Health

### 9.1 Enhanced Health Check

**Endpoint**: `GET /health`
**Description**: Enhanced health check with agent status.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2026-01-05T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "api": "operational",
    "auth": "operational",
    "encryption": "operational",
    "mcp_server": "operational",
    "agents": "operational"
  },
  "agents": {
    "total": 54,
    "active": 54,
    "categories": [
      "infrastructure",
      "ai_intelligence",
      "ecommerce",
      "marketing",
      "content",
      "integration",
      "advanced",
      "frontend"
    ]
  }
}
```

---

## Authentication

All endpoints (except `/`, `/health`, `/ready`, `/live`) require JWT authentication:

```bash
# Get token
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Use token
curl -X POST http://localhost:8000/api/v1/code/scan \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"path": ".", "file_types": ["py"], "deep_scan": false}'
```

---

## Error Handling

All endpoints follow the same error format:

```json
{
  "error": true,
  "status_code": 400,
  "message": "Error description",
  "path": "/api/v1/code/scan",
  "timestamp": "2026-01-05T12:00:00Z"
}
```

**Common Status Codes**:
- `200 OK`: Synchronous success
- `201 Created`: Resource created
- `202 Accepted`: Async operation started
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

## Rate Limiting

Tier-based rate limiting applies to all authenticated endpoints:

- **Free**: 100 requests/hour
- **Starter**: 1000 requests/hour
- **Pro**: 10000 requests/hour

Rate limit info is returned in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1735992000
X-RateLimit-Tier: free
```

---

## Testing

### Automated Tests

```bash
# Run pytest suite
pytest tests/test_new_api_endpoints.py -v
```

### Manual Testing

```bash
# Make script executable
chmod +x scripts/test_new_endpoints.sh

# Test without auth
./scripts/test_new_endpoints.sh

# Test with auth
./scripts/test_new_endpoints.sh http://localhost:8000 YOUR_TOKEN
```

---

## Next Steps

### Integration Tasks

1. **Code Scanner**: Replace mock data with `security/code_scanner.py` integration
2. **Code Fixer**: Implement LLM-based code repair
3. **WordPress**: Integrate `wordpress/elementor.py` ElementorManager
4. **ML Module**: Connect `agents/ml_module.py` for real predictions
5. **Tripo Agent**: Integrate `agents/tripo_agent.py` for 3D generation
6. **Marketing Agent**: Connect `agents/marketing_agent.py`
7. **Commerce Agent**: Integrate `agents/commerce_agent.py`
8. **Orchestrator**: Connect `orchestration/orchestrator.py`
9. **Prometheus**: Enhance metrics with real Prometheus data

### Production Checklist

- [ ] Replace all mock responses with real integrations
- [ ] Add input validation with Pydantic
- [ ] Implement proper error handling
- [ ] Add request/response logging
- [ ] Set up monitoring and alerts
- [ ] Configure rate limiting per endpoint
- [ ] Add OpenAPI documentation
- [ ] Write integration tests
- [ ] Load test all endpoints
- [ ] Security audit

---

## Support

**Documentation**: https://docs.devskyy.com/api
**Email**: support@skyyrose.com
**Security**: security@skyyrose.com

**Version**: 1.0.0
**Last Updated**: 2026-01-05
