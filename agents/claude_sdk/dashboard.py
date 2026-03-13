"""
Dashboard Orchestrator Agent
==============================

Coordinates all SDK domain agents for the admin dashboard.
Provides a unified interface for the dashboard to invoke
real-time operations across all domains.

The orchestrator replaces simulated dashboard data with
actual agent-driven operations:
- Health probes via SDKDeployRunnerAgent
- Code quality via SDKCodeDoctorAgent
- Security scans via SDKSecurityScannerAgent
- Business analytics via SDKDataAnalystAgent
- Brand compliance via SDKBrandAssetAgent
- Pipeline status via SDKImageGenAgent
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ------------------------------------------------------------------
# Request / Result models
# ------------------------------------------------------------------


class DashboardAction(BaseModel):
    """A single dashboard action request."""

    domain: str = Field(
        ...,
        description="Target domain: operations, commerce, content, "
        "analytics, imagery, creative, marketing, web_builder, "
        "immersive, customer_intelligence, influencer, supply_chain, "
        "brand_guardian, community, seo_discovery",
    )
    action: str = Field(
        ...,
        description="Action to perform within the domain",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Action parameters",
    )


class DashboardRequest(BaseModel):
    """Request to the dashboard orchestrator."""

    actions: list[DashboardAction] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Actions to execute (up to 10 per request)",
    )
    parallel: bool = Field(
        default=True,
        description="Execute independent actions in parallel",
    )


class ActionResult(BaseModel):
    """Result of a single dashboard action."""

    domain: str
    action: str
    success: bool
    result: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    duration_ms: float | None = None


class DashboardResult(BaseModel):
    """Aggregated result from the dashboard orchestrator."""

    total_actions: int
    successful: int
    failed: int
    results: list[ActionResult]
    total_duration_ms: float


class AgentHealthStatus(BaseModel):
    """Health status of an SDK agent."""

    name: str
    domain: str
    available: bool
    capabilities: list[str]
    last_used: str | None = None


class DashboardHealthResponse(BaseModel):
    """Response from the dashboard health endpoint."""

    total_agents: int
    available_agents: int
    unavailable_agents: int
    agents: list[AgentHealthStatus]
    domains: list[str]


# ------------------------------------------------------------------
# Agent Registry
# ------------------------------------------------------------------


@dataclass
class AgentEntry:
    """Registry entry for an SDK domain agent."""

    domain: str
    agent_class: type
    capabilities: list[str]
    last_used: datetime | None = None


@dataclass
class DashboardAgentRegistry:
    """Central registry of all SDK domain agents.

    Lazily imports agents to avoid import failures when
    optional dependencies are missing.
    """

    _agents: dict[str, AgentEntry] = field(default_factory=dict)
    _initialized: bool = False

    def _ensure_initialized(self) -> None:
        """Lazy-initialize the agent registry."""
        if self._initialized:
            return

        registrations: list[tuple[str, str, str, list[str]]] = [
            # (name, domain, module_path, capabilities)
            (
                "sdk_deploy_runner",
                "operations",
                "agents.claude_sdk.domain_agents.operations.SDKDeployRunnerAgent",
                ["deploy_run", "health_probe", "rollback_execute"],
            ),
            (
                "sdk_code_doctor",
                "operations",
                "agents.claude_sdk.domain_agents.operations.SDKCodeDoctorAgent",
                ["lint_run", "lint_fix", "type_check", "format_code"],
            ),
            (
                "sdk_security_scanner",
                "operations",
                "agents.claude_sdk.domain_agents.operations.SDKSecurityScannerAgent",
                ["dep_audit", "code_scan", "secret_scan"],
            ),
            (
                "sdk_seo_writer",
                "content",
                "agents.claude_sdk.domain_agents.content.SDKSeoWriterAgent",
                ["meta_optimize", "schema_org_generate", "keyword_research"],
            ),
            (
                "sdk_collection_publisher",
                "content",
                "agents.claude_sdk.domain_agents.content.SDKCollectionPublisherAgent",
                ["collection_description", "landing_page_copy"],
            ),
            (
                "sdk_data_analyst",
                "analytics",
                "agents.claude_sdk.domain_agents.analytics.SDKDataAnalystAgent",
                ["data_query", "chart_generate", "anomaly_detect"],
            ),
            (
                "sdk_report_generator",
                "analytics",
                "agents.claude_sdk.domain_agents.analytics.SDKReportGeneratorAgent",
                ["full_report", "executive_summary"],
            ),
            (
                "sdk_theme_dev",
                "web_builder",
                "agents.claude_sdk.domain_agents.web_builder.SDKThemeDevAgent",
                ["theme_edit", "css_modify", "js_modify", "build_verify"],
            ),
            (
                "sdk_template_builder",
                "web_builder",
                "agents.claude_sdk.domain_agents.web_builder.SDKTemplateBuilderAgent",
                ["page_template", "collection_template"],
            ),
            (
                "sdk_campaign_analyst",
                "marketing",
                "agents.claude_sdk.domain_agents.marketing.SDKCampaignAnalystAgent",
                ["campaign_analyze", "audience_research"],
            ),
            (
                "sdk_competitive_intel",
                "marketing",
                "agents.claude_sdk.domain_agents.marketing.SDKCompetitiveIntelAgent",
                ["competitor_research", "market_positioning"],
            ),
            (
                "sdk_catalog_manager",
                "commerce",
                "agents.claude_sdk.domain_agents.commerce.SDKCatalogManagerAgent",
                ["catalog_read", "sku_verify", "collection_audit"],
            ),
            (
                "sdk_price_optimizer",
                "commerce",
                "agents.claude_sdk.domain_agents.commerce.SDKPriceOptimizerAgent",
                ["price_analysis", "margin_calculate"],
            ),
            (
                "sdk_virtual_tryon",
                "imagery",
                "agents.claude_sdk.domain_agents.imagery.SDKVirtualTryOnAgent",
                ["vton_render", "batch_render", "garment_analysis"],
            ),
            (
                "sdk_compositor",
                "imagery",
                "agents.claude_sdk.domain_agents.imagery.SDKCompositorAgent",
                ["bg_removal", "scene_composite", "relight", "qa_gate"],
            ),
            (
                "sdk_image_gen",
                "imagery",
                "agents.claude_sdk.domain_agents.imagery.SDKImageGenAgent",
                ["flux_generate", "gemini_generate", "upscale"],
            ),
            (
                "sdk_brand_asset",
                "creative",
                "agents.claude_sdk.domain_agents.creative.SDKBrandAssetAgent",
                ["asset_audit", "brand_compliance", "color_verify"],
            ),
            (
                "sdk_design_system",
                "creative",
                "agents.claude_sdk.domain_agents.creative.SDKDesignSystemAgent",
                ["token_audit", "css_consistency", "typography_check"],
            ),
            (
                "sdk_garment_3d",
                "immersive",
                "agents.claude_sdk.domain_agents.immersive.SDKGarment3DAgent",
                ["garment_to_3d", "image_to_3d", "text_to_3d", "ar_export"],
            ),
            (
                "sdk_scene_builder",
                "immersive",
                "agents.claude_sdk.domain_agents.immersive.SDKSceneBuilderAgent",
                ["scene_create", "scene_edit", "hotspot_place", "scroll_animation"],
            ),
            (
                "sdk_avatar_stylist",
                "immersive",
                "agents.claude_sdk.domain_agents.immersive.SDKAvatarStylistAgent",
                ["outfit_change", "pose_render", "sprite_generate", "lookbook_generate"],
            ),
            # --- New agents: customer intelligence, influencer, supply chain,
            #     brand guardian, community/loyalty, SEO/discovery ---
            (
                "sdk_customer_intel",
                "customer_intelligence",
                "agents.claude_sdk.domain_agents.customer_intelligence.SDKCustomerIntelAgent",
                [
                    "customer_segment",
                    "clv_score",
                    "churn_predict",
                    "cohort_analysis",
                    "persona_build",
                    "purchase_pattern",
                ],
            ),
            (
                "sdk_influencer",
                "influencer",
                "agents.claude_sdk.domain_agents.influencer.SDKInfluencerAgent",
                [
                    "creator_discover",
                    "brand_fit_score",
                    "outreach_draft",
                    "campaign_roi",
                    "audience_overlap",
                    "collab_brief",
                ],
            ),
            (
                "sdk_supply_chain",
                "supply_chain",
                "agents.claude_sdk.domain_agents.supply_chain.SDKSupplyChainAgent",
                [
                    "inventory_track",
                    "demand_forecast",
                    "supplier_manage",
                    "fulfillment_optimize",
                    "lead_time_estimate",
                    "reorder_alert",
                ],
            ),
            (
                "sdk_brand_guardian",
                "brand_guardian",
                "agents.claude_sdk.domain_agents.brand_guardian.SDKBrandGuardianAgent",
                [
                    "brand_audit",
                    "tagline_enforce",
                    "tone_monitor",
                    "color_compliance",
                    "copy_review",
                    "brand_drift_detect",
                ],
            ),
            (
                "sdk_community_loyalty",
                "community",
                "agents.claude_sdk.domain_agents.community.SDKCommunityLoyaltyAgent",
                [
                    "engagement_track",
                    "loyalty_tier",
                    "referral_program",
                    "community_health",
                    "retention_strategy",
                    "ambassador_manage",
                ],
            ),
            (
                "sdk_seo_discovery",
                "seo_discovery",
                "agents.claude_sdk.domain_agents.seo_discovery.SDKSEODiscoveryAgent",
                [
                    "serp_analyze",
                    "content_gap",
                    "backlink_profile",
                    "keyword_cluster",
                    "visual_search_optimize",
                    "discovery_strategy",
                ],
            ),
        ]

        for name, domain, class_path, capabilities in registrations:
            try:
                module_path, class_name = class_path.rsplit(".", 1)
                import importlib

                module = importlib.import_module(module_path)
                agent_class = getattr(module, class_name)
                self._agents[name] = AgentEntry(
                    domain=domain,
                    agent_class=agent_class,
                    capabilities=capabilities,
                )
            except (ImportError, AttributeError) as e:
                logger.debug("agent_unavailable", name=name, error=str(e))

        self._initialized = True

    def get_agent(self, name: str) -> AgentEntry | None:
        """Get an agent entry by name."""
        self._ensure_initialized()
        return self._agents.get(name)

    def get_by_domain(self, domain: str) -> dict[str, AgentEntry]:
        """Get all agents for a domain."""
        self._ensure_initialized()
        return {name: entry for name, entry in self._agents.items() if entry.domain == domain}

    def find_by_capability(self, capability: str) -> list[str]:
        """Find agents that have a specific capability."""
        self._ensure_initialized()
        return [name for name, entry in self._agents.items() if capability in entry.capabilities]

    def all_agents(self) -> dict[str, AgentEntry]:
        """Get all registered agents."""
        self._ensure_initialized()
        return dict(self._agents)

    def domains(self) -> list[str]:
        """Get all registered domains."""
        self._ensure_initialized()
        return sorted({entry.domain for entry in self._agents.values()})


# Global registry
_registry = DashboardAgentRegistry()


# ------------------------------------------------------------------
# Dashboard Orchestrator
# ------------------------------------------------------------------


class DashboardOrchestrator:
    """Coordinates SDK domain agents for the admin dashboard.

    Provides a unified interface to execute actions across all domains.
    Supports parallel execution for independent actions and aggregates
    results into a single response.
    """

    def __init__(self) -> None:
        self._registry = _registry

    async def execute(self, request: DashboardRequest) -> DashboardResult:
        """Execute one or more dashboard actions.

        Args:
            request: Dashboard request with actions and execution mode.

        Returns:
            Aggregated results from all actions.
        """
        start = asyncio.get_event_loop().time()
        results: list[ActionResult] = []

        if request.parallel and len(request.actions) > 1:
            # Execute independent actions concurrently
            tasks = [self._execute_action(action) for action in request.actions]
            results = await asyncio.gather(*tasks)
        else:
            # Execute sequentially
            for action in request.actions:
                result = await self._execute_action(action)
                results.append(result)

        elapsed = (asyncio.get_event_loop().time() - start) * 1000
        successful = sum(1 for r in results if r.success)

        return DashboardResult(
            total_actions=len(results),
            successful=successful,
            failed=len(results) - successful,
            results=results,
            total_duration_ms=round(elapsed, 1),
        )

    async def _execute_action(self, action: DashboardAction) -> ActionResult:
        """Execute a single dashboard action."""
        start = asyncio.get_event_loop().time()

        # Find the right agent for this domain + action
        domain_agents = self._registry.get_by_domain(action.domain)
        if not domain_agents:
            return ActionResult(
                domain=action.domain,
                action=action.action,
                success=False,
                result="",
                error=f"No agents available for domain: {action.domain}",
            )

        # Find agent with the requested capability
        target_agent = None
        for name, entry in domain_agents.items():
            if action.action in entry.capabilities:
                target_agent = (name, entry)
                break

        if not target_agent:
            # Fall back to first agent in domain
            name, entry = next(iter(domain_agents.items()))
            target_agent = (name, entry)

        agent_name, agent_entry = target_agent

        try:
            agent_instance = agent_entry.agent_class()
            task_desc = action.params.get("task", action.action)
            result = await agent_instance.execute(task_desc, **action.params)

            agent_entry.last_used = datetime.now()
            elapsed = (asyncio.get_event_loop().time() - start) * 1000

            return ActionResult(
                domain=action.domain,
                action=action.action,
                success=result.get("success", False),
                result=result.get("result", ""),
                metrics=result.get("metrics", {}),
                duration_ms=round(elapsed, 1),
            )

        except Exception as e:
            elapsed = (asyncio.get_event_loop().time() - start) * 1000
            logger.error(
                "dashboard_action_failed",
                domain=action.domain,
                action=action.action,
                agent=agent_name,
                error=str(e)[:300],
            )
            return ActionResult(
                domain=action.domain,
                action=action.action,
                success=False,
                result="",
                error=str(e),
                duration_ms=round(elapsed, 1),
            )

    def get_health(self) -> DashboardHealthResponse:
        """Get health status of all registered dashboard agents."""
        all_agents = self._registry.all_agents()

        statuses = []
        for name, entry in all_agents.items():
            statuses.append(
                AgentHealthStatus(
                    name=name,
                    domain=entry.domain,
                    available=True,
                    capabilities=entry.capabilities,
                    last_used=(entry.last_used.isoformat() if entry.last_used else None),
                )
            )

        available = sum(1 for s in statuses if s.available)

        return DashboardHealthResponse(
            total_agents=len(statuses),
            available_agents=available,
            unavailable_agents=len(statuses) - available,
            agents=statuses,
            domains=self._registry.domains(),
        )

    def find_agent(self, capability: str) -> list[str]:
        """Find agents with a specific capability."""
        return self._registry.find_by_capability(capability)
