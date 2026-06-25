"""Tests for the LangGraph Postgres checkpointer.

Verifies:
    - URL normalization handles SQLAlchemy and Heroku-style URLs
    - `get_checkpointer()` returns None gracefully when no PG URL is set
    - sqlite URLs short-circuit to None (no checkpointing)
    - async runner returns a structured error envelope without raising
      when DATABASE_URL is unset (falls back to non-checkpointed graph)
"""

from __future__ import annotations

import pytest

from skyyrose.elite_studio.creative import checkpointer as checkpointer_mod


class TestNormalizePgUrl:
    def test_returns_none_for_empty(self):
        assert checkpointer_mod._normalize_pg_url("") is None

    def test_returns_none_for_sqlite(self):
        assert checkpointer_mod._normalize_pg_url("sqlite:///./db.sqlite") is None
        assert checkpointer_mod._normalize_pg_url("sqlite+aiosqlite:///./db.sqlite") is None

    def test_strips_sqlalchemy_driver_suffix(self):
        url = "postgresql+asyncpg://user:pw@host:5432/db"
        assert checkpointer_mod._normalize_pg_url(url) == "postgresql://user:pw@host:5432/db"

        url = "postgresql+psycopg://u:p@h:5432/d"
        assert checkpointer_mod._normalize_pg_url(url) == "postgresql://u:p@h:5432/d"

    def test_passes_through_plain_postgresql_url(self):
        url = "postgresql://u:p@h:5432/d"
        assert checkpointer_mod._normalize_pg_url(url) == url

    def test_passes_through_heroku_postgres_url(self):
        # Heroku still uses the legacy "postgres://" scheme; psycopg accepts it.
        url = "postgres://u:p@h:5432/d"
        assert checkpointer_mod._normalize_pg_url(url) == url

    def test_returns_none_for_unknown_scheme(self):
        assert checkpointer_mod._normalize_pg_url("mysql://x") is None


@pytest.mark.asyncio
async def test_get_checkpointer_returns_none_without_db_url(monkeypatch):
    """Without DATABASE_URL, the checkpointer factory returns None silently."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Reset module-level singletons so the test is order-independent.
    checkpointer_mod._pool = None
    checkpointer_mod._checkpointer = None

    result = await checkpointer_mod.get_checkpointer()
    assert result is None


@pytest.mark.asyncio
async def test_get_checkpointer_returns_none_for_sqlite(monkeypatch):
    """sqlite URLs short-circuit to None (LangGraph PG saver only supports PG)."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    checkpointer_mod._pool = None
    checkpointer_mod._checkpointer = None

    result = await checkpointer_mod.get_checkpointer()
    assert result is None


@pytest.mark.asyncio
async def test_arun_creative_falls_back_when_no_pg(monkeypatch):
    """arun_creative should still work (no checkpointing) when DATABASE_URL is unset."""
    from skyyrose.elite_studio.creative import router as router_mod
    from skyyrose.elite_studio.creative import runner as runner_mod

    monkeypatch.delenv("DATABASE_URL", raising=False)
    # Reset singletons
    checkpointer_mod._pool = None
    checkpointer_mod._checkpointer = None
    router_mod._CREATIVE_GRAPH_CHECKPOINTED = None

    # We don't care about the actual operation succeeding — we care that
    # the call doesn't blow up trying to import psycopg / connect to PG.
    result = await runner_mod.arun_creative(
        intent="design-ideation",
        params={"theme": "minimalist"},
    )
    assert isinstance(result, dict)
    assert "operation_id" in result
    assert "status" in result
