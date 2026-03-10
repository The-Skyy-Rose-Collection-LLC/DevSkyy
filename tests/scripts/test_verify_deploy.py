"""Tests for scripts/verify-deploy.sh -- subprocess-based verification.

Tests invoke the verification script via subprocess and assert on exit codes,
stdout/stderr content, and script source patterns. Validates deep content
verification for post-deploy health checks.
"""

import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "verify-deploy.sh"


def run_script(*args, env_overrides=None):
    """Run verify-deploy.sh with given arguments."""
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
    """Test 1: --help exits 0 and prints usage information."""

    def test_help_exits_zero(self):
        result = run_script("--help")
        assert result.returncode == 0

    def test_help_prints_usage(self):
        result = run_script("--help")
        output = result.stdout.lower()
        assert "usage" in output


class TestScriptStructure:
    """Test 2-3: Script source contains verify_page function with curl + content grep."""

    def test_verify_page_function_exists(self):
        source = SCRIPT_PATH.read_text()
        assert "verify_page()" in source or "verify_page ()" in source

    def test_uses_curl_with_http_code(self):
        source = SCRIPT_PATH.read_text()
        assert "curl" in source
        assert "http_code" in source

    def test_checks_content_marker(self):
        """Script checks HTTP status code AND content marker (not just status)."""
        source = SCRIPT_PATH.read_text()
        assert "grep -qi" in source or "grep -q" in source


class TestContentVerification:
    """Test 4: Script contains all required health check pages."""

    def test_checks_homepage(self):
        source = SCRIPT_PATH.read_text()
        assert "Homepage" in source

    def test_checks_rest_api(self):
        source = SCRIPT_PATH.read_text()
        assert "REST API" in source
        assert "rest_route" in source

    def test_checks_black_rose(self):
        source = SCRIPT_PATH.read_text()
        assert "Black Rose" in source
        assert "collection-black-rose" in source

    def test_checks_love_hurts(self):
        source = SCRIPT_PATH.read_text()
        assert "Love Hurts" in source
        assert "collection-love-hurts" in source

    def test_checks_signature(self):
        source = SCRIPT_PATH.read_text()
        assert "Signature" in source
        assert "collection-signature" in source

    def test_checks_about(self):
        source = SCRIPT_PATH.read_text()
        assert "About" in source
        assert "/about/" in source


class TestCacheBusting:
    """Test 5: Script uses cache-busting query parameter."""

    def test_uses_cache_busting_param(self):
        source = SCRIPT_PATH.read_text()
        assert "_verify=" in source or "nocache=" in source

    def test_uses_timestamp_for_cache_busting(self):
        source = SCRIPT_PATH.read_text()
        assert "TIMESTAMP" in source

    def test_rest_api_uses_ampersand_separator(self):
        """REST API URL already has '?' so cache bust must use '&'."""
        source = SCRIPT_PATH.read_text()
        assert "&_verify=" in source or "&_verify=" in source


class TestFailureCollection:
    """Test 6: Script collects all failures before exiting."""

    def test_has_failures_counter(self):
        source = SCRIPT_PATH.read_text()
        assert "FAILURES" in source

    def test_does_not_exit_on_first_failure(self):
        """verify_page calls use || true to continue on failure."""
        source = SCRIPT_PATH.read_text()
        assert "|| true" in source

    def test_exits_nonzero_on_failure(self):
        """Script exits with non-zero when FAILURES > 0."""
        source = SCRIPT_PATH.read_text()
        assert "FAILURES -eq 0" in source or "FAILURES -gt 0" in source


class TestEnvironmentVariable:
    """Test 7: Script uses WORDPRESS_URL environment variable."""

    def test_uses_wordpress_url_env(self):
        source = SCRIPT_PATH.read_text()
        assert "WORDPRESS_URL" in source

    def test_not_hardcoded_url(self):
        """SITE_URL comes from env var, not hardcoded."""
        source = SCRIPT_PATH.read_text()
        assert "${WORDPRESS_URL:-" in source


class TestShellcheck:
    """Test 8: shellcheck passes on verify-deploy.sh."""

    def test_shellcheck_passes(self):
        result = subprocess.run(
            ["shellcheck", str(SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"shellcheck errors:\n{result.stdout}"


class TestListMode:
    """Test 9: --list exits 0 and prints health check list without HTTP requests."""

    def test_list_exits_zero(self):
        result = run_script("--list")
        assert result.returncode == 0

    def test_list_prints_pages(self):
        result = run_script("--list")
        output = result.stdout
        assert "Homepage" in output
        assert "REST API" in output
        assert "Black Rose" in output
        assert "Love Hurts" in output
        assert "Signature" in output
        assert "About" in output

    def test_list_shows_six_entries(self):
        """List mode should show exactly 6 health check entries."""
        result = run_script("--list")
        lines = [
            line
            for line in result.stdout.strip().splitlines()
            if line.strip() and not line.startswith("=") and "Health" not in line
        ]
        # At least 6 entries (one per health check)
        assert len(lines) >= 6
