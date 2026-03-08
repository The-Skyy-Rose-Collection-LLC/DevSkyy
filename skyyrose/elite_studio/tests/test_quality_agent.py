"""Tests for QualityAgent — Claude Sonnet verification."""

from unittest.mock import MagicMock, patch

import pytest

from skyyrose.elite_studio.agents.quality_agent import QualityAgent


@pytest.fixture
def agent():
    return QualityAgent()


class TestQualityAgent:
    @patch("skyyrose.elite_studio.agents.quality_agent.get_anthropic_client")
    @patch("skyyrose.elite_studio.agents.quality_agent.resize_for_claude")
    def test_pass_result(self, mock_resize, mock_client, agent):
        mock_resize.return_value = "AAAA"

        # Mock Claude response with valid JSON
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[
            0
        ].text = '{"overall_status": "pass", "logo_accuracy": {"status": "pass", "notes": "exact"}, "garment_accuracy": {"status": "pass", "notes": "good"}, "photo_quality": {"status": "pass", "notes": "clean"}, "recommendation": "approve"}'

        mock_claude = MagicMock()
        mock_claude.messages.create.return_value = mock_response
        mock_client.return_value = mock_claude

        result = agent.verify("/fake/image.jpg", "test spec")
        assert result.success
        assert result.overall_status == "pass"
        assert result.recommendation == "approve"

    @patch("skyyrose.elite_studio.agents.quality_agent.get_anthropic_client")
    @patch("skyyrose.elite_studio.agents.quality_agent.resize_for_claude")
    def test_fail_result(self, mock_resize, mock_client, agent):
        mock_resize.return_value = "AAAA"

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[
            0
        ].text = '```json\n{"overall_status": "fail", "logo_accuracy": {"status": "fail", "notes": "wrong"}, "garment_accuracy": {"status": "warn", "notes": "close"}, "photo_quality": {"status": "pass", "notes": "ok"}, "recommendation": "regenerate"}\n```'

        mock_claude = MagicMock()
        mock_claude.messages.create.return_value = mock_response
        mock_client.return_value = mock_claude

        result = agent.verify("/fake/image.jpg", "test spec")
        assert result.success
        assert result.overall_status == "fail"
        assert result.recommendation == "regenerate"

    @patch("skyyrose.elite_studio.agents.quality_agent.get_anthropic_client")
    @patch("skyyrose.elite_studio.agents.quality_agent.resize_for_claude")
    def test_unparseable_json(self, mock_resize, mock_client, agent):
        mock_resize.return_value = "AAAA"

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[
            0
        ].text = "The image looks great overall but I can't provide structured JSON."

        mock_claude = MagicMock()
        mock_claude.messages.create.return_value = mock_response
        mock_client.return_value = mock_claude

        result = agent.verify("/fake/image.jpg", "test spec")
        assert result.success
        assert result.overall_status == "unknown"
        assert result.recommendation == "manual_review"
        assert result.details.get("parsed") is False

    @patch("skyyrose.elite_studio.agents.quality_agent.get_anthropic_client")
    @patch("skyyrose.elite_studio.agents.quality_agent.resize_for_claude")
    def test_api_error(self, mock_resize, mock_client, agent):
        mock_resize.return_value = "AAAA"

        mock_claude = MagicMock()
        mock_claude.messages.create.side_effect = Exception("API Error")
        mock_client.return_value = mock_claude

        result = agent.verify("/fake/image.jpg", "test spec")
        assert not result.success
        assert "API Error" in result.error


class TestQualityRetry:
    @patch("skyyrose.elite_studio.retry.time.sleep")
    @patch("skyyrose.elite_studio.agents.quality_agent.get_anthropic_client")
    @patch("skyyrose.elite_studio.agents.quality_agent.resize_for_claude")
    def test_retry_on_overloaded(self, mock_resize, mock_client, mock_sleep, agent):
        mock_resize.return_value = "AAAA"

        # First call fails with overloaded, second succeeds
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = '{"overall_status": "pass", "recommendation": "approve"}'

        mock_claude = MagicMock()
        mock_claude.messages.create.side_effect = [
            Exception("overloaded_error"),
            mock_response,
        ]
        mock_client.return_value = mock_claude

        result = agent.verify("/fake/image.jpg", "test spec")
        assert result.success
        mock_sleep.assert_called_once()


class TestParseResponse:
    def test_bare_code_fence(self, agent):
        """JSON wrapped in ``` (no json tag) should still parse."""
        text = '```\n{"overall_status": "warn", "recommendation": "manual_review"}\n```'
        result = agent._parse_response(text)
        assert result.success
        assert result.overall_status == "warn"
        assert result.recommendation == "manual_review"

    def test_plain_json(self, agent):
        """Plain JSON without code fences should parse."""
        text = '{"overall_status": "pass", "recommendation": "approve"}'
        result = agent._parse_response(text)
        assert result.success
        assert result.overall_status == "pass"


class TestQCPrompt:
    def test_prompt_includes_spec(self, agent):
        prompt = agent._build_qc_prompt("Black crewneck with rose gold logo")
        assert "Black crewneck" in prompt
        assert "overall_status" in prompt
        assert "recommendation" in prompt
