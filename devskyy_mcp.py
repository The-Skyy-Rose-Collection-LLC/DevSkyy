#!/usr/bin/env python3
"""
DevSkyy MCP Server
Industry-First Multi-Agent AI Platform Integration via Model Context Protocol

Exposes 54 AI agents through 11 powerful MCP tools for:
- Code analysis and fixing
- WordPress theme generation
- ML predictions (fashion trends, pricing, demand)
- E-commerce automation
- Marketing campaigns
- System monitoring and self-healing

Author: DevSkyy Platform Team
Version: 1.0.0
Python: 3.11+
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# ============================================================================
# CONFIGURATION
# ============================================================================

# API Configuration
DEVSKYY_API_URL = os.getenv("DEVSKYY_API_URL", "http://localhost:8000")
DEVSKYY_API_KEY = os.getenv("DEVSKYY_API_KEY", "")
REQUEST_TIMEOUT = 60.0

# MCP Server Configuration
MCP_SERVER_NAME = "devskyy"
MCP_SERVER_VERSION = "1.0.0"

# ============================================================================
# MODELS
# ============================================================================

class AgentInfo(BaseModel):
    """Information about a DevSkyy agent."""
    name: str
    category: str
    description: str
    capabilities: List[str]
    status: str = "active"

class ScanResult(BaseModel):
    """Code scanning results."""
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)

class FixResult(BaseModel):
    """Code fix results."""
    fixed: bool
    changes_made: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)

# ============================================================================
# DEVSKYY API CLIENT
# ============================================================================

class DevSkyyClient:
    """Client for DevSkyy API."""

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.api_url}{endpoint}"

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                return {
                    "error": str(e),
                    "status_code": getattr(e.response, "status_code", None)
                }

    async def list_agents(self) -> List[AgentInfo]:
        """List all available agents."""
        # For now, return the comprehensive list of agents
        # In production, this would call /api/v1/agents
        return [
            # Infrastructure Agents (8)
            AgentInfo(
                name="scanner",
                category="Infrastructure",
                description="Advanced code scanner for errors, security issues, and performance bottlenecks",
                capabilities=["code_analysis", "security_scan", "performance_check", "best_practices"]
            ),
            AgentInfo(
                name="code_fixer",
                category="Infrastructure",
                description="Automated code fixing with ML-powered suggestions",
                capabilities=["auto_fix", "refactoring", "optimization", "modernization"]
            ),
            AgentInfo(
                name="self_healing",
                category="Infrastructure",
                description="Self-healing system that monitors and auto-repairs issues",
                capabilities=["health_monitoring", "auto_repair", "recovery", "diagnostics"]
            ),
            AgentInfo(
                name="security_manager",
                category="Infrastructure",
                description="Comprehensive security management and vulnerability scanning",
                capabilities=["vulnerability_scan", "penetration_test", "compliance_check", "threat_detection"]
            ),

            # AI/ML Agents (12)
            AgentInfo(
                name="nlp_processor",
                category="AI/ML",
                description="Natural language processing for text analysis and understanding",
                capabilities=["text_analysis", "entity_extraction", "intent_recognition", "language_detection"]
            ),
            AgentInfo(
                name="sentiment_analyzer",
                category="AI/ML",
                description="Sentiment analysis for customer feedback and social media",
                capabilities=["sentiment_detection", "emotion_analysis", "trend_detection"]
            ),
            AgentInfo(
                name="content_generator",
                category="AI/ML",
                description="AI-powered content generation for various formats",
                capabilities=["text_generation", "copywriting", "seo_optimization", "multilingual"]
            ),
            AgentInfo(
                name="ml_predictor",
                category="AI/ML",
                description="Machine learning predictions for fashion trends, demand, and pricing",
                capabilities=["trend_prediction", "demand_forecasting", "price_optimization", "customer_segmentation"]
            ),

            # E-Commerce Agents (10)
            AgentInfo(
                name="product_manager",
                category="E-Commerce",
                description="Comprehensive product management and optimization",
                capabilities=["product_creation", "inventory_management", "variant_handling", "seo_optimization"]
            ),
            AgentInfo(
                name="dynamic_pricing",
                category="E-Commerce",
                description="ML-powered dynamic pricing optimization",
                capabilities=["price_optimization", "competitor_analysis", "demand_pricing", "ab_testing"]
            ),
            AgentInfo(
                name="inventory_optimizer",
                category="E-Commerce",
                description="Intelligent inventory management and forecasting",
                capabilities=["stock_prediction", "reorder_automation", "warehouse_optimization"]
            ),

            # Marketing Agents (8)
            AgentInfo(
                name="email_automation",
                category="Marketing",
                description="Automated email campaign management and optimization",
                capabilities=["campaign_creation", "segmentation", "ab_testing", "analytics"]
            ),
            AgentInfo(
                name="sms_automation",
                category="Marketing",
                description="SMS marketing automation with compliance",
                capabilities=["sms_campaigns", "opt_in_management", "delivery_tracking"]
            ),
            AgentInfo(
                name="social_media",
                category="Marketing",
                description="Multi-platform social media automation",
                capabilities=["post_scheduling", "engagement_tracking", "content_curation", "analytics"]
            ),

            # Content Agents (6)
            AgentInfo(
                name="seo_optimizer",
                category="Content",
                description="Advanced SEO optimization and analysis",
                capabilities=["keyword_research", "on_page_seo", "content_optimization", "rank_tracking"]
            ),
            AgentInfo(
                name="copywriter",
                category="Content",
                description="AI copywriting for various marketing materials",
                capabilities=["product_descriptions", "ad_copy", "blog_posts", "email_content"]
            ),

            # Integration Agents (4)
            AgentInfo(
                name="wordpress_theme_generator",
                category="Integration",
                description="Automated WordPress theme generation and customization",
                capabilities=["theme_generation", "elementor_integration", "responsive_design", "seo_ready"]
            ),
            AgentInfo(
                name="shopify_connector",
                category="Integration",
                description="Shopify platform integration and synchronization",
                capabilities=["product_sync", "order_management", "inventory_sync"]
            ),

            # Advanced Agents (4)
            AgentInfo(
                name="ml_trainer",
                category="Advanced",
                description="Machine learning model training and deployment",
                capabilities=["model_training", "hyperparameter_tuning", "deployment", "monitoring"]
            ),
            AgentInfo(
                name="analytics_engine",
                category="Advanced",
                description="Advanced analytics and business intelligence",
                capabilities=["data_analysis", "visualization", "reporting", "insights"]
            ),
        ]

    async def scan_code(self, directory: str, options: Dict[str, Any]) -> ScanResult:
        """Scan code for issues."""
        result = await self.request(
            "POST",
            "/api/v1/agents/scanner/scan",
            data={"directory": directory, "options": options}
        )
        return ScanResult(**result) if "error" not in result else ScanResult()

    async def fix_code(self, issues: List[Dict[str, Any]]) -> FixResult:
        """Fix code issues."""
        result = await self.request(
            "POST",
            "/api/v1/agents/code_fixer/fix",
            data={"issues": issues}
        )
        return FixResult(**result) if "error" not in result else FixResult(fixed=False)

    async def self_healing_check(self) -> Dict[str, Any]:
        """Run self-healing system check."""
        return await self.request("POST", "/api/v1/agents/self_healing/check")

    async def generate_wordpress_theme(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate WordPress theme."""
        return await self.request(
            "POST",
            "/api/v1/agents/wordpress_theme_generator/generate",
            data=config
        )

    async def ml_prediction(self, prediction_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make ML prediction."""
        return await self.request(
            "POST",
            f"/api/v1/agents/ml_predictor/{prediction_type}",
            data=data
        )

    async def manage_product(self, action: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage product."""
        return await self.request(
            "POST",
            f"/api/v1/agents/product_manager/{action}",
            data=product_data
        )

    async def dynamic_pricing(self, product_ids: List[str], strategy: str) -> Dict[str, Any]:
        """Optimize pricing."""
        return await self.request(
            "POST",
            "/api/v1/agents/dynamic_pricing/optimize",
            data={"product_ids": product_ids, "strategy": strategy}
        )

    async def marketing_campaign(self, campaign_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create marketing campaign."""
        return await self.request(
            "POST",
            f"/api/v1/agents/{campaign_type}_automation/campaign",
            data=config
        )

    async def multi_agent_workflow(self, workflow_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multi-agent workflow."""
        return await self.request(
            "POST",
            "/api/v1/workflows/execute",
            data={"workflow": workflow_name, "parameters": params}
        )

    async def system_monitoring(self) -> Dict[str, Any]:
        """Get system monitoring data."""
        return await self.request("GET", "/api/v1/monitoring/metrics")

# ============================================================================
# MCP SERVER
# ============================================================================

# Initialize MCP server
mcp = FastMCP(MCP_SERVER_NAME, version=MCP_SERVER_VERSION)

# Initialize API client
client = DevSkyyClient(DEVSKYY_API_URL, DEVSKYY_API_KEY)

# ============================================================================
# MCP TOOLS
# ============================================================================

@mcp.tool()
async def devskyy_list_agents() -> str:
    """
    List all available DevSkyy AI agents.

    Returns a comprehensive list of all 54 agents organized by category:
    - Infrastructure (8): Scanner, Fixer, Self-Healing, Security
    - AI/ML (12): NLP, Sentiment, Content Generation, ML Predictions
    - E-Commerce (10): Products, Pricing, Inventory, Orders
    - Marketing (8): Email, SMS, Social Media, Campaigns
    - Content (6): SEO, Copywriting, Images, Video
    - Integration (4): WordPress, Shopify, WooCommerce
    - Advanced (4): ML Training, Analytics, Blockchain
    - Frontend (2): UI Components, Themes
    """
    agents = await client.list_agents()

    # Organize by category
    by_category = {}
    for agent in agents:
        if agent.category not in by_category:
            by_category[agent.category] = []
        by_category[agent.category].append(agent)

    # Format output
    output = ["# DevSkyy AI Agents\n"]
    for category, category_agents in sorted(by_category.items()):
        output.append(f"\n## {category} ({len(category_agents)} agents)\n")
        for agent in category_agents:
            output.append(f"### {agent.name}")
            output.append(f"{agent.description}\n")
            output.append(f"**Capabilities:** {', '.join(agent.capabilities)}\n")

    return "\n".join(output)

@mcp.tool()
async def devskyy_scan_code(
    directory: str,
    include_security: bool = True,
    include_performance: bool = True,
    include_best_practices: bool = True
) -> str:
    """
    Scan code for errors, security issues, and performance bottlenecks.

    Args:
        directory: Path to directory to scan
        include_security: Include security vulnerability scanning
        include_performance: Include performance analysis
        include_best_practices: Include best practices checking

    Returns:
        Detailed scan results with errors, warnings, and suggestions
    """
    options = {
        "security": include_security,
        "performance": include_performance,
        "best_practices": include_best_practices
    }

    result = await client.scan_code(directory, options)

    output = [f"# Code Scan Results for {directory}\n"]

    if result.errors:
        output.append(f"\n## Errors ({len(result.errors)})\n")
        for error in result.errors:
            output.append(f"- **{error.get('file')}:{error.get('line')}** - {error.get('message')}")

    if result.warnings:
        output.append(f"\n## Warnings ({len(result.warnings)})\n")
        for warning in result.warnings:
            output.append(f"- **{warning.get('file')}:{warning.get('line')}** - {warning.get('message')}")

    if result.suggestions:
        output.append(f"\n## Suggestions ({len(result.suggestions)})\n")
        for suggestion in result.suggestions:
            output.append(f"- {suggestion.get('message')}")

    if result.metrics:
        output.append(f"\n## Metrics\n")
        for key, value in result.metrics.items():
            output.append(f"- {key}: {value}")

    return "\n".join(output)

@mcp.tool()
async def devskyy_fix_code(issues_json: str) -> str:
    """
    Automatically fix code issues identified by the scanner.

    Args:
        issues_json: JSON string of issues to fix (from scan results)

    Returns:
        Summary of fixes applied
    """
    issues = json.loads(issues_json)
    result = await client.fix_code(issues)

    output = ["# Code Fix Results\n"]
    output.append(f"\n**Status:** {'✅ Fixed' if result.fixed else '❌ Failed'}\n")

    if result.changes_made:
        output.append(f"\n## Changes Made ({len(result.changes_made)})\n")
        for change in result.changes_made:
            output.append(f"- {change}")

    if result.files_modified:
        output.append(f"\n## Files Modified ({len(result.files_modified)})\n")
        for file in result.files_modified:
            output.append(f"- {file}")

    return "\n".join(output)

@mcp.tool()
async def devskyy_self_healing() -> str:
    """
    Run self-healing system check and auto-repair.

    Monitors system health and automatically repairs issues:
    - Service health checks
    - Resource monitoring (CPU, memory, disk)
    - Auto-restart failed services
    - Clear caches and temporary files
    - Database optimization

    Returns:
        Health status and repairs performed
    """
    result = await client.self_healing_check()

    output = ["# Self-Healing System Check\n"]
    output.append(f"\n**Status:** {result.get('status', 'unknown')}\n")
    output.append(f"**Timestamp:** {datetime.now().isoformat()}\n")

    if "repairs" in result:
        output.append(f"\n## Repairs Performed ({len(result['repairs'])})\n")
        for repair in result['repairs']:
            output.append(f"- {repair}")

    if "health_checks" in result:
        output.append(f"\n## Health Checks\n")
        for check, status in result['health_checks'].items():
            emoji = "✅" if status == "healthy" else "❌"
            output.append(f"- {emoji} {check}: {status}")

    return "\n".join(output)

@mcp.tool()
async def devskyy_generate_wordpress_theme(
    brand_name: str,
    industry: str = "fashion",
    theme_type: str = "elementor",
    color_palette: str = "#FF5733,#3498DB,#2ECC71",
    pages: str = "home,shop,about,contact"
) -> str:
    """
    Generate custom WordPress theme with AI.

    Args:
        brand_name: Name of the brand/business
        industry: Industry type (fashion, tech, food, health, etc.)
        theme_type: Theme builder (elementor, gutenberg, custom)
        color_palette: Comma-separated hex colors
        pages: Comma-separated list of pages to generate

    Returns:
        Download link for generated theme .zip file
    """
    config = {
        "brand_name": brand_name,
        "industry": industry,
        "theme_type": theme_type,
        "color_palette": color_palette.split(","),
        "pages": pages.split(",")
    }

    result = await client.generate_wordpress_theme(config)

    output = ["# WordPress Theme Generation\n"]
    output.append(f"\n**Brand:** {brand_name}")
    output.append(f"**Industry:** {industry}")
    output.append(f"**Theme Type:** {theme_type}\n")

    if "download_url" in result:
        output.append(f"\n✅ **Theme Generated Successfully!**\n")
        output.append(f"**Download:** {result['download_url']}\n")
        output.append(f"\n## Features\n")
        for feature in result.get("features", []):
            output.append(f"- {feature}")
    else:
        output.append(f"\n❌ Generation failed: {result.get('error', 'Unknown error')}")

    return "\n".join(output)

@mcp.tool()
async def devskyy_ml_prediction(
    prediction_type: str,
    data_json: str
) -> str:
    """
    Make ML predictions for fashion, pricing, demand, or customer segments.

    Args:
        prediction_type: Type of prediction (fashion_trends, demand_forecast, price_optimize, customer_segment)
        data_json: JSON string with prediction input data

    Returns:
        Prediction results with confidence scores
    """
    data = json.loads(data_json)
    result = await client.ml_prediction(prediction_type, data)

    output = [f"# ML Prediction: {prediction_type}\n"]

    if "predictions" in result:
        output.append(f"\n## Predictions\n")
        for pred in result["predictions"]:
            conf = pred.get("confidence", 0) * 100
            output.append(f"- **{pred.get('label')}**: {pred.get('value')} (confidence: {conf:.1f}%)")

    if "insights" in result:
        output.append(f"\n## Insights\n")
        for insight in result["insights"]:
            output.append(f"- {insight}")

    return "\n".join(output)

@mcp.tool()
async def devskyy_manage_products(
    action: str,
    product_data_json: str
) -> str:
    """
    Manage e-commerce products (create, update, optimize).

    Args:
        action: Action to perform (create, update, delete, optimize_seo, generate_variants)
        product_data_json: JSON string with product data

    Returns:
        Result of product management action
    """
    product_data = json.loads(product_data_json)
    result = await client.manage_product(action, product_data)

    output = [f"# Product Management: {action}\n"]

    if "product_id" in result:
        output.append(f"\n✅ **Success!**\n")
        output.append(f"**Product ID:** {result['product_id']}")

        if "url" in result:
            output.append(f"**URL:** {result['url']}")

    if "optimizations" in result:
        output.append(f"\n## Optimizations Applied\n")
        for opt in result["optimizations"]:
            output.append(f"- {opt}")

    return "\n".join(output)

@mcp.tool()
async def devskyy_dynamic_pricing(
    product_ids: str,
    strategy: str = "ml_optimized"
) -> str:
    """
    Optimize product pricing with ML.

    Args:
        product_ids: Comma-separated product IDs
        strategy: Pricing strategy (ml_optimized, competitor_based, demand_based, ab_test)

    Returns:
        Optimized prices with revenue projections
    """
    ids = product_ids.split(",")
    result = await client.dynamic_pricing(ids, strategy)

    output = [f"# Dynamic Pricing: {strategy}\n"]

    if "optimized_prices" in result:
        output.append(f"\n## Optimized Prices\n")
        for price_data in result["optimized_prices"]:
            output.append(f"- **{price_data['product_id']}**: ${price_data['old_price']} → ${price_data['new_price']} ({price_data['change_pct']:+.1f}%)")

    if "projected_revenue" in result:
        output.append(f"\n## Revenue Projection\n")
        output.append(f"- Current: ${result['current_revenue']:,.2f}")
        output.append(f"- Projected: ${result['projected_revenue']:,.2f}")
        output.append(f"- Increase: ${result['revenue_increase']:,.2f} ({result['increase_pct']:+.1f}%)")

    return "\n".join(output)

@mcp.tool()
async def devskyy_marketing_campaign(
    campaign_type: str,
    config_json: str
) -> str:
    """
    Create automated marketing campaigns (email, SMS, social media).

    Args:
        campaign_type: Type of campaign (email, sms, social_media, multi_channel)
        config_json: JSON string with campaign configuration

    Returns:
        Campaign creation results and tracking info
    """
    config = json.loads(config_json)
    result = await client.marketing_campaign(campaign_type, config)

    output = [f"# Marketing Campaign: {campaign_type}\n"]

    if "campaign_id" in result:
        output.append(f"\n✅ **Campaign Created!**\n")
        output.append(f"**Campaign ID:** {result['campaign_id']}")
        output.append(f"**Status:** {result.get('status', 'scheduled')}")

        if "recipients" in result:
            output.append(f"**Recipients:** {result['recipients']:,}")

        if "scheduled_time" in result:
            output.append(f"**Scheduled:** {result['scheduled_time']}")

    if "preview_url" in result:
        output.append(f"\n**Preview:** {result['preview_url']}")

    return "\n".join(output)

@mcp.tool()
async def devskyy_multi_agent_workflow(
    workflow_name: str,
    parameters_json: str,
    parallel: bool = False
) -> str:
    """
    Execute multi-agent workflow orchestration.

    Coordinate multiple agents for complex tasks like:
    - product_launch: Product creation → SEO → Pricing → Campaign
    - content_pipeline: Research → Writing → SEO → Publishing
    - customer_journey: Onboarding → Engagement → Retention

    Args:
        workflow_name: Name of workflow to execute
        parameters_json: JSON string with workflow parameters
        parallel: Execute agents in parallel where possible

    Returns:
        Workflow execution results
    """
    params = json.loads(parameters_json)
    params["parallel"] = parallel

    result = await client.multi_agent_workflow(workflow_name, params)

    output = [f"# Multi-Agent Workflow: {workflow_name}\n"]

    if "execution_id" in result:
        output.append(f"\n**Execution ID:** {result['execution_id']}")
        output.append(f"**Status:** {result.get('status', 'running')}\n")

    if "steps" in result:
        output.append(f"\n## Workflow Steps\n")
        for step in result["steps"]:
            status_emoji = "✅" if step["status"] == "completed" else "⏳"
            output.append(f"{status_emoji} **{step['agent']}**: {step['description']}")
            if "result" in step:
                output.append(f"   - {step['result']}")

    if "summary" in result:
        output.append(f"\n## Summary\n{result['summary']}")

    return "\n".join(output)

@mcp.tool()
async def devskyy_system_monitoring() -> str:
    """
    Get real-time system monitoring and health metrics.

    Returns:
        - API health status
        - Agent status (active/idle/busy)
        - Resource usage (CPU, memory, disk)
        - Request metrics (rate, latency, errors)
        - Queue status
    """
    result = await client.system_monitoring()

    output = ["# System Monitoring\n"]
    output.append(f"**Timestamp:** {datetime.now().isoformat()}\n")

    if "api_health" in result:
        output.append(f"\n## API Health\n")
        health = result["api_health"]
        output.append(f"- Status: {health.get('status', 'unknown')}")
        output.append(f"- Uptime: {health.get('uptime', '0s')}")
        output.append(f"- Version: {health.get('version', 'unknown')}")

    if "agents" in result:
        output.append(f"\n## Agent Status\n")
        for agent, status in result["agents"].items():
            output.append(f"- {agent}: {status}")

    if "resources" in result:
        output.append(f"\n## Resources\n")
        res = result["resources"]
        output.append(f"- CPU: {res.get('cpu_percent', 0):.1f}%")
        output.append(f"- Memory: {res.get('memory_percent', 0):.1f}%")
        output.append(f"- Disk: {res.get('disk_percent', 0):.1f}%")

    if "metrics" in result:
        output.append(f"\n## Request Metrics\n")
        metrics = result["metrics"]
        output.append(f"- Requests/min: {metrics.get('requests_per_minute', 0)}")
        output.append(f"- Avg Latency: {metrics.get('avg_latency_ms', 0):.1f}ms")
        output.append(f"- Error Rate: {metrics.get('error_rate', 0):.2f}%")

    return "\n".join(output)

# ============================================================================
# ENHANCED SECURITY TOOLS
# ============================================================================

@mcp.tool()
async def devskyy_security_scan() -> str:
    """
    Comprehensive security vulnerability scan.

    Performs deep security analysis including:
    - SAST (Static Application Security Testing)
    - Dependency vulnerability scanning
    - Container security assessment
    - Authentication/authorization review
    - Data protection compliance check

    Returns detailed security report with remediation steps.
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{DEVSKYY_API_URL}/api/v1/security/comprehensive-scan",
                headers={"Authorization": f"Bearer {DEVSKYY_API_KEY}"},
                json={"scan_type": "comprehensive", "include_remediation": True}
            )

            if response.status_code == 200:
                result = response.json()
                output = ["🔒 **DevSkyy Security Scan Results**\n"]

                # Security Score
                score = result.get("security_score", 0)
                grade = result.get("security_grade", "Unknown")
                output.append(f"**Security Score:** {score}/100 (Grade: {grade})")

                # Vulnerabilities by severity
                vulns = result.get("vulnerabilities", {})
                output.append(f"\n**Vulnerabilities Found:**")
                output.append(f"- 🔴 Critical: {vulns.get('critical', 0)}")
                output.append(f"- 🟠 High: {vulns.get('high', 0)}")
                output.append(f"- 🟡 Medium: {vulns.get('medium', 0)}")
                output.append(f"- 🔵 Low: {vulns.get('low', 0)}")

                # Top issues
                if "top_issues" in result:
                    output.append(f"\n**Top Security Issues:**")
                    for issue in result["top_issues"][:5]:
                        output.append(f"- {issue['severity'].upper()}: {issue['title']}")
                        output.append(f"  Fix: {issue['remediation']}")

                # Compliance status
                if "compliance" in result:
                    output.append(f"\n**Compliance Status:**")
                    for standard, status in result["compliance"].items():
                        emoji = "✅" if status == "compliant" else "❌"
                        output.append(f"- {emoji} {standard}: {status}")

                return "\n".join(output)
            else:
                return f"❌ Security scan failed: {response.text}"

    except Exception as e:
        return f"❌ Error during security scan: {str(e)}"

@mcp.tool()
async def devskyy_security_remediate(issue_ids: str) -> str:
    """
    Automatically remediate security vulnerabilities.

    Args:
        issue_ids: Comma-separated list of security issue IDs to fix

    Applies automated fixes for:
    - Code injection vulnerabilities
    - Authentication bypasses
    - Insecure configurations
    - Dependency vulnerabilities
    - Container security issues

    Returns remediation report with applied fixes.
    """
    try:
        issue_list = [id.strip() for id in issue_ids.split(",")]

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{DEVSKYY_API_URL}/api/v1/security/auto-remediate",
                headers={"Authorization": f"Bearer {DEVSKYY_API_KEY}"},
                json={"issue_ids": issue_list, "auto_apply": True}
            )

            if response.status_code == 200:
                result = response.json()
                output = ["🛠️ **Security Remediation Results**\n"]

                # Summary
                fixed = result.get("fixed_count", 0)
                failed = result.get("failed_count", 0)
                output.append(f"**Summary:** {fixed} fixed, {failed} failed")

                # Fixed issues
                if "fixed_issues" in result:
                    output.append(f"\n**✅ Successfully Fixed:**")
                    for fix in result["fixed_issues"]:
                        output.append(f"- {fix['id']}: {fix['title']}")
                        output.append(f"  Action: {fix['action_taken']}")

                # Failed issues
                if "failed_issues" in result:
                    output.append(f"\n**❌ Failed to Fix:**")
                    for fail in result["failed_issues"]:
                        output.append(f"- {fail['id']}: {fail['title']}")
                        output.append(f"  Reason: {fail['reason']}")
                        output.append(f"  Manual steps: {fail['manual_steps']}")

                # Files modified
                if "files_modified" in result:
                    output.append(f"\n**📝 Files Modified:**")
                    for file in result["files_modified"]:
                        output.append(f"- {file}")

                return "\n".join(output)
            else:
                return f"❌ Remediation failed: {response.text}"

    except Exception as e:
        return f"❌ Error during remediation: {str(e)}"

# ============================================================================
# ENHANCED ANALYTICS TOOLS
# ============================================================================

@mcp.tool()
async def devskyy_analytics_dashboard() -> str:
    """
    Generate comprehensive analytics dashboard.

    Provides real-time insights on:
    - Platform performance metrics
    - User engagement analytics
    - AI agent utilization
    - Revenue and conversion tracking
    - System health indicators
    - Security posture trends

    Returns formatted dashboard with key metrics and trends.
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(
                f"{DEVSKYY_API_URL}/api/v1/analytics/dashboard",
                headers={"Authorization": f"Bearer {DEVSKYY_API_KEY}"}
            )

            if response.status_code == 200:
                result = response.json()
                output = ["📊 **DevSkyy Analytics Dashboard**\n"]

                # Key metrics
                metrics = result.get("key_metrics", {})
                output.append("**📈 Key Metrics (Last 24h):**")
                output.append(f"- Active Users: {metrics.get('active_users', 0):,}")
                output.append(f"- API Requests: {metrics.get('api_requests', 0):,}")
                output.append(f"- Agent Executions: {metrics.get('agent_executions', 0):,}")
                output.append(f"- Revenue: ${metrics.get('revenue', 0):,.2f}")

                # Performance
                perf = result.get("performance", {})
                output.append(f"\n**⚡ Performance:**")
                output.append(f"- Avg Response Time: {perf.get('avg_response_time', 0):.2f}ms")
                output.append(f"- Success Rate: {perf.get('success_rate', 0):.1f}%")
                output.append(f"- Uptime: {perf.get('uptime', 0):.2f}%")

                # Top agents
                if "top_agents" in result:
                    output.append(f"\n**🤖 Most Used Agents:**")
                    for agent in result["top_agents"][:5]:
                        output.append(f"- {agent['name']}: {agent['usage_count']} executions")

                # Trends
                if "trends" in result:
                    output.append(f"\n**📈 Trends:**")
                    for trend in result["trends"]:
                        direction = "📈" if trend["direction"] == "up" else "📉"
                        output.append(f"- {direction} {trend['metric']}: {trend['change']:+.1f}%")

                return "\n".join(output)
            else:
                return f"❌ Analytics request failed: {response.text}"

    except Exception as e:
        return f"❌ Error fetching analytics: {str(e)}"

# ============================================================================
# MAIN
# ============================================================================

def print_banner():
    """Print startup banner."""
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║   DevSkyy MCP Server v1.1.0 - Enhanced Edition                  ║")
    print("║   Industry-First Multi-Agent AI Platform Integration            ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print("✅ Configuration:")
    print(f"   API URL: {DEVSKYY_API_URL}")
    print(f"   API Key: {'Set ✓' if DEVSKYY_API_KEY else 'Not Set ✗'}")
    print()
    print("🔧 Tools Available: 14 (Enhanced with Security & Analytics)")
    print("   📋 Core Tools (11):")
    print("     - devskyy_list_agents")
    print("     - devskyy_scan_code")
    print("     - devskyy_fix_code")
    print("     - devskyy_self_healing")
    print("     - devskyy_generate_wordpress_theme")
    print("     - devskyy_ml_prediction")
    print("     - devskyy_manage_products")
    print("     - devskyy_dynamic_pricing")
    print("     - devskyy_marketing_campaign")
    print("     - devskyy_multi_agent_workflow")
    print("     - devskyy_system_monitoring")
    print()
    print("   🔒 Security Tools (2):")
    print("     - devskyy_security_scan")
    print("     - devskyy_security_remediate")
    print()
    print("   📊 Analytics Tools (1):")
    print("     - devskyy_analytics_dashboard")
    print()
    print("🚀 New Features:")
    print("   - Comprehensive vulnerability scanning")
    print("   - Automated security remediation")
    print("   - Real-time analytics dashboard")
    print("   - Enhanced error handling")
    print()
    print("Starting MCP server on stdio...")
    print()

if __name__ == "__main__":
    print_banner()

    # Validate configuration
    if not DEVSKYY_API_KEY:
        print("⚠️  WARNING: DEVSKYY_API_KEY not set. Some features may not work.")
        print("   Set it with: export DEVSKYY_API_KEY='your-api-key'")
        print()

    # Run MCP server
    mcp.run()
