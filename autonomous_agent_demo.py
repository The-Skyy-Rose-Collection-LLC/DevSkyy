#!/usr/bin/env python3
"""Autonomous coding agent demo for DevSkyy.

A self-contained CLI that turns the Claude Agent SDK into an autonomous
coding agent scoped to a single project directory. Point it at any folder
with ``--project-dir`` and give it a task; it reads, writes, edits, and runs
shell commands inside that directory until the task is done or a guardrail
(turn count / dollar budget) trips.

Foundation: claude-agent-sdk (already a declared dependency). The SDK spawns
the local ``claude`` CLI, which handles auth + the tool loop. Nothing here
calls the raw Anthropic Messages API, so no hand-rolled tool loop is needed.

Usage:
    python autonomous_agent_demo.py --project-dir ./my_project \\
        --task "Scaffold a FastAPI app with a /health endpoint and a test"

    # read-only audit (no Write/Edit/Bash):
    python autonomous_agent_demo.py --project-dir . --read-only \\
        --task "Summarize the architecture and flag the three biggest risks"

Run with the venv interpreter that has the SDK installed:
    .venv/bin/python autonomous_agent_demo.py --project-dir ./my_project ...

Docs: https://platform.claude.com/docs/en/agent-sdk/overview
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKError,
    CLINotFoundError,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

# Tool sets. Read-only mode deliberately omits Write/Edit/Bash so the agent
# cannot mutate the target directory or run commands.
MUTATING_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
READ_ONLY_TOOLS = ["Read", "Glob", "Grep"]

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TURNS = 24
DEFAULT_MAX_BUDGET_USD = 1.00

SYSTEM_PROMPT = (
    "You are an autonomous coding agent operating inside a single project "
    "directory. Work the task end to end: inspect what exists before "
    "changing it, make focused edits, run the project's own tests or linters "
    "to verify your work when they exist, and report what you changed and how "
    "to verify it. Prefer small, correct steps over large speculative ones. "
    "If the task is ambiguous, state the assumption you are proceeding under "
    "rather than stopping to ask."
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Build and parse the CLI argument namespace."""
    parser = argparse.ArgumentParser(
        prog="autonomous_agent_demo.py",
        description="Run an autonomous Claude coding agent scoped to a project directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--project-dir",
        required=True,
        help="Directory the agent operates in (created if it does not exist).",
    )
    parser.add_argument(
        "--task",
        default=None,
        help="What the agent should do. If omitted, read from stdin or prompt interactively.",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, help=f"Model id (default: {DEFAULT_MODEL})."
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=DEFAULT_MAX_TURNS,
        help=f"Hard cap on agent turns (default: {DEFAULT_MAX_TURNS}).",
    )
    parser.add_argument(
        "--max-budget-usd",
        type=float,
        default=DEFAULT_MAX_BUDGET_USD,
        help=f"Hard spend cap in USD; the run aborts when reached (default: {DEFAULT_MAX_BUDGET_USD}).",
    )
    parser.add_argument(
        "--permission-mode",
        choices=["default", "acceptEdits", "plan", "bypassPermissions"],
        default="acceptEdits",
        help="SDK permission mode (default: acceptEdits — auto-accept file edits).",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help="Restrict to Read/Glob/Grep and plan mode — the agent cannot write, edit, or run shell commands.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Also stream thinking blocks and tool results.",
    )
    return parser.parse_args(argv)


def resolve_task(task: str | None) -> str:
    """Return the task text from --task, piped stdin, or an interactive prompt."""
    if task and task.strip():
        return task.strip()
    if not sys.stdin.isatty():
        piped = sys.stdin.read().strip()
        if piped:
            return piped
    try:
        entered = input("Task for the agent: ").strip()
    except (EOFError, KeyboardInterrupt):
        entered = ""
    if not entered:
        print("No task provided. Pass --task or pipe the instruction on stdin.", file=sys.stderr)
        raise SystemExit(2)
    return entered


def prepare_project_dir(raw: str) -> Path:
    """Resolve --project-dir to an absolute path, creating it if missing."""
    project_dir = Path(raw).expanduser().resolve()
    if project_dir.exists() and not project_dir.is_dir():
        print(f"--project-dir is not a directory: {project_dir}", file=sys.stderr)
        raise SystemExit(2)
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def check_auth() -> None:
    """Warn (do not fail) if no obvious credential is present.

    The SDK delegates auth to the ``claude`` CLI, which may use a logged-in
    session instead of ANTHROPIC_API_KEY, so a missing env var is not fatal.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "Note: ANTHROPIC_API_KEY is not set. The agent will rely on the "
            "claude CLI's own login. If the run fails to authenticate, export "
            "the key or run `claude login`.",
            file=sys.stderr,
        )


def build_options(args: argparse.Namespace, project_dir: Path) -> ClaudeAgentOptions:
    """Translate parsed args into a ClaudeAgentOptions instance."""
    if args.read_only:
        allowed_tools = READ_ONLY_TOOLS
        permission_mode = "plan"
    else:
        allowed_tools = MUTATING_TOOLS
        permission_mode = args.permission_mode
    return ClaudeAgentOptions(
        cwd=str(project_dir),
        allowed_tools=allowed_tools,
        permission_mode=permission_mode,
        system_prompt=SYSTEM_PROMPT,
        model=args.model,
        max_turns=args.max_turns,
        max_budget_usd=args.max_budget_usd,
    )


def _format_tool_use(block: ToolUseBlock) -> str:
    """Render a tool call as a compact one-liner for the stream."""
    data = block.input or {}
    if block.name in {"Write", "Edit", "Read"} and isinstance(data, dict) and data.get("file_path"):
        detail = str(data["file_path"])
    elif block.name == "Bash" and isinstance(data, dict) and data.get("command"):
        detail = str(data["command"])
    elif isinstance(data, dict):
        detail = ", ".join(f"{k}={v!r}" for k, v in list(data.items())[:2])
    else:
        detail = str(data)
    if len(detail) > 100:
        detail = detail[:97] + "..."
    return f"  → {block.name}({detail})"


def print_assistant(message: AssistantMessage, verbose: bool) -> None:
    """Print the text, tool calls, and (optionally) thinking from one turn."""
    for block in message.content:
        if isinstance(block, TextBlock):
            text = block.text.strip()
            if text:
                print(text)
        elif isinstance(block, ToolUseBlock):
            print(_format_tool_use(block))
        elif isinstance(block, ThinkingBlock) and verbose:
            thinking = block.thinking.strip()
            if thinking:
                print(f"  💭 {thinking[:200]}")


def print_tool_results(message: UserMessage, verbose: bool) -> None:
    """Print tool-result blocks carried back on a UserMessage when verbose."""
    if not verbose or not isinstance(message.content, list):
        return
    for block in message.content:
        if isinstance(block, ToolResultBlock):
            marker = "✗" if block.is_error else "✓"
            content = block.content
            text = content if isinstance(content, str) else str(content)
            print(f"  {marker} result: {text[:200].strip()}")


def print_summary(message: ResultMessage) -> None:
    """Print the final run summary: status, turns, cost, duration."""
    status = "ERROR" if message.is_error else "OK"
    cost = f"${message.total_cost_usd:.4f}" if message.total_cost_usd is not None else "n/a"
    print("\n" + "=" * 60)
    print(f"  status   : {status}  ({message.subtype})")
    print(f"  turns    : {message.num_turns}")
    print(f"  cost     : {cost}")
    print(f"  duration : {message.duration_ms / 1000:.1f}s")
    if message.errors:
        print(f"  errors   : {message.errors}")
    print("=" * 60)


async def run_agent(task: str, options: ClaudeAgentOptions, verbose: bool) -> int:
    """Drive the agent to completion, streaming output. Returns a process exit code."""
    exit_code = 0
    async for message in query(prompt=task, options=options):
        if isinstance(message, SystemMessage):
            if message.subtype == "init":
                model = message.data.get("model", "?") if isinstance(message.data, dict) else "?"
                print(f"agent ready · model={model} · cwd={options.cwd}\n")
        elif isinstance(message, AssistantMessage):
            print_assistant(message, verbose)
        elif isinstance(message, UserMessage):
            print_tool_results(message, verbose)
        elif isinstance(message, ResultMessage):
            print_summary(message)
            exit_code = 1 if message.is_error else 0
    return exit_code


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse args, set up the run, and execute the agent."""
    args = parse_args(argv)
    project_dir = prepare_project_dir(args.project_dir)
    task = resolve_task(args.task)
    check_auth()
    options = build_options(args, project_dir)

    tool_summary = "read-only" if args.read_only else "read/write/exec"
    print("=" * 60)
    print("  DevSkyy · Autonomous Coding Agent")
    print(f"  project   : {project_dir}")
    print(f"  mode      : {tool_summary} ({options.permission_mode})")
    print(f"  model     : {args.model}")
    print(f"  guardrails: max {args.max_turns} turns · ${args.max_budget_usd:.2f} budget")
    print(f"  task      : {task[:200]}")
    print("=" * 60 + "\n")

    try:
        return asyncio.run(run_agent(task, options, args.verbose))
    except CLINotFoundError:
        print(
            "\nClaude CLI not found. The Agent SDK needs it on PATH.\n"
            "Install it with:  npm install -g @anthropic-ai/claude-code",
            file=sys.stderr,
        )
        return 127
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except ClaudeSDKError as exc:
        print(f"\nAgent SDK error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
