"""Tests for CLI entry point — argument parsing and command dispatch."""

from unittest.mock import MagicMock, patch

import pytest

from skyyrose.elite_studio import cli
from skyyrose.elite_studio.models import ProductionResult


@pytest.fixture
def mock_coordinator():
    """Return a mock coordinator with sensible defaults."""
    coord = MagicMock()
    coord.produce.return_value = ProductionResult(
        sku="br-001",
        view="front",
        status="success",
        output_path="/tmp/br-001-model-front-gemini.jpg",
    )
    coord.produce_batch.return_value = [
        ProductionResult(sku="br-001", view="front", status="success"),
    ]
    return coord


class TestMainProduce:
    @patch.object(cli, "build_team")
    def test_produce_single(self, mock_build, mock_coordinator, capsys):
        mock_build.return_value = mock_coordinator

        cli.main(["produce", "br-001"])

        mock_coordinator.produce.assert_called_once_with("br-001", "front")
        output = capsys.readouterr().out
        assert "success" in output

    @patch.object(cli, "build_team")
    def test_produce_with_view(self, mock_build, mock_coordinator):
        mock_build.return_value = mock_coordinator

        cli.main(["produce", "br-001", "--view", "back"])

        mock_coordinator.produce.assert_called_once_with("br-001", "back")

    @patch.object(cli, "build_team")
    def test_produce_shows_error(self, mock_build, capsys):
        coord = MagicMock()
        coord.produce.return_value = ProductionResult(
            sku="br-001",
            view="front",
            status="error",
            error="Vision failed",
        )
        mock_build.return_value = coord

        cli.main(["produce", "br-001"])

        output = capsys.readouterr().out
        assert "error" in output
        assert "Vision failed" in output


class TestMainBatch:
    @patch.object(cli, "build_team")
    def test_batch_all(self, mock_build, mock_coordinator):
        mock_build.return_value = mock_coordinator

        cli.main(["produce-batch", "--all"])

        mock_coordinator.produce_batch.assert_called_once()
        call_kwargs = mock_coordinator.produce_batch.call_args
        assert call_kwargs[1].get("skus") is None or call_kwargs[0][0] is None

    @patch.object(cli, "discover_all_skus")
    @patch.object(cli, "build_team")
    def test_batch_with_prefix(self, mock_build, mock_discover, mock_coordinator):
        mock_build.return_value = mock_coordinator
        mock_discover.return_value = ["br-001", "br-002", "sg-001"]

        cli.main(["produce-batch", "br"])

        call_kwargs = mock_coordinator.produce_batch.call_args[1]
        assert call_kwargs["skus"] == ["br-001", "br-002"]


class TestMainStatus:
    @patch.object(cli, "discover_all_skus")
    @patch.object(cli, "OUTPUT_DIR")
    def test_status_display(self, mock_output_dir, mock_discover, capsys):
        mock_discover.return_value = ["br-001", "br-002"]

        # br-001 exists, br-002 doesn't
        def mock_exists(sku_path):
            return "br-001" in str(sku_path)

        mock_path = MagicMock()
        mock_path.__truediv__ = MagicMock(
            side_effect=lambda x: MagicMock(
                __truediv__=MagicMock(
                    return_value=MagicMock(exists=MagicMock(return_value="br-001" in str(x)))
                )
            )
        )
        mock_output_dir.__truediv__ = mock_path.__truediv__

        cli.main(["status"])

        output = capsys.readouterr().out
        assert "Total products: 2" in output
        assert "Generated:" in output or "Remaining:" in output


class TestMainNoCommand:
    def test_no_command_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            cli.main([])

        assert exc_info.value.code == 1
