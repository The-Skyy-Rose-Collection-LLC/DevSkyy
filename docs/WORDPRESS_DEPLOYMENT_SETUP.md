# WordPress Deployment System Setup Guide

Complete guide for integrating WordPress API with DevSkyy's automated agent deployment system with multi-agent approval workflows.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [WordPress Credentials Setup](#wordpress-credentials-setup)
4. [Infrastructure Registration](#infrastructure-registration)
5. [Example Deployment Jobs](#example-deployment-jobs)
6. [API Usage](#api-usage)
7. [Multi-Agent Approval Workflow](#multi-agent-approval-workflow)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The WordPress deployment system enables:
- **Automated agent deployment** for WordPress tasks
- **Infrastructure validation** before execution
- **2-agent category-head approval** workflow
- **Token cost estimation** per deployment
- **Tool and resource requirements** specification

### Supported Authentication

1. **WordPress.com OAuth 2.0** (Recommended)
   - For WordPress.com hosted sites
   - Supports posts, media, themes, stats

2. **WordPress REST API with Application Passwords**
   - For self-hosted WordPress sites
   - Supports WooCommerce, Yoast SEO, Divi Builder

---

## Prerequisites

### Required
- Python 3.11+
- DevSkyy deployment system installed
- WordPress site (WordPress.com or self-hosted)

### WordPress.com OAuth App
1. Go to https://developer.wordpress.com/apps/
2. Create new application
3. Get Client ID and Client Secret
4. Set redirect URI: `http://localhost:8000/api/v1/wordpress/oauth/callback`

### Self-Hosted WordPress
1. Install WordPress 5.6+
2. Enable Application Passwords (Settings → Users → Application Passwords)
3. Generate application password for API access

---

## WordPress Credentials Setup

### Step 1: Copy `.env.example` to `.env`

```bash
cp .env.example .env
```

### Step 2: Configure WordPress OAuth (Option A)

Edit `.env` and add your WordPress.com OAuth credentials:

```bash
# WordPress.com OAuth 2.0
WORDPRESS_CLIENT_ID=your-client-id-here
WORDPRESS_CLIENT_SECRET=your-client-secret-here
WORDPRESS_REDIRECT_URI=http://localhost:8000/api/v1/wordpress/oauth/callback
WORDPRESS_TOKEN_URL=https://public-api.wordpress.com/oauth2/token
WORDPRESS_AUTHORIZE_URL=https://public-api.wordpress.com/oauth2/authorize
WORDPRESS_API_BASE=https://public-api.wordpress.com/rest/v1.1
```

### Step 3: Configure Basic Auth (Option B)

For self-hosted WordPress sites:

```bash
# Self-Hosted WordPress REST API
SKYY_ROSE_SITE_URL=https://your-wordpress-site.com
SKYY_ROSE_USERNAME=your-wp-admin-username
SKYY_ROSE_PASSWORD=your-wp-admin-password
SKYY_ROSE_APP_PASSWORD=your-application-password
```

### Step 4: Verify Configuration

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OAuth:', bool(os.getenv('WORDPRESS_CLIENT_ID'))); print('Basic:', bool(os.getenv('SKYY_ROSE_SITE_URL')))"
```

---

## Infrastructure Registration

### Run WordPress Infrastructure Setup

This script registers all WordPress tools, resources, and API keys with the deployment system:

```bash
python scripts/wordpress/setup_wordpress_infrastructure.py
```

### What Gets Registered

**Tools (14 WordPress APIs):**
- Content: `wordpress_create_post`, `wordpress_update_post`, `wordpress_create_page`, `wordpress_get_posts`
- Media: `wordpress_upload_media`, `wordpress_get_media`
- Theme: `wordpress_get_theme_info`, `wordpress_customize_theme`
- Site: `wordpress_get_site_info`, `wordpress_get_site_stats`
- E-commerce: `wordpress_woocommerce_products`, `wordpress_woocommerce_orders`
- SEO: `wordpress_yoast_seo`
- Builder: `wordpress_divi_builder`

**Resources:**
- API Quota: 10,000 requests/hour
- Storage: 50 GB
- Memory: 2 GB

**API Keys:**
- WordPress OAuth
- WordPress Basic Auth
- WooCommerce Integration

### Expected Output

```
🚀 WordPress Infrastructure Setup for DevSkyy Deployment System
================================================================================

🔧 Registering WordPress Tools...
   ✓ Registered: wordpress_create_post
   ✓ Registered: wordpress_update_post
   ...
✅ Registered 14 WordPress tools

💾 Registering WordPress Resources...
   ✓ Registered: API_QUOTA (10000.0 requests/hour)
   ✓ Registered: STORAGE (50.0 GB)
   ✓ Registered: MEMORY (2.0 GB)
✅ Registered 3 WordPress resources

🔑 Checking WordPress API Keys...
✅ WordPress OAuth 2.0 credentials configured

📊 API Key Status:
   WordPress OAuth: ✅
   WordPress Basic Auth: ❌
   WooCommerce: ❌

🔍 Running Infrastructure Validation...

📊 Infrastructure Readiness Report:
   Total WordPress Tools: 14
   Available Tools: 14
   Resources: 3
   API Keys Configured: 1/3
   Readiness Score: 100.0%

✅ WordPress infrastructure is READY for deployment!

================================================================================
📋 Setup Summary
================================================================================
✅ WordPress infrastructure setup COMPLETE!
✅ Ready to submit deployment jobs

📖 Next Steps:
   1. Update .env file with your actual WordPress credentials
   2. Review example jobs in docs/wordpress_deployment_examples.json
   3. Submit a job via API: POST /api/v1/deployment/jobs
   4. Monitor approval workflow and deployment status
================================================================================
```

---

## Example Deployment Jobs

### Example 1: Create Luxury Collection Page

**Job Definition:**

```json
{
  "job_name": "Create Luxury Collection Page",
  "job_description": "Create a new luxury product collection page with Divi builder, SEO optimization, and conversion-focused design",
  "category": "WORDPRESS_CMS",
  "primary_agent": "wordpress_fullstack_theme_builder",
  "supporting_agents": ["brand_intelligence", "seo_optimizer"],
  "required_tools": [
    {
      "tool_name": "wordpress_create_page",
      "tool_type": "api",
      "estimated_calls": 1,
      "required": true
    },
    {
      "tool_name": "wordpress_divi_builder",
      "tool_type": "api",
      "estimated_calls": 3,
      "required": true
    },
    {
      "tool_name": "wordpress_upload_media",
      "tool_type": "api",
      "estimated_calls": 5,
      "required": false
    },
    {
      "tool_name": "wordpress_yoast_seo",
      "tool_type": "api",
      "estimated_calls": 1,
      "required": true
    }
  ],
  "required_resources": [
    {
      "resource_type": "API_QUOTA",
      "amount": 20.0,
      "unit": "requests"
    },
    {
      "resource_type": "STORAGE",
      "amount": 0.5,
      "unit": "GB"
    }
  ],
  "max_execution_time_seconds": 600,
  "max_retries": 3,
  "priority": 8,
  "max_budget_usd": 2.0,
  "tags": ["wordpress", "luxury", "divi", "seo"]
}
```

**Estimated Costs:**
- Tokens: ~15,000
- Cost: ~$0.15
- Execution Time: 2-5 minutes
- API Calls: 10-20

### Example 2: Optimize WooCommerce Products

```json
{
  "job_name": "Optimize WooCommerce Products",
  "job_description": "Audit and optimize all WooCommerce products for SEO, descriptions, images, and conversion",
  "category": "ECOMMERCE",
  "primary_agent": "ecommerce_agent",
  "supporting_agents": ["seo_optimizer", "brand_intelligence"],
  "required_tools": [
    {
      "tool_name": "wordpress_woocommerce_products",
      "tool_type": "api",
      "estimated_calls": 50,
      "required": true
    },
    {
      "tool_name": "wordpress_get_media",
      "tool_type": "api",
      "estimated_calls": 100,
      "required": true
    },
    {
      "tool_name": "wordpress_yoast_seo",
      "tool_type": "api",
      "estimated_calls": 50,
      "required": true
    }
  ],
  "required_resources": [
    {
      "resource_type": "API_QUOTA",
      "amount": 300.0,
      "unit": "requests"
    },
    {
      "resource_type": "MEMORY",
      "amount": 1.0,
      "unit": "GB"
    }
  ],
  "max_execution_time_seconds": 1800,
  "max_retries": 3,
  "priority": 7,
  "max_budget_usd": 5.0,
  "tags": ["woocommerce", "ecommerce", "seo", "optimization"]
}
```

**Estimated Costs:**
- Tokens: ~50,000
- Cost: ~$0.50
- Execution Time: 10-30 minutes
- API Calls: 200+

### Example 3: Update Blog Content for SEO

```json
{
  "job_name": "Update Blog Content for SEO",
  "job_description": "Audit and update existing blog posts for SEO optimization, readability, and brand consistency",
  "category": "MARKETING_BRAND",
  "primary_agent": "seo_optimizer",
  "supporting_agents": ["brand_intelligence", "content_writer"],
  "required_tools": [
    {
      "tool_name": "wordpress_get_posts",
      "tool_type": "api",
      "estimated_calls": 1,
      "required": true
    },
    {
      "tool_name": "wordpress_update_post",
      "tool_type": "api",
      "estimated_calls": 20,
      "required": true
    },
    {
      "tool_name": "wordpress_yoast_seo",
      "tool_type": "api",
      "estimated_calls": 20,
      "required": true
    }
  ],
  "required_resources": [
    {
      "resource_type": "API_QUOTA",
      "amount": 100.0,
      "unit": "requests"
    }
  ],
  "max_execution_time_seconds": 900,
  "max_retries": 3,
  "priority": 6,
  "max_budget_usd": 3.0,
  "tags": ["blog", "seo", "content", "optimization"]
}
```

**Estimated Costs:**
- Tokens: ~35,000
- Cost: ~$0.35
- Execution Time: 5-15 minutes
- API Calls: 41+

---

## API Usage

### 1. Validate Job Without Deploying

```bash
curl -X POST http://localhost:8000/api/v1/deployment/validate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d @docs/wordpress_deployment_examples.json
```

**Response:**

```json
{
  "is_ready": true,
  "checks_passed": 12,
  "checks_failed": 0,
  "missing_tools": [],
  "missing_resources": [],
  "warnings": [],
  "estimated_tokens": 15000,
  "estimated_cost_usd": 0.15,
  "detailed_results": {
    "tools_available": true,
    "resources_sufficient": true,
    "api_keys_configured": true,
    "rate_limits_ok": true
  }
}
```

### 2. Submit Deployment Job

```bash
curl -X POST http://localhost:8000/api/v1/deployment/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "job_name": "Create Luxury Collection Page",
    "job_description": "Create a new luxury product collection page",
    "category": "WORDPRESS_CMS",
    "primary_agent": "wordpress_fullstack_theme_builder",
    "supporting_agents": ["brand_intelligence", "seo_optimizer"],
    "required_tools": [...],
    "required_resources": [...],
    "max_budget_usd": 2.0
  }'
```

**Response:**

```json
{
  "status": "success",
  "message": "Job submitted: pending_approval",
  "job_id": "job_01HQXYZ...",
  "deployment_id": null,
  "can_proceed": false,
  "validation": {
    "is_ready": true,
    "checks_passed": 12,
    "checks_failed": 0
  },
  "approval": {
    "status": "pending",
    "required_approvals": 2,
    "approved_count": 0,
    "rejected_count": 0
  },
  "estimated_tokens": 15000,
  "estimated_cost_usd": 0.15
}
```

### 3. Check Approval Status

```bash
curl http://localhost:8000/api/v1/deployment/approvals/job_01HQXYZ... \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**

```json
{
  "workflow_id": "approval_01HQXYZ...",
  "required_approvals": 2,
  "approved_count": 2,
  "rejected_count": 0,
  "final_decision": "APPROVED",
  "consensus_reasoning": "Both category heads approve. WordPress infrastructure validated. Budget within limits.",
  "individual_approvals": [
    {
      "agent_name": "wordpress_divi_elementor_agent",
      "status": "APPROVED",
      "confidence": 0.92,
      "reasoning": "Job aligns with Divi builder capabilities and luxury design standards",
      "concerns": [],
      "recommendations": ["Use Divi premium layouts", "Implement mobile-first design"],
      "timestamp": "2025-01-18T10:30:15Z"
    },
    {
      "agent_name": "wordpress_fullstack_theme_builder",
      "status": "APPROVED",
      "confidence": 0.95,
      "reasoning": "Infrastructure validated. All required tools available. SEO optimization included.",
      "concerns": [],
      "recommendations": ["Include schema markup", "Optimize for Core Web Vitals"],
      "timestamp": "2025-01-18T10:30:17Z"
    }
  ],
  "timestamp": "2025-01-18T10:30:20Z"
}
```

### 4. Get Job Status

```bash
curl http://localhost:8000/api/v1/deployment/jobs/job_01HQXYZ... \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**

```json
{
  "job_id": "job_01HQXYZ...",
  "job_name": "Create Luxury Collection Page",
  "category": "WORDPRESS_CMS",
  "status": "completed",
  "validation_status": {
    "is_ready": true,
    "checks_passed": 12
  },
  "approval_status": {
    "final_decision": "APPROVED",
    "approved_count": 2
  },
  "deployment_status": {
    "status": "completed",
    "start_time": "2025-01-18T10:31:00Z",
    "end_time": "2025-01-18T10:34:30Z",
    "execution_time_seconds": 210,
    "result": {
      "page_id": 1234,
      "page_url": "https://your-site.com/luxury-collection",
      "success": true
    }
  },
  "estimated_tokens": 15000,
  "estimated_cost_usd": 0.15,
  "actual_tokens_used": 14823,
  "actual_cost_usd": 0.148
}
```

---

## Multi-Agent Approval Workflow

### How It Works

1. **Job Submission**
   - User submits WordPress deployment job via API
   - System validates infrastructure readiness
   - System estimates token costs

2. **Category Head Selection**
   - System identifies job category (e.g., WORDPRESS_CMS)
   - Selects 2 category-head agents for that category
   - Example: `wordpress_divi_elementor_agent` + `wordpress_fullstack_theme_builder`

3. **Independent Review**
   - Each agent reviews job independently
   - Checks: Infrastructure, tools, budget, alignment with capabilities
   - Each votes: APPROVED, REJECTED, or ABSTAIN

4. **Consensus Decision**
   - **APPROVED**: Both agents approve (2/2)
   - **REJECTED**: Any agent rejects
   - **PENDING**: Abstentions or tied vote

5. **Deployment or Rejection**
   - If APPROVED → Job deploys and executes
   - If REJECTED → Job blocked, user notified with reasoning
   - If PENDING → Escalated or user contacted

### Category Heads by Category

| Category | Category Head 1 | Category Head 2 |
|----------|----------------|----------------|
| WORDPRESS_CMS | wordpress_fullstack_theme_builder | wordpress_divi_elementor_agent |
| ECOMMERCE | ecommerce_agent | inventory_manager |
| MARKETING_BRAND | brand_intelligence | seo_optimizer |
| CORE_SECURITY | scanner_v2 | security_compliance |

---

## Troubleshooting

### Error: "API key not configured for 'wordpress'"

**Cause:** WordPress credentials not in `.env` file

**Solution:**
1. Edit `.env` file
2. Add `WORDPRESS_CLIENT_ID` and `WORDPRESS_CLIENT_SECRET`
3. Run setup script again

### Error: "Missing required tool: wordpress_create_page"

**Cause:** WordPress infrastructure not registered

**Solution:**
```bash
python scripts/wordpress/setup_wordpress_infrastructure.py
```

### Error: "Job rejected by category heads"

**Cause:** Agents identified issues with job definition

**Solution:**
1. Check approval reasoning: `GET /api/v1/deployment/approvals/{job_id}`
2. Review agent concerns and recommendations
3. Update job definition to address concerns
4. Resubmit job

### Error: "Insufficient API quota"

**Cause:** Job requires more requests than available quota

**Solution:**
1. Reduce `estimated_calls` in tool requirements
2. Batch operations across multiple jobs
3. Increase API quota allocation (contact WordPress.com)

### Error: "Token expired"

**Cause:** WordPress OAuth token expired

**Solution:**
- System automatically refreshes tokens using refresh token
- If refresh fails, re-authenticate via OAuth flow

---

## Performance Metrics

### Expected Performance by Job Type

| Job Type | Avg Tokens | Avg Cost | Avg Time | Success Rate |
|----------|-----------|----------|----------|--------------|
| Create Page | 12,000 | $0.12 | 3 min | 98% |
| Update Posts | 30,000 | $0.30 | 8 min | 95% |
| WooCommerce Optimization | 45,000 | $0.45 | 15 min | 92% |
| Site Monitoring | 8,000 | $0.08 | 2 min | 99% |

### Token Cost Breakdown

**Input Tokens (30%):**
- Job definition
- Tool schemas
- Agent instructions
- Context data

**Output Tokens (70%):**
- Generated content
- API responses
- Approval reasoning
- Execution logs

---

## Security Best Practices

1. **Never Commit Credentials**
   - `.env` is in `.gitignore`
   - Use environment variables only

2. **Rotate Credentials Regularly**
   - WordPress Application Passwords monthly
   - OAuth tokens refreshed automatically

3. **Limit API Scopes**
   - Request minimum required scopes
   - Separate credentials for different agents

4. **Monitor API Usage**
   - Track API calls via deployment statistics
   - Set up rate limit alerts

5. **Audit Approvals**
   - Review approval logs regularly
   - Investigate rejected jobs

---

## Next Steps

1. ✅ Configure WordPress credentials in `.env`
2. ✅ Run infrastructure setup script
3. ✅ Verify readiness score ≥ 80%
4. 📝 Review example jobs in `docs/wordpress_deployment_examples.json`
5. 🚀 Submit your first deployment job via API
6. 📊 Monitor approval workflow and execution
7. 🔄 Iterate based on performance data

---

**Document Version:** 1.0.0
**Last Updated:** 2025-01-18
**Related Docs:**
- [Agent Deployment Guide](AGENT_DEPLOYMENT_GUIDE.md)
- [Research Findings 2025](../RESEARCH_FINDINGS_2025.md)
- [Agent Finetuning](AGENT_FINETUNING.md)
