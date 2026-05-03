"""
Tests for AgentMemory (skyyrose.core.memory.agent_memory).
==========================================================

AgentMemory is the per-agent semantic long-term store. It composes:
- a vector store (for embedding storage + similarity search), and
- an embedding engine (to encode memory content + recall queries).

We test AgentMemory's CONTRACTS, not the underlying ChromaDB or any specific
embedding model. We use:
- a real ChromaVectorStore on tmp_path (cheap, deterministic, exercises real
  namespace isolation logic), and
- a deterministic FakeEmbedder that hashes content into 64-D vectors so
  identical content collapses to identical embeddings (predictable recall).
"""

from __future__ import annotations

import hashlib

import pytest

# Skip module if ChromaDB is unavailable on this Python.
try:
    import chromadb  # noqa: F401
except Exception as e:  # noqa: BLE001
    pytest.skip(f"chromadb unavailable: {e}", allow_module_level=True)

from orchestration.embedding_engine import BaseEmbeddingEngine, EmbeddingConfig
from orchestration.vector_store import (
    ChromaVectorStore,
    VectorDBType,
    VectorStoreConfig,
    get_vector_search_cache,
)
from skyyrose.core.memory.agent_memory import (
    DEFAULT_NAMESPACE_PREFIX,
    AgentMemory,
)

# ---------------------------------------------------------------------------
# Deterministic fake embedder — content-hash → fixed 64-D vector
# ---------------------------------------------------------------------------


_DIM = 64


class FakeEmbedder(BaseEmbeddingEngine):
    """Maps text → deterministic 64-D unit-ish vector by hashing content.

    Identical text → identical embedding → cosine sim 1.0. Different text →
    different bytes in the hash → different embedding. We don't care about
    semantic quality, only that recall returns docs in stable order.
    """

    def __init__(self) -> None:
        super().__init__(EmbeddingConfig())
        self._dimension = _DIM
        self._initialized = True

    @staticmethod
    def _vec(text: str) -> list[float]:
        # SHA-256 → 32 bytes → repeat to 64 floats in [0,1)
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [(b / 255.0) for b in (digest + digest)[:_DIM]]

    async def initialize(self) -> None:  # already initialized
        return None

    async def embed_text(self, text: str) -> list[float]:
        return self._vec(text)

    async def embed_query(self, query: str) -> list[float]:
        return self._vec(query)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._vec(t) for t in texts]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def store(tmp_path):
    config = VectorStoreConfig(
        db_type=VectorDBType.CHROMADB,
        collection_name="test_agent_memory",
        persist_directory=str(tmp_path / "chroma"),
        dimension=_DIM,
        similarity_threshold=0.0,  # accept all matches; we test contracts, not relevance
        default_top_k=20,
    )
    s = ChromaVectorStore(config)
    await s.initialize()
    yield s
    await s.close()


@pytest.fixture
def embedder():
    return FakeEmbedder()


@pytest.fixture
async def memory(store, embedder):
    return AgentMemory(agent_id="compositor_agent", vector_store=store, embedder=embedder)


@pytest.fixture(autouse=True)
async def _clear_search_cache():
    cache = get_vector_search_cache()
    await cache.clear()
    yield
    await cache.clear()


# ---------------------------------------------------------------------------
# Construction & namespace
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_namespace_uses_agent_id(store, embedder):
    """The namespace AgentMemory writes to is `<prefix>:<agent_id>`."""
    m = AgentMemory(agent_id="alpha", vector_store=store, embedder=embedder)
    assert m.namespace == f"{DEFAULT_NAMESPACE_PREFIX}:alpha"


@pytest.mark.unit
def test_agent_id_must_be_non_empty_no_colon(store, embedder):
    """Empty agent_id or one containing ':' breaks namespace parsing."""
    with pytest.raises(ValueError, match="agent_id"):
        AgentMemory(agent_id="", vector_store=store, embedder=embedder)
    with pytest.raises(ValueError, match="agent_id"):
        AgentMemory(agent_id="bad:id", vector_store=store, embedder=embedder)


# ---------------------------------------------------------------------------
# remember()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_remember_returns_memory_id_and_persists(memory):
    mid = await memory.remember("Black Rose embroidery sits on left chest.")
    assert mid.startswith("mem:compositor_agent:")
    # Recall should find it
    found = await memory.recall("where does the BR logo go", k=1)
    assert len(found) == 1
    assert found[0].memory_id == mid


@pytest.mark.unit
@pytest.mark.asyncio
async def test_remember_rejects_out_of_range_importance(memory):
    with pytest.raises(ValueError, match="importance"):
        await memory.remember("x", importance=-0.1)
    with pytest.raises(ValueError, match="importance"):
        await memory.remember("x", importance=1.5)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_remember_filters_unsafe_metadata_types(memory):
    """Pinecone-safe metadata types: only str/int/float/bool survive."""
    mid = await memory.remember(
        "test",
        importance=0.7,
        metadata={
            "thread_id": "t-1",  # str — kept
            "turn": 4,  # int — kept
            "score": 0.95,  # float — kept
            "active": True,  # bool — kept
            "nested": {"x": 1},  # dict — DROPPED
            "tags_list": ["a", "b"],  # list — DROPPED
        },
    )
    found = await memory.recall("test", k=1)
    assert len(found) == 1
    meta = found[0].metadata
    assert meta.get("thread_id") == "t-1"
    assert meta.get("turn") == 4
    assert meta.get("score") == 0.95
    assert meta.get("active") is True
    assert "nested" not in meta
    assert "tags_list" not in meta


@pytest.mark.unit
@pytest.mark.asyncio
async def test_remember_preserves_tags_via_csv(memory):
    """Tags are encoded as CSV string (Pinecone metadata can't store list)."""
    await memory.remember("with tags", tags=["preferences", "embroidery"])
    found = await memory.recall("with tags", k=1)
    assert sorted(found[0].tags) == ["embroidery", "preferences"]


# ---------------------------------------------------------------------------
# recall()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_recall_top_k_respected(memory):
    for i in range(5):
        await memory.remember(f"memory entry {i}")
    found = await memory.recall("memory entry 0", k=2)
    assert len(found) <= 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_recall_min_importance_filters(memory):
    await memory.remember("low-importance fact", importance=0.1)
    await memory.remember("high-importance fact", importance=0.9)

    # All
    all_found = await memory.recall("fact", k=10)
    assert {m.content for m in all_found} == {
        "low-importance fact",
        "high-importance fact",
    }

    # Only high
    important = await memory.recall("fact", k=10, min_importance=0.5)
    assert {m.content for m in important} == {"high-importance fact"}


# ---------------------------------------------------------------------------
# Cross-agent isolation
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_two_agents_have_isolated_memories(store, embedder):
    """Memories written by agent A must not be recallable by agent B."""
    mem_a = AgentMemory(agent_id="alpha", vector_store=store, embedder=embedder)
    mem_b = AgentMemory(agent_id="bravo", vector_store=store, embedder=embedder)

    await mem_a.remember("alpha-only secret about Black Rose")
    await mem_b.remember("bravo-only fact about Signature")

    a_recall = await mem_a.recall("Black Rose", k=10)
    b_recall = await mem_b.recall("Black Rose", k=10)

    a_contents = {m.content for m in a_recall}
    b_contents = {m.content for m in b_recall}

    assert "alpha-only secret about Black Rose" in a_contents
    assert "bravo-only fact about Signature" not in a_contents
    assert "alpha-only secret about Black Rose" not in b_contents


# ---------------------------------------------------------------------------
# forget() / forget_many()
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_forget_removes_memory(memory):
    """forget() removes the underlying document from the store.

    Note: the vector search cache (5-min TTL) is not invalidated on writes —
    a known gap in vector_store.py. We clear it between recalls so this test
    isolates forget()'s contract from the cache layer.
    """
    mid = await memory.remember("ephemeral fact")
    assert len(await memory.recall("ephemeral", k=10)) == 1

    await memory.forget(mid)

    # Bypass the search cache so we hit the store fresh
    await get_vector_search_cache().clear()

    assert len(await memory.recall("ephemeral", k=10)) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_forget_many_empty_is_noop(memory):
    """Calling forget_many([]) returns 0 without hitting the store."""
    n = await memory.forget_many([])
    assert n == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_forget_many_does_not_cross_agent_boundary(store, embedder):
    """forget_many on agent A must not delete agent B's memories.

    This is the load-bearing namespace check on deletes — the bug-097 fix in
    vector_store.py is what makes this work.
    """
    mem_a = AgentMemory(agent_id="alpha", vector_store=store, embedder=embedder)
    mem_b = AgentMemory(agent_id="bravo", vector_store=store, embedder=embedder)

    a_id = await mem_a.remember("alpha thing")
    b_id = await mem_b.remember("bravo thing")

    # Try to delete BOTH ids via mem_a — only the alpha one should actually go
    await mem_a.forget_many([a_id, b_id])

    a_recall = await mem_a.recall("alpha thing", k=10)
    b_recall = await mem_b.recall("bravo thing", k=10)

    assert {m.memory_id for m in a_recall} == set()  # alpha's gone
    assert b_id in {m.memory_id for m in b_recall}  # bravo untouched
