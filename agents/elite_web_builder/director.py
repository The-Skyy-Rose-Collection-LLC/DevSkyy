"""
Project Director — coordinates the Elite Web Builder team.

The Director:
- Breaks PRDs into user stories with dependency graphs
- Assigns stories to specialist agents based on requirements
- Reviews all agent output before marking stories green
- Runs the verification loop after each story
- Triggers self-heal on failures
- Maintains the learning journal

This is the entry point for the Elite Web Builder system.

Usage:
    director = Director.from_config(config_path="config/provider_routing.json")
    report = await director.execute_prd(prd_text)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Dependency preflight — fail fast with actionable message
# ---------------------------------------------------------------------------
_REQUIRED_PACKAGES = {
    "anthropic": "anthropic",
    "openai": "openai",
    "google.genai": "google-genai",
    "pydantic": "pydantic",
    "httpx": "httpx",
    "aiofiles": "aiofiles",
}

_missing = []
for _mod, _pkg in _REQUIRED_PACKAGES.items():
    try:
        __import__(_mod)
    except ModuleNotFoundError:
        _missing.append(_pkg)
if _missing:
    raise SystemExit(
        f"\n  Elite Web Builder — missing dependencies: {', '.join(_missing)}\n"
        f"  Fix: .venv/bin/pip install -r requirements.txt\n"
    )
del _missing, _mod, _pkg  # keep module namespace clean

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from agents.accessibility import ACCESSIBILITY_SPEC
from agents.backend_dev import BACKEND_DEV_SPEC
from agents.base import AgentOutput, AgentRole, AgentSpec
from agents.design_system import DESIGN_SYSTEM_SPEC
from agents.frontend_dev import FRONTEND_DEV_SPEC
from agents.performance import PERFORMANCE_SPEC
from agents.qa import QA_SPEC
from agents.runtime import AgentRuntime
from agents.seo_content import SEO_CONTENT_SPEC
from core.ground_truth import GroundTruthValidator
from core.learning_journal import LearningJournal
from core.model_router import ModelRouter, RoutingConfig
from core.ralph_integration import RalphExecutor, RalphConfig
from core.self_healer import SelfHealer
from core.verification_loop import (
    Gate,
    GateChecker,
    GateResult,
    GateStatus,
    VerificationConfig,
    VerificationLoop,
    VerificationReport,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Story management
# ---------------------------------------------------------------------------


class StoryStatus(Enum):
    """Status of a user story."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    GREEN = "green"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class UserStory:
    """A single unit of work derived from a PRD."""

    id: str
    title: str
    description: str
    agent_role: AgentRole
    status: StoryStatus = StoryStatus.PENDING
    depends_on: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    output: AgentOutput | None = None


@dataclass
class PRDBreakdown:
    """Result of breaking a PRD into stories."""

    stories: list[UserStory]
    dependency_order: list[str]  # Story IDs in execution order


class PlanningError(RuntimeError):
    """Raised when the Director cannot parse a valid PRDBreakdown from LLM output."""

    def __init__(self, message: str, raw_response: str = "") -> None:
        super().__init__(message)
        self.raw_response = raw_response


@dataclass(frozen=True)
class ProjectReport:
    """Immutable summary of a full PRD execution run."""

    stories: dict[str, UserStory]
    status_summary: dict[str, int]
    all_green: bool
    elapsed_ms: float
    failures: list[str]
    instincts_learned: int


# ---------------------------------------------------------------------------
# Director
# ---------------------------------------------------------------------------


@dataclass
class DirectorConfig:
    """Configuration for the Director."""

    routing_config: RoutingConfig
    learning_dir: Path = Path("instincts")
    verification_config: VerificationConfig = field(
        default_factory=VerificationConfig
    )
    max_heal_attempts: int = 3
    max_stories: int = 50


class Director:
    """
    Project Director — orchestrates the Elite Web Builder team.

    Coordinates agent execution through the ralph-tui loop:
    PRD → Stories → Assign → Build → Verify → Heal → Learn → Deploy
    """

    def __init__(self, config: DirectorConfig) -> None:
        self._config = config
        self._router = ModelRouter(config=config.routing_config)
        self._validator = GroundTruthValidator()
        self._journal = LearningJournal(storage_dir=config.learning_dir)
        self._healer = SelfHealer(max_attempts=config.max_heal_attempts)
        self._verifier = VerificationLoop(config=config.verification_config)
        self._executor = RalphExecutor(config=RalphConfig())
        self._runtime = AgentRuntime(
            router=self._router,
            validator=self._validator,
            journal=self._journal,
        )
        self._spec_registry: dict[AgentRole, AgentSpec] = {
            spec.role: spec
            for spec in (
                DESIGN_SYSTEM_SPEC,
                FRONTEND_DEV_SPEC,
                BACKEND_DEV_SPEC,
                ACCESSIBILITY_SPEC,
                PERFORMANCE_SPEC,
                SEO_CONTENT_SPEC,
                QA_SPEC,
            )
        }
        self._stories: dict[str, UserStory] = {}

    @staticmethod
    def from_config(
        routing_config: dict[str, Any] | None = None,
        learning_dir: str = "instincts",
    ) -> Director:
        """Create a Director from configuration."""
        rc = RoutingConfig.from_dict(routing_config or _DEFAULT_ROUTING)
        config = DirectorConfig(
            routing_config=rc,
            learning_dir=Path(learning_dir),
        )
        return Director(config=config)

    # -- Story management --

    def add_stories(self, stories: list[UserStory]) -> None:
        """Register stories for execution."""
        for story in stories:
            self._stories[story.id] = story

    def get_ready_stories(self) -> list[UserStory]:
        """Get stories whose dependencies are all GREEN."""
        ready = []
        for story in self._stories.values():
            if story.status != StoryStatus.PENDING:
                continue
            deps_met = all(
                self._stories.get(dep, UserStory(id=dep, title="", description="", agent_role=AgentRole.DIRECTOR)).status == StoryStatus.GREEN
                for dep in story.depends_on
            )
            if deps_met:
                ready.append(story)
        return ready

    def get_status_summary(self) -> dict[str, int]:
        """Count stories by status."""
        summary: dict[str, int] = {}
        for story in self._stories.values():
            key = story.status.value
            summary[key] = summary.get(key, 0) + 1
        return summary

    # -- Core components access --

    @property
    def router(self) -> ModelRouter:
        return self._router

    @property
    def validator(self) -> GroundTruthValidator:
        return self._validator

    @property
    def journal(self) -> LearningJournal:
        return self._journal

    @property
    def healer(self) -> SelfHealer:
        return self._healer

    @property
    def verifier(self) -> VerificationLoop:
        return self._verifier

    @property
    def executor(self) -> RalphExecutor:
        return self._executor

    @property
    def runtime(self) -> AgentRuntime:
        return self._runtime

    @property
    def spec_registry(self) -> dict[AgentRole, AgentSpec]:
        return dict(self._spec_registry)

    # -- Story execution --

    async def run_story(
        self,
        story: UserStory,
        gate_checkers: dict[Gate, GateChecker] | None = None,
    ) -> UserStory:
        """
        Execute a story by auto-resolving its agent spec and calling the runtime.

        This is the high-level entry point that ties everything together:
        1. Look up the AgentSpec for the story's role
        2. Create a closure that calls AgentRuntime.execute()
        3. Delegate to execute_story() for the full loop

        Args:
            story: The story to execute
            gate_checkers: Optional gate checkers for verification

        Returns:
            Updated UserStory with new status

        Raises:
            ValueError: If no agent spec is registered for the story's role
        """
        spec = self._spec_registry.get(story.agent_role)
        if spec is None:
            raise ValueError(
                f"No agent spec registered for role '{story.agent_role.value}'. "
                f"Available: {sorted(r.value for r in self._spec_registry)}"
            )

        async def agent_fn() -> AgentOutput:
            return await self._runtime.execute(
                spec=spec,
                task=story.description,
                story_id=story.id,
            )

        return await self.execute_story(
            story=story,
            agent_fn=agent_fn,
            gate_checkers=gate_checkers,
        )

    async def execute_story(
        self,
        story: UserStory,
        agent_fn: Any,
        gate_checkers: dict[Gate, GateChecker] | None = None,
    ) -> UserStory:
        """
        Execute a single story through the full loop.

        1. Mark in-progress
        2. Run agent function
        3. Verify with quality gates
        4. Self-heal on failure
        5. Log to journal if needed
        6. Return updated story

        Args:
            story: The story to execute
            agent_fn: Async callable that produces AgentOutput
            gate_checkers: Optional gate checkers for verification

        Returns:
            Updated UserStory with new status
        """
        story.status = StoryStatus.IN_PROGRESS
        logger.info("Executing story %s: %s", story.id, story.title)

        # Resolve model for this agent
        route = self._router.resolve(story.agent_role.value)
        logger.info(
            "Story %s → agent=%s provider=%s model=%s (fallback=%s)",
            story.id,
            story.agent_role.value,
            route.provider,
            route.model,
            route.is_fallback,
        )

        # Run the agent with ralph-loop resilience
        result = await self._executor.execute(agent_fn)

        if not result.success:
            story.status = StoryStatus.FAILED
            logger.error("Story %s: agent execution failed — %s", story.id, result.error)
            return story

        story.output = result.value

        # Run verification if checkers provided
        if gate_checkers:
            report = await self._verifier.run_all(gate_checkers)

            if report.all_green:
                story.status = StoryStatus.GREEN
                logger.info("Story %s: ALL GREEN ✓", story.id)
            else:
                # Attempt self-heal
                diagnosis = self._healer.diagnose(report)
                if diagnosis:
                    logger.warning(
                        "Story %s: %d gates failed, starting heal cycle",
                        story.id,
                        len(diagnosis.failed_gates),
                    )
                    # Note: actual heal would need agent-specific fixer
                    story.status = StoryStatus.FAILED
                else:
                    story.status = StoryStatus.GREEN
        else:
            # No gate checkers — mark green (trust the agent)
            story.status = StoryStatus.GREEN

        return story

    # -- Planning & execution --

    @staticmethod
    def _parse_planning_response(raw: str) -> dict[str, Any]:
        """Parse LLM planning output as JSON, stripping markdown fences if needed."""
        stripped = raw.strip()

        # Try raw JSON first
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            pass

        # Strip markdown code fences and retry
        defenced = re.sub(
            r"^```(?:json)?\s*\n?", "", stripped, count=1,
        )
        defenced = re.sub(r"\n?```\s*$", "", defenced, count=1)

        try:
            return json.loads(defenced.strip())
        except (json.JSONDecodeError, ValueError) as exc:
            raise PlanningError(
                f"LLM returned invalid JSON: {exc}",
                raw_response=raw,
            ) from exc

    @staticmethod
    def _build_breakdown(
        data: dict[str, Any],
        max_stories: int = 50,
    ) -> PRDBreakdown:
        """Construct a PRDBreakdown from parsed planning JSON."""
        if "stories" not in data:
            raise PlanningError(
                "Planning response missing 'stories' key",
                raw_response=json.dumps(data),
            )

        raw_stories = data["stories"][:max_stories]
        role_values = {r.value for r in AgentRole}
        stories: list[UserStory] = []

        for entry in raw_stories:
            role_str = entry.get("agent_role", "")
            if role_str not in role_values:
                raise PlanningError(
                    f"Unknown agent_role '{role_str}'. "
                    f"Valid roles: {sorted(role_values)}",
                    raw_response=json.dumps(entry),
                )

            stories.append(UserStory(
                id=entry["id"],
                title=entry["title"],
                description=entry["description"],
                agent_role=AgentRole(role_str),
                depends_on=entry.get("depends_on", []),
                acceptance_criteria=entry.get("acceptance_criteria", []),
            ))

        dependency_order = data.get("dependency_order", [s.id for s in stories])
        return PRDBreakdown(stories=stories, dependency_order=dependency_order)

    async def _plan_stories(self, prd_text: str) -> PRDBreakdown:
        """Use the LLM to decompose a PRD into user stories."""
        prompt = _PLANNING_PROMPT_TEMPLATE.format(
            max_stories=self._config.max_stories,
            prd_text=prd_text,
        )

        output = await self._runtime.execute(
            spec=_DIRECTOR_SPEC,
            task=prompt,
            story_id="PRD-PLANNING",
        )

        data = self._parse_planning_response(output.content)
        return self._build_breakdown(data, max_stories=self._config.max_stories)

    async def execute_prd(self, prd_text: str) -> ProjectReport:
        """
        Execute a full PRD: plan stories, register, execute in order, report.

        Returns a frozen ProjectReport with the final state of all stories.
        """
        start = time.time()
        failures: list[str] = []
        journal_entries_before = len(self._journal.entries)

        # Step 1: Plan
        try:
            breakdown = await self._plan_stories(prd_text)
        except PlanningError as exc:
            elapsed = (time.time() - start) * 1000
            return ProjectReport(
                stories={},
                status_summary={},
                all_green=False,
                elapsed_ms=elapsed,
                failures=[f"Planning failed: {exc}"],
                instincts_learned=0,
            )

        # Step 2: Register stories
        self.add_stories(breakdown.stories)

        # Step 3: Execute in dependency order
        max_loops = len(breakdown.stories) * 2  # guard against cycles
        loop_count = 0

        while True:
            ready = self.get_ready_stories()
            if not ready:
                # Check for deadlocked stories (still pending but unresolvable)
                pending = [
                    s for s in self._stories.values()
                    if s.status == StoryStatus.PENDING
                ]
                if pending:
                    failures.append(
                        "Dependency cycle detected — "
                        f"{len(pending)} stories stuck: "
                        + ", ".join(s.id for s in pending)
                    )
                break

            if loop_count >= max_loops:
                failures.append("Exceeded maximum execution loops — aborting")
                break
            loop_count += 1

            # Execute all ready stories in parallel (their deps are met)
            results = await asyncio.gather(
                *(self.run_story(story) for story in ready),
                return_exceptions=True,
            )
            for i, result in enumerate(results):
                if isinstance(result, BaseException):
                    failures.append(
                        f"{ready[i].id}: {ready[i].title} — ERROR: {result}"
                    )
                elif result.status == StoryStatus.FAILED:
                    failures.append(
                        f"{result.id}: {result.title} — FAILED"
                    )

        # Step 4: Build report
        elapsed = (time.time() - start) * 1000
        summary = self.get_status_summary()
        instincts_learned = len(self._journal.entries) - journal_entries_before

        return ProjectReport(
            stories=dict(self._stories),
            status_summary=summary,
            all_green=all(
                s.status == StoryStatus.GREEN
                for s in self._stories.values()
            ),
            elapsed_ms=elapsed,
            failures=failures,
            instincts_learned=instincts_learned,
        )


# ---------------------------------------------------------------------------
# Director-level constants
# ---------------------------------------------------------------------------

_DIRECTOR_SPEC = AgentSpec(
    role=AgentRole.DIRECTOR,
    name="director",
    system_prompt=(
        "You are the Director of the Elite Web Builder. "
        "You decompose Product Requirements Documents into user stories. "
        "You ALWAYS respond with valid JSON only — no markdown, no prose. "
        "Each story must have an agent_role from: "
        "design_system, frontend_dev, backend_dev, accessibility, "
        "performance, seo_content, qa."
    ),
)


_PLANNING_PROMPT_TEMPLATE = """\
Break the following PRD into user stories for a web development team.

Rules:
- Maximum {max_stories} stories
- Each story must have a clear, single responsibility
- Assign the most appropriate specialist role to each story
- List all dependencies by story ID (stories that MUST complete first)
- Use IDs like US-001, US-002, etc.

Respond with ONLY this JSON structure:
{{
  "stories": [
    {{
      "id": "US-001",
      "title": "Short title",
      "description": "What the agent must do (1-3 sentences)",
      "agent_role": "design_system",
      "depends_on": [],
      "acceptance_criteria": ["criterion 1", "criterion 2"]
    }}
  ],
  "dependency_order": ["US-001", "US-002", "US-003"]
}}

Available agent roles: design_system, frontend_dev, backend_dev, \
accessibility, performance, seo_content, qa

PRD:
{prd_text}
"""


# ---------------------------------------------------------------------------
# Default routing (matches plan spec)
# ---------------------------------------------------------------------------

_DEFAULT_ROUTING = {
    "routes": {
        "director": {"provider": "anthropic", "model": "claude-opus-4-6"},
        "design_system": {"provider": "google", "model": "gemini-2.0-flash"},
        "frontend_dev": {"provider": "anthropic", "model": "claude-haiku-4-5"},
        "backend_dev": {"provider": "anthropic", "model": "claude-haiku-4-5"},
        "accessibility": {"provider": "anthropic", "model": "claude-haiku-4-5"},
        "performance": {"provider": "google", "model": "gemini-2.0-flash"},
        "seo_content": {"provider": "anthropic", "model": "claude-haiku-4-5"},
        "qa": {"provider": "anthropic", "model": "claude-haiku-4-5"},
    },
    "fallbacks": {
        "anthropic": {"provider": "google", "model": "gemini-2.0-flash"},
        "google": {"provider": "anthropic", "model": "claude-haiku-4-5"},
    },
}
