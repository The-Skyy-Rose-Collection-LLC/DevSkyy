from unittest.mock import patch

from skyyrose.elite_studio.agents.quality_agent import QualityAgent


def _make_agent():
    with patch("openai.OpenAI"):
        return QualityAgent()


def test_both_pass_at_80_threshold(tmp_path):
    """min(A,B) ≥ 80 → overall pass."""
    img = tmp_path / "render.webp"
    img.write_bytes(b"RIFF" + b"\x00" * 100)
    agent = _make_agent()
    with (
        patch.object(agent, "_score_openai", return_value=(85, False, "looks good")),
        patch.object(agent, "_score_gemini", return_value=(82, False, "approved")),
    ):
        result = agent.verify(
            image_path=str(img), expected_spec="br-004 hoodie", style="ghost_mannequin"
        )
    assert result.success
    assert result.overall_status == "pass"
    assert result.recommendation == "approve"


def test_min_score_below_80_fails(tmp_path):
    """min(A,B) < 80 → overall fail → recommend regenerate."""
    img = tmp_path / "render.webp"
    img.write_bytes(b"RIFF" + b"\x00" * 100)
    agent = _make_agent()
    with (
        patch.object(agent, "_score_openai", return_value=(90, False, "good")),
        patch.object(agent, "_score_gemini", return_value=(72, False, "drape off")),
    ):
        result = agent.verify(
            image_path=str(img), expected_spec="br-004 hoodie", style="ghost_mannequin"
        )
    assert result.overall_status == "fail"
    assert result.recommendation == "regenerate"


def test_identity_mismatch_auto_rejects(tmp_path):
    """Either model flagging product identity mismatch → auto-reject regardless of score."""
    img = tmp_path / "render.webp"
    img.write_bytes(b"RIFF" + b"\x00" * 100)
    agent = _make_agent()
    with (
        patch.object(
            agent,
            "_score_openai",
            return_value=(88, True, "IDENTITY MISMATCH: shows baseball not hockey"),
        ),
        patch.object(agent, "_score_gemini", return_value=(85, False, "ok")),
    ):
        result = agent.verify(
            image_path=str(img), expected_spec="br-011 hockey jersey", style="ghost_mannequin"
        )
    assert result.overall_status == "fail"
    assert result.recommendation == "regenerate"
    assert (
        "identity" in result.details.get("reject_reason", "").lower()
        or "mismatch" in result.details.get("reject_reason", "").lower()
    )
