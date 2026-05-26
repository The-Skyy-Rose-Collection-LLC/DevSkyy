"""Terminal skin for cli-anything-comfyui.

Emerald accent: ANSI 256 colour 42 (\\033[38;5;42m), hex #10B981.
Provides banner, prompt, table, and status-message helpers.
prompt_toolkit is an optional extra — falls back to input() when absent.
"""

from __future__ import annotations

import shutil
from typing import Any

# ANSI helpers
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

# Emerald — ANSI 256 colour 42
_ACCENT = "\033[38;5;42m"
_GREEN = "\033[38;5;82m"
_RED = "\033[38;5;196m"
_YELLOW = "\033[38;5;220m"
_BLUE = "\033[38;5;39m"
_GREY = "\033[38;5;245m"

_ACCENT_HEX = "#10B981"
_CLI_NAME = "comfyui"

_BANNER = f"""\
{_ACCENT}{_BOLD}╔══════════════════════════════════════════════════╗
║          cli-anything · comfyui REPL             ║
║          accent {_ACCENT_HEX} · emerald                  ║
╚══════════════════════════════════════════════════╝{_RESET}"""


class ReplSkin:
    """Terminal output helpers with emerald accent styling."""

    def __init__(self, json_mode: bool = False) -> None:
        self._json = json_mode
        self._width, _ = shutil.get_terminal_size(fallback=(100, 24))

    # ------------------------------------------------------------------
    # Banner / section
    # ------------------------------------------------------------------

    def print_banner(self) -> None:
        if not self._json:
            print(_BANNER)

    def section(self, title: str) -> None:
        if self._json:
            return
        bar = _ACCENT + "─" * min(len(title) + 4, self._width) + _RESET
        print(f"\n{bar}")
        print(f"{_ACCENT}{_BOLD}  {title}{_RESET}")
        print(bar)

    # ------------------------------------------------------------------
    # Status messages
    # ------------------------------------------------------------------

    def success(self, msg: str) -> None:
        if not self._json:
            print(f"{_GREEN}✔ {msg}{_RESET}")

    def error(self, msg: str) -> None:
        if not self._json:
            print(f"{_RED}✖ {msg}{_RESET}")

    def warning(self, msg: str) -> None:
        if not self._json:
            print(f"{_YELLOW}⚠ {msg}{_RESET}")

    def info(self, msg: str) -> None:
        if not self._json:
            print(f"{_BLUE}ℹ {msg}{_RESET}")

    def hint(self, msg: str) -> None:
        if not self._json:
            print(f"{_GREY}  {msg}{_RESET}")

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------

    def table(self, headers: list[str], rows: list[list[Any]]) -> None:
        if self._json:
            return
        if not rows:
            self.hint("(no rows)")
            return

        col_widths = [len(h) for h in headers]
        str_rows = [[str(cell) for cell in row] for row in rows]
        for row in str_rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(cell))

        fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
        header_line = fmt.format(*headers)
        sep = "  ".join("─" * w for w in col_widths)
        print(f"{_ACCENT}{_BOLD}{header_line}{_RESET}")
        print(f"{_GREY}{sep}{_RESET}")
        for row in str_rows:
            padded = row + [""] * max(0, len(headers) - len(row))
            print(fmt.format(*padded[: len(headers)]))

    # ------------------------------------------------------------------
    # Help
    # ------------------------------------------------------------------

    def help(self, command: str, description: str, examples: list[str] | None = None) -> None:
        if self._json:
            return
        print(f"\n{_ACCENT}{_BOLD}{command}{_RESET}  {_GREY}{description}{_RESET}")
        if examples:
            for ex in examples:
                print(f"  {_DIM}$ {ex}{_RESET}")

    # ------------------------------------------------------------------
    # Prompt / input
    # ------------------------------------------------------------------

    def prompt(self, text: str = "") -> str:
        """Return user input with an emerald prompt prefix."""
        label = f"{_ACCENT}{_BOLD}comfyui>{_RESET} {text}"
        try:
            from prompt_toolkit import prompt as pt_prompt  # type: ignore[import-untyped]

            return pt_prompt(label)
        except ImportError:
            return input(label)

    def create_prompt_session(self) -> Any:
        """Return a prompt_toolkit PromptSession or None if unavailable."""
        try:
            from prompt_toolkit import PromptSession  # type: ignore[import-untyped]
            from prompt_toolkit.history import InMemoryHistory  # type: ignore[import-untyped]

            return PromptSession(history=InMemoryHistory())
        except ImportError:
            return None

    def get_input(self, session: Any, text: str = "") -> str:
        label = f"{_ACCENT}{_BOLD}comfyui>{_RESET} {text}"
        if session is not None:
            try:
                return session.prompt(label)
            except (EOFError, KeyboardInterrupt):
                raise
        return input(label)
