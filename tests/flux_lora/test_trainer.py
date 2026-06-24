"""
tests.flux_lora.test_trainer — 3 tests covering trainer.py public API.

No real Replicate API calls are made. httpx is mocked at the transport level.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from scripts.flux_lora import RequiresConfirmationError
from scripts.flux_lora.config import (
    DEFAULT_STEPS,
    DEFAULT_TRIGGER_WORD,
    EST_COST_PER_RUN_USD,
)
from scripts.flux_lora.trainer import (
    build_manifest,
    save_run_record,
    start_training,
)


class TestBuildManifest:
    def test_manifest_contains_required_fields(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "dataset.zip"
        zip_path.write_bytes(b"PK")  # fake zip

        manifest = build_manifest(zip_path)

        assert manifest["model_owner"] == "ostris"
        assert manifest["model_name"] == "flux-dev-lora-trainer"
        assert manifest["training_input"]["trigger_word"] == DEFAULT_TRIGGER_WORD
        assert manifest["training_input"]["steps"] == DEFAULT_STEPS
        assert manifest["cost_usd"] == EST_COST_PER_RUN_USD
        assert manifest["dataset_zip"] == str(zip_path)

    def test_manifest_respects_overrides(self, tmp_path: Path) -> None:
        zip_path = tmp_path / "dataset.zip"
        zip_path.write_bytes(b"PK")

        manifest = build_manifest(
            zip_path,
            trigger_word="MYWORD",
            steps=500,
            lora_rank=8,
            destination_model="myuser/my-lora",
        )

        assert manifest["training_input"]["trigger_word"] == "MYWORD"
        assert manifest["training_input"]["steps"] == 500
        assert manifest["training_input"]["lora_rank"] == 8
        assert manifest["destination_model"] == "myuser/my-lora"


class TestStartTraining:
    def test_raises_requires_confirmation_when_confirmed_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SECURITY: confirmed=False must raise before any HTTP call."""
        # Set token so we don't fail on missing key
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")

        zip_path = tmp_path / "dataset.zip"
        zip_path.write_bytes(b"PK")
        manifest = build_manifest(zip_path)

        with pytest.raises(RequiresConfirmationError):
            start_training(
                manifest,
                confirmed=False,
                input_images_url="https://example.com/dataset.zip",
            )

    def test_no_http_call_made_when_confirmed_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SECURITY: no Replicate POST must fire when confirmed=False."""
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")

        zip_path = tmp_path / "dataset.zip"
        zip_path.write_bytes(b"PK")
        manifest = build_manifest(zip_path)

        with patch("scripts.flux_lora.trainer.httpx.post") as mock_post:
            with pytest.raises(RequiresConfirmationError):
                start_training(
                    manifest,
                    confirmed=False,
                    input_images_url="https://example.com/dataset.zip",
                )
            mock_post.assert_not_called()

    def test_submits_post_when_confirmed_true(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Happy path: confirmed=True fires one POST and returns response dict."""
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")

        zip_path = tmp_path / "dataset.zip"
        zip_path.write_bytes(b"PK")
        manifest = build_manifest(zip_path)

        fake_response_data = {
            "id": "train-abc123",
            "status": "starting",
            "urls": {"get": "https://api.replicate.com/v1/trainings/train-abc123"},
        }
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = fake_response_data

        with patch("scripts.flux_lora.trainer.httpx.post", return_value=mock_response) as mock_post:
            result = start_training(
                manifest,
                confirmed=True,
                input_images_url="https://example.com/dataset.zip",
            )

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        # Verify token in headers
        headers = (
            call_kwargs.kwargs.get("headers") or call_kwargs.args[1]
            if len(call_kwargs.args) > 1
            else {}
        )
        assert "Authorization" in str(call_kwargs)
        assert result["id"] == "train-abc123"
        assert result["status"] == "starting"


class TestSaveRunRecord:
    def test_saves_json_file_with_correct_keys(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Redirect RUNS_DIR to tmp_path
        monkeypatch.setattr("scripts.flux_lora.trainer.RUNS_DIR", tmp_path / "runs")

        zip_path = tmp_path / "dataset.zip"
        zip_path.write_bytes(b"PK")
        manifest = build_manifest(zip_path)

        training_resp = {
            "id": "train-xyz999",
            "status": "starting",
            "urls": {"get": "https://api.replicate.com/v1/trainings/train-xyz999"},
        }

        record_path = save_run_record(training_resp, manifest)

        assert record_path.exists()
        record = json.loads(record_path.read_text(encoding="utf-8"))
        assert record["training_id"] == "train-xyz999"
        assert "timestamp" in record
        assert record["manifest"]["model_name"] == "flux-dev-lora-trainer"
        assert record["replicate_response"]["status"] == "starting"
