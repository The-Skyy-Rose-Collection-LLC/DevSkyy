from pathlib import Path
from unittest.mock import AsyncMock, patch

from skyyrose.elite_studio.agents.generator_agent import GeneratorAgent


def _make_agent(tmp_path):
    with patch("skyyrose.elite_studio.agents.generator_agent.OpenAI"):
        return GeneratorAgent(output_dir=str(tmp_path))


async def test_generate_returns_generation_result(tmp_path):
    agent = _make_agent(tmp_path)

    fake_img = b"\x89PNG\r\n\x1a\n" + b"\x00" * 200  # fake PNG bytes

    with (
        patch.object(agent, "_generate_gpt_image", new=AsyncMock(return_value=fake_img)),
        patch.object(agent, "_generate_gemini_image", new=AsyncMock(return_value=fake_img)),
        patch.object(agent, "_pick_winner", return_value="a"),
        patch.object(agent, "execute", new=AsyncMock(return_value=None)),
    ):
        result = await agent.generate(
            sku="br-004",
            view="front",
            generation_spec="black hoodie ghost mannequin spec",
        )

    assert result.success
    assert result.output_path.endswith(".webp") or result.output_path.endswith(".png")
    assert Path(result.output_path).exists()


async def test_generate_fails_if_both_models_fail(tmp_path):
    agent = _make_agent(tmp_path)

    with (
        patch.object(
            agent, "_generate_gpt_image", new=AsyncMock(side_effect=RuntimeError("quota"))
        ),
        patch.object(
            agent, "_generate_gemini_image", new=AsyncMock(side_effect=RuntimeError("503"))
        ),
        patch.object(agent, "execute", new=AsyncMock(return_value=None)),
    ):
        result = await agent.generate(sku="br-004", view="front", generation_spec="spec")

    assert not result.success
    assert "quota" in result.error or "503" in result.error


def test_winner_selection_prefers_a_on_tie(tmp_path):
    """When scores are equal, agent A (GPT-Image) wins."""
    agent = _make_agent(tmp_path)
    winner = agent._pick_winner(score_a=85, score_b=85, path_a="/tmp/a.png", path_b="/tmp/b.png")
    assert winner == "a"
