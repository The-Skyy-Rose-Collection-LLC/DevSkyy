"""Tests for VisionAgent — multi-provider analysis."""

from unittest.mock import MagicMock, patch

import pytest

from skyyrose.elite_studio.agents.vision_agent import VisionAgent


@pytest.fixture
def agent():
    return VisionAgent()


class TestVisionAgentAnalyze:
    """Test the high-level analyze() method."""

    @patch("skyyrose.elite_studio.agents.vision_agent.get_reference_image_path")
    def test_no_reference_image(self, mock_path, agent):
        mock_path.return_value = ""
        result = agent.analyze("fake-001")
        assert not result.success
        assert "No reference image" in result.error

    @patch("skyyrose.elite_studio.agents.vision_agent.image_to_base64")
    @patch("skyyrose.elite_studio.agents.vision_agent.get_reference_image_path")
    @patch("skyyrose.elite_studio.agents.vision_agent.load_product_data")
    def test_both_providers_succeed(self, mock_load, mock_path, mock_b64, agent):
        from skyyrose.elite_studio.models import ProductData

        mock_load.return_value = ProductData(sku="br-001", collection="black-rose")
        mock_path.return_value = "/fake/image.jpg"
        mock_b64.return_value = "AAAA"  # minimal base64

        # Mock both providers
        agent._analyze_gemini = MagicMock(
            return_value=MagicMock(
                success=True,
                provider="google",
                model="flash",
                analysis="Gemini analysis",
                char_count=15,
                error="",
            )
        )
        agent._analyze_openai = MagicMock(
            return_value=MagicMock(
                success=True,
                provider="openai",
                model="gpt-4o",
                analysis="OpenAI analysis",
                char_count=15,
                error="",
            )
        )

        result = agent.analyze("br-001")
        assert result.success
        assert result.provider_count == 2
        assert "gemini" in result.providers_used
        assert "openai" in result.providers_used
        assert "SYNTHESIZED" in result.unified_spec

    @patch("skyyrose.elite_studio.agents.vision_agent.image_to_base64")
    @patch("skyyrose.elite_studio.agents.vision_agent.get_reference_image_path")
    @patch("skyyrose.elite_studio.agents.vision_agent.load_product_data")
    def test_gemini_only_fallback(self, mock_load, mock_path, mock_b64, agent):
        from skyyrose.elite_studio.models import ProductData

        mock_load.return_value = ProductData(sku="br-001", collection="black-rose")
        mock_path.return_value = "/fake/image.jpg"
        mock_b64.return_value = "AAAA"

        agent._analyze_gemini = MagicMock(
            return_value=MagicMock(
                success=True,
                provider="google",
                model="flash",
                analysis="Gemini only",
                char_count=11,
                error="",
            )
        )
        agent._analyze_openai = MagicMock(
            return_value=MagicMock(
                success=False,
                provider="openai",
                model="gpt-4o",
                analysis="",
                char_count=0,
                error="Rate limited",
            )
        )

        result = agent.analyze("br-001")
        assert result.success
        assert result.provider_count == 1
        assert "gemini" in result.providers_used
        assert result.unified_spec == "Gemini only"

    @patch("skyyrose.elite_studio.agents.vision_agent.image_to_base64")
    @patch("skyyrose.elite_studio.agents.vision_agent.get_reference_image_path")
    @patch("skyyrose.elite_studio.agents.vision_agent.load_product_data")
    def test_openai_only_fallback(self, mock_load, mock_path, mock_b64, agent):
        from skyyrose.elite_studio.models import ProductData

        mock_load.return_value = ProductData(sku="br-001", collection="black-rose")
        mock_path.return_value = "/fake/image.jpg"
        mock_b64.return_value = "AAAA"

        agent._analyze_gemini = MagicMock(
            return_value=MagicMock(
                success=False,
                provider="google",
                model="flash",
                analysis="",
                char_count=0,
                error="Timeout",
            )
        )
        agent._analyze_openai = MagicMock(
            return_value=MagicMock(
                success=True,
                provider="openai",
                model="gpt-4o",
                analysis="OpenAI only",
                char_count=11,
                error="",
            )
        )

        result = agent.analyze("br-001")
        assert result.success
        assert result.provider_count == 1
        assert "openai" in result.providers_used

    @patch("skyyrose.elite_studio.agents.vision_agent.image_to_base64")
    @patch("skyyrose.elite_studio.agents.vision_agent.get_reference_image_path")
    @patch("skyyrose.elite_studio.agents.vision_agent.load_product_data")
    def test_both_providers_fail(self, mock_load, mock_path, mock_b64, agent):
        from skyyrose.elite_studio.models import ProductData

        mock_load.return_value = ProductData(sku="br-001", collection="black-rose")
        mock_path.return_value = "/fake/image.jpg"
        mock_b64.return_value = "AAAA"

        agent._analyze_gemini = MagicMock(
            return_value=MagicMock(
                success=False,
                provider="google",
                model="flash",
                analysis="",
                char_count=0,
                error="Gemini down",
            )
        )
        agent._analyze_openai = MagicMock(
            return_value=MagicMock(
                success=False,
                provider="openai",
                model="gpt-4o",
                analysis="",
                char_count=0,
                error="OpenAI down",
            )
        )

        result = agent.analyze("br-001")
        assert not result.success
        assert "All vision providers failed" in result.error


class TestAnalyzeGemini:
    """Test _analyze_gemini with mocked REST client."""

    @patch("skyyrose.elite_studio.gemini_rest.analyze_vision")
    def test_success(self, mock_analyze, agent):
        mock_analyze.return_value = {"success": True, "text": "Detailed analysis here"}

        result = agent._analyze_gemini("prompt", "AAAA")
        assert result.success
        assert result.provider == "google"
        assert result.analysis == "Detailed analysis here"
        assert result.char_count == len("Detailed analysis here")

    @patch("skyyrose.elite_studio.gemini_rest.analyze_vision")
    def test_api_returns_failure(self, mock_analyze, agent):
        mock_analyze.return_value = {"success": False, "error": "Bad request"}

        result = agent._analyze_gemini("prompt", "AAAA")
        assert not result.success
        assert "Bad request" in result.error

    @patch("skyyrose.elite_studio.gemini_rest.analyze_vision")
    def test_exception(self, mock_analyze, agent):
        mock_analyze.side_effect = Exception("Connection refused")

        result = agent._analyze_gemini("prompt", "AAAA")
        assert not result.success
        assert "Connection refused" in result.error


class TestAnalyzeOpenAI:
    """Test _analyze_openai with mocked OpenAI client."""

    @patch("skyyrose.elite_studio.agents.vision_agent.get_openai_client")
    def test_success(self, mock_get_client, agent):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "OpenAI sees a crewneck"

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = agent._analyze_openai("prompt", "AAAA")
        assert result.success
        assert result.provider == "openai"
        assert result.analysis == "OpenAI sees a crewneck"
        assert result.char_count == len("OpenAI sees a crewneck")

    @patch("skyyrose.elite_studio.agents.vision_agent.get_openai_client")
    def test_api_error(self, mock_get_client, agent):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Rate limit")
        mock_get_client.return_value = mock_client

        result = agent._analyze_openai("prompt", "AAAA")
        assert not result.success
        assert "Rate limit" in result.error

    @patch("skyyrose.elite_studio.agents.vision_agent.get_openai_client")
    def test_empty_response(self, mock_get_client, agent):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None  # Empty response

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = agent._analyze_openai("prompt", "AAAA")
        assert result.success
        assert result.analysis == ""
        assert result.char_count == 0


class TestVisionAgentSynthesize:
    def test_single_result(self, agent):
        from skyyrose.elite_studio.models import VisionAnalysis

        results = [VisionAnalysis(success=True, provider="google", model="flash", analysis="Solo")]
        unified = agent._synthesize(results, ["gemini"])
        assert unified == "Solo"

    def test_dual_results(self, agent):
        from skyyrose.elite_studio.models import VisionAnalysis

        results = [
            VisionAnalysis(success=True, provider="google", model="flash", analysis="Gemini part"),
            VisionAnalysis(success=True, provider="openai", model="gpt-4o", analysis="OpenAI part"),
        ]
        unified = agent._synthesize(results, ["gemini", "openai"])
        assert "SYNTHESIZED" in unified
        assert "GOOGLE ANALYSIS" in unified
        assert "OPENAI ANALYSIS" in unified
        assert "Gemini part" in unified
        assert "OpenAI part" in unified
