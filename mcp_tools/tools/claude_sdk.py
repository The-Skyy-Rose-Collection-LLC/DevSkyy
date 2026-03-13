"""Claude Agent SDK MCP tools: research, email triage, spreadsheet ops, dashboard."""

from pydantic import Field

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import mcp
from mcp_tools.types import BaseAgentInput

# ------------------------------------------------------------------
# Research tool
# ------------------------------------------------------------------


class ResearchInput(BaseAgentInput):
    """Input for multi-agent research pipeline."""

    topic: str = Field(
        ..., description="Research topic to investigate", min_length=3, max_length=500
    )
    subtopics: list[str] | None = Field(
        default=None,
        description="Optional specific subtopics (2-4 recommended)",
        max_length=6,
    )
    model: str = Field(
        default="haiku", description="Claude model for subagents (haiku, sonnet, opus)"
    )


@mcp.tool(
    name="devskyy_research_topic",
    annotations={
        "title": "DevSkyy Research Pipeline",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
    },
)
@secure_tool("research_topic")
async def research_topic(params: ResearchInput) -> str:
    """Research any topic using a multi-agent pipeline.

    Spawns researcher, data-analyst, and report-writer subagents to produce
    a comprehensive PDF report with data visualizations.

    The research pipeline:
    1. Lead agent breaks topic into 2-4 subtopics
    2. Researcher subagents gather data via web search (parallel)
    3. Data-analyst generates charts from findings
    4. Report-writer synthesizes everything into a PDF

    Output: PDF report in data/research/{topic}/reports/

    Args:
        params (ResearchInput): Research configuration containing:
            - topic: The research topic
            - subtopics: Optional specific angles to investigate
            - model: Claude model for subagents

    Returns:
        str: Research results with report path
    """
    response = await _make_api_request(
        "POST",
        "/api/v1/claude-sdk/research",
        json={
            "topic": params.topic,
            "subtopics": params.subtopics,
            "model": params.model,
        },
    )
    return _format_response(response)


# ------------------------------------------------------------------
# Email triage tool
# ------------------------------------------------------------------


class EmailTriageInput(BaseAgentInput):
    """Input for AI email triage."""

    mailbox: str = Field(default="INBOX", description="IMAP mailbox to scan")
    limit: int = Field(default=10, ge=1, le=100, description="Max emails to process")
    unread_only: bool = Field(default=True, description="Only process unread emails")


@mcp.tool(
    name="devskyy_email_triage",
    annotations={
        "title": "DevSkyy Email Triage",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
        "defer_loading": True,
    },
)
@secure_tool("email_triage")
async def email_triage(params: EmailTriageInput) -> str:
    """Triage emails from IMAP with AI-powered classification.

    Fetches emails from the configured IMAP server, classifies each by
    priority and category, extracts action items, and drafts responses.

    Requires env vars: EMAIL_USER, EMAIL_PASSWORD, IMAP_HOST

    Categories: customer_support, order, newsletter, partnership, urgent, spam
    Priorities: urgent, high, medium, low, spam

    Args:
        params (EmailTriageInput): Triage configuration containing:
            - mailbox: IMAP mailbox name
            - limit: Maximum emails to process
            - unread_only: Whether to skip already-read emails

    Returns:
        str: Triage results with classified emails and action items
    """
    response = await _make_api_request(
        "POST",
        "/api/v1/claude-sdk/email",
        json={
            "mailbox": params.mailbox,
            "limit": params.limit,
            "unread_only": params.unread_only,
        },
    )
    return _format_response(response)


# ------------------------------------------------------------------
# Spreadsheet tools
# ------------------------------------------------------------------


class GenerateSpreadsheetInput(BaseAgentInput):
    """Input for spreadsheet generation."""

    description: str = Field(
        ...,
        description="Natural language description of the spreadsheet to create",
        min_length=5,
        max_length=2000,
    )
    output_filename: str | None = Field(
        default=None, description="Desired output filename (auto-generated if omitted)"
    )


@mcp.tool(
    name="devskyy_generate_spreadsheet",
    annotations={
        "title": "DevSkyy Spreadsheet Generator",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "defer_loading": True,
    },
)
@secure_tool("generate_spreadsheet")
async def generate_spreadsheet(params: GenerateSpreadsheetInput) -> str:
    """Create an Excel spreadsheet from natural language description.

    Uses openpyxl to generate professional spreadsheets with:
    - Proper Excel formulas (never hardcoded values)
    - Professional formatting and styling
    - SkyyRose brand colors when applicable
    - Formula recalculation via LibreOffice

    Output: .xlsx file in data/spreadsheets/

    Args:
        params (GenerateSpreadsheetInput): Generation config containing:
            - description: What the spreadsheet should contain
            - output_filename: Optional filename

    Returns:
        str: Result with output file path and formula check status
    """
    response = await _make_api_request(
        "POST",
        "/api/v1/claude-sdk/excel",
        json={
            "operation": "create",
            "description": params.description,
            "output_filename": params.output_filename,
        },
    )
    return _format_response(response)


class AnalyzeSpreadsheetInput(BaseAgentInput):
    """Input for spreadsheet analysis."""

    input_file: str = Field(..., description="Path to the Excel file to analyze", min_length=1)
    description: str = Field(
        ...,
        description="What analysis to perform on the spreadsheet",
        min_length=5,
        max_length=2000,
    )


@mcp.tool(
    name="devskyy_analyze_spreadsheet",
    annotations={
        "title": "DevSkyy Spreadsheet Analyzer",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "defer_loading": True,
    },
)
@secure_tool("analyze_spreadsheet")
async def analyze_spreadsheet(params: AnalyzeSpreadsheetInput) -> str:
    """Analyze an existing Excel spreadsheet with AI.

    Uses pandas for data analysis, providing statistical summaries,
    trend detection, and actionable insights.

    Args:
        params (AnalyzeSpreadsheetInput): Analysis config containing:
            - input_file: Path to the .xlsx file
            - description: What to analyze

    Returns:
        str: Analysis results and insights
    """
    response = await _make_api_request(
        "POST",
        "/api/v1/claude-sdk/excel",
        json={
            "operation": "analyze",
            "description": params.description,
            "input_file": params.input_file,
        },
    )
    return _format_response(response)


# ------------------------------------------------------------------
# Dashboard orchestrator tools
# ------------------------------------------------------------------


class DashboardActionInput(BaseAgentInput):
    """Input for dashboard action execution."""

    domain: str = Field(
        ...,
        description="Target domain: operations, commerce, content, "
        "analytics, imagery, creative, marketing, web_builder",
    )
    action: str = Field(
        ...,
        description="Action/capability to execute (e.g., deploy_run, "
        "vton_render, brand_compliance, data_query)",
    )
    task: str = Field(
        default="",
        description="Task description for the agent",
    )


@mcp.tool(
    name="devskyy_dashboard_action",
    annotations={
        "title": "DevSkyy Dashboard Action",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
    },
)
@secure_tool("dashboard_action")
async def dashboard_action(params: DashboardActionInput) -> str:
    """Execute a dashboard action via SDK domain agents.

    Invokes one of 18 SDK agents across 8 domains to perform
    real operations: deploy, render, analyze, audit, scan, etc.

    Domains: operations, commerce, content, analytics, imagery,
    creative, marketing, web_builder.

    Args:
        params (DashboardActionInput): Action config containing:
            - domain: Target domain
            - action: Capability to invoke
            - task: Task description

    Returns:
        str: Action result with metrics
    """
    response = await _make_api_request(
        "POST",
        "/api/v1/claude-sdk/dashboard",
        json={
            "actions": [
                {
                    "domain": params.domain,
                    "action": params.action,
                    "params": {"task": params.task},
                }
            ],
            "parallel": False,
        },
    )
    return _format_response(response)


class DashboardHealthInput(BaseAgentInput):
    """Input for dashboard health check."""

    domain: str | None = Field(
        default=None,
        description="Optional domain filter",
    )


@mcp.tool(
    name="devskyy_dashboard_health",
    annotations={
        "title": "DevSkyy Dashboard Health",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "defer_loading": True,
    },
)
@secure_tool("dashboard_health")
async def dashboard_health(params: DashboardHealthInput) -> str:
    """Check health and availability of all SDK dashboard agents.

    Returns 18 agents across 8 domains with their capabilities,
    availability status, and last-used timestamps.

    Args:
        params (DashboardHealthInput): Optional domain filter.

    Returns:
        str: Agent health status across all domains
    """
    endpoint = "/api/v1/claude-sdk/dashboard/health"
    if params.domain:
        endpoint = f"/api/v1/claude-sdk/dashboard/agents?domain={params.domain}"
    response = await _make_api_request("GET", endpoint)
    return _format_response(response)
