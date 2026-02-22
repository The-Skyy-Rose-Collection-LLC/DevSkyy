"""
Agent execution runtime — the bridge from AgentSpec to LLM execution.

Takes an AgentSpec + task, resolves the model via ModelRouter, builds the
full prompt (system + knowledge refs + learning context), calls the LLM
via the appropriate provider adapter, and returns an AgentOutput.

This is the missing layer between the agent specifications (static config)
and actual LLM-powered execution. The Director delegates to this runtime
for every story execution.

Usage:
    runtime = AgentRuntime(router=router, validator=validator, journal=journal)
    output = await runtime.execute(
        spec=FRONTEND_DEV_SPEC,
        task="Create a responsive navigation component",
        story_id="US-001",
    )
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from agents.base import AgentOutput, AgentSpec
from agents.provider_adapters import LLMMessage, LLMResponse, get_adapter
from core.ground_truth import GroundTruthValidator
from core.learning_journal import LearningJournal
from core.model_router import ModelRouter, RouteResult

logger = logging.getLogger(__name__)

# Regex for extracting file paths from LLM output
_FILE_REF = re.compile(r"`([a-zA-Z0-9_\-./]+\.[a-zA-Z]{1,10})`")


class AgentRuntime:
    """
    Executes agent tasks by routing to the correct LLM provider.

    Responsibilities:
    1. Build full prompt from spec (system + knowledge + learning context)
    2. Resolve provider/model via ModelRouter (health-aware fallback)
    3. Call LLM via provider adapter
    4. Parse response and extract file references
    5. Return immutable AgentOutput

    The runtime does NOT validate claims against ground truth — that's the
    Director's job (via the verification loop). The runtime just gets the
    LLM response and packages it.
    """

    def __init__(
        self,
        router: ModelRouter,
        validator: GroundTruthValidator,
        journal: LearningJournal,
    ) -> None:
        self._router = router
        self._validator = validator
        self._journal = journal

    # -- Prompt building --

    def _build_messages(
        self,
        spec: AgentSpec,
        task: str,
    ) -> list[LLMMessage]:
        """Build the full message list for an LLM call.

        Structure:
        1. System message = spec.system_prompt + knowledge refs + learning context
        2. User message = the actual task

        Args:
            spec: Agent specification with system prompt and knowledge files
            task: The task description / user story to execute

        Returns:
            List of LLMMessage in [system, user] order
        """
        # Build system prompt with learning context
        learning_context = self._journal.generate_context(spec.name)
        system_prompt = spec.build_prompt(learning_context)

        # Append knowledge file references
        if spec.knowledge_files:
            refs = "\n".join(f"- {f}" for f in spec.knowledge_files)
            system_prompt += f"\n\nReference knowledge files:\n{refs}"

        return [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=task),
        ]

    # -- File extraction --

    @staticmethod
    def _extract_files(content: str) -> tuple[str, ...]:
        """Extract file paths mentioned in backtick-quoted references.

        Looks for patterns like `theme.json`, `functions.php`, etc.

        Args:
            content: LLM response text

        Returns:
            Tuple of unique file paths found
        """
        if not content:
            return ()

        matches = _FILE_REF.findall(content)
        if not matches:
            return ()

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                unique.append(m)

        return tuple(unique)

    # -- Execution --

    async def execute(
        self,
        spec: AgentSpec,
        task: str,
        story_id: str = "",
    ) -> AgentOutput:
        """Execute an agent task by calling the appropriate LLM.

        Steps:
        1. Resolve provider/model via ModelRouter
        2. Build prompt from spec + learning context
        3. Call LLM via adapter
        4. On failure, try fallback provider
        5. Extract file references from response
        6. Return AgentOutput

        Args:
            spec: Agent specification (role, prompt, capabilities)
            task: Task description to execute
            story_id: Optional story ID for tracking

        Returns:
            AgentOutput with response content and metadata

        Raises:
            RuntimeError: If all providers and fallbacks are exhausted
        """
        messages = self._build_messages(spec, task)
        route = self._router.resolve(spec.name)

        logger.info(
            "AgentRuntime: executing %s → %s/%s (fallback=%s)",
            spec.name,
            route.provider,
            route.model,
            route.is_fallback,
        )

        # Try primary provider
        response = await self._try_provider(route, messages)

        if response is not None:
            return self._build_output(
                spec=spec,
                story_id=story_id,
                response=response,
                is_fallback=route.is_fallback,
            )

        # Primary failed — try fallback
        logger.warning(
            "AgentRuntime: primary %s failed, trying fallback",
            route.provider,
        )
        fallback_config = self._router.get_fallback(route.provider)
        fallback_route = RouteResult(
            provider=fallback_config.provider,
            model=fallback_config.model,
            is_fallback=True,
        )

        response = await self._try_provider(fallback_route, messages)

        if response is not None:
            return self._build_output(
                spec=spec,
                story_id=story_id,
                response=response,
                is_fallback=True,
            )

        # All exhausted
        raise RuntimeError(
            f"All providers exhausted for agent '{spec.name}'. "
            f"Tried: {route.provider}, {fallback_config.provider}"
        )

    async def _try_provider(
        self,
        route: RouteResult,
        messages: list[LLMMessage],
    ) -> LLMResponse | None:
        """Try calling a single provider. Returns None on failure."""
        try:
            adapter = get_adapter(route.provider)
            start = time.time()
            response = await adapter.call(route.model, messages)
            elapsed = time.time() - start

            self._router.record_success(route.provider)
            self._router.record_latency(route.provider, elapsed)

            logger.info(
                "AgentRuntime: %s/%s responded in %.1fs (%d tokens)",
                route.provider,
                route.model,
                elapsed,
                response.usage.get("output_tokens", 0),
            )
            return response

        except Exception as exc:
            self._router.record_failure(route.provider)
            logger.warning(
                "AgentRuntime: %s/%s failed: %s",
                route.provider,
                route.model,
                exc,
            )
            return None

    def _build_output(
        self,
        spec: AgentSpec,
        story_id: str,
        response: LLMResponse,
        is_fallback: bool,
    ) -> AgentOutput:
        """Build an AgentOutput from a successful LLM response."""
        files = self._extract_files(response.text)

        return AgentOutput(
            agent=spec.name,
            story_id=story_id,
            content=response.text,
            files_changed=files,
            metadata={
                "provider": response.provider,
                "model": response.model,
                "usage": dict(response.usage),
                "is_fallback": is_fallback,
            },
        )
