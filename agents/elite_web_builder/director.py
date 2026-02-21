"""
Elite Web Builder Director — Project coordinator and orchestrator.

The Director decomposes PRDs into user stories, assigns them to
specialist agents, enforces dependency order, reviews all output,
and maintains the learning journal.

Key public methods:
- add_stories(): Register stories from a PRDBreakdown
- get_ready_stories(): Topological sort — stories with deps satisfied
- run_story(): Execute a single story through an agent
- get_status_summary(): Count stories by status
- execute_prd(): Full lifecycle: PRD → stories → execute → ProjectReport
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .agents.accessibility import ACCESSIBILITY_SPEC
from .agents.backend_dev import BACKEND_DEV_SPEC
from .agents.design_system import DESIGN_SYSTEM_SPEC
from .agents.frontend_dev import FRONTEND_DEV_SPEC
from .agents.performance import PERFORMANCE_SPEC
from .agents.qa import QA_SPEC
from .agents.seo_content import SEO_CONTENT_SPEC
from .core.learning_journal import LearningJournal
from .core.model_router import LLMResponse, ModelRouter
from .core.self_healer import SelfHealer
from .core.verification_loop import VerificationLoop

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class AgentRole(str, Enum):
    """Roles available in the Elite Web Builder team."""

    DIRECTOR = "director"
    DESIGN_SYSTEM = "design_system"
    FRONTEND_DEV = "frontend_dev"
    BACKEND_DEV = "backend_dev"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    SEO_CONTENT = "seo_content"
    QA = "qa"


class StoryStatus(str, Enum):
    """Lifecycle status of a user story."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    GREEN = "green"
    FAILED = "failed"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class AgentSpec:
    """Specification for a specialist agent."""

    role: AgentRole
    name: str
    system_prompt: str
    capabilities: list[dict[str, Any]] = field(default_factory=list)
    knowledge_files: list[str] = field(default_factory=list)


@dataclass
class UserStory:
    """A single user story derived from a PRD."""

    id: str
    title: str
    description: str
    agent_role: AgentRole
    depends_on: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    status: StoryStatus = StoryStatus.PENDING
    output: str = ""
    error: str = ""


@dataclass
class PRDBreakdown:
    """Result of decomposing a PRD into user stories."""

    stories: list[UserStory]
    dependency_order: list[str] = field(default_factory=list)


class PlanningError(RuntimeError):
    """Raised when the Director cannot parse a valid PRDBreakdown from LLM output."""

    def __init__(self, message: str, raw_response: str = "") -> None:
        """
        Exception raised for errors encountered while planning or parsing a PRD breakdown.
        
        Parameters:
        	message (str): Human-readable error message explaining the planning or parsing failure.
        	raw_response (str): Optional raw LLM response that triggered the error, useful for debugging and inspection.
        """
        super().__init__(message)
        self.raw_response = raw_response


@dataclass(frozen=True)
class ProjectReport:
    """Immutable report from a full PRD execution."""

    stories: tuple[UserStory, ...]
    status_summary: dict[str, int]
    all_green: bool
    elapsed_ms: float
    failures: tuple[str, ...]
    instincts_learned: int


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class DirectorConfig:
    """Configuration for the Director."""

    max_heal_attempts: int = 3
    verification_enabled: bool = True
    learning_enabled: bool = True
    routing_config_path: Path | None = None
    max_stories: int = 50


# =============================================================================
# Agent Runtime
# =============================================================================


class AgentRuntime:
    """Executes agent tasks through the model router."""

    def __init__(self, router: ModelRouter) -> None:
        """
        Initialize the AgentRuntime with a ModelRouter used to execute agent tasks.
        
        Parameters:
            router (ModelRouter): Router that dispatches model requests for agent execution; stored as the runtime's internal router.
        """
        self._router = router

    async def execute(
        self,
        spec: AgentSpec,
        task: str,
        *,
        story_id: str = "",
    ) -> LLMResponse:
        """
        Send a prompt to the agent described by spec and return the model response.
        
        Parameters:
            spec (AgentSpec): Agent specification containing the agent role and system prompt used for routing.
            task (str): The prompt or task to deliver to the agent.
            story_id (str): Optional identifier associated with the task; may be empty.
        
        Returns:
            LLMResponse: The model's response to the provided prompt.
        """
        role = spec.role.value if isinstance(spec.role, AgentRole) else spec.role
        return await self._router.route(
            role=role,
            prompt=task,
            system_prompt=spec.system_prompt,
        )


# =============================================================================
# Spec Registry
# =============================================================================

spec_registry: dict[AgentRole, dict] = {
    AgentRole.DESIGN_SYSTEM: DESIGN_SYSTEM_SPEC,
    AgentRole.FRONTEND_DEV: FRONTEND_DEV_SPEC,
    AgentRole.BACKEND_DEV: BACKEND_DEV_SPEC,
    AgentRole.ACCESSIBILITY: ACCESSIBILITY_SPEC,
    AgentRole.PERFORMANCE: PERFORMANCE_SPEC,
    AgentRole.SEO_CONTENT: SEO_CONTENT_SPEC,
    AgentRole.QA: QA_SPEC,
}


# =============================================================================
# Planning Constants
# =============================================================================

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

Platform compliance: stories MUST validate against platform rules:
- WordPress: theme.json schema valid, hooks use proper priorities, REST routes use index.php?rest_route=
- Shopify: Liquid syntax valid, settings_schema.json valid, Online Store 2.0 patterns used
- Both: WCAG 2.2 AA, Core Web Vitals targets met, no hardcoded values

Respond with ONLY this JSON structure:
{{"stories": [{{"id": "US-001", "title": "Short title", "description": "What the agent must do", "agent_role": "design_system", "depends_on": [], "acceptance_criteria": ["criterion 1"]}}], "dependency_order": ["US-001"]}}

Available roles: design_system, frontend_dev, backend_dev, accessibility, performance, seo_content, qa

PRD:
{prd_text}
"""


# =============================================================================
# Default Routing
# =============================================================================

_DEFAULT_ROUTING = {
    "routing": {
        "director": {"provider": "anthropic", "model": "claude-opus-4-6"},
        "design_system": {"provider": "google", "model": "gemini-3-pro-preview"},
        "frontend_dev": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
        "backend_dev": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
        "accessibility": {"provider": "anthropic", "model": "claude-haiku-4-5"},
        "performance": {"provider": "google", "model": "gemini-3-flash-preview"},
        "seo_content": {"provider": "openai", "model": "gpt-4o"},
        "qa": {"provider": "xai", "model": "grok-3"},
    },
    "fallbacks": {
        "anthropic": {"provider": "google", "model": "gemini-3-pro-preview"},
        "google": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
        "openai": {"provider": "anthropic", "model": "claude-sonnet-4-6"},
        "xai": {"provider": "google", "model": "gemini-3-flash-preview"},
    },
}


# =============================================================================
# Director
# =============================================================================


class Director:
    """Project Director — coordinates the Elite Web Builder team.

    Decomposes PRDs into user stories, assigns to specialist agents,
    enforces dependency order, and maintains project state.
    """

    def __init__(
        self,
        config: DirectorConfig | None = None,
        router: ModelRouter | None = None,
        journal: LearningJournal | None = None,
        healer: SelfHealer | None = None,
        verifier: VerificationLoop | None = None,
    ) -> None:
        """
        Initialize the Director orchestration instance and its runtime components.
        
        Creates and stores configuration, model router (with default routing when omitted), agent runtime, learning journal, self-healer, verification loop, and an empty story registry.
        
        Parameters:
            config (DirectorConfig | None): Director configuration; a default DirectorConfig is created if omitted.
            router (ModelRouter | None): ModelRouter to route model calls; a default router is created when omitted.
            journal (LearningJournal | None): LearningJournal to record instincts; a new LearningJournal is created if omitted.
            healer (SelfHealer | None): SelfHealer used for automated healing attempts; a SelfHealer with config.max_heal_attempts is created if omitted.
            verifier (VerificationLoop | None): VerificationLoop used to verify agent outputs; a default VerificationLoop is created if omitted.
        """
        self._config = config or DirectorConfig()
        self._router = router or ModelRouter(
            routing=_DEFAULT_ROUTING["routing"],
            fallbacks=_DEFAULT_ROUTING["fallbacks"],
        )
        self._runtime = AgentRuntime(self._router)
        self._journal = journal or LearningJournal()
        self._healer = healer or SelfHealer(
            max_attempts=self._config.max_heal_attempts
        )
        self._verifier = verifier or VerificationLoop()
        self._stories: dict[str, UserStory] = {}

    @property
    def stories(self) -> dict[str, UserStory]:
        """Read-only access to stories."""
        return dict(self._stories)

    @property
    def router(self) -> ModelRouter:
        """
        Expose the configured ModelRouter used for dispatching model requests.
        
        Returns:
            model_router (ModelRouter): The Director's configured ModelRouter instance.
        """
        return self._router

    # -----------------------------------------------------------------
    # Story Management
    # -----------------------------------------------------------------

    def add_stories(self, stories: list[UserStory]) -> None:
        """
        Register a list of UserStory objects into the director's internal story store.
        
        Parameters:
            stories (list[UserStory]): Stories to add; stories are indexed by their `id`. If a story id already exists, the new story replaces the existing entry.
        """
        for story in stories:
            self._stories[story.id] = story
            logger.info("Registered story %s: %s", story.id, story.title)

    def get_ready_stories(self) -> list[UserStory]:
        """
        Identify pending stories whose dependencies are all GREEN.
        
        Returns:
            list[UserStory]: Pending stories whose dependencies are all GREEN, ordered by readiness.
        """
        ready = []
        for story in self._stories.values():
            if story.status != StoryStatus.PENDING:
                continue
            deps_satisfied = all(
                self._stories.get(dep_id, UserStory(id=dep_id, title="", description="", agent_role=AgentRole.DIRECTOR)).status
                == StoryStatus.GREEN
                for dep_id in story.depends_on
            )
            if deps_satisfied:
                ready.append(story)
        return ready

    def get_status_summary(self) -> dict[str, int]:
        """
        Produce a count of current stories grouped by their status.
        
        Returns:
            mapping (dict[str, int]): A dictionary mapping each story status name (string) to the number of stories in that status.
        """
        summary: dict[str, int] = {}
        for story in self._stories.values():
            key = story.status.value
            summary[key] = summary.get(key, 0) + 1
        return summary

    # -----------------------------------------------------------------
    # Story Execution
    # -----------------------------------------------------------------

    async def run_story(self, story: UserStory) -> UserStory:
        """
        Execute a UserStory by sending its task to the assigned agent, optionally verify and attempt self-healing, and update the story's status and output.
        
        Parameters:
            story (UserStory): The story to execute; this object is mutated in-place with updated `status`, `output`, and `error` fields.
        
        Returns:
            UserStory: The same `story` instance after execution; `status` will be `GREEN` on success or `FAILED` on failure, with `output` and optional `error` populated accordingly.
        """
        story.status = StoryStatus.IN_PROGRESS
        logger.info("Executing story %s: %s (agent=%s)", story.id, story.title, story.agent_role.value)

        agent_spec_dict = spec_registry.get(story.agent_role, {})
        spec = AgentSpec(
            role=story.agent_role,
            name=agent_spec_dict.get("name", story.agent_role.value),
            system_prompt=agent_spec_dict.get("system_prompt", ""),
        )

        try:
            result = await self._runtime.execute(
                spec=spec,
                task=story.description,
                story_id=story.id,
            )
            story.output = result.content

            # Verification
            if self._config.verification_enabled:
                vresult = await self._verifier.run(result.content)
                if not vresult.all_green:
                    # Attempt self-healing
                    healed = False
                    for _attempt in range(self._config.max_heal_attempts):
                        diagnosis = await self._healer.diagnose(
                            str(vresult.failures)
                        )
                        fixed = await self._healer.heal(result.content, diagnosis)
                        re_verify = await self._verifier.run(fixed)
                        if re_verify.all_green:
                            story.output = fixed
                            healed = True
                            break

                    if not healed:
                        story.status = StoryStatus.FAILED
                        story.error = f"Verification failed after {self._config.max_heal_attempts} heal attempts"
                        return story

            story.status = StoryStatus.GREEN
            logger.info("Story %s: GREEN", story.id)

        except Exception as exc:
            story.status = StoryStatus.FAILED
            story.error = str(exc)
            logger.error("Story %s: FAILED — %s", story.id, exc)

        return story

    # -----------------------------------------------------------------
    # Planning Methods
    # -----------------------------------------------------------------

    @staticmethod
    def _parse_planning_response(raw: str) -> dict:
        """Parse JSON from LLM planning response.

        Handles both raw JSON and markdown-fenced JSON.
        """
        # Try direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Strip markdown fences
        stripped = re.sub(
            r"^```(?:json)?\s*\n?|\n?```\s*$", "", raw.strip()
        )
        try:
            return json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise PlanningError(
                f"Invalid JSON in planning response: {exc}",
                raw_response=raw,
            ) from exc

    @staticmethod
    def _build_breakdown(
        data: dict, *, max_stories: int = 50
    ) -> PRDBreakdown:
        """
        Builds a PRDBreakdown from parsed planning data.
        
        Parses the provided planning dictionary into a list of UserStory objects and a dependency order, validating required fields and mapping agent role strings to the AgentRole enum.
        
        Parameters:
            data (dict): Parsed JSON-like planning response expected to contain a "stories" list and optionally "dependency_order".
            max_stories (int): Maximum number of stories to process from `data["stories"]`. Defaults to 50.
        
        Returns:
            PRDBreakdown: A breakdown containing the validated list of UserStory instances and the dependency order (from `dependency_order` if present, otherwise the order of parsed stories).
        
        Raises:
            PlanningError: If the top-level "stories" key is missing, if any story is missing a required field ("id", "title", "description", "agent_role"), or if a story's `agent_role` string is not a recognized AgentRole.
        """
        if "stories" not in data:
            raise PlanningError(
                "Planning response missing 'stories' key",
                raw_response=json.dumps(data),
            )

        role_map = {r.value: r for r in AgentRole if r != AgentRole.DIRECTOR}
        stories: list[UserStory] = []

        for raw_story in data["stories"][:max_stories]:
            # Validate required fields
            for field_name in ("id", "title", "description", "agent_role"):
                if field_name not in raw_story:
                    raise PlanningError(
                        f"Story missing required field: {field_name}",
                        raw_response=json.dumps(raw_story),
                    )

            role_str = raw_story["agent_role"]
            if role_str not in role_map:
                raise PlanningError(
                    f"Unknown agent_role: {role_str}. "
                    f"Valid roles: {list(role_map.keys())}",
                    raw_response=json.dumps(raw_story),
                )

            stories.append(
                UserStory(
                    id=raw_story["id"],
                    title=raw_story["title"],
                    description=raw_story["description"],
                    agent_role=role_map[role_str],
                    depends_on=raw_story.get("depends_on", []),
                    acceptance_criteria=raw_story.get(
                        "acceptance_criteria", []
                    ),
                )
            )

        dependency_order = data.get("dependency_order", [s.id for s in stories])
        return PRDBreakdown(stories=stories, dependency_order=dependency_order)

    async def _plan_stories(self, prd_text: str) -> PRDBreakdown:
        """
        Decompose a product requirement document into a structured PRDBreakdown of user stories.
        
        Parameters:
            prd_text (str): The full PRD text to be decomposed into user stories.
        
        Returns:
            PRDBreakdown: The parsed planning result containing the list of UserStory objects and their dependency order.
        """
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

    # -----------------------------------------------------------------
    # Full PRD Execution
    # -----------------------------------------------------------------

    async def execute_prd(self, prd_text: str) -> ProjectReport:
        """
        Run the full PRD lifecycle: plan the PRD, register resulting stories, execute them in dependency order, and produce a ProjectReport.
        
        If planning with the LLM fails, does not raise but returns a ProjectReport containing the planning failure in `failures`.
        
        Returns:
            ProjectReport: immutable summary of the run containing the final stories, status_summary, `all_green` flag, elapsed_ms, any failures, and the number of instincts_learned.
        """
        start = time.time()
        failures: list[str] = []
        journal_count_before = len(self._journal.entries)

        # Step 1: Plan
        try:
            breakdown = await self._plan_stories(prd_text)
        except PlanningError as exc:
            elapsed = (time.time() - start) * 1000
            return ProjectReport(
                stories=(),
                status_summary={},
                all_green=False,
                elapsed_ms=elapsed,
                failures=(f"Planning failed: {exc}",),
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
                break
            if loop_count >= max_loops:
                failures.append("Dependency cycle detected — aborting")
                break
            loop_count += 1
            for story in ready:
                result = await self.run_story(story)
                if result.status == StoryStatus.FAILED:
                    failures.append(
                        f"{result.id}: {result.title} — FAILED"
                    )

        # Step 4: Build frozen report
        elapsed = (time.time() - start) * 1000
        summary = self.get_status_summary()
        instincts_learned = len(self._journal.entries) - journal_count_before
        return ProjectReport(
            stories=tuple(self._stories.values()),
            status_summary=summary,
            all_green=all(
                s.status == StoryStatus.GREEN
                for s in self._stories.values()
            ),
            elapsed_ms=elapsed,
            failures=tuple(failures),
            instincts_learned=instincts_learned,
        )