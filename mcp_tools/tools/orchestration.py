"""Orchestration MCP tools — ported from mcp_servers/agent_bridge_server.py.

Exposes four tools:
    orchestration_round_table    — run LLM Round Table provider competition
    orchestration_router_select  — select optimal LLM provider for a task
    orchestration_learning_report — per-agent or fleet self-learning stats
    operations_deploy            — deploy/rollback to staging or production

All heavy imports (agents, llm.*) are deferred into each tool body so that
``import mcp_tools.tools.orchestration`` succeeds on slim containers where
those optional packages are absent.

Registration: imported as a side-effect via _TOOL_MODULES in mcp_tools/tools/__init__.py.
"""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from mcp_tools.server import CHARACTER_LIMIT, logger, mcp

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


class _ResponseFormat(StrEnum):
    MARKDOWN = "markdown"
    JSON = "json"


def _fmt(data: dict[str, Any], fmt: _ResponseFormat) -> str:
    """Minimal format helper — mirrors the original format_response logic."""
    if fmt == _ResponseFormat.JSON:
        return json.dumps(data, indent=2, default=str)

    lines: list[str] = []

    if "error" in data:
        msg = f"**Error:** {data['error']}"
        if "note" in data:
            msg += f"\n- Note: {data['note']}"
        return msg

    if "agent" in data:
        lines.append(f"*Agent: {data['agent']}*\n")

    if "result" in data:
        result = data["result"]
        if isinstance(result, dict):
            lines.append("## Result\n")
            for k, v in result.items():
                lines.append(f"- **{k}:** {v}")
        elif isinstance(result, list):
            lines.append(f"## Results ({len(result)} items)\n")
            for i, item in enumerate(result[:10], 1):
                lines.append(f"{i}. {item}")
        else:
            lines.append(f"## Result\n{result}")

    # stats block used by learning_report
    if "stats" in data:
        lines.append("\n## Statistics")
        lines.append(f"```json\n{json.dumps(data['stats'], indent=2, default=str)}\n```")

    # generic key-value fall-through
    for key in (
        "competition",
        "winner",
        "scores",
        "router",
        "recommended_provider",
        "task_type",
        "budget",
        "report",
        "metric",
        "period",
    ):
        if key in data and key not in ("result", "agent", "stats", "error"):
            lines.append(f"- **{key}:** {data[key]}")

    return "\n".join(lines) if lines else json.dumps(data, indent=2, default=str)


def _err(msg: str, fmt: _ResponseFormat, *, note: str = "") -> str:
    payload: dict[str, Any] = {"error": msg}
    if note:
        payload["note"] = note
    return _fmt(payload, fmt)


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class _BaseInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    response_format: _ResponseFormat = Field(
        default=_ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class _RoundTableInput(_BaseInput):
    prompt: str = Field(..., description="Prompt for all LLMs to compete on")
    task_type: str = Field(default="general", description="Task type for scoring")
    max_providers: int = Field(default=4, ge=2, le=6, description="Max providers to compete")


class _RouterSelectInput(_BaseInput):
    task_type: str = Field(..., description="Task type: reasoning, creative, code, analysis")
    requirements: str | None = Field(default=None, description="Specific requirements")
    budget: str = Field(default="balanced", description="Budget: economy, balanced, premium")


class _LearningReportInput(_BaseInput):
    agent_type: str | None = Field(
        default=None,
        description="Filter by agent type: commerce, creative, marketing, support, operations, "
        "analytics. Omit for all agents.",
    )
    metric: str = Field(default="all", description="Metric: success_rate, latency, cost, all")
    period: str = Field(default="7d", description="Time period, e.g. 7d, 30d")


class _OperationsDeployInput(_BaseInput):
    environment: str = Field(
        default="staging", description="Target environment: staging, production"
    )
    version: str | None = Field(default=None, description="Version tag to deploy (default: latest)")
    rollback: bool = Field(
        default=False, description="Rollback to the previous version instead of deploying"
    )


# ---------------------------------------------------------------------------
# Tool: orchestration_round_table
# ---------------------------------------------------------------------------


@mcp.tool()
async def orchestration_round_table(input: _RoundTableInput) -> str:
    """Run LLM Round Table competition.

    All configured LLM providers compete on the same prompt, scored on
    quality, relevance, and efficiency.

    Returns winning response with provider scores.
    """
    try:
        # Deferred import — unavailable on slim containers
        try:
            from llm.round_table import LLMRoundTable  # type: ignore[import]
        except ImportError as exc:
            return _err(
                "Round Table not available",
                input.response_format,
                note=f"llm.round_table import failed: {exc}",
            )

        round_table = LLMRoundTable()

        result = await round_table.compete(
            prompt=input.prompt,
            # LLMRoundTable.compete does not accept task_type or max_providers
            # directly — pass as context so downstream scoring can use them.
            context={"task_type": input.task_type, "max_providers": input.max_providers},
        )

        winner_provider = result.winner.provider.value if result.winner else "N/A"
        winner_text = (
            str(result.winner.response.content)
            if result.winner and result.winner.response
            else "N/A"
        )
        scores: dict[str, Any] = {e.provider.value: e.total_score for e in result.entries}

        return _fmt(
            {
                "competition": "round_table",
                "winner": winner_provider,
                "scores": scores,
                "result": winner_text,
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as exc:
        logger.error("orchestration_round_table failed: %s", exc)
        return _err(str(exc), input.response_format)


# ---------------------------------------------------------------------------
# Tool: orchestration_router_select
# ---------------------------------------------------------------------------


@mcp.tool()
async def orchestration_router_select(input: _RouterSelectInput) -> str:
    """Select the optimal LLM provider for a task.

    Uses intelligent routing based on task type, requirements, and budget
    constraints.

    Returns recommended provider with reasoning.
    """
    try:
        try:
            from llm.router import LLMRouter, RoutingStrategy  # type: ignore[import]
        except ImportError as exc:
            return _err(
                "Router not available",
                input.response_format,
                note=f"llm.router import failed: {exc}",
            )

        # Map budget hint → routing strategy
        strategy_map: dict[str, RoutingStrategy] = {
            "economy": RoutingStrategy.COST,
            "balanced": RoutingStrategy.PRIORITY,
            "premium": RoutingStrategy.PRIORITY,
        }
        strategy = strategy_map.get(input.budget, RoutingStrategy.PRIORITY)

        router = LLMRouter(strategy=strategy)

        # LLMRouter exposes _select_provider (private) not a public select_provider.
        # Use the public get_available_providers + _select_provider pattern faithfully.
        available = router.get_available_providers()
        if not available:
            return _err("No LLM providers are enabled", input.response_format)

        # _select_provider returns the best ModelProvider given current strategy
        provider = router._select_provider(available)  # noqa: SLF001

        return _fmt(
            {
                "router": "llm_router",
                "recommended_provider": (
                    provider.value if hasattr(provider, "value") else str(provider)
                ),
                "task_type": input.task_type,
                "budget": input.budget,
                "strategy": strategy.value,
                "requirements": input.requirements or "none",
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as exc:
        logger.error("orchestration_router_select failed: %s", exc)
        return _err(str(exc), input.response_format)


# ---------------------------------------------------------------------------
# Tool: orchestration_learning_report
# ---------------------------------------------------------------------------


@mcp.tool()
async def orchestration_learning_report(input: _LearningReportInput) -> str:
    """Get self-learning insights and reports.

    Retrieves agent performance metrics, technique effectiveness, and
    optimization recommendations.

    Returns learning analytics and per-agent stats.
    """
    try:
        try:
            from agents import (  # type: ignore[import]
                AnalyticsAgent,
                CommerceAgent,
                CreativeAgent,
                MarketingAgent,
                OperationsAgent,
                SupportAgent,
            )
            from agents.base_super_agent import TaskCategory  # type: ignore[import]  # noqa: F401
        except ImportError as exc:
            return _err(
                "Agents module not available",
                input.response_format,
                note=f"import failed: {exc}",
            )

        _AGENT_CLASSES: dict[str, Any] = {
            "commerce": CommerceAgent,
            "creative": CreativeAgent,
            "marketing": MarketingAgent,
            "support": SupportAgent,
            "operations": OperationsAgent,
            "analytics": AnalyticsAgent,
        }

        stats: dict[str, Any] = {}

        targets: list[str] = [input.agent_type] if input.agent_type else list(_AGENT_CLASSES.keys())

        for name in targets:
            cls = _AGENT_CLASSES.get(name)
            if cls is None:
                stats[name] = {"error": "unknown agent type"}
                continue
            try:
                agent = cls()
                await agent.initialize()
                if hasattr(agent, "get_stats"):
                    stats[name] = agent.get_stats()
                else:
                    stats[name] = {"note": "get_stats not implemented"}
            except Exception as agent_exc:
                logger.warning("learning_report: could not get stats for %s: %s", name, agent_exc)
                stats[name] = {"error": str(agent_exc)}

        return _fmt(
            {
                "report": "self_learning",
                "metric": input.metric,
                "period": input.period,
                "stats": stats,
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as exc:
        logger.error("orchestration_learning_report failed: %s", exc)
        return _err(str(exc), input.response_format)


# ---------------------------------------------------------------------------
# Tool: operations_deploy
# ---------------------------------------------------------------------------


@mcp.tool()
async def operations_deploy(input: _OperationsDeployInput) -> str:
    """Manage deployments.

    Deploy to staging or production, or rollback to the previous version.
    The ``rollback`` field preserves the no-rollback-primitive gap-fill.

    Returns deployment status and details from the OperationsAgent.
    """
    try:
        try:
            from agents import OperationsAgent  # type: ignore[import]
            from agents.base_super_agent import TaskCategory  # type: ignore[import]
        except ImportError as exc:
            return _err(
                "Operations agent not available",
                input.response_format,
                note=f"import failed: {exc}",
            )

        agent = OperationsAgent()
        await agent.initialize()

        action = "Rollback" if input.rollback else "Deploy"
        version_label = input.version or "latest"
        prompt = f"{action} to {input.environment} — version: {version_label}"

        result = await agent.execute_with_learning(
            prompt=prompt,
            task_category=TaskCategory.REASONING,
            context={
                "environment": input.environment,
                "version": input.version,
                "rollback": input.rollback,
            },
        )

        return _fmt(
            {
                "agent": "operations",
                "action": action.lower(),
                "environment": input.environment,
                "version": version_label,
                "rollback": input.rollback,
                "result": result.response if hasattr(result, "response") else str(result),
            },
            input.response_format,
        )[:CHARACTER_LIMIT]

    except Exception as exc:
        logger.error("operations_deploy failed: %s", exc)
        return _err(str(exc), input.response_format)
