"""
tests.flux_lora.test_trainer — covers trainer.py public API + Replicate contract.

No real Replicate API calls are made. httpx is mocked at the transport level.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

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

        manifest = build_manifest(zip_path, destination_model="skyyrose/skyyrose-lora")

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

    def test_destination_model_is_required(self, tmp_path: Path) -> None:
        """Replicate trainings require a destination; build_manifest must enforce it."""
        zip_path = tmp_path / "dataset.zip"
        zip_path.write_bytes(b"PK")

        with pytest.raises(ValueError, match="destination_model is required"):
            build_manifest(zip_path)
        with pytest.raises(ValueError, match="destination_model is required"):
            build_manifest(zip_path, destination_model="no-slash")

    def test_training_input_has_no_unknown_fields(self, tmp_path: Path) -> None:
        """
        Guard against the lr_scheduler regression: every key in training_input must
        exist in the ostris/flux-dev-lora-trainer TrainingInput schema (verified
        live 2026-06-24). lr_scheduler is NOT a valid field — its presence 422s.
        """
        zip_path = tmp_path / "dataset.zip"
        zip_path.write_bytes(b"PK")
        manifest = build_manifest(zip_path, destination_model="skyyrose/skyyrose-lora")

        allowed = {
            "autocaption",
            "autocaption_prefix",
            "autocaption_suffix",
            "batch_size",
            "cache_latents_to_disk",
            "caption_dropout_rate",
            "gradient_checkpointing",
            "hf_repo_id",
            "hf_token",
            "input_images",
            "layers_to_optimize_regex",
            "learning_rate",
            "lora_rank",
            "optimizer",
            "resolution",
            "skip_training_and_use_pretrained_hf_lora_url",
            "steps",
            "trigger_word",
        }
        unknown = set(manifest["training_input"]) - allowed
        assert not unknown, f"unknown TrainingInput fields would 422: {unknown}"
        assert "lr_scheduler" not in manifest["training_input"]


class TestStartTraining:
    def test_raises_requires_confirmation_when_confirmed_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SECURITY: confirmed=False must raise before any HTTP call."""
        # Set token so we don't fail on missing key
        monkeypatch.setenv("REPLICATE_API_TOKEN", "test-token-abc")

        zip_path = tmp_path / "dataset.zip"
        zip_path.write_bytes(b"PK")
        manifest = build_manifest(zip_path, destination_model="skyyrose/skyyrose-lora")

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
        manifest = build_manifest(zip_path, destination_model="skyyrose/skyyrose-lora")

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
        manifest = build_manifest(zip_path, destination_model="skyyrose/skyyrose-lora")

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
        assert "Authorization" in str(call_kwargs)
        assert result["id"] == "train-abc123"
        assert result["status"] == "starting"

        # Contract: URL must carry the version id in the path (Replicate requires it).
        url = call_kwargs.args[0] if call_kwargs.args else call_kwargs.kwargs["url"]
        assert "/versions/" in url and url.endswith("/trainings"), url

        # Contract: payload must include destination + input_images, and no lr_scheduler.
        payload = call_kwargs.kwargs["json"]
        assert payload["destination"] == "skyyrose/skyyrose-lora"
        assert payload["input"]["input_images"] == "https://example.com/dataset.zip"
        assert "lr_scheduler" not in payload["input"]


class TestSaveRunRecord:
    def test_saves_json_file_with_correct_keys(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Redirect RUNS_DIR to tmp_path
        monkeypatch.setattr("scripts.flux_lora.trainer.RUNS_DIR", tmp_path / "runs")

        zip_path = tmp_path / "dataset.zip"
        zip_path.write_bytes(b"PK")
        manifest = build_manifest(zip_path, destination_model="skyyrose/skyyrose-lora")

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
