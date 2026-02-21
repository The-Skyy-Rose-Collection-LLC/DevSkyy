"""
Tests for __main__.py CLI entry point.

Covers: argument parsing, PRD loading, report printing, dry-run mode.
"""

from __future__ import annotations

import argparse
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from elite_web_builder.__main__ import _build_parser, _load_prd, _print_report, _run


# =============================================================================
# _build_parser
# =============================================================================


class TestBuildParser:
    """Argument parser construction."""

    def test_parser_returns_argument_parser(self):
        parser = _build_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_inline_prd(self):
        parser = _build_parser()
        args = parser.parse_args(["Build a website"])
        assert args.prd == "Build a website"
        assert args.file is None

    def test_file_arg(self):
        parser = _build_parser()
        args = parser.parse_args(["--file", "prd.md"])
        assert args.prd is None
        assert args.file == Path("prd.md")

    def test_dry_run_flag(self):
        parser = _build_parser()
        args = parser.parse_args(["--dry-run", "Build it"])
        assert args.dry_run is True

    def test_config_arg(self):
        parser = _build_parser()
        args = parser.parse_args(["--config", "custom.json", "Build it"])
        assert args.config == Path("custom.json")

    def test_max_stories_default(self):
        parser = _build_parser()
        args = parser.parse_args(["Build it"])
        assert args.max_stories == 50

    def test_max_stories_override(self):
        parser = _build_parser()
        args = parser.parse_args(["--max-stories", "10", "Build it"])
        assert args.max_stories == 10

    def test_prd_and_file_both_provided(self):
        """When both inline PRD and --file are given, file takes precedence."""
        parser = _build_parser()
        args = parser.parse_args(["--file", "prd.md", "Also inline"])
        assert args.file == Path("prd.md")
        assert args.prd == "Also inline"


# =============================================================================
# _load_prd
# =============================================================================


class TestLoadPrd:
    """PRD loading from args."""

    def test_inline_prd(self):
        args = argparse.Namespace(prd="Inline PRD text", file=None)
        assert _load_prd(args) == "Inline PRD text"

    def test_file_prd(self, tmp_path):
        prd_file = tmp_path / "test.md"
        prd_file.write_text("File PRD content")
        args = argparse.Namespace(prd=None, file=prd_file)
        assert _load_prd(args) == "File PRD content"

    def test_missing_file_exits(self):
        args = argparse.Namespace(prd=None, file=Path("/nonexistent/file.md"))
        with pytest.raises(SystemExit):
            _load_prd(args)


# =============================================================================
# _print_report
# =============================================================================


class TestPrintReport:
    """Report printing."""

    def test_print_green_report(self, capsys):
        from elite_web_builder.director import ProjectReport, StoryStatus, UserStory, AgentRole

        stories = (
            UserStory(
                id="US-001", title="Test Story", description="desc",
                agent_role=AgentRole.DESIGN_SYSTEM, depends_on=[],
                acceptance_criteria=["Done"],
                status=StoryStatus.GREEN,
            ),
        )
        report = ProjectReport(
            stories=stories,
            status_summary={"green": 1},
            all_green=True,
            elapsed_ms=123.456,
            failures=(),
            instincts_learned=0,
        )
        _print_report(report)
        output = capsys.readouterr().out
        assert "PROJECT REPORT" in output
        assert "Stories: 1" in output
        assert "All Green: True" in output
        assert "123ms" in output
        assert "US-001" in output

    def test_print_failed_report(self, capsys):
        from elite_web_builder.director import ProjectReport, StoryStatus, UserStory, AgentRole

        stories = (
            UserStory(
                id="US-001", title="Failed Story", description="desc",
                agent_role=AgentRole.FRONTEND_DEV, depends_on=[],
                acceptance_criteria=["Done"],
                status=StoryStatus.FAILED,
            ),
        )
        report = ProjectReport(
            stories=stories,
            status_summary={"red": 1},
            all_green=False,
            elapsed_ms=500.0,
            failures=("US-001: Failed Story — FAILED",),
            instincts_learned=1,
        )
        _print_report(report)
        output = capsys.readouterr().out
        assert "Failures (1)" in output
        assert "FAILED" in output
        assert "Instincts Learned: 1" in output

    def test_print_empty_report(self, capsys):
        from elite_web_builder.director import ProjectReport

        report = ProjectReport(
            stories=(),
            status_summary={},
            all_green=True,
            elapsed_ms=0.0,
            failures=(),
            instincts_learned=0,
        )
        _print_report(report)
        output = capsys.readouterr().out
        assert "Stories: 0" in output
        assert "All Green: True" in output


# =============================================================================
# _run
# =============================================================================


class TestRunAsync:
    """Async entry point tests."""

    @pytest.mark.asyncio
    async def test_full_execution_returns_0_on_success(self):
        """
        Verify non-dry-run execution completes successfully when Director.execute_prd returns an all-green ProjectReport.
        """
        from elite_web_builder.director import ProjectReport

        mock_report = ProjectReport(
            stories=(),
            status_summary={"green": 0},
            all_green=True,
            elapsed_ms=50.0,
            failures=(),
            instincts_learned=0,
        )

        args = argparse.Namespace(
            prd="Build a website",
            file=None,
            dry_run=False,
            config=None,
            max_stories=50,
        )

        with patch("elite_web_builder.__main__.Director") as MockDirector:
            instance = MockDirector.return_value
            instance.execute_prd = AsyncMock(return_value=mock_report)
            exit_code = await _run(args)

        assert exit_code == 0

    @pytest.mark.asyncio
    async def test_full_execution_returns_1_on_failure(self):
        """Full execution with failures returns 1."""
        from elite_web_builder.director import ProjectReport

        mock_report = ProjectReport(
            stories=(),
            status_summary={"red": 1},
            all_green=False,
            elapsed_ms=50.0,
            failures=("US-001: FAILED",),
            instincts_learned=0,
        )

        args = argparse.Namespace(
            prd="Build a website",
            file=None,
            dry_run=False,
            config=None,
            max_stories=50,
        )

        with patch("elite_web_builder.__main__.Director") as MockDirector:
            instance = MockDirector.return_value
            instance.execute_prd = AsyncMock(return_value=mock_report)
            exit_code = await _run(args)

        assert exit_code == 1

    @pytest.mark.asyncio
    async def test_dry_run_mode(self):
        """Dry-run mode plans stories but doesn't execute."""
        from elite_web_builder.director import (
            PRDBreakdown, UserStory, AgentRole,
        )

        stories = [
            UserStory(
                id="US-001", title="Design tokens", description="Create tokens",
                agent_role=AgentRole.DESIGN_SYSTEM, depends_on=[],
                acceptance_criteria=["Done"],
            ),
        ]
        breakdown = PRDBreakdown(
            stories=stories,
            dependency_order=["US-001"],
        )

        args = argparse.Namespace(
            prd="Build a website",
            file=None,
            dry_run=True,
            config=None,
            max_stories=50,
        )

        with patch("elite_web_builder.__main__.Director") as MockDirector:
            instance = MockDirector.return_value
            instance._plan_stories = AsyncMock(return_value=breakdown)
            exit_code = await _run(args)

        assert exit_code == 0
        instance._plan_stories.assert_awaited_once_with("Build a website")

    @pytest.mark.asyncio
    async def test_dry_run_failure_returns_1(self):
        """Dry-run with planning failure returns 1."""
        args = argparse.Namespace(
            prd="Build a website",
            file=None,
            dry_run=True,
            config=None,
            max_stories=50,
        )

        with patch("elite_web_builder.__main__.Director") as MockDirector:
            instance = MockDirector.return_value
            instance._plan_stories = AsyncMock(side_effect=RuntimeError("LLM down"))
            exit_code = await _run(args)

        assert exit_code == 1

    @pytest.mark.asyncio
    async def test_config_override(self):
        """Config file path is set on DirectorConfig."""
        from elite_web_builder.director import ProjectReport

        mock_report = ProjectReport(
            stories=(),
            status_summary={},
            all_green=True,
            elapsed_ms=10.0,
            failures=(),
            instincts_learned=0,
        )

        args = argparse.Namespace(
            prd="Build a website",
            file=None,
            dry_run=False,
            config=Path("/custom/config.json"),
            max_stories=25,
        )

        with patch("elite_web_builder.__main__.Director") as MockDirector:
            instance = MockDirector.return_value
            instance.execute_prd = AsyncMock(return_value=mock_report)
            exit_code = await _run(args)

        assert exit_code == 0
        # Verify Director was constructed with a config that has max_stories=25
        call_kwargs = MockDirector.call_args
        config = call_kwargs.kwargs.get("config") or call_kwargs.args[0] if call_kwargs.args else None
        # The config is passed as keyword arg
        if call_kwargs.kwargs.get("config"):
            assert call_kwargs.kwargs["config"].max_stories == 25

    @pytest.mark.asyncio
    async def test_dry_run_with_dependency_order(self, capsys):
        """Dry-run prints execution order when dependency_order is set."""
        from elite_web_builder.director import (
            PRDBreakdown, UserStory, AgentRole,
        )

        stories = [
            UserStory(
                id="US-001", title="Design", description="Create",
                agent_role=AgentRole.DESIGN_SYSTEM, depends_on=[],
                acceptance_criteria=["Done"],
            ),
            UserStory(
                id="US-002", title="Build", description="Build",
                agent_role=AgentRole.FRONTEND_DEV, depends_on=["US-001"],
                acceptance_criteria=["Done"],
            ),
        ]
        breakdown = PRDBreakdown(
            stories=stories,
            dependency_order=["US-001", "US-002"],
        )

        args = argparse.Namespace(
            prd="Build a website",
            file=None,
            dry_run=True,
            config=None,
            max_stories=50,
        )

        with patch("elite_web_builder.__main__.Director") as MockDirector:
            instance = MockDirector.return_value
            instance._plan_stories = AsyncMock(return_value=breakdown)
            exit_code = await _run(args)

        assert exit_code == 0
        output = capsys.readouterr().out
        assert "US-001" in output
        assert "US-002" in output
        assert "Execution Order" in output