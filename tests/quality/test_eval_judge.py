import pytest

from evaluation.judge import ClaudeJudge, anthropic_cost_usd, image_block


class _Block:
    type = "tool_use"

    def __init__(self, inp):
        self.input = inp
        self.name = "render_qc_verdict"


class _Usage:
    def __init__(self):
        self.input_tokens = 1200
        self.output_tokens = 180


class _Resp:
    def __init__(self, inp):
        self.content = [_Block(inp)]
        self.usage = _Usage()
        self.stop_reason = "tool_use"


class _Messages:
    def __init__(self, inp):
        self._inp = inp
        self.calls = []

    def create(self, **kw):
        self.calls.append(kw)
        return _Resp(self._inp)


class _Client:
    def __init__(self, inp):
        self.messages = _Messages(inp)


def test_judge_returns_tool_input_and_cost():
    payload = {
        "visual_analysis": "navy bomber, white script",
        "is_single_photograph": True,
        "reason": "pass",
    }
    client = _Client(payload)
    judge = ClaudeJudge(client=client, model="claude-sonnet-4-6")
    out, cost = judge.run(
        messages=[{"role": "user", "content": [{"type": "text", "text": "x"}]}],
        tool={"name": "render_qc_verdict", "input_schema": {"type": "object"}},
    )
    assert out["is_single_photograph"] is True
    assert out["visual_analysis"].startswith("navy")
    assert cost > 0
    sent = client.messages.calls[0]
    assert sent["tool_choice"] == {
        "type": "tool",
        "name": "render_qc_verdict",
        "disable_parallel_tool_use": True,
    }


def test_cost_formula():
    assert round(anthropic_cost_usd("claude-sonnet-4-6", 1_000_000, 0), 4) == 3.0
    assert round(anthropic_cost_usd("claude-sonnet-4-6", 0, 1_000_000), 4) == 15.0


def test_judge_raises_when_no_tool_use():
    class _Empty(_Client):
        def __init__(self):
            self.messages = type(
                "M",
                (),
                {
                    "create": lambda s, **k: type(
                        "R", (), {"content": [], "usage": _Usage(), "stop_reason": "end_turn"}
                    )()
                },
            )()

    judge = ClaudeJudge(client=_Empty(), model="claude-sonnet-4-6")
    with pytest.raises(RuntimeError):
        judge.run(messages=[], tool={"name": "t", "input_schema": {}})


def test_cost_formula_unknown_model_falls_back_to_sonnet():
    assert anthropic_cost_usd("claude-future-99", 1_000_000, 0) == 3.0


def test_image_block_rejects_bad_media_type():
    with pytest.raises(ValueError):
        image_block("x", "jpg")


def test_image_block_valid():
    assert image_block("abc", "image/png")["source"]["media_type"] == "image/png"
