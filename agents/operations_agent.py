"""
DevSkyy Operations SuperAgent
=============================

Handles all technical operations for SkyyRose.

Consolidates:
- WordPress management
- Elementor templates
- Server monitoring
- Deployment automation
- Backup management
- Performance optimization

ML Capabilities:
- Anomaly detection
- Log analysis
- Performance prediction
"""

import logging
from datetime import UTC, datetime
from typing import Any

from adk.base import (
    ADKProvider,
    AgentCapability,
    AgentConfig,
    AgentResult,
    AgentStatus,
    ToolDefinition,
)
from core.runtime.tool_registry import (
    ParameterType,
    ToolCategory,
    ToolParameter,
    ToolRegistry,
    ToolSeverity,
    ToolSpec,
)
from orchestration.prompt_engineering import PromptTechnique

from .base_super_agent import EnhancedSuperAgent, SuperAgentType, TaskCategory

logger = logging.getLogger(__name__)


class OperationsAgent(EnhancedSuperAgent):
    """
    Operations Super Agent - Handles all technical operations.

    Features:
    - 17 prompt engineering techniques
    - ML-based anomaly detection
    - Performance prediction
    - WordPress/WooCommerce management
    - Automated deployments

    Example:
        agent = OperationsAgent()
        await agent.initialize()
        result = await agent.check_health()
    """

    agent_type = SuperAgentType.OPERATIONS
    sub_capabilities = [
        "wordpress_management",
        "elementor_templates",
        "server_monitoring",
        "deployment_automation",
        "backup_management",
        "performance_optimization",
    ]

    # Operations-specific technique preferences
    TECHNIQUE_PREFERENCES = {
        "wordpress": PromptTechnique.REACT,
        "elementor": PromptTechnique.STRUCTURED_OUTPUT,
        "monitoring": PromptTechnique.CHAIN_OF_THOUGHT,
        "deployment": PromptTechnique.CHAIN_OF_THOUGHT,
        "backup": PromptTechnique.STRUCTURED_OUTPUT,
        "performance": PromptTechnique.REACT,
    }

    # Performance thresholds
    THRESHOLDS = {
        "page_load_seconds": 3.0,
        "uptime_percent": 99.9,
        "error_rate_percent": 0.1,
        "cpu_percent": 80,
        "memory_percent": 85,
        "disk_percent": 90,
    }

    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig(
                name="operations_agent",
                provider=ADKProvider.PYDANTIC,
                model="gpt-4o-mini",
                system_prompt=self._build_system_prompt(),
                capabilities=[
                    AgentCapability.WORDPRESS,
                    AgentCapability.CODE_EXECUTION,
                    AgentCapability.FILE_OPERATIONS,
                ],
                tools=self._build_tools(),
                temperature=0.2,  # Low for precision
            )
        super().__init__(config)

    def _build_system_prompt(self) -> str:
        """Build the operations agent system prompt"""
        return """You are the Operations SuperAgent for SkyyRose platform.

## IDENTITY
You are a senior DevOps engineer and WordPress specialist with expertise in:
- WordPress and WooCommerce administration
- Server infrastructure management
- Performance optimization
- Security hardening
- Automated deployments
- Monitoring and alerting

## TECH STACK
**Platform:**
- WordPress 6.x with WooCommerce
- Shoptimizer 2.9.0 theme
- Elementor Pro 3.32.2
- PHP 8.2, MySQL 8.0

**Infrastructure:**
- Managed WordPress hosting
- Cloudflare CDN and WAF
- Redis object caching
- Automated daily backups

**Integrations:**
- Google Analytics 4
- Klaviyo email marketing
- Various payment gateways
- Shipping APIs

## PERFORMANCE STANDARDS
- **Uptime:** 99.9% minimum
- **Page Load:** Under 3 seconds
- **TTFB:** Under 600ms
- **Core Web Vitals:** All green
- **Mobile PageSpeed:** 90+

## SECURITY STANDARDS
- WAF enabled on all endpoints
- Rate limiting on authentication
- Regular security scans
- Automated updates for security patches
- Two-factor authentication enforced

## RESPONSIBILITIES
1. **WordPress Management**
   - Plugin updates and compatibility
   - Theme customization and updates
   - Database optimization
   - User and role management

2. **Elementor Templates**
   - Create and manage page templates
   - Global widgets and styles
   - Performance optimization
   - Mobile responsiveness

3. **Server Monitoring**
   - Real-time health checks
   - Performance metrics tracking
   - Error log analysis
   - Resource utilization monitoring

4. **Deployment Automation**
   - Code deployments
   - Configuration management
   - Rollback procedures
   - Environment sync

5. **Backup Management**
   - Automated backup schedules
   - Backup verification
   - Disaster recovery procedures
   - Point-in-time restoration

6. **Performance Optimization**
   - Caching strategies
   - Image optimization
   - Database query optimization
   - CDN configuration

## RESPONSE FORMAT
When diagnosing issues:
1. Current Status
2. Identified Issues
3. Root Cause Analysis
4. Recommended Actions
5. Prevention Measures"""

    def _build_tools(self) -> list[ToolDefinition]:
        """Build operations-specific tools"""
        return [
            # WordPress Tools
            ToolDefinition(
                name="wp_get_status",
                description="Get WordPress site status and health",
                parameters={
                    "include_plugins": {"type": "boolean", "description": "Include plugin status"},
                    "include_theme": {"type": "boolean", "description": "Include theme info"},
                    "include_db": {"type": "boolean", "description": "Include database stats"},
                },
            ),
            ToolDefinition(
                name="wp_update_plugin",
                description="Update WordPress plugin",
                parameters={
                    "plugin_slug": {"type": "string", "description": "Plugin slug"},
                    "version": {
                        "type": "string",
                        "description": "Target version (latest if omitted)",
                    },
                    "backup_first": {
                        "type": "boolean",
                        "description": "Create backup before update",
                    },
                },
            ),
            ToolDefinition(
                name="wp_manage_cache",
                description="Manage WordPress caching",
                parameters={
                    "action": {"type": "string", "description": "clear, enable, disable, status"},
                    "cache_type": {"type": "string", "description": "object, page, browser, all"},
                },
            ),
            ToolDefinition(
                name="wp_optimize_db",
                description="Optimize WordPress database",
                parameters={
                    "operations": {"type": "array", "description": "Optimization operations"},
                    "backup_first": {"type": "boolean", "description": "Backup before optimize"},
                },
            ),
            # Elementor Tools
            ToolDefinition(
                name="elementor_get_templates",
                description="List Elementor templates",
                parameters={
                    "template_type": {
                        "type": "string",
                        "description": "page, section, popup, etc.",
                    },
                    "category": {"type": "string", "description": "Template category"},
                },
            ),
            ToolDefinition(
                name="elementor_export_template",
                description="Export Elementor template",
                parameters={
                    "template_id": {"type": "integer", "description": "Template ID"},
                    "format": {"type": "string", "description": "json or zip"},
                },
            ),
            ToolDefinition(
                name="elementor_regenerate_css",
                description="Regenerate Elementor CSS files",
                parameters={
                    "scope": {"type": "string", "description": "all, page, or template ID"},
                },
            ),
            # Monitoring Tools
            ToolDefinition(
                name="get_server_metrics",
                description="Get current server metrics",
                parameters={
                    "metrics": {"type": "array", "description": "Metrics to retrieve"},
                    "time_range": {"type": "string", "description": "Time range for data"},
                },
            ),
            ToolDefinition(
                name="get_error_logs",
                description="Retrieve error logs",
                parameters={
                    "log_type": {"type": "string", "description": "php, wordpress, access, etc."},
                    "severity": {"type": "string", "description": "Minimum severity level"},
                    "lines": {"type": "integer", "description": "Number of lines to retrieve"},
                },
            ),
            ToolDefinition(
                name="check_uptime",
                description="Check site uptime status",
                parameters={
                    "time_range": {"type": "string", "description": "Time period to check"},
                    "include_incidents": {
                        "type": "boolean",
                        "description": "Include incident history",
                    },
                },
            ),
            ToolDefinition(
                name="run_health_check",
                description="Run comprehensive health check",
                parameters={
                    "checks": {"type": "array", "description": "Specific checks to run"},
                    "alert_threshold": {"type": "string", "description": "Alert level threshold"},
                },
            ),
            # Deployment Tools
            ToolDefinition(
                name="deploy_code",
                description="Deploy code changes",
                parameters={
                    "environment": {"type": "string", "description": "staging or production"},
                    "commit": {"type": "string", "description": "Commit hash or branch"},
                    "run_tests": {"type": "boolean", "description": "Run tests before deploy"},
                },
            ),
            ToolDefinition(
                name="rollback_deployment",
                description="Rollback to previous deployment",
                parameters={
                    "environment": {"type": "string", "description": "Environment to rollback"},
                    "target_version": {"type": "string", "description": "Version to rollback to"},
                },
            ),
            # Backup Tools
            ToolDefinition(
                name="create_backup",
                description="Create site backup",
                parameters={
                    "backup_type": {"type": "string", "description": "full, database, files"},
                    "compression": {"type": "boolean", "description": "Compress backup"},
                    "destination": {"type": "string", "description": "Storage destination"},
                },
            ),
            ToolDefinition(
                name="restore_backup",
                description="Restore from backup",
                parameters={
                    "backup_id": {"type": "string", "description": "Backup identifier"},
                    "components": {"type": "array", "description": "Components to restore"},
                    "target_environment": {"type": "string", "description": "Target environment"},
                },
            ),
            ToolDefinition(
                name="list_backups",
                description="List available backups",
                parameters={
                    "date_range": {"type": "object", "description": "Date range filter"},
                    "backup_type": {"type": "string", "description": "Type filter"},
                },
            ),
            # Performance Tools
            ToolDefinition(
                name="analyze_performance",
                description="Analyze site performance",
                parameters={
                    "url": {"type": "string", "description": "Page URL to analyze"},
                    "device": {"type": "string", "description": "desktop or mobile"},
                    "include_suggestions": {
                        "type": "boolean",
                        "description": "Include optimization suggestions",
                    },
                },
            ),
            ToolDefinition(
                name="optimize_images",
                description="Optimize images in media library",
                parameters={
                    "scope": {"type": "string", "description": "all, unoptimized, or specific IDs"},
                    "quality": {"type": "integer", "description": "Target quality (1-100)"},
                    "formats": {"type": "array", "description": "Output formats (webp, avif)"},
                },
            ),
        ]

    def _register_tools(self) -> None:
        """Register operations tools with the global ToolRegistry for MCP integration."""
        registry = ToolRegistry.get_instance()

        operations_tools = [
            ToolSpec(
                name="operations_wp_get_status",
                description="Get WordPress site status and health",
                category=ToolCategory.SYSTEM,
                severity=ToolSeverity.READ_ONLY,
                parameters=[
                    ToolParameter(
                        name="include_plugins",
                        type=ParameterType.BOOLEAN,
                        description="Include plugin status",
                        required=False,
                    ),
                    ToolParameter(
                        name="include_theme",
                        type=ParameterType.BOOLEAN,
                        description="Include theme info",
                        required=False,
                    ),
                    ToolParameter(
                        name="include_db",
                        type=ParameterType.BOOLEAN,
                        description="Include database stats",
                        required=False,
                    ),
                ],
                idempotent=True,
                cacheable=True,
                tags={"operations", "wordpress", "health"},
            ),
            ToolSpec(
                name="operations_wp_update_plugin",
                description="Update WordPress plugin",
                category=ToolCategory.SYSTEM,
                severity=ToolSeverity.MEDIUM,
                parameters=[
                    ToolParameter(
                        name="plugin_slug",
                        type=ParameterType.STRING,
                        description="Plugin slug to update",
                        required=True,
                    ),
                    ToolParameter(
                        name="version",
                        type=ParameterType.STRING,
                        description="Target version (latest if omitted)",
                        required=False,
                    ),
                    ToolParameter(
                        name="backup_first",
                        type=ParameterType.BOOLEAN,
                        description="Create backup before update",
                        required=False,
                    ),
                ],
                idempotent=False,
                cacheable=False,
                tags={"operations", "wordpress", "plugin"},
            ),
            ToolSpec(
                name="operations_wp_manage_cache",
                description="Manage WordPress caching",
                category=ToolCategory.SYSTEM,
                severity=ToolSeverity.LOW,
                parameters=[
                    ToolParameter(
                        name="action",
                        type=ParameterType.STRING,
                        description="Action: clear, enable, disable, status",
                        required=True,
                    ),
                    ToolParameter(
                        name="cache_type",
                        type=ParameterType.STRING,
                        description="Cache type: object, page, browser, all",
                        required=False,
                    ),
                ],
                idempotent=False,
                cacheable=False,
                tags={"operations", "wordpress", "cache"},
            ),
            ToolSpec(
                name="operations_get_server_metrics",
                description="Get current server metrics",
                category=ToolCategory.SYSTEM,
                severity=ToolSeverity.READ_ONLY,
                parameters=[
                    ToolParameter(
                        name="metrics",
                        type=ParameterType.ARRAY,
                        description="Metrics to retrieve (cpu, memory, disk)",
                        required=False,
                    ),
                    ToolParameter(
                        name="time_range",
                        type=ParameterType.STRING,
                        description="Time range for data (1h, 24h, 7d)",
                        required=False,
                    ),
                ],
                idempotent=True,
                cacheable=True,
                tags={"operations", "monitoring", "metrics"},
            ),
            ToolSpec(
                name="operations_get_error_logs",
                description="Retrieve error logs",
                category=ToolCategory.SYSTEM,
                severity=ToolSeverity.READ_ONLY,
                parameters=[
                    ToolParameter(
                        name="log_type",
                        type=ParameterType.STRING,
                        description="Log type: php, wordpress, access, error",
                        required=True,
                    ),
                    ToolParameter(
                        name="severity",
                        type=ParameterType.STRING,
                        description="Minimum severity level",
                        required=False,
                    ),
                    ToolParameter(
                        name="lines",
                        type=ParameterType.INTEGER,
                        description="Number of lines to retrieve",
                        required=False,
                    ),
                ],
                idempotent=True,
                cacheable=True,
                tags={"operations", "logs", "debugging"},
            ),
            ToolSpec(
                name="operations_run_health_check",
                description="Run comprehensive health check",
                category=ToolCategory.SYSTEM,
                severity=ToolSeverity.READ_ONLY,
                parameters=[
                    ToolParameter(
                        name="checks",
                        type=ParameterType.ARRAY,
                        description="Specific checks to run",
                        required=False,
                    ),
                    ToolParameter(
                        name="alert_threshold",
                        type=ParameterType.STRING,
                        description="Alert level threshold",
                        required=False,
                    ),
                ],
                idempotent=True,
                cacheable=True,
                tags={"operations", "health", "monitoring"},
            ),
            ToolSpec(
                name="operations_deploy_code",
                description="Deploy code changes to environment",
                category=ToolCategory.SYSTEM,
                severity=ToolSeverity.HIGH,
                parameters=[
                    ToolParameter(
                        name="environment",
                        type=ParameterType.STRING,
                        description="Target environment: staging, production",
                        required=True,
                    ),
                    ToolParameter(
                        name="commit",
                        type=ParameterType.STRING,
                        description="Commit hash or branch",
                        required=False,
                    ),
                    ToolParameter(
                        name="run_tests",
                        type=ParameterType.BOOLEAN,
                        description="Run tests before deploy",
                        required=False,
                    ),
                ],
                idempotent=False,
                cacheable=False,
                tags={"operations", "deployment", "devops"},
            ),
            ToolSpec(
                name="operations_rollback_deployment",
                description="Rollback to previous deployment",
                category=ToolCategory.SYSTEM,
                severity=ToolSeverity.HIGH,
                parameters=[
                    ToolParameter(
                        name="environment",
                        type=ParameterType.STRING,
                        description="Environment to rollback",
                        required=True,
                    ),
                    ToolParameter(
                        name="target_version",
                        type=ParameterType.STRING,
                        description="Version to rollback to",
                        required=False,
                    ),
                ],
                idempotent=False,
                cacheable=False,
                tags={"operations", "rollback", "devops"},
            ),
            ToolSpec(
                name="operations_create_backup",
                description="Create site backup",
                category=ToolCategory.SYSTEM,
                severity=ToolSeverity.MEDIUM,
                parameters=[
                    ToolParameter(
                        name="backup_type",
                        type=ParameterType.STRING,
                        description="Backup type: full, database, files",
                        required=True,
                    ),
                    ToolParameter(
                        name="compression",
                        type=ParameterType.BOOLEAN,
                        description="Compress backup",
                        required=False,
                    ),
                    ToolParameter(
                        name="destination",
                        type=ParameterType.STRING,
                        description="Storage destination",
                        required=False,
                    ),
                ],
                idempotent=False,
                cacheable=False,
                tags={"operations", "backup", "data"},
            ),
            ToolSpec(
                name="operations_restore_backup",
                description="Restore from backup",
                category=ToolCategory.SYSTEM,
                severity=ToolSeverity.DESTRUCTIVE,
                parameters=[
                    ToolParameter(
                        name="backup_id",
                        type=ParameterType.STRING,
                        description="Backup identifier",
                        required=True,
                    ),
                    ToolParameter(
                        name="components",
                        type=ParameterType.ARRAY,
                        description="Components to restore",
                        required=False,
                    ),
                    ToolParameter(
                        name="target_environment",
                        type=ParameterType.STRING,
                        description="Target environment",
                        required=False,
                    ),
                ],
                idempotent=False,
                cacheable=False,
                tags={"operations", "restore", "backup"},
            ),
            ToolSpec(
                name="operations_analyze_performance",
                description="Analyze site performance",
                category=ToolCategory.AI,
                severity=ToolSeverity.READ_ONLY,
                parameters=[
                    ToolParameter(
                        name="url",
                        type=ParameterType.STRING,
                        description="Page URL to analyze",
                        required=False,
                    ),
                    ToolParameter(
                        name="device",
                        type=ParameterType.STRING,
                        description="Device type: desktop, mobile",
                        required=False,
                    ),
                    ToolParameter(
                        name="include_suggestions",
                        type=ParameterType.BOOLEAN,
                        description="Include optimization suggestions",
                        required=False,
                    ),
                ],
                idempotent=True,
                cacheable=True,
                tags={"operations", "performance", "analysis"},
            ),
        ]

        for spec in operations_tools:
            registry.register(spec)

    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute operations task"""
        start_time = datetime.now(UTC)

        try:
            task_type = self._classify_ops_task(prompt)
            technique = self.TECHNIQUE_PREFERENCES.get(
                task_type, self.select_technique(TaskCategory.DEBUGGING)
            )

            enhanced = self.apply_technique(
                technique,
                prompt,
                tools=["server_metrics", "error_logs", "health_check", "cache_clear"],
                **kwargs,
            )

            if hasattr(self, "_backend_agent"):
                result = await self._backend_agent.run(enhanced.enhanced_prompt)
                content = str(result.output) if hasattr(result, "output") else str(result)
            else:
                content = await self._fallback_process(prompt, task_type)

            return AgentResult(
                agent_name=self.name,
                agent_provider=self._active_provider,
                content=content,
                status=AgentStatus.COMPLETED,
                started_at=start_time,
                metadata={"task_type": task_type, "technique": technique.value},
            )

        except Exception as e:
            logger.error(f"Operations agent error: {e}")
            return AgentResult(
                agent_name=self.name,
                agent_provider=self._active_provider,
                content="",
                status=AgentStatus.FAILED,
                error=str(e),
                started_at=start_time,
            )

    def _classify_ops_task(self, prompt: str) -> str:
        """Classify the operations task type"""
        prompt_lower = prompt.lower()

        task_keywords = {
            "wordpress": ["wordpress", "plugin", "theme", "wp-admin", "woocommerce"],
            "elementor": ["elementor", "template", "widget", "page builder"],
            "monitoring": ["monitor", "alert", "health", "status", "uptime", "error"],
            "deployment": ["deploy", "release", "rollback", "version", "update"],
            "backup": ["backup", "restore", "recovery", "snapshot"],
            "performance": ["performance", "speed", "optimize", "cache", "slow"],
        }

        for task_type, keywords in task_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                return task_type

        return "monitoring"

    async def _fallback_process(self, prompt: str, task_type: str) -> str:
        """Fallback processing"""
        return f"""Operations Agent Analysis

Task Type: {task_type}
Query: {prompt[:200]}...

Tech Stack: WordPress 6.x + WooCommerce + Elementor Pro
Hosting: Managed WordPress with Cloudflare CDN

For full operations capabilities, ensure backend is configured."""

    # =========================================================================
    # Operations-Specific Methods
    # =========================================================================

    async def check_health(self) -> AgentResult:
        """Run comprehensive health check"""
        prompt = """Run comprehensive health check for SkyyRose platform:

Check the following:
1. WordPress core status
2. Plugin update status
3. Theme compatibility
4. Database health
5. Server resource utilization
6. Page load performance
7. SSL certificate status
8. Security scan results
9. Backup status
10. CDN configuration

For each check, report:
- Status (OK, Warning, Critical)
- Current value/state
- Threshold/expected value
- Recommended action if needed"""

        return await self.execute_with_learning(
            prompt,
            task_type="monitoring",
            technique=PromptTechnique.STRUCTURED_OUTPUT,
            schema={
                "overall_status": "string",
                "checks": "array",
                "critical_issues": "array",
                "warnings": "array",
                "recommendations": "array",
            },
        )

    async def detect_anomalies(self, metrics: dict[str, float]) -> dict[str, Any]:
        """Detect anomalies in server metrics using ML"""
        if self.ml_module:
            prediction = await self.ml_module.predict("anomaly_detector", metrics)
            return {
                "anomalies_detected": prediction.prediction.get("anomalies", []),
                "confidence": prediction.confidence,
                "metrics_analyzed": list(metrics.keys()),
            }

        # Fallback threshold-based detection
        anomalies = []
        for metric, value in metrics.items():
            threshold = self.THRESHOLDS.get(metric)
            if threshold and value > threshold:
                anomalies.append(
                    {
                        "metric": metric,
                        "value": value,
                        "threshold": threshold,
                        "severity": "critical" if value > threshold * 1.2 else "warning",
                    }
                )

        return {
            "anomalies_detected": anomalies,
            "confidence": 0.8,
            "metrics_analyzed": list(metrics.keys()),
        }

    async def optimize_performance(self, url: str | None = None) -> AgentResult:
        """Optimize site performance"""
        prompt = f"""Performance optimization for SkyyRose:

Target URL: {url or 'Homepage'}

Please:
1. Analyze current performance metrics
2. Identify bottlenecks
3. Recommend optimization actions:
   - Caching improvements
   - Image optimization
   - Database query optimization
   - CDN configuration
   - Code minification
   - Resource prioritization
4. Estimate impact of each recommendation
5. Prioritize by effort vs. impact"""

        return await self.execute_with_learning(
            prompt, task_type="performance", technique=PromptTechnique.CHAIN_OF_THOUGHT
        )

    async def manage_backup(self, action: str = "status", **kwargs) -> AgentResult:
        """Manage site backups"""
        prompt = f"""Backup management task:

Action: {action}
Parameters: {kwargs}

Please:
1. Execute the backup action
2. Verify backup integrity
3. Report backup status
4. Confirm storage location
5. Check retention policy compliance"""

        return await self.execute_with_learning(
            prompt,
            task_type="backup",
            technique=PromptTechnique.STRUCTURED_OUTPUT,
            schema={
                "action_completed": "boolean",
                "backup_id": "string",
                "size_mb": "number",
                "location": "string",
                "verified": "boolean",
                "retention_days": "number",
            },
        )

    async def deploy_changes(
        self, environment: str = "staging", commit: str | None = None
    ) -> AgentResult:
        """Deploy code changes"""
        prompt = f"""Deploy changes to {environment}:

Commit: {commit or 'latest'}

Deployment process:
1. Pre-deployment checks
   - Verify tests pass
   - Check dependencies
   - Backup current state
2. Deploy changes
3. Post-deployment verification
   - Health check
   - Performance check
   - Error log review
4. Rollback plan if needed

Report deployment status and any issues."""

        return await self.execute_with_learning(
            prompt, task_type="deployment", technique=PromptTechnique.CHAIN_OF_THOUGHT
        )


# =============================================================================
# Export
# =============================================================================

__all__ = ["OperationsAgent"]
