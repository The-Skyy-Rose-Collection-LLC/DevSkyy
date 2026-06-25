"""Tests for the AosShell REPL I/O layer."""

from __future__ import annotations

import io

import pytest

from aos.kernel.kernel import Kernel
from aos.kernel.types import SpawnRequest
from aos.shell.repl import AosShell


@pytest.fixture
async def kernel(tmp_path):
    k = Kernel(audit_db_path=str(tmp_path / "audit.db"), system_budget_usd=100.0)
    await k.boot()
    return k


class TestFeed:
    @pytest.mark.asyncio
    async def test_feed_runs_all_lines_and_returns_results(self, kernel):
        shell = AosShell(kernel, out=io.StringIO())
        results = await shell.feed(["budget", "ps"])
        assert len(results) == 2
        assert all(r.ok for r in results)

    @pytest.mark.asyncio
    async def test_feed_stops_on_exit(self, kernel):
        shell = AosShell(kernel, out=io.StringIO())
        results = await shell.feed(["budget", "exit", "ps"])
        assert len(results) == 2  # ps after exit is never run
        assert results[-1].should_exit is True

    @pytest.mark.asyncio
    async def test_feed_writes_output_to_stream(self, kernel):
        buf = io.StringIO()
        shell = AosShell(kernel, out=buf)
        await shell.feed(["budget"])
        assert "$100.0000" in buf.getvalue()

    @pytest.mark.asyncio
    async def test_feed_empty_line_emits_nothing(self, kernel):
        buf = io.StringIO()
        shell = AosShell(kernel, out=buf)
        await shell.feed([""])
        assert buf.getvalue() == ""

    @pytest.mark.asyncio
    async def test_feed_reflects_kernel_state_changes(self, kernel):
        buf = io.StringIO()
        shell = AosShell(kernel, out=buf)
        await kernel.spawn(SpawnRequest(agent_type="worker", prompt="t"))
        results = await shell.feed(["ps"])
        assert "worker" in results[0].output


class TestRunInteractive:
    @pytest.mark.asyncio
    async def test_run_exits_on_eof(self, kernel, monkeypatch):
        def _raise_eof(_prompt):
            raise EOFError

        monkeypatch.setattr("builtins.input", _raise_eof)
        shell = AosShell(kernel, out=io.StringIO())
        await shell.run()  # returns cleanly, no hang

    @pytest.mark.asyncio
    async def test_run_processes_then_exits(self, kernel):
        lines = iter(["budget", "exit"])
        buf = io.StringIO()

        def _fake_input(_prompt):
            return next(lines)

        import builtins

        original = builtins.input
        builtins.input = _fake_input
        try:
            shell = AosShell(kernel, out=buf)
            await shell.run()
        finally:
            builtins.input = original
        assert "$100.0000" in buf.getvalue()
        assert "bye" in buf.getvalue()

    @pytest.mark.asyncio
    async def test_run_exits_on_keyboard_interrupt(self, kernel, monkeypatch):
        def _raise_kbd(_prompt):
            raise KeyboardInterrupt

        monkeypatch.setattr("builtins.input", _raise_kbd)
        shell = AosShell(kernel, out=io.StringIO())
        await shell.run()
