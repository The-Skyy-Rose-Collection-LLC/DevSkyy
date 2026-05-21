"""AOS Shell — interactive REPL over the live Kernel API."""

from aos.shell.commands import CommandResult, execute_command
from aos.shell.repl import AosShell

__all__ = [
    "AosShell",
    "CommandResult",
    "execute_command",
]
