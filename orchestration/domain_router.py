"""
Domain-Specific LLM Router
==========================

Routes LLM requests to optimal providers based on domain/task type.

Domain Routing Matrix:
| Domain            | Primary LLM    | Fallback LLM | Rationale              |
|-------------------|----------------|--------------|------------------------|
| Code Generation   | Claude         | GPT-4o       | Best coding accuracy   |
| Web Design        | Gemini         | Claude       | Visual understanding   |
| Product Content   | GPT-4o         | Claude       | Marketing copy quality |
| Fast Inference    | Groq           | Mistral      | Sub-300ms latency      |
| RAG & Search      | Cohere         | Claude       | Native RAG capabilities|

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from llm import LLMRouter, Message, ModelProvider

logger = logging.getLogger(__name__)


class TaskDomain(str, Enum):
    """Task domains for LLM routing."""

    CODE_GENERATION = "code_generation"
    WEB_DESIGN = "web_design"
    PRODUCT_CONTENT = "product_content"
    FAST_INFERENCE = "fast_inference"
    RAG_SEARCH = "rag_search"
    GENERAL = "general"


@dataclass
class DomainConfig:
    """Configuration for a task domain."""

    domain: TaskDomain
    primary_provider: ModelProvider
    primary_model: str
    fallback_provider: ModelProvider | None = None
    fallback_model: str | None = None
    description: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7


# Domain routing configuration
DOMAIN_CONFIGS: dict[TaskDomain, DomainConfig] = {
    TaskDomain.CODE_GENERATION: DomainConfig(
        domain=TaskDomain.CODE_GENERATION,
        primary_provider=ModelProvider.ANTHROPIC,
        primary_model="claude-sonnet-4-20250514",
        fallback_provider=ModelProvider.OPENAI,
        fallback_model="gpt-4o",
        description="Code generation, debugging, refactoring",
        max_tokens=8192,
        temperature=0.3,
    ),
    TaskDomain.WEB_DESIGN: DomainConfig(
        domain=TaskDomain.WEB_DESIGN,
        primary_provider=ModelProvider.GOOGLE,
        primary_model="gemini-2.0-flash",
        fallback_provider=ModelProvider.ANTHROPIC,
        fallback_model="claude-sonnet-4-20250514",
        description="Web templates, CSS, visual design",
        max_tokens=4096,
        temperature=0.5,
    ),
    TaskDomain.PRODUCT_CONTENT: DomainConfig(
        domain=TaskDomain.PRODUCT_CONTENT,
        primary_provider=ModelProvider.OPENAI,
        primary_model="gpt-4o",
        fallback_provider=ModelProvider.ANTHROPIC,
        fallback_model="claude-sonnet-4-20250514",
        description="Product descriptions, marketing copy",
        max_tokens=2048,
        temperature=0.8,
    ),
    TaskDomain.FAST_INFERENCE: DomainConfig(
        domain=TaskDomain.FAST_INFERENCE,
        primary_provider=ModelProvider.GROQ,
        primary_model="llama-3.3-70b-versatile",
        fallback_provider=ModelProvider.MISTRAL,
        fallback_model="mistral-small-latest",
        description="Real-time chat, streaming responses",
        max_tokens=1024,
        temperature=0.7,
    ),
    TaskDomain.RAG_SEARCH: DomainConfig(
        domain=TaskDomain.RAG_SEARCH,
        primary_provider=ModelProvider.COHERE,
        primary_model="command-r-08-2024",
        fallback_provider=ModelProvider.ANTHROPIC,
        fallback_model="claude-sonnet-4-20250514",
        description="Document retrieval, search queries",
        max_tokens=4096,
        temperature=0.3,
    ),
    TaskDomain.GENERAL: DomainConfig(
        domain=TaskDomain.GENERAL,
        primary_provider=ModelProvider.OPENAI,
        primary_model="gpt-4o-mini",
        fallback_provider=ModelProvider.GROQ,
        fallback_model="llama-3.3-70b-versatile",
        description="General purpose tasks",
        max_tokens=4096,
        temperature=0.7,
    ),
}

# File path patterns for domain detection (ordered by specificity)
PATH_PATTERNS: list[tuple[TaskDomain, str]] = [
    # Product content patterns (most specific - check first)
    (TaskDomain.PRODUCT_CONTENT, r"product"),
    (TaskDomain.PRODUCT_CONTENT, r"catalog"),
    (TaskDomain.PRODUCT_CONTENT, r"description"),

    # Web design patterns
    (TaskDomain.WEB_DESIGN, r"/wordpress/"),
    (TaskDomain.WEB_DESIGN, r"/templates/"),
    (TaskDomain.WEB_DESIGN, r"/elementor/"),
    (TaskDomain.WEB_DESIGN, r"\.html$"),
    (TaskDomain.WEB_DESIGN, r"\.css$"),
    (TaskDomain.WEB_DESIGN, r"\.scss$"),
    (TaskDomain.WEB_DESIGN, r"\.json$"),

    # Code generation patterns (less specific - check last)
    (TaskDomain.CODE_GENERATION, r"/orchestration/"),
    (TaskDomain.CODE_GENERATION, r"/llm/"),
    (TaskDomain.CODE_GENERATION, r"/security/"),
    (TaskDomain.CODE_GENERATION, r"/api/"),
    (TaskDomain.CODE_GENERATION, r"/agents/"),
    (TaskDomain.CODE_GENERATION, r"/runtime/"),
    (TaskDomain.CODE_GENERATION, r"base\.py$"),
    (TaskDomain.CODE_GENERATION, r"\.py$"),
]


@dataclass
class DomainRouter:
    """
    Domain-specific LLM router.

    Routes requests to optimal LLM providers based on task domain.

    Usage:
        router = DomainRouter()

        # Route by file path
        response = await router.complete_for_path(
            "/orchestration/llm_orchestrator.py",
            messages=[Message.user("Refactor this function...")]
        )

        # Route by explicit domain
        response = await router.complete_for_domain(
            TaskDomain.PRODUCT_CONTENT,
            messages=[Message.user("Write a product description...")]
        )
    """

    llm_router: LLMRouter = field(default_factory=LLMRouter)

    def detect_domain(self, file_path: str | None = None, task_hint: str | None = None) -> TaskDomain:
        """
        Detect the task domain from file path or task hint.

        Args:
            file_path: Path to file being worked on
            task_hint: Optional hint about the task type

        Returns:
            Detected TaskDomain
        """
        # Check task hints first
        if task_hint:
            hint_lower = task_hint.lower()
            if any(kw in hint_lower for kw in ["code", "function", "class", "refactor", "debug", "python"]):
                return TaskDomain.CODE_GENERATION
            if any(kw in hint_lower for kw in ["html", "css", "template", "design", "layout", "elementor"]):
                return TaskDomain.WEB_DESIGN
            if any(kw in hint_lower for kw in ["product", "description", "marketing", "copy", "catalog"]):
                return TaskDomain.PRODUCT_CONTENT
            if any(kw in hint_lower for kw in ["fast", "quick", "chat", "streaming", "realtime"]):
                return TaskDomain.FAST_INFERENCE
            if any(kw in hint_lower for kw in ["search", "retrieve", "rag", "document", "query"]):
                return TaskDomain.RAG_SEARCH

        # Check file path patterns (in order of specificity)
        if file_path:
            path_str = str(file_path).replace("\\", "/")

            for domain, pattern in PATH_PATTERNS:
                if re.search(pattern, path_str, re.IGNORECASE):
                    logger.debug(f"Domain {domain.value} matched by pattern '{pattern}'")
                    return domain

        return TaskDomain.GENERAL

    def get_config(self, domain: TaskDomain) -> DomainConfig:
        """Get configuration for a domain."""
        return DOMAIN_CONFIGS.get(domain, DOMAIN_CONFIGS[TaskDomain.GENERAL])

    async def complete_for_domain(
        self,
        domain: TaskDomain,
        messages: list[Message],
        **kwargs: Any,
    ) -> Any:
        """
        Complete a request using the optimal provider for a domain.

        Args:
            domain: Task domain
            messages: Chat messages
            **kwargs: Additional arguments passed to LLM

        Returns:
            LLM response
        """
        config = self.get_config(domain)

        # Set defaults from domain config
        kwargs.setdefault("max_tokens", config.max_tokens)
        kwargs.setdefault("temperature", config.temperature)

        try:
            response = await self.llm_router.complete(
                messages=messages,
                provider=config.primary_provider,
                model=config.primary_model,
                **kwargs,
            )
            logger.info(
                f"Domain {domain.value}: {config.primary_provider.value} "
                f"({config.primary_model}) - {response.latency_ms:.0f}ms"
            )
            return response

        except Exception as e:
            logger.warning(f"Primary provider failed: {e}")

            # Try fallback
            if config.fallback_provider and config.fallback_model:
                logger.info(f"Falling back to {config.fallback_provider.value}")
                return await self.llm_router.complete(
                    messages=messages,
                    provider=config.fallback_provider,
                    model=config.fallback_model,
                    **kwargs,
                )
            raise

    async def complete_for_path(
        self,
        file_path: str,
        messages: list[Message],
        task_hint: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Complete a request using provider optimal for file path.

        Args:
            file_path: Path to file being worked on
            messages: Chat messages
            task_hint: Optional hint about the task
            **kwargs: Additional arguments

        Returns:
            LLM response with domain metadata
        """
        domain = self.detect_domain(file_path, task_hint)
        response = await self.complete_for_domain(domain, messages, **kwargs)

        # Add domain metadata
        response.metadata = response.metadata or {}
        response.metadata["domain"] = domain.value
        response.metadata["file_path"] = file_path

        return response

    async def complete_fast(
        self,
        messages: list[Message],
        **kwargs: Any,
    ) -> Any:
        """Quick completion using fastest provider (Groq)."""
        kwargs.setdefault("max_tokens", 1024)
        return await self.complete_for_domain(TaskDomain.FAST_INFERENCE, messages, **kwargs)

    async def complete_code(
        self,
        messages: list[Message],
        **kwargs: Any,
    ) -> Any:
        """Code completion using Claude."""
        kwargs.setdefault("max_tokens", 8192)
        kwargs.setdefault("temperature", 0.3)
        return await self.complete_for_domain(TaskDomain.CODE_GENERATION, messages, **kwargs)

    async def complete_content(
        self,
        messages: list[Message],
        **kwargs: Any,
    ) -> Any:
        """Marketing content using GPT-4o."""
        kwargs.setdefault("temperature", 0.8)
        return await self.complete_for_domain(TaskDomain.PRODUCT_CONTENT, messages, **kwargs)

    async def close(self) -> None:
        """Close underlying LLM router."""
        await self.llm_router.close()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "DomainRouter",
    "DomainConfig",
    "TaskDomain",
    "DOMAIN_CONFIGS",
]

