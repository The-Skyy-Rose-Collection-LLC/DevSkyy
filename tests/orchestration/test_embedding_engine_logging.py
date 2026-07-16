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

``tests/test_utils_modules.py`` exercises ``utils.logging_utils.configure_logging()``,
which calls ``structlog.configure(wrapper_class=structlog.make_filtering_bound_logger
(logging.INFO), ...)`` and never resets it. That reconfiguration is process-global and
outlives the test that made it: for the rest of the pytest session, every
``structlog.get_logger()`` proxy resolves to ``BoundLoggerFilteringAtInfo``, whose
``.debug()`` is an unconditional no-op (``_nop``, returns immediately) that never reaches
the processor chain -- so ``capture_logs()`` never sees the event at all, independent of
whatever processors are installed. This only reproduces in full-suite order (something
must call ``configure_logging()`` before this file runs); each test below forces its own
non-filtering wrapper class on the module logger so the ``.debug()``/``.info()`` calls
always reach ``capture_logs()``'s processor chain, regardless of ambient global structlog
config left behind by other tests.
"""

import pytest
import structlog
from structlog.testing import capture_logs

import orchestration.embedding_engine as engine_mod
from orchestration.embedding_engine import EmbeddingCache, get_embedding_cache


@pytest.fixture(autouse=True)
def _unfiltered_module_logger(monkeypatch):
    """Force a non-filtering wrapper class on the module logger.

    Guards against ``utils.logging_utils.configure_logging()`` /
    ``core.structured_logging.configure_logging()`` (called by other tests
    earlier in a full-suite run, never reset) installing
    ``make_filtering_bound_logger(logging.INFO)`` process-wide, which turns
    ``logger.debug(...)`` into a silent no-op before it ever reaches
    ``capture_logs()``.
    """
    monkeypatch.setattr(
        engine_mod,
        "logger",
        structlog.wrap_logger(None, wrapper_class=structlog.make_filtering_bound_logger(0)),
    )


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
