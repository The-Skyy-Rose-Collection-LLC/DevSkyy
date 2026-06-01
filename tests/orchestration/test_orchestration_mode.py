"""Tests for orchestration mode (orchestration/orchestration_mode.py + _tools).

The orchestration-mode loop is the first streaming tool-use feedback loop in
the repo. These tests pin the contract WITHOUT any live API call — the
Anthropic client is faked at the boundary (mirrors the AsyncMock injection in
tests/llm/test_verification.py). The only real subprocesses are the local bash
tests, which run harmless commands (echo / sleep / printf).

Design spec: docs/superpowers/specs/2026-06-01-orchestration-mode-design.html
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from orchestration.orchestration_mode import (
    MODE_ENTER,
    MODE_EXIT,
    MODE_REFRESH,
    SYSTEM_PROMPT,
    ModeAgent,
    ModeConfig,
    ReminderTransport,
)
from orchestration.orchestration_mode_tools import (
    WORKFLOW_TOOL,
    handle_bash_block,
    normalize_subtasks,
    run_bash,
    run_workflow,
)

# ---------------------------------------------------------------------------
# Fakes — stand in for the Anthropic streaming client at the boundary.
# ---------------------------------------------------------------------------


def _text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _tool_block(name: str, payload: dict, block_id: str = "tool-1") -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", name=name, input=payload, id=block_id)


def _message(stop_reason: str, content: list) -> SimpleNamespace:
    return SimpleNamespace(stop_reason=stop_reason, content=content)


class _FakeStream:
    """Async context manager mirroring client.messages.stream(...)."""

    def __init__(self, message: SimpleNamespace) -> None:
        self._message = message

    async def __aenter__(self) -> _FakeStream:
        return self

    async def __aexit__(self, *exc: object) -> bool:
        return False

    async def get_final_message(self) -> SimpleNamespace:
        return self._message


class _FakeMessages:
    def __init__(self, messages: list[SimpleNamespace]) -> None:
        self._queue = list(messages)
        self.calls: list[dict] = []

    def stream(self, **kwargs: object) -> _FakeStream:
        self.calls.append(kwargs)
        return _FakeStream(self._queue.pop(0))


class _FakeClient:
    def __init__(self, messages: list[SimpleNamespace]) -> None:
        self.messages = _FakeMessages(messages)


def _agent(messages: list[SimpleNamespace], **kwargs: object) -> ModeAgent:
    return ModeAgent(client=_FakeClient(messages), **kwargs)


# ---------------------------------------------------------------------------
# Mode state machine — pure, no API.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_enter_emitted_once_then_silent() -> None:
    agent = _agent([], mode_on=True)
    assert agent._due_reminder_texts() == [MODE_ENTER]
    # Not yet at the refresher threshold → nothing more owed.
    assert agent._due_reminder_texts() == []


@pytest.mark.unit
def test_refresh_emitted_at_threshold() -> None:
    config = ModeConfig(turns_between_refreshers=3)
    agent = _agent([], config=config, mode_on=True)
    agent._due_reminder_texts()  # consumes ENTER, resets counter
    agent._turns_since_reminder = 3
    assert agent._due_reminder_texts() == [MODE_REFRESH]


@pytest.mark.unit
def test_exit_emitted_once_after_turn_off() -> None:
    agent = _agent([], mode_on=True)
    agent._due_reminder_texts()  # ENTER
    agent.set_mode(False)
    assert agent._due_reminder_texts() == [MODE_EXIT]
    # Mode off → nothing further owed.
    assert agent._due_reminder_texts() == []


@pytest.mark.unit
def test_no_exit_if_never_announced() -> None:
    agent = _agent([], mode_on=True)
    agent.set_mode(False)  # turned off before any ENTER was emitted
    assert agent._due_reminder_texts() == []


@pytest.mark.unit
def test_setmode_noop_when_unchanged() -> None:
    agent = _agent([], mode_on=True)
    agent._due_reminder_texts()
    agent.set_mode(True)  # already on
    assert agent._due_reminder_texts() == []


# ---------------------------------------------------------------------------
# Reminder transport.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_user_reminder_folds_into_single_user_turn() -> None:
    agent = _agent([], config=ModeConfig(reminder_transport=ReminderTransport.USER_REMINDER))
    messages = agent._build_user_messages("hi there", ["HELLO"])
    # Folded into ONE user turn — no consecutive same-role turns.
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    content = messages[0]["content"]
    assert isinstance(content, list)
    assert content[0] == {"type": "text", "text": "hi there"}
    assert "<system-reminder>" in content[1]["text"]
    assert "HELLO" in content[1]["text"]


@pytest.mark.unit
def test_system_role_emits_standalone_system_message() -> None:
    agent = _agent([], config=ModeConfig(reminder_transport=ReminderTransport.SYSTEM_ROLE))
    messages = agent._build_user_messages("hi there", ["HELLO"])
    assert messages[0] == {"role": "user", "content": "hi there"}
    assert messages[1] == {"role": "system", "content": "HELLO"}


@pytest.mark.unit
def test_no_reminder_yields_plain_user_turn() -> None:
    agent = _agent([])
    assert agent._build_user_messages("hi there", []) == [{"role": "user", "content": "hi there"}]


# ---------------------------------------------------------------------------
# Standing consent text lives in the tool description.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_workflow_tool_carries_standing_consent() -> None:
    description = WORKFLOW_TOOL["description"].lower()
    assert "standing consent" in description
    assert "orchestration mode" in description
    assert WORKFLOW_TOOL["input_schema"]["required"] == ["subtasks"]


# ---------------------------------------------------------------------------
# normalize_subtasks — array / json-string / newline / junk.
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_normalize_subtasks_accepts_array() -> None:
    assert normalize_subtasks(["a", " b ", ""]) == ["a", "b"]


@pytest.mark.unit
def test_normalize_subtasks_accepts_json_string() -> None:
    assert normalize_subtasks('["x", "y"]') == ["x", "y"]


@pytest.mark.unit
def test_normalize_subtasks_accepts_newlines() -> None:
    assert normalize_subtasks("one\ntwo\n") == ["one", "two"]


@pytest.mark.unit
def test_normalize_subtasks_rejects_junk() -> None:
    assert normalize_subtasks(42) == []
    assert normalize_subtasks([1, 2, None]) == []


# ---------------------------------------------------------------------------
# Fan-out — cap + per-subagent failure isolation.
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_workflow_caps_and_notes_dropped(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def fake_subagent(client: object, prompt: str, config: object) -> str:
        calls.append(prompt)
        return f"done:{prompt}"

    monkeypatch.setattr("orchestration.orchestration_mode_tools.run_subagent", fake_subagent)
    config = ModeConfig(max_parallel_agents=3)
    subtasks = [f"task-{i}" for i in range(5)]
    output, is_error = await run_workflow(_FakeClient([]), subtasks, config)

    assert is_error is False
    assert len(calls) == 3  # capped
    assert "2 subtasks" in output  # 2 dropped, surfaced not silent


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_workflow_isolates_failed_subagent(monkeypatch: pytest.MonkeyPatch) -> None:
    async def flaky(client: object, prompt: str, config: object) -> str:
        if prompt == "boom":
            raise RuntimeError("kaboom")
        return f"ok:{prompt}"

    monkeypatch.setattr("orchestration.orchestration_mode_tools.run_subagent", flaky)
    output, is_error = await run_workflow(_FakeClient([]), ["fine", "boom"], ModeConfig())

    assert is_error is False
    assert "ok:fine" in output
    assert "subagent failed" in output.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_workflow_empty_is_error() -> None:
    output, is_error = await run_workflow(_FakeClient([]), [], ModeConfig())
    assert is_error is True


# ---------------------------------------------------------------------------
# turn() — streaming loop, tool dispatch, cache integrity, reminder placement.
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_turn_returns_text_on_end_turn() -> None:
    agent = _agent([_message("end_turn", [_text_block("final answer")])])
    result = await agent.turn("hi")
    assert result == "final answer"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_turn_places_reminder_after_user_turn() -> None:
    agent = _agent([_message("end_turn", [_text_block("ok")])], mode_on=True)
    await agent.turn("do the thing")
    # One user turn, reminder folded in as a trailing content block — the
    # user's text stays first so the cached prefix ahead of it is untouched.
    first = agent.messages[0]
    assert first["role"] == "user"
    assert first["content"][0] == {"type": "text", "text": "do the thing"}
    assert "<system-reminder>" in first["content"][1]["text"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_turn_system_prefix_is_byte_stable() -> None:
    agent = _agent(
        [
            _message("tool_use", [_tool_block("bash", {"command": "echo hi"})]),
            _message("end_turn", [_text_block("done")]),
        ]
    )
    await agent.turn("run something")
    systems = [call["system"] for call in agent._client.messages.calls]
    assert len(systems) == 2
    assert all(s == SYSTEM_PROMPT for s in systems)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_turn_dispatches_workflow(monkeypatch: pytest.MonkeyPatch) -> None:
    workflow_mock = AsyncMock(return_value=("fanned out", False))
    monkeypatch.setattr("orchestration.orchestration_mode.run_workflow", workflow_mock)
    agent = _agent(
        [
            _message("tool_use", [_tool_block("Workflow", {"subtasks": ["a", "b"]})]),
            _message("end_turn", [_text_block("synth")]),
        ]
    )
    result = await agent.turn("review repo")
    assert result == "synth"
    workflow_mock.assert_awaited_once()
    assert workflow_mock.await_args.args[1] == ["a", "b"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_turn_unknown_tool_is_error() -> None:
    agent = _agent(
        [
            _message("tool_use", [_tool_block("nope", {})]),
            _message("end_turn", [_text_block("recovered")]),
        ]
    )
    await agent.turn("x")
    # The tool_result fed back must be flagged is_error.
    tool_result_turn = agent.messages[-2]  # user turn carrying tool_result
    block = tool_result_turn["content"][0]
    assert block["is_error"] is True
    assert "unknown tool" in block["content"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_turn_pause_turn_continues() -> None:
    agent = _agent(
        [
            _message("pause_turn", [_text_block("thinking...")]),
            _message("end_turn", [_text_block("resumed answer")]),
        ]
    )
    result = await agent.turn("long task")
    assert result == "resumed answer"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_turn_max_tokens_drops_truncated_turn() -> None:
    agent = _agent([_message("max_tokens", [_text_block("partial")])])
    result = await agent.turn("x")
    assert "partial" in result
    assert "truncated" in result.lower()
    # The truncated assistant turn must not poison history.
    assert all(m.get("role") != "assistant" for m in agent.messages)


# ---------------------------------------------------------------------------
# Local bash tool.
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_bash_captures_output() -> None:
    output, is_error = await run_bash("echo hello", timeout_seconds=10, max_chars=8000)
    assert is_error is False
    assert "hello" in output


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_bash_truncates() -> None:
    output, _ = await run_bash("printf 'x%.0s' $(seq 1 500)", timeout_seconds=10, max_chars=50)
    assert "truncated" in output.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_bash_times_out() -> None:
    output, is_error = await run_bash("sleep 5", timeout_seconds=1, max_chars=8000)
    assert is_error is True
    assert "timed out" in output.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_bash_nonzero_exit_flagged() -> None:
    output, is_error = await run_bash("exit 3", timeout_seconds=10, max_chars=8000)
    assert is_error is True
    assert "3" in output


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_bash_block_restart() -> None:
    block = SimpleNamespace(input={"restart": True})
    output, is_error = await handle_bash_block(block, ModeConfig())
    assert is_error is False
    assert "restart" in output.lower()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_bash_block_missing_command_is_error() -> None:
    block = SimpleNamespace(input={})
    output, is_error = await handle_bash_block(block, ModeConfig())
    assert is_error is True


# ---------------------------------------------------------------------------
# Live smoke — excluded by default addopts (`-m "not integration"`). Costs a
# few cents per run; run only with the founder's go-ahead:
#     pytest tests/orchestration/test_orchestration_mode.py -m integration
# It is the ONLY thing that proves the request shape end-to-end against the real
# API: the folded <system-reminder> transport (mode on) plus effort="xhigh" on
# the streaming endpoint with adaptive thinking. The prompt is deliberately
# trivial so the standing-consent instruction keeps the model solo (no fan-out,
# no local bash).
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_smoke_single_turn() -> None:
    import os

    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")

    agent = ModeAgent(mode_on=True)  # mode on → folded reminder is exercised
    result = await agent.turn("Reply with exactly one word: hi")
    assert isinstance(result, str)
    assert result.strip()
