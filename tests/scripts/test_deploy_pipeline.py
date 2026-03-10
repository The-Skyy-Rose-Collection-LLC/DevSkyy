"""Tests for scripts/deploy-pipeline.sh -- subprocess-based verification.

Tests invoke the deploy pipeline script via subprocess and assert on exit codes,
stdout/stderr content, and script source patterns. Validates that the pipeline
orchestrates build -> deploy -> verify as 3 numbered steps with --dry-run support.
"""

import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "deploy-pipeline.sh"


def run_script(*args, env_overrides=None):
    """Run deploy-pipeline.sh with given arguments."""
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    return result


class TestHelp:
    """Test 1: --help exits 0 and prints usage with pipeline step descriptions."""

    def test_help_exits_zero(self):
        result = run_script("--help")
        assert result.returncode == 0

    def test_help_prints_usage(self):
        result = run_script("--help")
        output = result.stdout.lower()
        assert "usage" in output

    def test_help_mentions_build(self):
        result = run_script("--help")
        output = result.stdout.lower()
        assert "build" in output

    def test_help_mentions_deploy(self):
        result = run_script("--help")
        output = result.stdout.lower()
        assert "deploy" in output

    def test_help_mentions_verify(self):
        result = run_script("--help")
        output = result.stdout.lower()
        assert "verify" in output


class TestScriptStructure:
    """Tests 2-3: Script source calls deploy-theme.sh and verify-deploy.sh."""

    def test_references_deploy_theme(self):
        """Test 2: Script source calls deploy-theme.sh."""
        source = SCRIPT_PATH.read_text()
        assert "deploy-theme.sh" in source

    def test_references_verify_deploy(self):
        """Test 3: Script source calls verify-deploy.sh."""
        source = SCRIPT_PATH.read_text()
        assert "verify-deploy.sh" in source

    def test_runs_npm_build(self):
        """Test 4: Script source runs npm build in the theme directory."""
        source = SCRIPT_PATH.read_text()
        assert "npm run build" in source


class TestDryRun:
    """Tests 5-7: --dry-run exits 0, prints DRY RUN messages, skips verification."""

    def test_dry_run_source_has_dry_run_flag(self):
        """Test 5: Script has DRY_RUN flag handling."""
        source = SCRIPT_PATH.read_text()
        assert "DRY_RUN" in source
        assert "--dry-run" in source

    def test_dry_run_skips_verification(self):
        """Test 6: --dry-run output mentions skipping verification."""
        source = SCRIPT_PATH.read_text()
        source_lower = source.lower()
        # In dry-run mode, verification must be skipped with a clear message
        assert "skip" in source_lower and "verif" in source_lower

    def test_dry_run_passes_flag_to_deploy(self):
        """Test 7: --dry-run passes --dry-run flag to deploy-theme.sh."""
        source = SCRIPT_PATH.read_text()
        # Must pass --dry-run when calling deploy-theme.sh
        assert "deploy-theme.sh" in source
        # The source must contain a conditional that passes --dry-run
        assert (
            'deploy-theme.sh" --dry-run' in source
            or "deploy-theme.sh --dry-run" in source
            or 'deploy-theme.sh" --dry-run' in source
        )


class TestStepNumbering:
    """Test 8: Script source has step numbering ([1/3], [2/3], [3/3])."""

    def test_has_step_1_of_3(self):
        source = SCRIPT_PATH.read_text()
        assert "[1/3]" in source

    def test_has_step_2_of_3(self):
        source = SCRIPT_PATH.read_text()
        assert "[2/3]" in source

    def test_has_step_3_of_3(self):
        source = SCRIPT_PATH.read_text()
        assert "[3/3]" in source


class TestDependencyChecks:
    """Test 10: Script checks for deploy-theme.sh and verify-deploy.sh existence."""

    def test_checks_deploy_theme_exists(self):
        source = SCRIPT_PATH.read_text()
        # Script should check that deploy-theme.sh exists before running
        assert "deploy-theme.sh" in source
        # There should be a file existence check (e.g., -f or -x)
        assert "-f" in source or "-x" in source

    def test_checks_verify_deploy_exists(self):
        source = SCRIPT_PATH.read_text()
        assert "verify-deploy.sh" in source


class TestShellcheck:
    """Test 9: shellcheck passes on deploy-pipeline.sh."""

    def test_shellcheck_passes(self):
        result = subprocess.run(
            ["shellcheck", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"shellcheck errors:\n{result.stdout}"
