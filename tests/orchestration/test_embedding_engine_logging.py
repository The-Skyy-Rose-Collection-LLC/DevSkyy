"""
Structured-logging contract for the embedding engine
=====================================================

The embedding engine feeds the ``token_tracker`` -> ``EmbeddingObserver``
observability pipeline, which queries on structured fields (provider, model,
dim). These tests pin the engine to ``structlog`` event-name + kwargs logging
so those fields stay machine-queryable instead of buried in free-text.

``structlog.testing.capture_logs`` captures emitted events as dicts with an
``event`` key plus any bound kwargs; it captures nothing for stdlib
``logging.getLogger`` calls, so these tests fail loudly if the engine ever
regresses to f-string logging.
"""

import pytest
from structlog.testing import capture_logs

import orchestration.embedding_engine as engine_mod
from orchestration.embedding_engine import EmbeddingCache, get_embedding_cache


@pytest.mark.unit
def test_cache_init_emits_structured_event(monkeypatch):
    """get_embedding_cache() logs a queryable event with the maxsize field."""
    monkeypatch.setattr(engine_mod, "_embedding_cache", None)
    monkeypatch.setenv("EMBEDDING_CACHE_SIZE", "256")

    with capture_logs() as cap_logs:
        get_embedding_cache()

    events = {entry["event"]: entry for entry in cap_logs}
    assert "embedding_cache_initialized" in events
    assert events["embedding_cache_initialized"]["maxsize"] == 256


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cache_hit_emits_structured_event():
    """A cache hit logs a structured debug event carrying the key prefix."""
    cache = EmbeddingCache(maxsize=8)
    await cache.put("hello", [0.1, 0.2, 0.3])

    with capture_logs() as cap_logs:
        result = await cache.get("hello")

    assert result == [0.1, 0.2, 0.3]
    hits = [e for e in cap_logs if e["event"] == "embedding_cache_hit"]
    assert len(hits) == 1
    assert "key_prefix" in hits[0]
