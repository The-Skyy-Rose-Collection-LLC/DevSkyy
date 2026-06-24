"""
tests.flux_lora.test_inference — covers inference.py public API + Replicate contract.

No real Replicate API calls are made. httpx is mocked at the transport level.
Field names asserted here (lora_weights, lora_scale, guidance) were verified against
the live black-forest-labs/flux-dev-lora Input schema on 2026-06-24.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.flux_lora import RequiresConfirmationError
from scripts.flux_lora.inference import (
    FLUX_INFERENCE_MODEL,
    generate,
    load_latest_lora,
)


class TestGenerateStopAndShow:
    def test_raises_requires_confirmation_when_confirmed_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SECURITY: confirmed=False must raise before any HTTP call."""
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")
        with pytest.raises(RequiresConfirmationError):
            generate("SKYYROSE hoodie", "https://example.com/lora.tar", confirmed=False)

    def test_no_http_call_when_confirmed_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """SECURITY: no Replicate POST must fire when confirmed=False."""
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")
        with patch("scripts.flux_lora.inference.httpx.post") as mock_post:
            with pytest.raises(RequiresConfirmationError):
                generate("SKYYROSE hoodie", "https://example.com/lora.tar", confirmed=False)
            mock_post.assert_not_called()


class TestGenerateContract:
    def test_post_uses_lora_model_and_verified_fields(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        confirmed=True fires exactly one POST against the LoRA-capable model with the
        field names that exist in its live schema — and NONE that would 422.
        """
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"output": ["https://example.com/out.png"]}

        with patch(
            "scripts.flux_lora.inference.httpx.post", return_value=mock_response
        ) as mock_post:
            urls = generate(
                "SKYYROSE hoodie",
                "https://example.com/lora.tar",
                confirmed=True,
                num_outputs=2,
            )

        mock_post.assert_called_once()
        call = mock_post.call_args

        # Endpoint: the LoRA-capable official model, predictions route.
        url = call.args[0] if call.args else call.kwargs["url"]
        assert FLUX_INFERENCE_MODEL == "black-forest-labs/flux-dev-lora"
        assert url.endswith(f"/v1/models/{FLUX_INFERENCE_MODEL}/predictions"), url

        inp = call.kwargs["json"]["input"]
        # Fields that EXIST in the flux-dev-lora schema.
        assert inp["lora_weights"] == "https://example.com/lora.tar"
        assert "lora_scale" in inp
        assert "guidance" in inp
        assert inp["num_outputs"] == 2
        # Fields that do NOT exist → would 422. Must be absent.
        assert "extra_lora" not in inp
        assert "extra_lora_scale" not in inp
        assert "guidance_scale" not in inp

        assert urls == ["https://example.com/out.png"]


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
