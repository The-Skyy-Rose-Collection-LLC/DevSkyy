"""Tests for scripts/deploy-theme.sh -- subprocess-based verification.

Tests invoke the deploy script via subprocess and assert on exit codes,
stdout/stderr content, and script source patterns. Uses temporary directories
with fake .env.wordpress for controlled testing.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "deploy-theme.sh"


@pytest.fixture
def fake_env(tmp_path):
    """Create a fake .env.wordpress and theme directory for testing."""
    env_file = tmp_path / ".env.wordpress"
    env_file.write_text(
        "SSH_HOST=ssh.wp.com\n"
        "SSH_PORT=22\n"
        "SSH_USER=test.wordpress.com\n"
        "SSH_PASS=fake-password\n"
        "WP_THEME_PATH=/htdocs/wp-content/themes/skyyrose-flagship\n"
        "SFTP_HOST=sftp.wp.com\n"
        "SFTP_PORT=22\n"
        "SFTP_USER=test.wordpress.com\n"
        "SFTP_PASS=fake-password\n"
    )
    theme_dir = tmp_path / "wordpress-theme" / "skyyrose-flagship"
    theme_dir.mkdir(parents=True)
    (theme_dir / "style.css").write_text("/* Theme */")
    (theme_dir / "functions.php").write_text("<?php // ok")
    return tmp_path, env_file, theme_dir


def run_script(*args, env_overrides=None):
    """Run deploy-theme.sh with given arguments."""
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


class TestDryRun:
    """Test 1: --dry-run exits 0 and prints DRY RUN messages."""

    def test_dry_run_exits_zero(self, fake_env):
        tmp_path, env_file, theme_dir = fake_env
        result = run_script(
            "--dry-run",
            env_overrides={
                "ENV_FILE": str(env_file),
                "THEME_DIR_OVERRIDE": str(theme_dir),
            },
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_dry_run_prints_dry_run_label(self, fake_env):
        tmp_path, env_file, theme_dir = fake_env
        result = run_script(
            "--dry-run",
            env_overrides={
                "ENV_FILE": str(env_file),
                "THEME_DIR_OVERRIDE": str(theme_dir),
            },
        )
        assert "[DRY RUN]" in result.stdout

    def test_dry_run_mentions_maintenance_mode(self, fake_env):
        tmp_path, env_file, theme_dir = fake_env
        result = run_script(
            "--dry-run",
            env_overrides={
                "ENV_FILE": str(env_file),
                "THEME_DIR_OVERRIDE": str(theme_dir),
            },
        )
        assert "maintenance" in result.stdout.lower()

    def test_dry_run_mentions_file_transfer(self, fake_env):
        tmp_path, env_file, theme_dir = fake_env
        result = run_script(
            "--dry-run",
            env_overrides={
                "ENV_FILE": str(env_file),
                "THEME_DIR_OVERRIDE": str(theme_dir),
            },
        )
        output = result.stdout.lower()
        assert "transfer" in output or "rsync" in output or "lftp" in output

    def test_dry_run_mentions_cache_flush(self, fake_env):
        tmp_path, env_file, theme_dir = fake_env
        result = run_script(
            "--dry-run",
            env_overrides={
                "ENV_FILE": str(env_file),
                "THEME_DIR_OVERRIDE": str(theme_dir),
            },
        )
        assert "cache flush" in result.stdout.lower()


class TestHelp:
    """Test 2: --help exits 0 and prints usage."""

    def test_help_exits_zero(self):
        result = run_script("--help")
        assert result.returncode == 0

    def test_help_prints_usage(self):
        result = run_script("--help")
        output = result.stdout.lower()
        assert "usage" in output or "deploy" in output


class TestMissingEnv:
    """Test 3: Missing .env.wordpress causes non-zero exit."""

    def test_missing_env_exits_nonzero(self, tmp_path):
        result = run_script(
            env_overrides={"ENV_FILE": str(tmp_path / "nonexistent.env")},
        )
        assert result.returncode != 0

    def test_missing_env_prints_error(self, tmp_path):
        result = run_script(
            env_overrides={"ENV_FILE": str(tmp_path / "nonexistent.env")},
        )
        output = (result.stdout + result.stderr).lower()
        assert "credential" in output or "env" in output or "not found" in output


class TestTrapCleanup:
    """Test 4: Script contains trap cleanup EXIT and cleanup checks MAINTENANCE_ACTIVE."""

    def test_trap_cleanup_exit_registered(self):
        source = SCRIPT_PATH.read_text()
        assert "trap cleanup EXIT" in source or "trap cleanup EXIT INT TERM" in source

    def test_cleanup_checks_maintenance_active(self):
        source = SCRIPT_PATH.read_text()
        assert "MAINTENANCE_ACTIVE" in source
        # cleanup function should check the flag
        cleanup_match = re.search(
            r"cleanup\s*\(\)\s*\{[^}]+MAINTENANCE_ACTIVE[^}]+\}", source, re.DOTALL
        )
        assert cleanup_match is not None, "cleanup() must check MAINTENANCE_ACTIVE"

    def test_trap_before_maintenance_activation(self):
        """Trap must be registered BEFORE any maintenance mode activation."""
        source = SCRIPT_PATH.read_text()
        trap_pos = source.find("trap cleanup")
        activate_pos = source.find("maintenance-mode activate")
        assert trap_pos < activate_pos, "trap must be registered before maintenance-mode activate"


class TestCommandOrdering:
    """Test 5: In dry-run output, activate before transfer, deactivate after."""

    def test_activate_before_transfer(self, fake_env):
        tmp_path, env_file, theme_dir = fake_env
        result = run_script(
            "--dry-run",
            env_overrides={
                "ENV_FILE": str(env_file),
                "THEME_DIR_OVERRIDE": str(theme_dir),
            },
        )
        output = result.stdout.lower()
        activate_pos = output.find("maintenance-mode activate")
        # Look for transfer indicators
        transfer_pos = min(
            (
                p
                for p in (
                    output.find("rsync"),
                    output.find("transfer"),
                    output.find("lftp"),
                )
                if p != -1
            ),
            default=-1,
        )
        assert activate_pos != -1, "activate not found in output"
        assert transfer_pos != -1, "transfer not found in output"
        assert activate_pos < transfer_pos

    def test_deactivate_after_transfer(self, fake_env):
        tmp_path, env_file, theme_dir = fake_env
        result = run_script(
            "--dry-run",
            env_overrides={
                "ENV_FILE": str(env_file),
                "THEME_DIR_OVERRIDE": str(theme_dir),
            },
        )
        output = result.stdout.lower()
        transfer_pos = min(
            (
                p
                for p in (
                    output.find("rsync"),
                    output.find("transfer"),
                    output.find("lftp"),
                )
                if p != -1
            ),
            default=-1,
        )
        deactivate_pos = output.find("maintenance-mode deactivate")
        assert transfer_pos != -1, "transfer not found"
        assert deactivate_pos != -1, "deactivate not found"
        assert transfer_pos < deactivate_pos


class TestCacheFlush:
    """Test 6: Cache flush commands appear after file transfer."""

    def test_cache_flush_in_output(self, fake_env):
        tmp_path, env_file, theme_dir = fake_env
        result = run_script(
            "--dry-run",
            env_overrides={
                "ENV_FILE": str(env_file),
                "THEME_DIR_OVERRIDE": str(theme_dir),
            },
        )
        output = result.stdout.lower()
        assert "cache flush" in output

    def test_transient_delete_in_output(self, fake_env):
        tmp_path, env_file, theme_dir = fake_env
        result = run_script(
            "--dry-run",
            env_overrides={
                "ENV_FILE": str(env_file),
                "THEME_DIR_OVERRIDE": str(theme_dir),
            },
        )
        output = result.stdout.lower()
        assert "transient delete" in output

    def test_rewrite_flush_in_output(self, fake_env):
        tmp_path, env_file, theme_dir = fake_env
        result = run_script(
            "--dry-run",
            env_overrides={
                "ENV_FILE": str(env_file),
                "THEME_DIR_OVERRIDE": str(theme_dir),
            },
        )
        output = result.stdout.lower()
        assert "rewrite flush" in output

    def test_cache_flush_after_transfer(self, fake_env):
        tmp_path, env_file, theme_dir = fake_env
        result = run_script(
            "--dry-run",
            env_overrides={
                "ENV_FILE": str(env_file),
                "THEME_DIR_OVERRIDE": str(theme_dir),
            },
        )
        output = result.stdout.lower()
        transfer_pos = min(
            (
                p
                for p in (
                    output.find("rsync"),
                    output.find("transfer"),
                    output.find("lftp"),
                )
                if p != -1
            ),
            default=-1,
        )
        cache_pos = output.find("cache flush")
        assert transfer_pos < cache_pos


class TestExcludes:
    """Test 7: Rsync exclude list covers critical patterns."""

    def test_excludes_node_modules(self):
        source = SCRIPT_PATH.read_text()
        assert "node_modules" in source

    def test_excludes_git(self):
        source = SCRIPT_PATH.read_text()
        assert re.search(r"--exclude=['\"]?\.git['\"]?", source)

    def test_excludes_env_files(self):
        source = SCRIPT_PATH.read_text()
        assert ".env" in source

    def test_excludes_map_files(self):
        source = SCRIPT_PATH.read_text()
        assert "*.map" in source

    def test_excludes_tests(self):
        source = SCRIPT_PATH.read_text()
        assert re.search(r"--exclude=['\"]?tests/?['\"]?", source)

    def test_excludes_package_json(self):
        source = SCRIPT_PATH.read_text()
        assert "package.json" in source

    def test_excludes_package_lock(self):
        source = SCRIPT_PATH.read_text()
        assert "package-lock.json" in source


class TestShellcheck:
    """Test 8: shellcheck passes on the deploy script."""

    def test_shellcheck_passes(self):
        result = subprocess.run(
            ["shellcheck", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"shellcheck errors:\n{result.stdout}"
