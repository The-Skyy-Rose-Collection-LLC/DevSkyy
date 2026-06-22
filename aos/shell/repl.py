"""AOS Shell REPL — thin stdin/stdout loop over execute_command.

AosShell.run() drives an interactive session; AosShell.feed() runs a
scripted list of lines (used by tests and non-interactive automation).
All command logic lives in commands.py — this layer is pure I/O glue.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Iterable
from typing import TYPE_CHECKING, TextIO

from aos.shell.commands import CommandResult, execute_command

if TYPE_CHECKING:
    from aos.kernel.kernel import Kernel


class AosShell:
    """Interactive command shell bound to a single booted Kernel.

    Usage::

        shell = AosShell(kernel)
        await shell.run()                       # interactive REPL
        results = await shell.feed(["ps", "exit"])  # scripted, returns results
    """

    def __init__(
        self,
        kernel: Kernel,
        *,
        prompt: str = "aos> ",
        out: TextIO | None = None,
    ) -> None:
        self._kernel = kernel
        self._prompt = prompt
        self._out = out if out is not None else sys.stdout

    def _emit(self, result: CommandResult) -> None:
        if result.output:
            print(result.output, file=self._out)

    async def feed(self, lines: Iterable[str]) -> list[CommandResult]:
        """Run each line in order; stop early on an exit command.

        Returns the CommandResult for every line that was executed. Pure —
        no stdin, deterministic — the unit-test entry point.
        """
        results: list[CommandResult] = []
        for line in lines:
            result = await execute_command(self._kernel, line)
            results.append(result)
            self._emit(result)
            if result.should_exit:
                break
        return results

    async def run(self) -> None:
        """Interactive loop. Reads stdin off-thread so the event loop is free.

        Exits on an exit/quit command, EOF (Ctrl-D), or KeyboardInterrupt.
        """
        while True:
            try:
                line = await asyncio.to_thread(input, self._prompt)
            except (EOFError, KeyboardInterrupt):
                print(file=self._out)
                return
            result = await execute_command(self._kernel, line)
            self._emit(result)
            if result.should_exit:
                return
