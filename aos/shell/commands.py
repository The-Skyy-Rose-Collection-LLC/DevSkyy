"""AOS Shell command dispatch — pure async, zero I/O.

Each command maps a parsed line to a CommandResult by calling the live
Kernel API. The REPL layer (repl.py) handles stdin/stdout; this module is
fully unit-testable with a booted Kernel and no terminal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from aos.kernel.types import SpawnRequest

if TYPE_CHECKING:
    from aos.kernel.kernel import Kernel


@dataclass(frozen=True)
class CommandResult:
    """Outcome of one shell command line."""

    output: str
    ok: bool = True
    should_exit: bool = False


_HELP_TEXT = """\
Commands:
  ps                       list all processes
  kill <pid> [reason]      kill a process
  spawn <type> <prompt>    spawn a new agent process
  budget                   show system budget
  modules                  list loaded modules + registered types
  audit [limit]            show recent audit entries (default 20)
  help                     show this help
  exit | quit              leave the shell"""


async def execute_command(kernel: Kernel, line: str) -> CommandResult:
    """Parse and run a single shell line against the kernel.

    Never raises — command failures are returned as ok=False results so the
    REPL loop stays alive across bad input.
    """
    tokens = line.strip().split()
    if not tokens:
        return CommandResult(output="", ok=True)

    cmd, args = tokens[0], tokens[1:]
    handler = _HANDLERS.get(cmd)
    if handler is None:
        return CommandResult(output=f"unknown command: {cmd!r} (try 'help')", ok=False)
    try:
        return await handler(kernel, args)
    except Exception as exc:  # noqa: BLE001 — shell must survive any handler error
        return CommandResult(output=f"error: {exc}", ok=False)


# ----------------------------------------------------------------- handlers


async def _cmd_help(_kernel: Kernel, _args: list[str]) -> CommandResult:
    return CommandResult(output=_HELP_TEXT)


async def _cmd_exit(_kernel: Kernel, _args: list[str]) -> CommandResult:
    return CommandResult(output="bye", should_exit=True)


async def _cmd_ps(kernel: Kernel, _args: list[str]) -> CommandResult:
    procs = await kernel.processes.list_processes()
    if not procs:
        return CommandResult(output="no processes")
    lines = [f"{'PID':>5}  {'TYPE':<20} {'STATUS':<10} {'SPEND':>8}"]
    for p in sorted(procs, key=lambda x: x.pid):
        lines.append(f"{p.pid:>5}  {p.agent_type:<20} {p.status.name:<10} ${p.spent_usd:>7.4f}")
    return CommandResult(output="\n".join(lines))


async def _cmd_kill(kernel: Kernel, args: list[str]) -> CommandResult:
    if not args:
        return CommandResult(output="usage: kill <pid> [reason]", ok=False)
    try:
        pid = int(args[0])
    except ValueError:
        return CommandResult(output=f"invalid pid: {args[0]!r}", ok=False)
    reason = " ".join(args[1:]) or "killed via shell"
    proc = await kernel.kill(pid, reason=reason)
    return CommandResult(output=f"killed pid {pid} ({proc.status.name})")


async def _cmd_spawn(kernel: Kernel, args: list[str]) -> CommandResult:
    if len(args) < 2:
        return CommandResult(output="usage: spawn <agent_type> <prompt>", ok=False)
    agent_type = args[0]
    prompt = " ".join(args[1:])
    request = SpawnRequest(agent_type=agent_type, prompt=prompt)
    proc = await kernel.spawn(request)
    return CommandResult(output=f"spawned pid {proc.pid} ({agent_type}) status={proc.status.name}")


async def _cmd_budget(kernel: Kernel, _args: list[str]) -> CommandResult:
    remaining = kernel.budget.system_remaining_usd
    limit = kernel.budget.system_budget_usd
    pct = (remaining / limit * 100) if limit else 0.0
    return CommandResult(output=(f"budget: ${remaining:.4f} / ${limit:.4f} remaining ({pct:.1f}%)"))


async def _cmd_modules(kernel: Kernel, _args: list[str]) -> CommandResult:
    manifests = kernel.modules.manifests
    types = sorted(kernel.modules.registered_types)
    lines = [f"registered types ({len(types)}): {', '.join(types) or '—'}"]
    if not manifests:
        lines.append("no modules loaded")
    else:
        lines.append(f"loaded modules ({len(manifests)}):")
        for m in manifests:
            agent_types = ", ".join(m.agent_types)
            lines.append(f"  {m.name} v{m.version} [{agent_types}]")
    return CommandResult(output="\n".join(lines))


async def _cmd_audit(kernel: Kernel, args: list[str]) -> CommandResult:
    limit = 20
    if args:
        try:
            limit = int(args[0])
        except ValueError:
            return CommandResult(output=f"invalid limit: {args[0]!r}", ok=False)
    entries = await kernel.audit.query(limit=limit)
    if not entries:
        return CommandResult(output="no audit entries")
    lines = []
    for e in entries:
        ts = e.timestamp.strftime("%H:%M:%S")
        actor = e.actor_pid if e.actor_pid is not None else "-"
        target = e.target_pid if e.target_pid is not None else "-"
        lines.append(f"{ts}  {e.event_type.value:<22} actor={actor} target={target}")
    return CommandResult(output="\n".join(lines))


_HANDLERS: dict[str, Any] = {
    "help": _cmd_help,
    "exit": _cmd_exit,
    "quit": _cmd_exit,
    "ps": _cmd_ps,
    "kill": _cmd_kill,
    "spawn": _cmd_spawn,
    "budget": _cmd_budget,
    "modules": _cmd_modules,
    "audit": _cmd_audit,
}
