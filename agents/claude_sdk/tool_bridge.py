"""
DevSkyy Tool Bridge
====================

Maps DevSkyy internal capabilities as tool sets that SDK agents
can access. Instead of SDK agents operating in a vacuum, they get
domain-aware tool configurations.

Tool Profiles:
    COMMERCE_TOOLS   — Product catalog, WooCommerce, pricing
    CONTENT_TOOLS    — Blog, SEO, copy generation
    CREATIVE_TOOLS   — Design system, brand assets
    OPERATIONS_TOOLS — Deploy, CI/CD, shell access
    ANALYTICS_TOOLS  — Data analysis, reporting
    IMAGERY_TOOLS    — Image gen, VTON, 3D models
    WEB_BUILDER_TOOLS — WordPress theme, templates
    RESEARCH_TOOLS   — Web search, document analysis
    FULL_TOOLS       — Everything (orchestrator-level)

Usage:
    from agents.claude_sdk.tool_bridge import ToolProfile

    class MyAgent(SDKSubAgent):
        sdk_tools = ToolProfile.OPERATIONS
"""

from __future__ import annotations

from claude_agent_sdk import AgentDefinition


class ToolProfile:
    """Predefined tool sets aligned with CoreAgentType domains.

    Each profile grants the minimum tools needed for the domain,
    following the principle of least privilege.
    """

    # Core tools available to all agents
    BASE: list[str] = ["Read", "Write"]

    # Domain-specific profiles
    COMMERCE: list[str] = [
        "Read",
        "Write",
        "Bash",
        "Glob",
        "Grep",
    ]

    CONTENT: list[str] = [
        "Read",
        "Write",
        "Edit",
        "Bash",
        "WebSearch",
        "WebFetch",
    ]

    CREATIVE: list[str] = [
        "Read",
        "Write",
        "Bash",
        "Glob",
    ]

    MARKETING: list[str] = [
        "Read",
        "Write",
        "Bash",
        "WebSearch",
        "WebFetch",
    ]

    OPERATIONS: list[str] = [
        "Read",
        "Write",
        "Edit",
        "Bash",
        "Glob",
        "Grep",
    ]

    ANALYTICS: list[str] = [
        "Read",
        "Write",
        "Bash",
        "Glob",
        "Grep",
    ]

    IMAGERY: list[str] = [
        "Read",
        "Write",
        "Bash",
        "Glob",
    ]

    WEB_BUILDER: list[str] = [
        "Read",
        "Write",
        "Edit",
        "Bash",
        "Glob",
        "Grep",
        "WebFetch",
    ]

    RESEARCH: list[str] = [
        "Read",
        "Write",
        "Bash",
        "WebSearch",
        "WebFetch",
        "Glob",
        "Grep",
    ]

    # Full access — orchestrator or escalation-level agents
    FULL: list[str] = [
        "Read",
        "Write",
        "Edit",
        "Bash",
        "Glob",
        "Grep",
        "WebSearch",
        "WebFetch",
        "Task",
    ]

    @classmethod
    def for_domain(cls, domain: str) -> list[str]:
        """Get tool profile by domain name string.

        Args:
            domain: CoreAgentType value or domain name.

        Returns:
            Tool list for the domain, falls back to BASE.
        """
        mapping = {
            "commerce": cls.COMMERCE,
            "content": cls.CONTENT,
            "creative": cls.CREATIVE,
            "marketing": cls.MARKETING,
            "operations": cls.OPERATIONS,
            "analytics": cls.ANALYTICS,
            "imagery": cls.IMAGERY,
            "web_builder": cls.WEB_BUILDER,
            "research": cls.RESEARCH,
            "orchestrator": cls.FULL,
        }
        return list(mapping.get(domain.lower(), cls.BASE))


# ------------------------------------------------------------------
# Reusable AgentDefinition builders
# ------------------------------------------------------------------


def build_researcher_agent(
    *,
    topic_hint: str = "",
    model: str = "haiku",
) -> AgentDefinition:
    """Build a researcher subagent definition for SDK delegation.

    The researcher uses web search and file tools to gather data
    on a topic and save structured notes.
    """
    prompt = (
        "You are a DevSkyy research agent. Your job is to gather "
        "comprehensive data on the assigned topic using web search "
        "and available tools. Save findings as structured notes.\n"
    )
    if topic_hint:
        prompt += f"\nFocus area: {topic_hint}\n"

    return AgentDefinition(
        model=model,
        tools=ToolProfile.RESEARCH,
        prompt=prompt,
    )


def build_analyst_agent(*, model: str = "haiku") -> AgentDefinition:
    """Build a data analyst subagent for SDK delegation.

    The analyst reads gathered data/notes and produces charts,
    summaries, and statistical analysis.
    """
    return AgentDefinition(
        model=model,
        tools=["Read", "Write", "Bash"],
        prompt=(
            "You are a DevSkyy data analyst. Read the research notes "
            "in the session directory, analyze the data, and produce "
            "charts using matplotlib. Save visualizations as PNG files."
        ),
    )


def build_writer_agent(
    *,
    output_format: str = "markdown",
    model: str = "sonnet",
) -> AgentDefinition:
    """Build a report writer subagent for SDK delegation.

    The writer synthesizes research and analysis into a final
    deliverable (markdown, PDF, or HTML).
    """
    return AgentDefinition(
        model=model,
        tools=["Read", "Write", "Bash"],
        prompt=(
            f"You are a DevSkyy report writer. Read the research notes "
            f"and analysis in the session directory, then produce a "
            f"comprehensive report in {output_format} format. "
            f"Include data visualizations if available."
        ),
    )


def build_code_agent(
    *,
    language: str = "python",
    model: str = "sonnet",
) -> AgentDefinition:
    """Build a code specialist subagent for SDK delegation.

    The code agent reads, writes, and tests code with full
    tool access.
    """
    return AgentDefinition(
        model=model,
        tools=ToolProfile.OPERATIONS,
        prompt=(
            f"You are a DevSkyy {language} specialist. Read existing "
            f"code, implement changes, and verify with tests. "
            f"Follow DevSkyy coding standards (100 char line length, "
            f"type hints, structlog for logging)."
        ),
    )


def build_domain_agents(
    domain: str,
    *,
    model: str = "haiku",
) -> dict[str, AgentDefinition]:
    """Build a standard set of subagents for a domain.

    Returns researcher + analyst + writer agents configured
    for the given domain.
    """
    return {
        f"{domain}_researcher": build_researcher_agent(
            topic_hint=f"{domain} domain analysis",
            model=model,
        ),
        f"{domain}_analyst": build_analyst_agent(model=model),
        f"{domain}_writer": build_writer_agent(model=model),
    }
