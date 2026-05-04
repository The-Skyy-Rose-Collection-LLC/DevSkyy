"""AgentMemory — per-agent semantic long-term memory.

Each agent has an isolated namespace in the shared vector store
(``"memory:agent:<agent_id>"``). Memories are embedded with the configured
embedding engine and stored alongside metadata (importance, tags, source,
created_at). Recall is semantic — for chronological "last N turns" use
``ConversationStore`` instead.

The split between ``AgentMemory`` (semantic, vector-backed) and
``ConversationStore`` (chronological, SQLite-backed) is deliberate. Embedding
every conversation turn for chronological recall wastes money and adds
latency for zero retrieval benefit. Use the right tool for the access pattern.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from orchestration.embedding_engine import BaseEmbeddingEngine
from orchestration.vector_store import BaseVectorStore, Document

logger = logging.getLogger(__name__)


DEFAULT_NAMESPACE_PREFIX = "memory:agent"


@dataclass
class Memory:
    """A single durable agent memory."""

    memory_id: str
    agent_id: str
    content: str
    importance: float
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    score: float = 0.0  # similarity score from recall (0 if unset)


class AgentMemory:
    """Per-agent semantic memory store backed by a vector store namespace.

    Usage:
        memory = AgentMemory(
            agent_id="compositor_agent",
            vector_store=store,  # already initialized
            embedder=embedder,   # already initialized
        )
        mid = await memory.remember(
            "Corey prefers Black Rose embroidery on left chest, not centered",
            tags=["preferences", "embroidery"],
            importance=0.9,
        )
        relevant = await memory.recall("where should the BR logo go?", k=3)
    """

    def __init__(
        self,
        agent_id: str,
        vector_store: BaseVectorStore,
        embedder: BaseEmbeddingEngine,
        namespace_prefix: str = DEFAULT_NAMESPACE_PREFIX,
    ) -> None:
        if not agent_id or ":" in agent_id:
            raise ValueError(f"agent_id must be a non-empty string without ':' (got {agent_id!r})")
        self.agent_id = agent_id
        self._store = vector_store
        self._embedder = embedder
        self._namespace = f"{namespace_prefix}:{agent_id}"

    @property
    def namespace(self) -> str:
        """The vector-store namespace this AgentMemory writes to."""
        return self._namespace

    async def remember(
        self,
        content: str,
        *,
        tags: list[str] | None = None,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Store a new memory, returning its memory_id.

        Args:
            content: the memory text (will be embedded with the configured engine)
            tags: optional categorical tags for filtering or future analysis
            importance: 0.0..1.0; higher means "keep this longer when consolidating"
            metadata: arbitrary structured attachments (e.g. source thread_id).
                Only str/int/float/bool values survive — other types are dropped
                because Pinecone metadata only supports those primitives.
        """
        if not 0.0 <= importance <= 1.0:
            raise ValueError(f"importance must be in [0.0, 1.0], got {importance}")

        memory_id = f"mem:{self.agent_id}:{uuid4().hex[:16]}"
        created_at = datetime.now(UTC)

        embedding = await self._embedder.embed_text(content)

        # Filter metadata to vector-store-safe types (str/int/float/bool)
        safe_metadata: dict[str, Any] = {
            "agent_id": self.agent_id,
            "importance": float(importance),
            "tags_csv": ",".join(tags) if tags else "",
            "created_at_ts": created_at.timestamp(),
        }
        if metadata:
            safe_metadata.update(
                {k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}
            )

        document = Document(
            id=memory_id,
            content=content,
            metadata=safe_metadata,
            source=f"agent_memory:{self.agent_id}",
            created_at=created_at,
        )

        await self._store.add_documents([document], [embedding], namespace=self._namespace)
        logger.info(
            "AgentMemory.remember: stored %s (importance=%.2f, ns=%s)",
            memory_id,
            importance,
            self._namespace,
        )
        return memory_id

    async def recall(
        self,
        query: str,
        *,
        k: int = 5,
        min_importance: float | None = None,
    ) -> list[Memory]:
        """Semantically retrieve the top-k memories matching ``query``.

        Args:
            query: free-form natural language
            k: max memories to return (post-filter)
            min_importance: optional floor on importance (filtered post-search,
                so the underlying top_k may pull more candidates to compensate)
        """
        # If min_importance is set, pull a wider net to survive post-filtering
        search_k = k * 3 if min_importance is not None else k

        query_embedding = await self._embedder.embed_query(query)

        results = await self._store.search(
            query_embedding=query_embedding,
            top_k=search_k,
            namespace=self._namespace,
        )

        memories: list[Memory] = []
        for r in results:
            if len(memories) >= k:
                break
            meta = r.document.metadata or {}
            importance = float(meta.get("importance", 0.5))
            if min_importance is not None and importance < min_importance:
                continue

            tags_csv = meta.get("tags_csv", "")
            tags = [t for t in tags_csv.split(",") if t] if tags_csv else []

            ts = meta.get("created_at_ts")
            created_at = datetime.fromtimestamp(ts, tz=UTC) if ts else datetime.now(UTC)

            memories.append(
                Memory(
                    memory_id=r.document.id,
                    agent_id=meta.get("agent_id", self.agent_id),
                    content=r.document.content,
                    importance=importance,
                    tags=tags,
                    metadata={
                        k: v
                        for k, v in meta.items()
                        if k not in {"agent_id", "importance", "tags_csv", "created_at_ts"}
                    },
                    created_at=created_at,
                    score=r.score,
                )
            )
        return memories

    async def forget(self, memory_id: str) -> int:
        """Delete a single memory by id; returns rows deleted (0 or 1)."""
        return await self._store.delete_documents([memory_id], namespace=self._namespace)

    async def forget_many(self, memory_ids: list[str]) -> int:
        """Delete multiple memories by id; returns rows deleted."""
        if not memory_ids:
            return 0
        return await self._store.delete_documents(memory_ids, namespace=self._namespace)


__all__ = ["AgentMemory", "Memory", "DEFAULT_NAMESPACE_PREFIX"]
