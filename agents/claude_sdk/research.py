"""
Research Multi-Agent
====================

Orchestrates a lead agent that spawns researcher, data-analyst, and
report-writer subagents to produce comprehensive PDF research reports.

Adapted from claude-agent-sdk-demos/research-agent.
"""

from __future__ import annotations

from pathlib import Path

import structlog
from claude_agent_sdk import AgentDefinition
from pydantic import BaseModel, Field

from agents.claude_sdk.base import ClaudeSDKBaseAgent, SDKAgentConfig

logger = structlog.get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(filename: str) -> str:
    prompt_path = PROMPTS_DIR / filename
    return prompt_path.read_text(encoding="utf-8").strip()


# ------------------------------------------------------------------
# Request / Result models
# ------------------------------------------------------------------


class ResearchRequest(BaseModel):
    """Input model for research API endpoint."""

    topic: str = Field(..., description="Research topic", min_length=3, max_length=500)
    subtopics: list[str] | None = Field(
        default=None,
        description="Optional specific subtopics to investigate",
        max_length=6,
    )
    model: str = Field(default="haiku", description="Claude model for subagents")


class ResearchResult(BaseModel):
    """Output model for research API endpoint."""

    topic: str
    session_dir: str
    report_path: str | None = None
    response: str


# ------------------------------------------------------------------
# Agent
# ------------------------------------------------------------------


class ResearchAgent(ClaudeSDKBaseAgent):
    """Multi-agent research pipeline.

    Topology:
        Lead Agent (coordinator)
        ├── Researcher × 2-4 (parallel web search)
        ├── Data Analyst × 1 (charts from findings)
        └── Report Writer × 1 (PDF synthesis)

    Output directory: ``data/research/{topic}/``
    """

    def __init__(self, config: SDKAgentConfig | None = None) -> None:
        cfg = config or SDKAgentConfig(output_dir=Path("data/research"))
        super().__init__(cfg)

    def _build_system_prompt(self) -> str:
        return _load_prompt("research_lead.txt")

    def _build_agents(self) -> dict[str, AgentDefinition]:
        return {
            "researcher": AgentDefinition(
                description=(
                    "Use this agent to gather research information on any topic. "
                    "Uses web search to find data-rich sources. Writes findings to "
                    "data/research/{topic}/notes/ for later use by report writers."
                ),
                tools=["WebSearch", "Write"],
                prompt=_load_prompt("researcher.txt"),
                model=self.config.model,
            ),
            "data-analyst": AgentDefinition(
                description=(
                    "Use this agent AFTER researchers complete to generate charts. "
                    "Reads notes from data/research/{topic}/notes/, extracts numbers, "
                    "generates matplotlib charts to data/research/{topic}/charts/."
                ),
                tools=["Glob", "Read", "Bash", "Write"],
                prompt=_load_prompt("data_analyst.txt"),
                model=self.config.model,
            ),
            "report-writer": AgentDefinition(
                description=(
                    "Use this agent to create a PDF report from research notes "
                    "and charts. Reads from notes/, charts/, data/ and produces "
                    "a professional PDF in data/research/{topic}/reports/."
                ),
                tools=["Write", "Glob", "Read", "Bash"],
                prompt=_load_prompt("report_writer.txt"),
                model=self.config.model,
            ),
        }

    async def research(self, request: ResearchRequest) -> ResearchResult:
        """Execute the full research pipeline for a topic.

        Args:
            request: Research request with topic and optional subtopics.

        Returns:
            ResearchResult with paths to generated artifacts.
        """
        topic_slug = request.topic.lower().replace(" ", "_")[:50]
        session_dir = self.config.output_dir / topic_slug

        prompt = f"Research the following topic comprehensively: {request.topic}"
        if request.subtopics:
            prompt += f"\n\nFocus on these subtopics: {', '.join(request.subtopics)}"

        logger.info("research_started", topic=request.topic, session_dir=str(session_dir))

        response = await self.run(prompt, session_dir=session_dir)

        # Find the generated report
        report_path = None
        reports_dir = session_dir / "reports"
        if reports_dir.exists():
            pdfs = list(reports_dir.glob("*.pdf"))
            if pdfs:
                report_path = str(pdfs[0])

        return ResearchResult(
            topic=request.topic,
            session_dir=str(session_dir),
            report_path=report_path,
            response=response,
        )
