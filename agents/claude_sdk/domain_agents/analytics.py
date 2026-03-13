"""
SDK Analytics Domain Agents
==============================

SDK-powered sub-agents for the Analytics core domain.
These agents can run data queries, generate charts with matplotlib,
write reports, and analyze real files — not just describe analysis.

Agents:
    SDKDataAnalystAgent     — Query data, generate charts, detect anomalies
    SDKReportGeneratorAgent — Multi-agent research → analysis → PDF report
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_agent_sdk import AgentDefinition

from agents.claude_sdk.sdk_sub_agent import SDKSubAgent
from agents.claude_sdk.tool_bridge import (
    ToolProfile,
    build_analyst_agent,
    build_researcher_agent,
    build_writer_agent,
)
from agents.core.base import CoreAgentType


class SDKDataAnalystAgent(SDKSubAgent):
    """Data analyst with real computation capabilities.

    Can read CSV/JSON data files, run Python scripts for analysis,
    generate matplotlib charts, and write structured reports.
    """

    name = "sdk_data_analyst"
    parent_type = CoreAgentType.ANALYTICS
    description = "Run data queries, generate charts, detect anomalies"
    capabilities = [
        "data_query",
        "chart_generate",
        "anomaly_detect",
        "trend_analysis",
        "cohort_analysis",
        "export_csv",
    ]
    sdk_tools = ToolProfile.ANALYTICS
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/analytics/analysis")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy Data Analyst for SkyyRose e-commerce.\n\n"
            "You have full access to read data files, run Python scripts, "
            "and generate visualizations.\n\n"
            "Key metrics:\n"
            "- AOV (Average Order Value), Conversion Rate, Cart Abandonment\n"
            "- Revenue by collection (Black Rose, Love Hurts, Signature)\n"
            "- Customer LTV, Cohort retention, Traffic sources\n\n"
            "Tools:\n"
            "- Read CSV/JSON data files in data/ directory\n"
            "- Run Python with pandas, matplotlib, numpy via Bash\n"
            "- Write charts as PNG to session directory\n"
            "- Grep logs for pattern analysis\n\n"
            "Always show your work: include the actual data points, "
            "chart file paths, and statistical measures in your response."
        )


class SDKReportGeneratorAgent(SDKSubAgent):
    """Report generator using multi-agent delegation.

    Spawns researcher + analyst + writer subagents for comprehensive
    reports. The researcher gathers data, analyst creates charts,
    and writer synthesizes into a final report.
    """

    name = "sdk_report_generator"
    parent_type = CoreAgentType.ANALYTICS
    description = "Multi-agent report generation with research + analysis"
    capabilities = [
        "full_report",
        "executive_summary",
        "competitive_analysis",
        "market_report",
    ]
    sdk_tools = ["Task"]  # Lead agent delegates, doesn't do direct work
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/analytics/reports")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy Report Generator lead agent.\n\n"
            "You coordinate subagents to produce comprehensive reports:\n"
            "1. Delegate research to the researcher agent\n"
            "2. Delegate data analysis to the analyst agent\n"
            "3. Delegate final report writing to the writer agent\n\n"
            "Use the Task tool to spawn each subagent in sequence. "
            "Pass context between agents by referencing the session "
            "directory where they save their outputs.\n\n"
            "Final output: a complete report with data, charts, "
            "and actionable recommendations."
        )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """Execute via multi-agent delegation."""
        topic = kwargs.get("topic", task)
        agents: dict[str, AgentDefinition] = {
            "researcher": build_researcher_agent(topic_hint=topic, model="haiku"),
            "analyst": build_analyst_agent(model="haiku"),
            "writer": build_writer_agent(output_format="markdown", model="sonnet"),
        }

        result = await self._sdk_delegate(
            self._build_task_prompt(task, **kwargs),
            agents=agents,
            label="report",
        )

        return {
            "success": result.success,
            "result": result.response,
            "agent": self.name,
            "execution_mode": "sdk_delegation",
            "metrics": result.metrics,
            "error": result.error,
        }


__all__ = [
    "SDKDataAnalystAgent",
    "SDKReportGeneratorAgent",
]
