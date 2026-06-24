"""
tests.flux_lora.test_inference — covers inference.py public API + Replicate contract.

No real Replicate API calls are made. httpx is mocked at the transport level.
Field names asserted here (lora_weights, lora_scale, guidance) were verified against
the live black-forest-labs/flux-dev-lora Input schema on 2026-06-24, and the response
handling (status / output / urls.get / Prefer: wait) against Replicate's HTTP docs.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.flux_lora import InferenceError, RequiresConfirmationError
from scripts.flux_lora.inference import (
    FLUX_INFERENCE_MODEL,
    generate,
    load_latest_lora,
)

_HTTPS_LORA = "https://example.com/lora.tar"


def _resp(status_code: int, body: dict) -> MagicMock:
    m = MagicMock()
    m.status_code = status_code
    m.json.return_value = body
    return m


class TestGenerateStopAndShow:
    def test_raises_requires_confirmation_when_confirmed_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SECURITY: confirmed=False must raise before any HTTP call."""
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")
        with pytest.raises(RequiresConfirmationError):
            generate("SKYYROSE hoodie", _HTTPS_LORA, confirmed=False)

    def test_no_http_call_when_confirmed_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """SECURITY: no Replicate POST must fire when confirmed=False."""
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")
        with patch("scripts.flux_lora.inference.httpx.post") as mock_post:
            with pytest.raises(RequiresConfirmationError):
                generate("SKYYROSE hoodie", _HTTPS_LORA, confirmed=False)
            mock_post.assert_not_called()


class TestGenerateContract:
    def test_post_uses_lora_model_and_verified_fields(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        confirmed=True fires one POST against the LoRA-capable model with field names
        that exist in its live schema — and NONE that would 422. A succeeded response
        returns the output URLs directly (no poll).
        """
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")
        ok = _resp(201, {"status": "succeeded", "output": ["https://example.com/out.png"]})

        with patch("scripts.flux_lora.inference.httpx.post", return_value=ok) as mock_post:
            urls = generate("SKYYROSE hoodie", _HTTPS_LORA, confirmed=True, num_outputs=2)

        mock_post.assert_called_once()
        call = mock_post.call_args

        url = call.args[0] if call.args else call.kwargs["url"]
        assert FLUX_INFERENCE_MODEL == "black-forest-labs/flux-dev-lora"
        assert url.endswith(f"/v1/models/{FLUX_INFERENCE_MODEL}/predictions"), url
        assert call.kwargs["headers"]["Prefer"] == "wait"

        inp = call.kwargs["json"]["input"]
        assert inp["lora_weights"] == _HTTPS_LORA
        assert "lora_scale" in inp
        assert "guidance" in inp
        assert inp["num_outputs"] == 2
        # Fields that do NOT exist in flux-dev-lora → would 422. Must be absent.
        assert "extra_lora" not in inp
        assert "extra_lora_scale" not in inp
        assert "guidance_scale" not in inp
        # seed omitted unless requested
        assert "seed" not in inp

        assert urls == ["https://example.com/out.png"]

    def test_seed_included_only_when_provided(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")
        ok = _resp(201, {"status": "succeeded", "output": ["u"]})
        with patch("scripts.flux_lora.inference.httpx.post", return_value=ok) as mock_post:
            generate("SKYYROSE hoodie", _HTTPS_LORA, confirmed=True, seed=42)
        assert mock_post.call_args.kwargs["json"]["input"]["seed"] == 42

    def test_polls_when_post_returns_non_terminal(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A non-terminal POST result must be polled via urls.get until terminal."""
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")
        starting = _resp(
            201,
            {
                "status": "processing",
                "urls": {"get": "https://api.replicate.com/v1/predictions/p1"},
            },
        )
        done = _resp(200, {"status": "succeeded", "output": ["https://example.com/out.png"]})

        with (
            patch("scripts.flux_lora.inference.httpx.post", return_value=starting),
            patch("scripts.flux_lora.inference.httpx.get", return_value=done) as mock_get,
            patch("scripts.flux_lora.inference.time.sleep") as mock_sleep,
        ):
            urls = generate("SKYYROSE hoodie", _HTTPS_LORA, confirmed=True)

        mock_get.assert_called_once()  # terminal on first poll
        mock_sleep.assert_not_called()  # terminal checked before sleeping
        assert urls == ["https://example.com/out.png"]

    def test_failed_prediction_raises_inference_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")
        failed = _resp(201, {"status": "failed", "error": "OOM on GPU"})
        with patch("scripts.flux_lora.inference.httpx.post", return_value=failed):
            with pytest.raises(InferenceError, match="OOM on GPU"):
                generate("SKYYROSE hoodie", _HTTPS_LORA, confirmed=True)

    def test_non_https_lora_url_rejected_before_http(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """SSRF guard: a non-https lora_url must raise before any POST."""
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")
        with patch("scripts.flux_lora.inference.httpx.post") as mock_post:
            with pytest.raises(ValueError, match="https"):
                generate("SKYYROSE hoodie", "http://evil.local/lora.tar", confirmed=True)
            mock_post.assert_not_called()


class TestLoadLatestLora:
    def test_returns_output_url_from_succeeded_run(self) -> None:
        runs = [
            {"replicate_response": {"status": "failed", "output": None}},
            {"replicate_response": {"status": "succeeded", "output": "https://x/weights.tar"}},
        ]
        with patch("scripts.flux_lora.inference.list_runs", return_value=runs):
            assert load_latest_lora() == "https://x/weights.tar"

    def test_returns_none_when_no_succeeded_run(self) -> None:
        runs = [{"replicate_response": {"status": "starting", "output": None}}]
        with patch("scripts.flux_lora.inference.list_runs", return_value=runs):
            assert load_latest_lora() is None
