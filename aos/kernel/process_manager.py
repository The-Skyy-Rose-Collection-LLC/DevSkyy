"""ProcessManager — lifecycle controller for agent processes.

Maintains the in-memory process table. All mutations atomic via single asyncio.Lock.
PIDs auto-increment from 1 (PID 0 reserved for kernel).
"""

from __future__ import annotations

import asyncio
import itertools
from typing import Any

from aos.kernel.types import (
    AgentProcess,
    ProcessStatus,
    SpawnRequest,
)


class ProcessNotFoundError(KeyError):
    """Raised when a PID is not in the process table."""


class ProcessManager:
    """In-memory process table + lifecycle controller.

    All public methods are coroutines. State changes are atomic.
    The process table is rebuilt on each mutation (immutable AgentProcess).
    """

    def __init__(self) -> None:
        self._table: dict[int, AgentProcess] = {}
        self._lock = asyncio.Lock()
        self._pid_counter = itertools.count(1)

    async def spawn(self, request: SpawnRequest) -> AgentProcess:
        """Create a new process and add it to the table.

        Raises ProcessNotFoundError if parent_pid is set but doesn't exist.
        """
        async with self._lock:
            if request.parent_pid is not None and request.parent_pid not in self._table:
                msg = f"Parent PID {request.parent_pid} not found"
                raise ProcessNotFoundError(msg)

            pid = next(self._pid_counter)
            proc = AgentProcess(
                pid=pid,
                parent_pid=request.parent_pid,
                agent_type=request.agent_type,
                prompt=request.prompt,
                priority=request.priority,
                budget_usd=request.budget_usd,
                metadata=request.metadata,
            )
            self._table[pid] = proc

            if request.parent_pid is not None:
                parent = self._table[request.parent_pid]
                self._table[request.parent_pid] = parent.add_child(pid)

            return proc

    async def get(self, pid: int) -> AgentProcess:
        """Fetch a process by PID. Raises if not found."""
        async with self._lock:
            return self._get_locked(pid)

    def _get_locked(self, pid: int) -> AgentProcess:
        if pid not in self._table:
            msg = f"PID {pid} not found"
            raise ProcessNotFoundError(msg)
        return self._table[pid]

    async def transition(
        self,
        pid: int,
        new_status: ProcessStatus,
        **kwargs: Any,
    ) -> AgentProcess:
        """Transition a process to a new state. Raises on invalid transition."""
        async with self._lock:
            proc = self._get_locked(pid)
            updated = proc.with_status(new_status, **kwargs)
            self._table[pid] = updated
            return updated

    async def pause(self, pid: int) -> AgentProcess:
        """Pause a running process."""
        return await self.transition(pid, ProcessStatus.PAUSED)

    async def resume(self, pid: int) -> AgentProcess:
        """Resume a paused process."""
        return await self.transition(pid, ProcessStatus.RUNNING)

    async def kill(self, pid: int, reason: str = "killed") -> AgentProcess:
        """Forcibly terminate a process (FAILED state)."""
        async with self._lock:
            proc = self._get_locked(pid)
            if proc.status in {ProcessStatus.PENDING, ProcessStatus.READY}:
                updated = proc.with_status(ProcessStatus.FAILED, error=reason)
            elif proc.status in {
                ProcessStatus.RUNNING,
                ProcessStatus.PAUSED,
                ProcessStatus.WAITING,
            }:
                updated = proc.with_status(ProcessStatus.FAILED, error=reason)
            else:
                msg = f"Cannot kill PID {pid} in terminal status {proc.status.name}"
                raise ValueError(msg)
            self._table[pid] = updated
            return updated

    async def complete(self, pid: int, result: Any) -> AgentProcess:
        """Mark a running process as completed with a result."""
        return await self.transition(pid, ProcessStatus.COMPLETED, result=result)

    async def fail(self, pid: int, error: str) -> AgentProcess:
        """Mark a running process as failed with an error message."""
        return await self.transition(pid, ProcessStatus.FAILED, error=error)

    async def reap(self, pid: int) -> AgentProcess:
        """Transition a terminal process to ZOMBIE (parent has read result)."""
        return await self.transition(pid, ProcessStatus.ZOMBIE)

    async def list_processes(
        self,
        *,
        status: ProcessStatus | None = None,
        agent_type: str | None = None,
        parent_pid: int | None = None,
    ) -> list[AgentProcess]:
        """List processes optionally filtered by status, agent_type, or parent."""
        async with self._lock:
            procs = list(self._table.values())
        if status is not None:
            procs = [p for p in procs if p.status == status]
        if agent_type is not None:
            procs = [p for p in procs if p.agent_type == agent_type]
        if parent_pid is not None:
            procs = [p for p in procs if p.parent_pid == parent_pid]
        return procs

    async def count_alive(self) -> int:
        """Count non-terminal processes."""
        async with self._lock:
            return sum(1 for p in self._table.values() if p.is_alive)

    async def record_spend(self, pid: int, amount: float) -> AgentProcess:
        """Add to a process's accumulated USD spend."""
        async with self._lock:
            proc = self._get_locked(pid)
            updated = proc.add_spend(amount)
            self._table[pid] = updated
            return updated

    async def snapshot(self) -> dict[int, AgentProcess]:
        """Return a frozen snapshot of the process table."""
        async with self._lock:
            return dict(self._table)
