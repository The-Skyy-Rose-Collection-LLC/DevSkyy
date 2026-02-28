"""Tests for AI CLI train subcommand."""
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()


def test_train_run_replicate():
    """train run --provider replicate starts Replicate training."""
    from scripts.ai import app

    with patch.dict("os.environ", {"REPLICATE_API_TOKEN": "r8_test"}):
        with patch("scripts.ai.PROVIDERS") as mock_providers:
            mock_provider = MagicMock()
            mock_provider.start_training.return_value = "train_abc123"
            mock_providers.__getitem__ = MagicMock(return_value=mock_provider)
            mock_providers.__contains__ = MagicMock(return_value=True)
            result = runner.invoke(app, ["train", "run", "--provider", "replicate"])

    assert result.exit_code == 0
    assert "train_abc123" in result.stdout


def test_train_run_hf():
    """train run --provider hf triggers HF Space training."""
    from scripts.ai import app

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.PROVIDERS") as mock_providers:
            mock_provider = MagicMock()
            mock_provider.start_training.return_value = "damBruh/skyyrose-lora-trainer"
            mock_providers.__getitem__ = MagicMock(return_value=mock_provider)
            mock_providers.__contains__ = MagicMock(return_value=True)
            result = runner.invoke(app, ["train", "run", "--provider", "hf"])

    assert result.exit_code == 0


def test_train_status():
    """train status shows training status."""
    from scripts.ai import app

    with patch.dict("os.environ", {"REPLICATE_API_TOKEN": "r8_test"}):
        with patch("scripts.ai.PROVIDERS") as mock_providers:
            mock_provider = MagicMock()
            mock_provider.get_status.return_value = {"status": "succeeded", "logs": "Step 1000/1000"}
            mock_providers.__getitem__ = MagicMock(return_value=mock_provider)
            mock_providers.__contains__ = MagicMock(return_value=True)
            result = runner.invoke(
                app, ["train", "status", "--provider", "replicate", "--job-id", "train_abc123"]
            )

    assert result.exit_code == 0
    assert "succeeded" in result.stdout


def test_train_run_invalid_provider():
    """train run with invalid provider shows error."""
    from scripts.ai import app

    with patch("scripts.ai.PROVIDERS") as mock_providers:
        mock_providers.__contains__ = MagicMock(return_value=False)
        result = runner.invoke(app, ["train", "run", "--provider", "invalid"])

    assert result.exit_code != 0
