"""Consolidator — close a conversation thread into durable agent memories.

The pattern:
    1. Read the full chronological thread log from ``ConversationStore``
    2. Ask an LLM to summarize into 3-5 durable facts (preferences, decisions,
       commitments — not chitchat)
    3. Write each fact as a high-importance ``Memory`` in the agent's namespace

This is what separates "chat with retention" from "agent that learns."
Without consolidation, the agent's long-term namespace fills with raw
conversation chunks and recall returns noise; with it, the namespace becomes
a curated set of durable facts that improves agent behavior over time.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from skyyrose.core.memory.agent_memory import AgentMemory
from skyyrose.core.memory.conversation import ConversationStore

logger = logging.getLogger(__name__)


# Type alias for the LLM summarization callable. Decouples this module from
# any specific LLM client (Anthropic / OpenAI / Gemini / local) — the caller
# wires up whichever one they want.
SummarizeFn = Callable[[str], Awaitable[str]]


DEFAULT_PROMPT = """\
Summarize the following conversation transcript into 3-5 durable facts that \
capture the user's preferences, decisions, and key context. Each fact should \
be:
- A single self-contained sentence
- About the USER or the project, not about the conversation itself
- Specific enough to be useful in a future conversation

Format: each fact on its own line, prefixed with '- '.

Skip chitchat, acknowledgments, and information already captured in the \
project's source code or docs.

<transcript>
{transcript}
</transcript>

Facts:
"""


async def consolidate_thread(
    thread_id: str,
    *,
    conversation_store: ConversationStore,
    agent_memory: AgentMemory,
    summarize_fn: SummarizeFn,
    importance: float = 0.8,
    prompt_template: str = DEFAULT_PROMPT,
) -> list[str]:
    """Read a thread, summarize it via LLM, write durable agent memories.

    Args:
        thread_id: the conversation thread to consolidate
        conversation_store: source of the chronological log
        agent_memory: destination for the durable facts (writes to its namespace)
        summarize_fn: async callable that takes a prompt and returns a completion
        importance: importance score for each consolidated fact (default 0.8 —
            consolidated facts are intentionally above the 0.5 ``remember`` default
            so they survive future importance-floored recalls)
        prompt_template: format string with a ``{transcript}`` placeholder

    Returns:
        List of memory_ids that were written to ``agent_memory``.
    """
    turns = await conversation_store.thread_log(thread_id)
    if not turns:
        logger.info(
            "consolidate_thread: thread %s has no turns; nothing to consolidate",
            thread_id,
        )
        return []

    transcript = "\n".join(f"{t.role}: {t.content}" for t in turns)
    prompt = prompt_template.format(transcript=transcript)

    summary = await summarize_fn(prompt)
    facts = _parse_facts(summary)

    if not facts:
        logger.warning(
            "consolidate_thread: summarizer returned no parseable facts for "
            "thread %s. Raw summary length=%d.",
            thread_id,
            len(summary),
        )
        return []

    memory_ids: list[str] = []
    for fact in facts:
        mid = await agent_memory.remember(
            content=fact,
            importance=importance,
            tags=["consolidated"],
            metadata={"source": "consolidator", "thread_id": thread_id},
        )
        memory_ids.append(mid)

    logger.info(
        "consolidate_thread: wrote %d facts for thread %s into ns=%s",
        len(memory_ids),
        thread_id,
        agent_memory.namespace,
    )
    return memory_ids


def _parse_facts(summary: str) -> list[str]:
    """Extract bullet-prefixed facts from a free-form summary.

    Tolerates ``- ``, ``* ``, ``• `` prefixes and trims whitespace. Lines
    without a recognized prefix are dropped — keeps "Facts:" preambles or
    closing paragraphs out of the output.
    """
    facts: list[str] = []
    for raw in summary.splitlines():
        line = raw.strip()
        if not line:
            continue
        for prefix in ("- ", "* ", "• "):
            if line.startswith(prefix):
                stripped = line[len(prefix) :].strip()
                if stripped:
                    facts.append(stripped)
                break
    return facts


__all__ = ["consolidate_thread", "SummarizeFn", "DEFAULT_PROMPT"]
