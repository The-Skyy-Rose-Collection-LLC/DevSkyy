"""Agent memory layer — three concerns separated by access pattern.

- ``ConversationStore``: chronological turn buffer (SQLite, per-thread)
- ``AgentMemory``: semantic long-term memory (vector store, per-agent namespace)
- ``consolidate_thread``: close-of-thread LLM summarization that turns
  conversation history into durable ``AgentMemory`` entries

The split is deliberate. "Last N turns" is a B-tree-on-timestamp question,
not a similarity question — embedding turns wastes money and adds latency
for zero retrieval benefit. The vector store is for "find anything similar
to this," the SQLite store is for "what just happened."
"""

from skyyrose.core.memory.agent_memory import (
    DEFAULT_NAMESPACE_PREFIX,
    AgentMemory,
    Memory,
)
from skyyrose.core.memory.consolidator import (
    DEFAULT_PROMPT,
    SummarizeFn,
    consolidate_thread,
)
from skyyrose.core.memory.conversation import (
    DEFAULT_DB_PATH,
    ConversationStore,
    ConversationTurn,
)

__all__ = [
    "AgentMemory",
    "ConversationStore",
    "ConversationTurn",
    "DEFAULT_DB_PATH",
    "DEFAULT_NAMESPACE_PREFIX",
    "DEFAULT_PROMPT",
    "Memory",
    "SummarizeFn",
    "consolidate_thread",
]
