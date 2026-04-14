"""Tests for SafetyAgent — OpenAI moderation + GPT-4o image check."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from skyyrose.elite_studio.agents.safety_agent import SafetyAgent
from skyyrose.elite_studio.models import SafetyResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_test_image(tmp_path: Path, name: str = "test.jpg", size=(32, 32)) -> Path:
    """Create a minimal JPEG test image."""
    img_path = tmp_path / name
    img = Image.new("RGB", size, color=(50, 50, 50))
    img.save(str(img_path), "JPEG")
    return img_path


def _make_moderation_response(flagged: bool = False, categories: dict | None = None) -> MagicMock:
    """Build a mock OpenAI moderation response."""
    cat = categories or {}
    mock_categories = MagicMock()
    mock_categories.model_dump.return_value = {
        "hate": cat.get("hate", False),
        "hate/threatening": cat.get("hate/threatening", False),
        "self-harm": cat.get("self-harm", False),
        "sexual": cat.get("sexual", False),
        "sexual/minors": cat.get("sexual/minors", False),
        "violence": cat.get("violence", False),
        "violence/graphic": cat.get("violence/graphic", False),
    }

    mock_result = MagicMock()
    mock_result.flagged = flagged
    mock_result.categories = mock_categories

    mock_response = MagicMock()
    mock_response.results = [mock_result]
    return mock_response


def _make_chat_response(safe: bool = True, flagged_categories: list | None = None) -> MagicMock:
    """Build a mock GPT-4o chat response."""
    import json

    cats = flagged_categories or []
    content = json.dumps({"safe": safe, "flagged_categories": cats})

    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestSafetyResultModel:
    def test_frozen(self):
        r = SafetyResult(success=True)
        with pytest.raises((AttributeError, TypeError)):
            r.success = False  # type: ignore[misc]

    def test_defaults(self):
        r = SafetyResult(success=False)
        assert r.flagged is False
        assert r.categories == ()
        assert r.error == ""


# ---------------------------------------------------------------------------
# SafetyAgent — safe image
# ---------------------------------------------------------------------------


class TestSafetyAgentSafeImage:
    def setup_method(self):
        self.agent = SafetyAgent()

    def _mock_clients(self, moderation_flagged=False, image_safe=True):
        """Return patched openai client mock."""
        mock_client = MagicMock()
        mock_client.moderations.create.return_value = _make_moderation_response(
            flagged=moderation_flagged
        )
        mock_client.chat.completions.create.return_value = _make_chat_response(safe=image_safe)
        return mock_client

    def test_safe_image_not_flagged(self, tmp_path):
        src = make_test_image(tmp_path)
        mock_client = self._mock_clients()

        with patch(
            "skyyrose.elite_studio.agents.safety_agent.get_openai_client",
            return_value=mock_client,
        ):
            result = self.agent.check(str(src))

        assert result.success is True
        assert result.flagged is False
        assert result.categories == ()

    def test_safe_result_is_frozen(self, tmp_path):
        src = make_test_image(tmp_path)
        mock_client = self._mock_clients()

        with patch(
            "skyyrose.elite_studio.agents.safety_agent.get_openai_client",
            return_value=mock_client,
        ):
            result = self.agent.check(str(src))

        with pytest.raises((AttributeError, TypeError)):
            result.flagged = True  # type: ignore[misc]


# ---------------------------------------------------------------------------
# SafetyAgent — flagged by moderation text check
# ---------------------------------------------------------------------------


class TestSafetyAgentModerationFlag:
    def setup_method(self):
        self.agent = SafetyAgent()

    def test_moderation_flag_sets_flagged_true(self, tmp_path):
        src = make_test_image(tmp_path)
        mock_client = MagicMock()
        mock_client.moderations.create.return_value = _make_moderation_response(
            flagged=True, categories={"violence": True}
        )
        mock_client.chat.completions.create.return_value = _make_chat_response(safe=True)

        with patch(
            "skyyrose.elite_studio.agents.safety_agent.get_openai_client",
            return_value=mock_client,
        ):
            result = self.agent.check(str(src))

        assert result.success is True
        assert result.flagged is True
        assert "violence" in result.categories

    def test_image_flag_sets_flagged_true(self, tmp_path):
        src = make_test_image(tmp_path)
        mock_client = MagicMock()
        mock_client.moderations.create.return_value = _make_moderation_response(flagged=False)
        mock_client.chat.completions.create.return_value = _make_chat_response(
            safe=False, flagged_categories=["explicit"]
        )

        with patch(
            "skyyrose.elite_studio.agents.safety_agent.get_openai_client",
            return_value=mock_client,
        ):
            result = self.agent.check(str(src))

        assert result.success is True
        assert result.flagged is True
        assert "explicit" in result.categories

    def test_categories_merged_from_both_checks(self, tmp_path):
        src = make_test_image(tmp_path)
        mock_client = MagicMock()
        mock_client.moderations.create.return_value = _make_moderation_response(
            flagged=True, categories={"hate": True}
        )
        mock_client.chat.completions.create.return_value = _make_chat_response(
            safe=False, flagged_categories=["violence"]
        )

        with patch(
            "skyyrose.elite_studio.agents.safety_agent.get_openai_client",
            return_value=mock_client,
        ):
            result = self.agent.check(str(src))

        assert "hate" in result.categories
        assert "violence" in result.categories


# ---------------------------------------------------------------------------
# SafetyAgent — error cases
# ---------------------------------------------------------------------------


class TestSafetyAgentErrors:
    def setup_method(self):
        self.agent = SafetyAgent()

    def test_missing_file_returns_failure(self):
        result = self.agent.check("/nonexistent/image.jpg")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_api_exception_returns_failure(self, tmp_path):
        src = make_test_image(tmp_path)
        mock_client = MagicMock()
        mock_client.moderations.create.side_effect = Exception("API down")

        with patch(
            "skyyrose.elite_studio.agents.safety_agent.get_openai_client",
            return_value=mock_client,
        ):
            result = self.agent.check(str(src))

        assert result.success is False
        assert "API down" in result.error

    def test_unparseable_vision_response_defaults_to_safe(self, tmp_path):
        """Malformed JSON from GPT-4o should not block the pipeline (false positive risk)."""
        src = make_test_image(tmp_path)
        mock_client = MagicMock()
        mock_client.moderations.create.return_value = _make_moderation_response(flagged=False)

        mock_message = MagicMock()
        mock_message.content = "This is not JSON at all."
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        with patch(
            "skyyrose.elite_studio.agents.safety_agent.get_openai_client",
            return_value=mock_client,
        ):
            result = self.agent.check(str(src))

        assert result.success is True
        assert result.flagged is False

    def test_unexpected_exception_returns_failure(self, monkeypatch):
        def _boom(*args, **kwargs):
            raise RuntimeError("Unexpected")

        monkeypatch.setattr(
            "skyyrose.elite_studio.agents.safety_agent.SafetyAgent._check",
            _boom,
        )
        result = self.agent.check("/any.jpg")
        assert result.success is False
        assert "Unexpected" in result.error
