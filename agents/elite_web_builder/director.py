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
        Initialize the PlanningError with an error message and the raw planning response.
        
        Parameters:
            message (str): Human-readable error message describing the parsing failure.
            raw_response (str): The original raw response text from the planner (may contain malformed JSON); stored for debugging.
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
        Create an AgentRuntime that uses the provided ModelRouter to route and execute agent requests.
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
        Route the given task to the agent described by `spec` and return the model's response.
        
        Returns:
            LLMResponse: Response produced by the routed model.
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
        Initialize a Director coordinating PRD decomposition, story execution, verification, self-healing, and learning journaling.
        
        Parameters:
            config (DirectorConfig | None): Director settings; when None a default DirectorConfig is created.
            router (ModelRouter | None): ModelRouter used for agent routing; when None a ModelRouter is constructed using the module's default routing and fallbacks.
            journal (LearningJournal | None): LearningJournal used to record instincts/observations; when None a new LearningJournal is created.
            healer (SelfHealer | None): Self-healing component used to diagnose and attempt repairs on failed story outputs; when None a SelfHealer is created using `config.max_heal_attempts`.
            verifier (VerificationLoop | None): Verification component used to validate agent outputs; when None a default VerificationLoop is created.
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
        """
        Return a read-only copy of the director's story mapping keyed by story ID.
        
        Returns:
            dict[str, UserStory]: A shallow copy of the internal stories mapping where keys are story IDs and values are UserStory instances.
        """
        return dict(self._stories)

    @property
    def router(self) -> ModelRouter:
        """
        Expose the Director's ModelRouter instance.
        
        Returns:
            model_router (ModelRouter): The underlying ModelRouter used to route model requests.
        """
        return self._router

    # -----------------------------------------------------------------
    # Story Management
    # -----------------------------------------------------------------

    def add_stories(self, stories: list[UserStory]) -> None:
        """Register stories for execution."""
        for story in stories:
            self._stories[story.id] = story
            logger.info("Registered story %s: %s", story.id, story.title)

    def get_ready_stories(self) -> list[UserStory]:
        """
        Selects PENDING user stories whose dependencies are all marked GREEN.
        
        Returns:
            ready_stories (list[UserStory]): List of UserStory objects that currently have status
            StoryStatus.PENDING and whose every dependency ID in `depends_on` refers to a story
            with status StoryStatus.GREEN.
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
        Return a mapping of story status values to their counts.
        
        Returns:
            dict[str, int]: A dictionary where each key is a StoryStatus enum value string and each value is the number of stories with that status.
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
        Execute a UserStory by dispatching its task to the appropriate agent and updating the story's lifecycle.
        
        This will set the story's status to IN_PROGRESS, run the task through the configured agent runtime, optionally run verification and attempt self-healing if verification fails, and then set the story's final status to GREEN or FAILED while populating `output` and `error` as applicable.
        
        Returns:
            The same UserStory instance updated with final `status`, `output`, and `error`.
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
        """
        Parse an LLM planning response and return the decoded JSON object.
        
        Accepts either raw JSON or JSON enclosed in markdown code fences; strips common fence markers before attempting to parse.
        
        Parameters:
            raw (str): The raw text returned by the planning LLM (may include markdown code fences).
        
        Returns:
            dict: The parsed JSON object.
        
        Raises:
            PlanningError: If the input cannot be parsed as JSON; the original raw response is attached to the error.
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
        Builds a PRDBreakdown from a parsed planning response dictionary.
        
        Parameters:
            data (dict): Parsed planning response expected to contain a "stories" key with a list of story objects. Each story object must include the keys: "id", "title", "description", and "agent_role". May optionally include "depends_on" (list) and "acceptance_criteria" (list). The top-level "dependency_order" may be provided as a list of story IDs; if omitted, the returned dependency_order preserves the story list order.
            max_stories (int): Maximum number of stories to process from `data["stories"]`. Stories beyond this count are ignored.
        
        Returns:
            PRDBreakdown: Container with `stories` converted to UserStory instances and `dependency_order` as a list of story IDs.
        
        Raises:
            PlanningError: If required top-level or per-story fields are missing, or if a story's `agent_role` is not a recognized AgentRole. The raised error includes the raw planning response for debugging.
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
        Decompose a product requirements document (PRD) into a PRDBreakdown of user stories.
        
        Parameters:
            prd_text (str): The PRD content to decompose.
        
        Returns:
            PRDBreakdown: Parsed and validated breakdown containing the list of user stories and their dependency order.
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
        Run a full PRD lifecycle: decompose the PRD into user stories, register them, execute stories in dependency order, and produce a final ProjectReport.
        
        On planning failures the function returns a ProjectReport describing the failure instead of raising.
        
        Returns:
            ProjectReport: Immutable report containing all executed stories, a status summary, whether all stories are green, elapsed time in milliseconds, any failures encountered, and the number of learning journal entries added during execution.
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