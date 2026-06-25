"""Local tool layer for orchestration mode.

Carries the three tools the orchestration-mode loop exposes and the parallel
subagent fan-out:

* ``WORKFLOW_TOOL`` — the standing-consent fan-out tool. Its description holds
  the behavioural contract: opt-in normally, standing consent while the mode is
  on, plus the quality patterns the model can reach for.
* ``BASH_TOOL`` — the Anthropic-defined ``bash_20250124`` tool, executed
  locally (no sandbox — see :func:`run_bash`).
* ``REPORT_TOOL`` — ``report_findings``; a subagent calls it once to return
  structured findings instead of prose.

Concurrency follows the house idiom (``asyncio.gather`` + ``Semaphore``; cf.
``agents/elite_web_builder/director.py`` and ``llm/round_table.py``), not the
reference's ``ThreadPoolExecutor``.

WARNING: :func:`run_bash` runs model-written commands directly on this machine
with no sandbox, and the fan-out runs several of those subagents in parallel.
This is for trusted local experimentation only; add sandboxing before any other
use.

Spec: docs/superpowers/specs/2026-06-01-orchestration-mode-design.html
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids an import cycle
    from anthropic import AsyncAnthropic

    from orchestration.orchestration_mode import ModeConfig

logger = structlog.get_logger(__name__)


SUBAGENT_SYSTEM = (
    "You are one agent in a larger parallel fan-out, assigned a single subtask. "
    "Investigate it directly, using bash to check facts rather than guessing, and "
    "finish by calling report_findings exactly once. Return findings, not narration."
)


WORKFLOW_TOOL: dict[str, Any] = {
    "name": "Workflow",
    "description": (
        "Orchestrate a multi-agent workflow: split a large task into independent "
        "subtasks and run them as parallel agents, then collect their results.\n\n"
        "Opt-in: only use this tool when the user explicitly asks for a workflow, or "
        "when a system message confirms that orchestration mode is on.\n\n"
        "Quality patterns: adversarial verification (a second wave of agents checks the "
        "first wave's findings against the source), a completeness critic (one agent "
        "hunts for what the others missed), and multi-phase sequencing (understand, "
        "design, implement, and review as separate workflow calls, reading results "
        "between phases). A useful default is hybrid: scout inline first to discover the "
        "work-list, then fan out over it.\n\n"
        "Standing consent: while a system message confirms orchestration mode is on, "
        "that opt-in is standing. Author and run a workflow for every substantive task "
        "by default, and lean toward verifying findings adversarially. Work solo only on "
        "conversational turns or trivial mechanical edits. When a system message says the "
        "mode is off, revert to the opt-in rule above."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "subtasks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Independent subtask prompts to run as parallel agents",
            }
        },
        "required": ["subtasks"],
    },
}


BASH_TOOL: dict[str, Any] = {"type": "bash_20250124", "name": "bash"}


REPORT_TOOL: dict[str, Any] = {
    "name": "report_findings",
    "description": (
        "Report the final findings for your subtask. Call this exactly once, when you "
        "are done investigating; it ends your task."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Two or three sentences of synthesis",
            },
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {
                            "type": "string",
                            "description": "The finding, one sentence",
                        },
                        "evidence": {
                            "type": "string",
                            "description": "How it was verified (file, line, or command output)",
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["high", "medium", "low", "info"],
                        },
                    },
                    "required": ["claim", "evidence", "severity"],
                },
            },
        },
        "required": ["summary", "findings"],
    },
}


def normalize_subtasks(raw: Any) -> list[str]:
    """Accept the subtasks input in whatever shape the model emits.

    The model may pass an array, the array JSON-encoded as a single string, or a
    newline-separated list. Anything unusable normalizes to an empty list.
    """
    value = raw
    if isinstance(raw, str):
        try:
            value = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            value = raw.splitlines() if "\n" in raw else [raw]
    if not isinstance(value, list):
        return []
    return [task.strip() for task in value if isinstance(task, str) and task.strip()]


async def run_bash(command: str, *, timeout_seconds: int, max_chars: int) -> tuple[str, bool]:
    """Run a shell command, returning ``(output, is_error)``.

    No sandbox: the command runs with this process's permissions. Output is
    truncated to ``max_chars`` so a runaway command cannot flood the context.
    """
    logger.info("orchestration_mode.bash", command=command)
    try:
        proc = await asyncio.create_subprocess_exec(
            "bash",
            "-c",
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except OSError as exc:
        return f"bash error: {exc}", True

    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        return f"command timed out after {timeout_seconds}s", True

    output = stdout.decode("utf-8", "replace").strip() or "(no output)"
    if len(output) > max_chars:
        output = output[:max_chars] + f"\n(truncated at {max_chars} chars)"
    if proc.returncode != 0:
        return f"(exit code {proc.returncode})\n{output}", True
    return output, False


async def handle_bash_block(block: Any, config: ModeConfig) -> tuple[str, bool]:
    """Execute one ``bash`` tool-use block. Honours the ``restart`` action."""
    payload = getattr(block, "input", None) or {}
    if payload.get("restart") is True:
        return "Shell restarted.", False
    command = payload.get("command")
    if not isinstance(command, str) or not command:
        return "bash error: no command was provided.", True
    return await run_bash(
        command,
        timeout_seconds=config.bash_timeout_seconds,
        max_chars=config.tool_result_max_chars,
    )


async def run_subagent(client: AsyncAnthropic, prompt: str, config: ModeConfig) -> str:
    """One subagent: a small nested agent loop with bash + report_findings.

    Subagents inherit the main loop's effort level and run on the cheaper
    ``subagent_model``. Returns the structured ``report_findings`` JSON, or the
    final text if the subagent stops without reporting.
    """
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    for _ in range(config.max_subagent_turns):
        async with client.messages.stream(
            model=config.subagent_model,
            max_tokens=config.max_tokens,
            system=SUBAGENT_SYSTEM,
            thinking={"type": "adaptive"},
            output_config={"effort": config.effort},
            tools=[BASH_TOOL, REPORT_TOOL],
            messages=messages,
        ) as stream:
            response = await stream.get_final_message()
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "pause_turn":
            continue
        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
            if response.stop_reason == "max_tokens":
                text += "\n\n(warning: subagent response was truncated at max_tokens)"
            return text

        tool_results: list[dict[str, Any]] = []
        report: str | None = None
        for block in response.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            if block.name == "report_findings":
                report = json.dumps(block.input, indent=2)
                output, is_error = "Findings recorded.", False
            elif block.name == "bash":
                output, is_error = await handle_bash_block(block, config)
            else:
                output, is_error = f"unknown tool: {block.name}", True
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                    "is_error": is_error,
                }
            )
        if report is not None:
            return report
        messages.append({"role": "user", "content": tool_results})
    return "(subagent hit the turn limit before finishing)"


async def run_workflow(
    client: AsyncAnthropic, raw_subtasks: Any, config: ModeConfig
) -> tuple[str, bool]:
    """Run subtasks as parallel subagents and collect their structured reports.

    Caps the number run at ``config.max_parallel_agents`` and surfaces any
    overflow (never silently truncated). One failing subagent degrades to an
    error string instead of ending the run.
    """
    all_subtasks = normalize_subtasks(raw_subtasks)
    subtasks = all_subtasks[: config.max_parallel_agents]
    dropped = len(all_subtasks) - len(subtasks)
    if not subtasks:
        return "Workflow error: no usable subtasks were provided.", True

    logger.info("orchestration_mode.fanout", count=len(subtasks), dropped=dropped)
    semaphore = asyncio.Semaphore(config.max_parallel_agents)

    async def _bounded(prompt: str) -> str:
        async with semaphore:
            return await run_subagent(client, prompt, config)

    results = await asyncio.gather(
        *(_bounded(prompt) for prompt in subtasks), return_exceptions=True
    )

    sections: list[str] = []
    for index, (task, result) in enumerate(zip(subtasks, results, strict=True)):
        if isinstance(result, BaseException):
            # Isolation boundary: one bad subagent must not end the run.
            result = f"(subagent failed: {type(result).__name__}: {result})"
        sections.append(f"[agent {index + 1}: {task}]\n{result}")

    joined = "\n\n".join(sections)
    if dropped > 0:
        joined = (
            f"(note: {dropped} subtasks beyond max_parallel_agents="
            f"{config.max_parallel_agents} were not run; rerun them in a follow-up "
            f"Workflow call)\n\n" + joined
        )
    return joined, False
