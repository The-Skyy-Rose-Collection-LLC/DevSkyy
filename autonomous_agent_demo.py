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

Capabilities wired here:
  * Read / Write / Edit / Bash / Glob / Grep over ``--project-dir``
  * Multi-turn autonomous loop with --max-turns and --max-budget-usd guardrails
  * --read-only audit mode (no Write/Edit/Bash, plan permission mode)
  * Sessions: --session-id / --resume / --continue / --new (persisted per project)
  * MCP: --mcp-config loads external servers; an in-process SDK server adds
    project_stat + record_note tools; --load-project-settings reads .mcp.json
  * Sandbox: --sandbox enables OS-level bash isolation (macOS/Linux), with
    --sandbox-allow-domain and --sandbox-exclude-cmd

Usage:
    python autonomous_agent_demo.py --project-dir ./my_project \\
        --task "Scaffold a FastAPI app with a /health endpoint and a test"

    # resume the previous conversation in this project, sandboxed:
    python autonomous_agent_demo.py --project-dir ./my_project --resume --sandbox \\
        --task "Now add a /version endpoint and update the test"

Run with the venv interpreter that has the SDK installed:
    .venv/bin/python autonomous_agent_demo.py --project-dir ./my_project ...

Docs: https://platform.claude.com/docs/en/agent-sdk/overview
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
    create_sdk_mcp_server,
    query,
    tool,
)

# Tool sets. Read-only mode deliberately omits Write/Edit/Bash so the agent
# cannot mutate the target directory or run commands.
MUTATING_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
READ_ONLY_TOOLS = ["Read", "Glob", "Grep"]

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TURNS = 24
DEFAULT_MAX_BUDGET_USD = 1.00

# In-process SDK MCP server name; tools are addressed as mcp__<SERVER>__<tool>.
BUILTIN_SERVER = "devskyy"
SESSION_FILE = ".agent_session.json"
NOTES_FILE = ".agent/notes.md"

# Text-ish extensions counted by the project_stat tool.
_CODE_EXTS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".php",
    ".css",
    ".html",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sh",
    ".sql",
    ".go",
    ".rs",
}

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
        help="Restrict to Read/Glob/Grep and plan mode — no writes, edits, or shell commands.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Also stream thinking blocks and tool results."
    )

    sessions = parser.add_argument_group("sessions")
    sessions.add_argument(
        "--session-id", default=None, help="Use a specific session id for this run."
    )
    sessions.add_argument(
        "--resume",
        action="store_true",
        help=f"Resume the last session saved for this project ({SESSION_FILE}).",
    )
    sessions.add_argument(
        "--continue",
        dest="continue_",
        action="store_true",
        help="Continue the most recent conversation in the project directory.",
    )
    sessions.add_argument(
        "--new",
        action="store_true",
        help="Ignore any saved session and start fresh.",
    )

    mcp = parser.add_argument_group("mcp tools")
    mcp.add_argument(
        "--mcp-config",
        default=None,
        help='Path to a .mcp.json-style file ({"mcpServers": {...}}) of external MCP servers.',
    )
    mcp.add_argument(
        "--no-builtin-tools",
        action="store_true",
        help="Disable the in-process SDK tools (project_stat, record_note).",
    )
    mcp.add_argument(
        "--load-project-settings",
        action="store_true",
        help="Load the project's settings (CLAUDE.md, .mcp.json) via setting_sources=['project'].",
    )

    sandbox = parser.add_argument_group("sandbox")
    sandbox.add_argument(
        "--sandbox",
        action="store_true",
        help="Run bash commands in an OS-level sandbox (macOS/Linux) for filesystem/network isolation.",
    )
    sandbox.add_argument(
        "--sandbox-allow-domain",
        action="append",
        default=[],
        metavar="DOMAIN",
        help="Domain the sandbox may reach (repeatable). Implies --sandbox.",
    )
    sandbox.add_argument(
        "--sandbox-exclude-cmd",
        action="append",
        default=[],
        metavar="CMD",
        help="Command that runs OUTSIDE the sandbox, e.g. docker (repeatable). Implies --sandbox.",
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


# --------------------------------------------------------------------------
# Sessions
# --------------------------------------------------------------------------
def _session_path(project_dir: Path) -> Path:
    return project_dir / SESSION_FILE


def load_saved_session(project_dir: Path) -> str | None:
    """Return the session id persisted from a prior run, if any."""
    path = _session_path(project_dir)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("session_id")
    except (json.JSONDecodeError, OSError):
        return None


def save_session(project_dir: Path, session_id: str) -> None:
    """Persist the session id so a later --resume can pick it up."""
    payload = {"session_id": session_id, "updated": datetime.now(UTC).isoformat()}
    try:
        _session_path(project_dir).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as exc:
        print(f"Warning: could not save session id: {exc}", file=sys.stderr)


def resolve_session(args: argparse.Namespace, project_dir: Path) -> dict[str, Any]:
    """Turn the session flags into ClaudeAgentOptions kwargs."""
    if args.new:
        return {}
    kwargs: dict[str, Any] = {}
    if args.session_id:
        kwargs["session_id"] = args.session_id
    if args.continue_:
        kwargs["continue_conversation"] = True
    if args.resume:
        saved = load_saved_session(project_dir)
        if saved:
            kwargs["resume"] = saved
            print(f"Resuming session {saved}")
        else:
            print(
                f"No saved session in {_session_path(project_dir)} — starting fresh.",
                file=sys.stderr,
            )
    return kwargs


# --------------------------------------------------------------------------
# MCP tools
# --------------------------------------------------------------------------
def load_mcp_servers(path_str: str | None) -> dict[str, Any]:
    """Load external MCP servers from a .mcp.json-style file."""
    if not path_str:
        return {}
    path = Path(path_str).expanduser()
    if not path.exists():
        print(f"--mcp-config not found: {path}", file=sys.stderr)
        raise SystemExit(2)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"--mcp-config is not valid JSON: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    servers = data.get("mcpServers", data)
    if not isinstance(servers, dict):
        print(
            '--mcp-config must contain an object (optionally under "mcpServers").', file=sys.stderr
        )
        raise SystemExit(2)
    return servers


def build_builtin_server(project_dir: Path, read_only: bool) -> tuple[Any, list[str]]:
    """Create the in-process SDK MCP server and the tool names to auto-allow."""

    @tool("project_stat", "Count files, languages, and total lines in the project directory", {})
    async def project_stat(_args: dict[str, Any]) -> dict[str, Any]:
        files = [p for p in project_dir.rglob("*") if p.is_file() and ".agent" not in p.parts]
        by_ext: dict[str, int] = {}
        total_lines = 0
        for p in files:
            by_ext[p.suffix or "(none)"] = by_ext.get(p.suffix or "(none)", 0) + 1
            if p.suffix in _CODE_EXTS:
                try:
                    total_lines += sum(1 for _ in p.open("r", encoding="utf-8", errors="ignore"))
                except OSError:
                    pass
        top = sorted(by_ext.items(), key=lambda kv: kv[1], reverse=True)[:8]
        summary = f"{len(files)} files, {total_lines} code lines. By type: " + ", ".join(
            f"{ext}:{n}" for ext, n in top
        )
        return {"content": [{"type": "text", "text": summary}]}

    @tool("record_note", "Append a timestamped note to the agent's run journal", {"note": str})
    async def record_note(args: dict[str, Any]) -> dict[str, Any]:
        note = str(args.get("note", "")).strip()
        if not note:
            return {"content": [{"type": "text", "text": "No note provided."}], "is_error": True}
        journal = project_dir / NOTES_FILE
        journal.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")
        with journal.open("a", encoding="utf-8") as fh:
            fh.write(f"- {stamp} {note}\n")
        return {"content": [{"type": "text", "text": f"Recorded to {NOTES_FILE}"}]}

    tools = [project_stat] if read_only else [project_stat, record_note]
    server = create_sdk_mcp_server(name=BUILTIN_SERVER, version="1.0.0", tools=tools)
    allow = [f"mcp__{BUILTIN_SERVER}__{t.name}" for t in tools]
    return server, allow


# --------------------------------------------------------------------------
# Sandbox
# --------------------------------------------------------------------------
def build_sandbox(args: argparse.Namespace) -> dict[str, Any] | None:
    """Build a SandboxSettings dict, or None when sandboxing is off."""
    if not (args.sandbox or args.sandbox_allow_domain or args.sandbox_exclude_cmd):
        return None
    settings: dict[str, Any] = {"enabled": True, "autoAllowBashIfSandboxed": True}
    if args.sandbox_exclude_cmd:
        settings["excludedCommands"] = list(args.sandbox_exclude_cmd)
    if args.sandbox_allow_domain:
        settings["network"] = {"allowedDomains": list(args.sandbox_allow_domain)}
    return settings


def build_options(args: argparse.Namespace, project_dir: Path) -> ClaudeAgentOptions:
    """Translate parsed args into a ClaudeAgentOptions instance."""
    if args.read_only:
        allowed_tools = list(READ_ONLY_TOOLS)
        permission_mode = "plan"
    else:
        allowed_tools = list(MUTATING_TOOLS)
        permission_mode = args.permission_mode

    mcp_servers: dict[str, Any] = load_mcp_servers(args.mcp_config)
    for name in mcp_servers:
        allowed_tools.append(f"mcp__{name}")  # server-scoped auto-approve
    if not args.no_builtin_tools:
        server, allow = build_builtin_server(project_dir, args.read_only)
        mcp_servers[BUILTIN_SERVER] = server
        allowed_tools.extend(allow)

    setting_sources = ["project"] if (args.load_project_settings or args.mcp_config) else None
    sandbox = build_sandbox(args)

    return ClaudeAgentOptions(
        cwd=str(project_dir),
        allowed_tools=allowed_tools,
        permission_mode=permission_mode,
        system_prompt=SYSTEM_PROMPT,
        model=args.model,
        max_turns=args.max_turns,
        max_budget_usd=args.max_budget_usd,
        mcp_servers=mcp_servers,
        setting_sources=setting_sources,
        sandbox=sandbox,
        **resolve_session(args, project_dir),
    )


# --------------------------------------------------------------------------
# Streaming output
# --------------------------------------------------------------------------
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
    print(f"  session  : {message.session_id}")
    if message.errors:
        print(f"  errors   : {message.errors}")
    print("=" * 60)


async def run_agent(
    task: str, options: ClaudeAgentOptions, project_dir: Path, verbose: bool
) -> int:
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
            if message.session_id:
                save_session(project_dir, message.session_id)
            exit_code = 1 if message.is_error else 0
    return exit_code


def _describe_extras(args: argparse.Namespace, options: ClaudeAgentOptions) -> str:
    """One-line summary of the session/mcp/sandbox configuration."""
    parts = []
    server_names = list(options.mcp_servers or {})
    if server_names:
        parts.append("mcp=" + ",".join(server_names))
    if options.sandbox:
        parts.append("sandbox=on")
    if options.resume:
        parts.append("resume")
    elif options.continue_conversation:
        parts.append("continue")
    return " · ".join(parts) if parts else "none"


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
    print(f"  extras    : {_describe_extras(args, options)}")
    print(f"  task      : {task[:200]}")
    print("=" * 60 + "\n")

    try:
        return asyncio.run(run_agent(task, options, project_dir, args.verbose))
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
