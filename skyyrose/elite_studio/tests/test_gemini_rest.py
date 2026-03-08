"""Tests for gemini_rest — direct REST client for Gemini API."""

import base64
from unittest.mock import MagicMock, patch

from skyyrose.elite_studio import gemini_rest


class TestGetKey:
    @patch.dict("os.environ", {"GEMINI_API_KEY": "test-key-123"}, clear=False)
    def test_prefers_gemini_key(self):
        assert gemini_rest._get_key() == "test-key-123"

    @patch.dict(
        "os.environ",
        {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": "google-key-456"},
        clear=False,
    )
    def test_falls_back_to_google_key(self):
        assert gemini_rest._get_key() == "google-key-456"

    @patch.dict("os.environ", {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=False)
    def test_returns_empty_if_no_key(self):
        assert gemini_rest._get_key() == ""


class TestEndpoint:
    @patch.object(gemini_rest, "_get_key", return_value="abc123")
    def test_builds_url(self, _mock_key):
        url = gemini_rest._endpoint("gemini-3-flash-preview")
        assert "models/gemini-3-flash-preview:generateContent" in url
        assert "key=abc123" in url

    @patch.object(gemini_rest, "_get_key", return_value="abc123")
    def test_custom_method(self, _mock_key):
        url = gemini_rest._endpoint("gemini-3-pro", method="streamGenerateContent")
        assert "streamGenerateContent" in url


class TestGenerateText:
    @patch("skyyrose.elite_studio.gemini_rest.requests.post")
    @patch.object(gemini_rest, "_get_key", return_value="test-key")
    def test_success(self, _mock_key, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Hello world"}]}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = gemini_rest.generate_text("gemini-2.0-flash", "Say hello")
        assert result["success"] is True
        assert result["text"] == "Hello world"

    @patch("skyyrose.elite_studio.gemini_rest.requests.post")
    @patch.object(gemini_rest, "_get_key", return_value="test-key")
    def test_network_error(self, _mock_key, mock_post):
        mock_post.side_effect = Exception("Connection refused")

        result = gemini_rest.generate_text("gemini-2.0-flash", "test")
        assert result["success"] is False
        assert "Connection refused" in result["error"]


class TestAnalyzeVision:
    @patch("skyyrose.elite_studio.gemini_rest.requests.post")
    @patch.object(gemini_rest, "_get_key", return_value="test-key")
    def test_success(self, _mock_key, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Detailed garment analysis..."}]}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = gemini_rest.analyze_vision(
            model="gemini-3-flash-preview",
            prompt="Analyze this product",
            image_b64="AAAA",
        )
        assert result["success"] is True
        assert "garment analysis" in result["text"]

        # Verify payload includes image data
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        parts = payload["contents"][0]["parts"]
        assert len(parts) == 2
        assert parts[1]["inline_data"]["data"] == "AAAA"

    @patch("skyyrose.elite_studio.gemini_rest.requests.post")
    @patch.object(gemini_rest, "_get_key", return_value="test-key")
    def test_http_error(self, _mock_key, mock_post):
        mock_post.side_effect = Exception("403 Forbidden")

        result = gemini_rest.analyze_vision(
            model="gemini-3-flash-preview",
            prompt="test",
            image_b64="AAAA",
        )
        assert result["success"] is False
        assert "403" in result["error"]


class TestGenerateImage:
    @patch("skyyrose.elite_studio.gemini_rest.requests.post")
    @patch.object(gemini_rest, "_get_key", return_value="test-key")
    def test_success_with_image(self, _mock_key, mock_post):
        # Simulate Gemini returning base64 image
        fake_image = b"\xff\xd8\xff\xe0fake-jpeg-data"
        fake_b64 = base64.b64encode(fake_image).decode()

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "data": fake_b64,
                                    "mimeType": "image/jpeg",
                                }
                            }
                        ]
                    }
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = gemini_rest.generate_image(
            model="gemini-3-pro-image-preview",
            prompt="Generate a fashion photo",
            reference_b64="REF_IMAGE_B64",
            aspect_ratio="3:4",
        )
        assert result["success"] is True
        assert result["image_data"] == fake_image
        assert result["mime_type"] == "image/jpeg"

        # Verify generation config in payload
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        gen_config = payload["generationConfig"]
        assert gen_config["responseModalities"] == ["IMAGE"]
        assert gen_config["imageConfig"]["aspectRatio"] == "3:4"

    @patch("skyyrose.elite_studio.gemini_rest.requests.post")
    @patch.object(gemini_rest, "_get_key", return_value="test-key")
    def test_no_image_in_response(self, _mock_key, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "I cannot generate that image."}]}}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = gemini_rest.generate_image(
            model="gemini-3-pro-image-preview",
            prompt="test",
            reference_b64="AAAA",
        )
        assert result["success"] is False
        assert "No image in response" in result["error"]
        assert "text(" in result["error"]

    @patch("skyyrose.elite_studio.gemini_rest.requests.post")
    @patch.object(gemini_rest, "_get_key", return_value="test-key")
    def test_network_error(self, _mock_key, mock_post):
        mock_post.side_effect = Exception("Connection timed out")

        result = gemini_rest.generate_image(
            model="gemini-3-pro-image-preview",
            prompt="test",
            reference_b64="AAAA",
        )
        assert result["success"] is False
        assert "timed out" in result["error"]
