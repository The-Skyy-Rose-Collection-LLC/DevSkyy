"""Tests for AOS shell command dispatch (execute_command)."""

from __future__ import annotations

import pytest

from aos.kernel.kernel import Kernel
from aos.kernel.types import SpawnRequest
from aos.modules.types import ModuleManifest
from aos.shell.commands import CommandResult, execute_command


async def _noop_factory() -> object:
    return object()


@pytest.fixture
async def kernel(tmp_path):
    k = Kernel(audit_db_path=str(tmp_path / "audit.db"), system_budget_usd=100.0)
    await k.boot()
    return k


class TestParsing:
    @pytest.mark.asyncio
    async def test_empty_line_is_noop_ok(self, kernel):
        result = await execute_command(kernel, "   ")
        assert result == CommandResult(output="", ok=True)

    @pytest.mark.asyncio
    async def test_unknown_command_not_ok(self, kernel):
        result = await execute_command(kernel, "frobnicate")
        assert result.ok is False
        assert "unknown command" in result.output

    @pytest.mark.asyncio
    async def test_handler_error_returns_not_ok(self, kernel):
        # kill of a non-existent pid raises inside the handler -> caught
        result = await execute_command(kernel, "kill 9999")
        assert result.ok is False
        assert result.output.startswith("error:")


class TestHelpAndExit:
    @pytest.mark.asyncio
    async def test_help_lists_commands(self, kernel):
        result = await execute_command(kernel, "help")
        assert result.ok is True
        for cmd in ("ps", "kill", "spawn", "budget", "modules", "audit"):
            assert cmd in result.output

    @pytest.mark.asyncio
    async def test_exit_sets_should_exit(self, kernel):
        result = await execute_command(kernel, "exit")
        assert result.should_exit is True

    @pytest.mark.asyncio
    async def test_quit_is_alias_for_exit(self, kernel):
        result = await execute_command(kernel, "quit")
        assert result.should_exit is True


class TestPs:
    @pytest.mark.asyncio
    async def test_ps_empty(self, kernel):
        result = await execute_command(kernel, "ps")
        assert result.output == "no processes"

    @pytest.mark.asyncio
    async def test_ps_lists_spawned_process(self, kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="worker", prompt="t"))
        result = await execute_command(kernel, "ps")
        assert "worker" in result.output
        assert str(proc.pid) in result.output


class TestKill:
    @pytest.mark.asyncio
    async def test_kill_missing_arg(self, kernel):
        result = await execute_command(kernel, "kill")
        assert result.ok is False
        assert "usage:" in result.output

    @pytest.mark.asyncio
    async def test_kill_non_numeric_pid(self, kernel):
        result = await execute_command(kernel, "kill abc")
        assert result.ok is False
        assert "invalid pid" in result.output

    @pytest.mark.asyncio
    async def test_kill_valid_pid(self, kernel):
        proc = await kernel.spawn(SpawnRequest(agent_type="x", prompt="y"))
        result = await execute_command(kernel, f"kill {proc.pid}")
        assert result.ok is True
        assert f"killed pid {proc.pid}" in result.output


class TestSpawn:
    @pytest.mark.asyncio
    async def test_spawn_missing_args(self, kernel):
        result = await execute_command(kernel, "spawn worker")
        assert result.ok is False
        assert "usage:" in result.output

    @pytest.mark.asyncio
    async def test_spawn_creates_process(self, kernel):
        result = await execute_command(kernel, "spawn worker do the thing")
        assert result.ok is True
        assert "spawned pid" in result.output
        procs = await kernel.processes.list_processes()
        assert len(procs) == 1
        assert procs[0].agent_type == "worker"
        assert procs[0].prompt == "do the thing"


class TestBudget:
    @pytest.mark.asyncio
    async def test_budget_shows_remaining_and_limit(self, kernel):
        result = await execute_command(kernel, "budget")
        assert result.ok is True
        assert "$100.0000" in result.output
        assert "100.0%" in result.output


class TestModules:
    @pytest.mark.asyncio
    async def test_modules_empty(self, kernel):
        result = await execute_command(kernel, "modules")
        assert "no modules loaded" in result.output
        assert "registered types (0)" in result.output

    @pytest.mark.asyncio
    async def test_modules_lists_loaded(self, kernel):
        manifest = ModuleManifest(name="alpha", version="1.0", agent_types=("worker",))
        await kernel.load_module(manifest, {"worker": _noop_factory})
        result = await execute_command(kernel, "modules")
        assert "alpha v1.0" in result.output
        assert "worker" in result.output


class TestAudit:
    @pytest.mark.asyncio
    async def test_audit_invalid_limit(self, kernel):
        result = await execute_command(kernel, "audit notanumber")
        assert result.ok is False
        assert "invalid limit" in result.output

    @pytest.mark.asyncio
    async def test_audit_shows_entries_after_activity(self, kernel):
        await kernel.spawn(SpawnRequest(agent_type="x", prompt="y"))
        result = await execute_command(kernel, "audit 10")
        assert result.ok is True
        assert "actor=" in result.output

    @pytest.mark.asyncio
    async def test_audit_default_limit_parses(self, kernel):
        result = await execute_command(kernel, "audit")
        assert result.ok is True
