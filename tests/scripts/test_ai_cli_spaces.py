"""Tests for AI CLI spaces subcommand."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

runner = CliRunner()


def test_spaces_list():
    """spaces list shows damBruh Spaces."""
    from scripts.ai import app

    mock_space_1 = MagicMock()
    mock_space_1.id = "damBruh/skyyrose-lora-trainer"
    mock_space_2 = MagicMock()
    mock_space_2.id = "damBruh/skyyrose-3d-converter"

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.list_spaces.return_value = [mock_space_1, mock_space_2]
            result = runner.invoke(app, ["spaces", "list"])

    assert result.exit_code == 0
    assert "skyyrose-lora-trainer" in result.stdout


def test_spaces_status():
    """spaces status shows runtime info."""
    from scripts.ai import app

    mock_runtime = MagicMock()
    mock_runtime.stage = "RUNNING"
    mock_runtime.hardware = MagicMock()
    mock_runtime.hardware.current = "t4-medium"
    mock_runtime.hardware.requested = "t4-medium"

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            mock_api.get_space_runtime.return_value = mock_runtime
            result = runner.invoke(app, ["spaces", "status", "skyyrose-lora-trainer"])

    assert result.exit_code == 0
    assert "RUNNING" in result.stdout


def test_spaces_restart():
    """spaces restart calls restart_space API."""
    from scripts.ai import app

    with patch.dict("os.environ", {"HF_TOKEN": "hf_test"}):
        with patch("scripts.ai.HfApi") as mock_api_cls:
            mock_api = mock_api_cls.return_value
            result = runner.invoke(app, ["spaces", "restart", "skyyrose-lora-trainer"])

    assert result.exit_code == 0
    mock_api.restart_space.assert_called_once()
