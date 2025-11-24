"""
Context Engineering for AI Agents - 2025 Best Practices

Per Anthropic's "Effective Context Engineering for AI Agents" (2025):
- Context compaction for long-horizon tasks
- Progressive disclosure of information
- Token-efficient tool descriptions
- Just-in-time context loading

References:
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://www.anthropic.com/engineering/claude-code-best-practices
- Per Truth Protocol Rule #1: Never guess - All patterns from official docs

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# Configuration via environment (per Truth Protocol Rule #15)
MAX_CONTEXT_TOKENS = int(os.getenv("AGENT_MAX_CONTEXT_TOKENS", "100000"))
COMPACTION_THRESHOLD = float(os.getenv("AGENT_COMPACTION_THRESHOLD", "0.7"))  # 70%
RECENT_FILES_LIMIT = int(os.getenv("AGENT_RECENT_FILES_LIMIT", "5"))


class ContextPriority(str, Enum):
    """Priority levels for context items."""

    CRITICAL = "critical"  # Must be preserved (errors, blockers)
    HIGH = "high"  # Important decisions, architecture
    MEDIUM = "medium"  # Implementation details
    LOW = "low"  # Verbose outputs, intermediate results


@dataclass
class ContextItem:
    """
    A single item in the agent's context window.

    Per Anthropic: "Good context engineering means finding the smallest
    possible set of high-signal tokens that maximize the likelihood
    of some desired outcome."
    """

    content: str
    priority: ContextPriority
    category: str  # e.g., "tool_output", "decision", "file_content"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    token_estimate: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""

    def __post_init__(self):
        """Calculate token estimate and content hash."""
        # Rough estimate: 1 token ≈ 4 characters
        self.token_estimate = len(self.content) // 4
        self.content_hash = hashlib.md5(self.content.encode()).hexdigest()[:8]


@dataclass
class CompactionResult:
    """Result of context compaction."""

    original_tokens: int
    compacted_tokens: int
    reduction_percentage: float
    preserved_items: int
    discarded_items: int
    summary: str


class ContextManager:
    """
    Manages agent context with intelligent compaction.

    Key strategies from Anthropic's engineering blog:
    1. Preserve architectural decisions and unresolved bugs
    2. Discard redundant tool outputs
    3. Keep most recently accessed files
    4. Compress verbose outputs into summaries
    """

    def __init__(
        self,
        max_tokens: int = MAX_CONTEXT_TOKENS,
        compaction_threshold: float = COMPACTION_THRESHOLD,
    ):
        self.max_tokens = max_tokens
        self.compaction_threshold = compaction_threshold
        self.context_items: list[ContextItem] = []
        self.recent_files: list[str] = []
        self._total_tokens = 0

    def add_context(
        self,
        content: str,
        priority: ContextPriority = ContextPriority.MEDIUM,
        category: str = "general",
        metadata: dict[str, Any] | None = None,
    ) -> ContextItem:
        """
        Add content to context window with priority-based management.

        Args:
            content: The content to add
            priority: Priority level for compaction decisions
            category: Category for filtering and analysis
            metadata: Additional metadata

        Returns:
            The created ContextItem
        """
        item = ContextItem(
            content=content,
            priority=priority,
            category=category,
            metadata=metadata or {},
        )

        self.context_items.append(item)
        self._total_tokens += item.token_estimate

        # Check if compaction needed
        if self._total_tokens > self.max_tokens * self.compaction_threshold:
            self._auto_compact()

        logger.debug(
            f"Added context item: {category} ({item.token_estimate} tokens, "
            f"priority={priority.value})"
        )

        return item

    def add_file_context(self, file_path: str, content: str) -> ContextItem:
        """
        Add file content with recent-file tracking.

        Per Anthropic: "Keep the five most recently accessed files."
        """
        # Update recent files list
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self.recent_files = self.recent_files[:RECENT_FILES_LIMIT]

        return self.add_context(
            content=content,
            priority=ContextPriority.HIGH,
            category="file_content",
            metadata={"file_path": file_path},
        )

    def add_tool_output(
        self,
        tool_name: str,
        output: str,
        is_error: bool = False,
    ) -> ContextItem:
        """
        Add tool output with appropriate priority.

        Errors get HIGH priority, successful outputs get MEDIUM/LOW.
        """
        priority = ContextPriority.HIGH if is_error else ContextPriority.LOW

        return self.add_context(
            content=output,
            priority=priority,
            category="tool_output",
            metadata={"tool_name": tool_name, "is_error": is_error},
        )

    def add_decision(self, decision: str, rationale: str) -> ContextItem:
        """
        Add architectural decision with HIGH priority.

        Per Anthropic: "Preserve architectural decisions."
        """
        content = f"DECISION: {decision}\nRATIONALE: {rationale}"

        return self.add_context(
            content=content,
            priority=ContextPriority.CRITICAL,
            category="decision",
        )

    def add_unresolved_issue(self, issue: str, context: str = "") -> ContextItem:
        """
        Add unresolved bug/issue with CRITICAL priority.

        Per Anthropic: "Preserve unresolved bugs."
        """
        content = f"UNRESOLVED ISSUE: {issue}"
        if context:
            content += f"\nCONTEXT: {context}"

        return self.add_context(
            content=content,
            priority=ContextPriority.CRITICAL,
            category="unresolved_issue",
        )

    def _auto_compact(self) -> CompactionResult:
        """
        Automatically compact context when threshold exceeded.

        Strategy:
        1. Keep all CRITICAL items
        2. Keep HIGH items from recent interactions
        3. Summarize MEDIUM items
        4. Discard most LOW items (keep last few)
        """
        original_count = len(self.context_items)
        original_tokens = self._total_tokens

        # Separate by priority
        critical = [i for i in self.context_items if i.priority == ContextPriority.CRITICAL]
        high = [i for i in self.context_items if i.priority == ContextPriority.HIGH]
        medium = [i for i in self.context_items if i.priority == ContextPriority.MEDIUM]
        low = [i for i in self.context_items if i.priority == ContextPriority.LOW]

        # Keep all critical items
        preserved = list(critical)

        # Keep recent HIGH items (last 10)
        preserved.extend(high[-10:])

        # Keep recent MEDIUM items (last 5)
        preserved.extend(medium[-5:])

        # Keep last 2 LOW items
        preserved.extend(low[-2:])

        # Calculate tokens
        new_tokens = sum(item.token_estimate for item in preserved)
        discarded_count = original_count - len(preserved)

        # Create summary of discarded content
        summary_parts = []
        if len(high) > 10:
            summary_parts.append(f"Compacted {len(high) - 10} HIGH-priority items")
        if len(medium) > 5:
            summary_parts.append(f"Compacted {len(medium) - 5} MEDIUM-priority items")
        if len(low) > 2:
            summary_parts.append(f"Discarded {len(low) - 2} LOW-priority items")

        summary = "; ".join(summary_parts) if summary_parts else "No compaction needed"

        # Add compaction summary as context
        if discarded_count > 0:
            compaction_note = ContextItem(
                content=f"[CONTEXT COMPACTED: {summary}]",
                priority=ContextPriority.MEDIUM,
                category="system",
            )
            preserved.append(compaction_note)

        # Update state
        self.context_items = preserved
        self._total_tokens = new_tokens + (
            compaction_note.token_estimate if discarded_count > 0 else 0
        )

        reduction = (1 - new_tokens / original_tokens) * 100 if original_tokens > 0 else 0

        logger.info(
            f"Context compacted: {original_tokens} → {new_tokens} tokens "
            f"({reduction:.1f}% reduction)"
        )

        return CompactionResult(
            original_tokens=original_tokens,
            compacted_tokens=new_tokens,
            reduction_percentage=reduction,
            preserved_items=len(preserved),
            discarded_items=discarded_count,
            summary=summary,
        )

    def get_context_window(self) -> str:
        """
        Get the current context window as a formatted string.

        Returns:
            Formatted context for inclusion in prompts
        """
        if not self.context_items:
            return ""

        sections = {}
        for item in self.context_items:
            if item.category not in sections:
                sections[item.category] = []
            sections[item.category].append(item.content)

        output_parts = []
        for category, contents in sections.items():
            output_parts.append(f"## {category.upper()}")
            output_parts.extend(contents)
            output_parts.append("")

        return "\n".join(output_parts)

    def get_stats(self) -> dict[str, Any]:
        """Get context statistics."""
        by_priority = {}
        by_category = {}

        for item in self.context_items:
            by_priority[item.priority.value] = by_priority.get(item.priority.value, 0) + 1
            by_category[item.category] = by_category.get(item.category, 0) + 1

        return {
            "total_items": len(self.context_items),
            "total_tokens": self._total_tokens,
            "max_tokens": self.max_tokens,
            "utilization_percent": (self._total_tokens / self.max_tokens) * 100,
            "by_priority": by_priority,
            "by_category": by_category,
            "recent_files": self.recent_files,
        }

    def clear(self):
        """Clear all context."""
        self.context_items = []
        self.recent_files = []
        self._total_tokens = 0


class ProgressiveDisclosure:
    """
    Progressive Disclosure for Agent Skills.

    Per Anthropic: "Like a well-organized manual that starts with a
    table of contents, skills let Claude load information only as needed."
    """

    def __init__(self, skills_directory: str | None = None):
        self.skills_directory = skills_directory or "config/agent_skills"
        self._skill_index: dict[str, dict] = {}
        self._loaded_skills: dict[str, str] = {}

    def register_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        tags: list[str],
        content_path: str | None = None,
        content: str | None = None,
    ):
        """
        Register a skill with minimal index information.

        The full content is only loaded when needed.
        """
        self._skill_index[skill_id] = {
            "name": name,
            "description": description,
            "tags": tags,
            "content_path": content_path,
            "content": content,  # For inline skills
        }

        logger.debug(f"Registered skill: {skill_id} ({name})")

    def get_skill_index(self) -> str:
        """
        Get a minimal skill index (table of contents).

        Returns only names and descriptions, not full content.
        """
        if not self._skill_index:
            return "No skills registered."

        lines = ["# Available Skills\n"]

        for skill_id, info in self._skill_index.items():
            lines.append(f"- **{info['name']}** (`{skill_id}`)")
            lines.append(f"  {info['description']}")
            lines.append(f"  Tags: {', '.join(info['tags'])}")
            lines.append("")

        return "\n".join(lines)

    def load_skill(self, skill_id: str) -> str | None:
        """
        Load full skill content on-demand.

        Per Anthropic: "Agents with a filesystem and code execution tools
        don't need to read the entirety of a skill into their context window."
        """
        if skill_id in self._loaded_skills:
            return self._loaded_skills[skill_id]

        if skill_id not in self._skill_index:
            logger.warning(f"Skill not found: {skill_id}")
            return None

        info = self._skill_index[skill_id]

        # Load from content or path
        if info.get("content"):
            content = info["content"]
        elif info.get("content_path"):
            try:
                with open(info["content_path"]) as f:
                    content = f.read()
            except FileNotFoundError:
                logger.error(f"Skill file not found: {info['content_path']}")
                return None
        else:
            logger.error(f"Skill {skill_id} has no content or path")
            return None

        self._loaded_skills[skill_id] = content
        logger.info(f"Loaded skill: {skill_id} ({len(content)} chars)")

        return content

    def search_skills(self, query: str) -> list[str]:
        """
        Search skills by name, description, or tags.

        Returns list of matching skill IDs.
        """
        query_lower = query.lower()
        matches = []

        for skill_id, info in self._skill_index.items():
            if (
                query_lower in info["name"].lower()
                or query_lower in info["description"].lower()
                or any(query_lower in tag.lower() for tag in info["tags"])
            ):
                matches.append(skill_id)

        return matches

    def unload_skill(self, skill_id: str):
        """Unload a skill to free memory."""
        if skill_id in self._loaded_skills:
            del self._loaded_skills[skill_id]
            logger.debug(f"Unloaded skill: {skill_id}")


class TokenBudgetManager:
    """
    Manages token budgets across agent operations.

    Per Anthropic: "LLMs are constrained by a finite attention budget."
    """

    def __init__(self, total_budget: int = MAX_CONTEXT_TOKENS):
        self.total_budget = total_budget
        self.allocations: dict[str, int] = {}
        self._used: dict[str, int] = {}

    def allocate(self, category: str, tokens: int) -> bool:
        """
        Allocate tokens to a category.

        Returns True if allocation successful, False if over budget.
        """
        current_used = sum(self._used.values())
        if current_used + tokens > self.total_budget:
            logger.warning(
                f"Token allocation rejected: {category} requested {tokens}, "
                f"but only {self.total_budget - current_used} available"
            )
            return False

        self.allocations[category] = tokens
        return True

    def use(self, category: str, tokens: int) -> bool:
        """Record token usage for a category."""
        if category not in self.allocations:
            # Auto-allocate if not pre-allocated
            self.allocations[category] = tokens

        current = self._used.get(category, 0)
        if current + tokens > self.allocations[category]:
            logger.warning(
                f"Token budget exceeded for {category}: "
                f"{current + tokens} > {self.allocations[category]}"
            )
            return False

        self._used[category] = current + tokens
        return True

    def get_remaining(self, category: str) -> int:
        """Get remaining tokens for a category."""
        allocated = self.allocations.get(category, 0)
        used = self._used.get(category, 0)
        return max(0, allocated - used)

    def get_total_remaining(self) -> int:
        """Get total remaining budget."""
        return self.total_budget - sum(self._used.values())

    def get_stats(self) -> dict[str, Any]:
        """Get budget statistics."""
        return {
            "total_budget": self.total_budget,
            "total_used": sum(self._used.values()),
            "total_remaining": self.get_total_remaining(),
            "by_category": {
                cat: {
                    "allocated": self.allocations.get(cat, 0),
                    "used": self._used.get(cat, 0),
                    "remaining": self.get_remaining(cat),
                }
                for cat in set(list(self.allocations.keys()) + list(self._used.keys()))
            },
        }


# Global instances
_context_manager: ContextManager | None = None
_progressive_disclosure: ProgressiveDisclosure | None = None


def get_context_manager() -> ContextManager:
    """Get global context manager instance."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def get_progressive_disclosure() -> ProgressiveDisclosure:
    """Get global progressive disclosure instance."""
    global _progressive_disclosure
    if _progressive_disclosure is None:
        _progressive_disclosure = ProgressiveDisclosure()
    return _progressive_disclosure


__all__ = [
    "ContextItem",
    "ContextManager",
    "ContextPriority",
    "CompactionResult",
    "ProgressiveDisclosure",
    "TokenBudgetManager",
    "get_context_manager",
    "get_progressive_disclosure",
]
