"""Tests for GeneratorAgent — Gemini 3 Pro image generation."""

from unittest.mock import patch

import pytest

from skyyrose.elite_studio.agents.generator_agent import GeneratorAgent


@pytest.fixture
def agent():
    return GeneratorAgent()


class TestGeneratorAgent:
    @patch("skyyrose.elite_studio.agents.generator_agent.get_reference_image_path")
    def test_no_reference_image(self, mock_path, agent):
        mock_path.return_value = ""
        result = agent.generate("fake-001", "front", "some spec")
        assert not result.success
        assert "No reference image" in result.error

    @patch("skyyrose.elite_studio.gemini_rest.generate_image")
    @patch("skyyrose.elite_studio.agents.generator_agent.image_to_base64")
    @patch("skyyrose.elite_studio.agents.generator_agent.get_reference_image_path")
    def test_success(self, mock_path, mock_b64, mock_gen, agent, tmp_path):
        mock_path.return_value = "/fake/image.jpg"
        mock_b64.return_value = "AAAA"

        # Mock REST response with image data
        mock_gen.return_value = {
            "success": True,
            "image_data": b"\xff\xd8\xff\xe0fake-jpeg",
            "mime_type": "image/jpeg",
        }

        # Override OUTPUT_DIR to tmp
        with patch("skyyrose.elite_studio.agents.generator_agent.OUTPUT_DIR", tmp_path):
            result = agent.generate("br-001", "front", "test spec")

        assert result.success
        assert result.provider == "google"
        assert "br-001-model-front-gemini.jpg" in result.output_path

    @patch("skyyrose.elite_studio.gemini_rest.generate_image")
    @patch("skyyrose.elite_studio.agents.generator_agent.image_to_base64")
    @patch("skyyrose.elite_studio.agents.generator_agent.get_reference_image_path")
    def test_no_image_in_response(self, mock_path, mock_b64, mock_gen, agent, tmp_path):
        mock_path.return_value = "/fake/image.jpg"
        mock_b64.return_value = "AAAA"

        # REST client returns failure when no image in response
        mock_gen.return_value = {
            "success": False,
            "error": "No image in response. Parts: [text(42 chars)]",
        }

        with patch("skyyrose.elite_studio.agents.generator_agent.OUTPUT_DIR", tmp_path):
            result = agent.generate("br-001", "front", "test spec")

        assert not result.success
        assert "No image in response" in result.error

    @patch("skyyrose.elite_studio.gemini_rest.generate_image")
    @patch("skyyrose.elite_studio.agents.generator_agent.image_to_base64")
    @patch("skyyrose.elite_studio.agents.generator_agent.get_reference_image_path")
    def test_api_error(self, mock_path, mock_b64, mock_gen, agent):
        mock_path.return_value = "/fake/image.jpg"
        mock_b64.return_value = "AAAA"

        # REST client raises exception on network failure
        mock_gen.side_effect = Exception("API Error")

        result = agent.generate("br-001", "front", "test spec")
        assert not result.success
        assert "API Error" in result.error

    def test_build_prompt(self, agent):
        prompt = agent._build_prompt("Black crewneck with rose gold logo", "front", "4K")
        assert "Black crewneck" in prompt
        assert "front" in prompt
        assert "4K" in prompt
        assert "CRITICAL" in prompt


class TestGeneratorRetry:
    @patch("skyyrose.elite_studio.retry.time.sleep")
    @patch("skyyrose.elite_studio.gemini_rest.generate_image")
    @patch("skyyrose.elite_studio.agents.generator_agent.image_to_base64")
    @patch("skyyrose.elite_studio.agents.generator_agent.get_reference_image_path")
    def test_retry_on_timeout(self, mock_path, mock_b64, mock_gen, mock_sleep, agent, tmp_path):
        mock_path.return_value = "/fake/image.jpg"
        mock_b64.return_value = "AAAA"

        # First call returns transient error, second succeeds
        mock_gen.side_effect = [
            {"success": False, "error": "The read operation timed out"},
            {"success": True, "image_data": b"\xff\xd8\xff\xe0fake", "mime_type": "image/jpeg"},
        ]

        with patch("skyyrose.elite_studio.agents.generator_agent.OUTPUT_DIR", tmp_path):
            result = agent.generate("br-001", "front", "spec")

        assert result.success
        mock_sleep.assert_called_once()
