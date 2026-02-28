"""Tests for AI training providers."""
from unittest.mock import MagicMock, patch

import pytest

from scripts.ai_config import AIConfig


def test_provider_registry_has_both_providers():
    """PROVIDERS dict contains 'replicate' and 'hf'."""
    from scripts.ai_providers import PROVIDERS
    assert "replicate" in PROVIDERS
    assert "hf" in PROVIDERS


def test_replicate_provider_start_training():
    """ReplicateProvider.start_training calls replicate.trainings.create."""
    from scripts.ai_providers import ReplicateProvider
    provider = ReplicateProvider()
    config = AIConfig()

    mock_training = MagicMock()
    mock_training.id = "train_abc123"

    with patch.dict("os.environ", {"REPLICATE_API_TOKEN": "r8_test"}):
        with patch("scripts.ai_providers.replicate") as mock_rep:
            mock_rep.trainings.create.return_value = mock_training
            job_id = provider.start_training(config)

    assert job_id == "train_abc123"
    mock_rep.trainings.create.assert_called_once()


def test_replicate_provider_get_status():
    """ReplicateProvider.get_status returns dict with status/logs."""
    from scripts.ai_providers import ReplicateProvider
    provider = ReplicateProvider()

    mock_training = MagicMock()
    mock_training.status = "processing"
    mock_training.logs = "Step 100/1000"

    with patch.dict("os.environ", {"REPLICATE_API_TOKEN": "r8_test"}):
        with patch("scripts.ai_providers.replicate") as mock_rep:
            mock_rep.trainings.get.return_value = mock_training
            status = provider.get_status("train_abc123")

    assert status["status"] == "processing"
    assert "logs" in status


def test_hf_provider_start_training():
    """HuggingFaceProvider.start_training deploys Space and triggers training."""
    from scripts.ai_providers import HuggingFaceProvider
    provider = HuggingFaceProvider()
    config = AIConfig()

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai_providers.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.get_space_runtime.return_value = MagicMock(stage="RUNNING")

            with patch("scripts.ai_providers.Client") as mock_client_cls:
                mock_client = mock_client_cls.return_value
                mock_client.predict.return_value = "Training complete"
                job_id = provider.start_training(config)

    assert job_id == config.trainer_space


def test_hf_provider_get_status():
    """HuggingFaceProvider.get_status checks Space runtime."""
    from scripts.ai_providers import HuggingFaceProvider
    provider = HuggingFaceProvider()
    mock_runtime = MagicMock()
    mock_runtime.stage = "RUNNING"
    mock_runtime.hardware = "t4-medium"

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai_providers.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.get_space_runtime.return_value = mock_runtime
            status = provider.get_status("damBruh/skyyrose-lora-trainer")

    assert status["status"] == "RUNNING"
    assert status["hardware"] == "t4-medium"
