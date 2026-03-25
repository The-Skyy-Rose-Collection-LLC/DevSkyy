"""Tests for AI CLI model subcommand."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()


def test_model_list():
    """model list shows damBruh models."""
    from scripts.ai import app

    mock_model = MagicMock()
    mock_model.id = "damBruh/skyyrose-lora-v1"
    mock_model.downloads = 5
    mock_model.tags = ["lora"]

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.list_models.return_value = [mock_model]
            result = runner.invoke(app, ["model", "list"])

    assert result.exit_code == 0
    assert "skyyrose-lora-v1" in result.stdout


def test_model_info():
    """model info shows model details."""
    from scripts.ai import app

    mock_info = MagicMock()
    mock_info.id = "damBruh/skyyrose-lora-v1"
    mock_info.downloads = 5
    mock_info.siblings = [MagicMock(rfilename="pytorch_lora_weights.safetensors", size=50_000_000)]

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.model_info.return_value = mock_info
            result = runner.invoke(app, ["model", "info", "skyyrose-lora-v1"])

    assert result.exit_code == 0
    assert "skyyrose-lora-v1" in result.stdout


def test_model_download():
    """model download calls snapshot_download."""
    from scripts.ai import app

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.snapshot_download") as mock_download:
            mock_download.return_value = "/tmp/models/skyyrose-lora-v1"
            result = runner.invoke(app, ["model", "download", "skyyrose-lora-v1"])

    assert result.exit_code == 0
    mock_download.assert_called_once()
