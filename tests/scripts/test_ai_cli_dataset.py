"""Tests for AI CLI dataset subcommand."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()


def test_dataset_info():
    """dataset info shows dataset metadata."""
    from scripts.ai import app

    mock_info = MagicMock()
    mock_info.id = "damBruh/skyyrose-lora-dataset-v5"
    mock_info.downloads = 42
    mock_info.siblings = [MagicMock(rfilename=f"img_{i}.png") for i in range(78)]

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.dataset_info.return_value = mock_info
            result = runner.invoke(app, ["dataset", "info", "skyyrose-lora-dataset-v5"])

    assert result.exit_code == 0
    assert "skyyrose-lora-dataset-v5" in result.stdout


def test_dataset_push():
    """dataset push uploads folder to Hub."""
    from scripts.ai import app

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            with patch("scripts.ai.Path") as mock_path_cls:
                mock_path = mock_path_cls.return_value
                mock_path.exists.return_value = True
                result = runner.invoke(
                    app,
                    ["dataset", "push", "--source", "/tmp/test-data", "--name", "test-dataset-v1"],
                )

    assert result.exit_code == 0
    mock_api.create_repo.assert_called_once()
