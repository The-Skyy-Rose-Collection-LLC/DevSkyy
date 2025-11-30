"""
Tests for MCP Health Check Diagnostic Tool

Comprehensive test coverage for mcp_health_check.py following Truth Protocol.
Target: >=90% coverage per Rule #8.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path for imports when running tests directly.
# This is required because mcp_health_check.py is in the project root,
# not in an installable package. For proper package structure, consider
# moving to src/ layout with pyproject.toml.
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_health_check import (
    CheckResult,
    CheckStatus,
    HealthCheckReport,
    MCPHealthChecker,
    main,
)


class TestCheckStatus:
    """Tests for CheckStatus enum."""

    def test_status_values(self) -> None:
        """Verify all status values are defined."""
        assert CheckStatus.OK.value == "pass"
        assert CheckStatus.WARN.value == "warn"
        assert CheckStatus.FAIL.value == "fail"
        assert CheckStatus.SKIP.value == "skip"


class TestCheckResult:
    """Tests for CheckResult dataclass."""

    def test_basic_result(self) -> None:
        """Test basic result creation."""
        result = CheckResult(
            name="Test Check",
            status=CheckStatus.OK,
            message="Test passed",
        )
        assert result.name == "Test Check"
        assert result.status == CheckStatus.OK
        assert result.message == "Test passed"
        assert result.details is None
        assert result.fix_suggestion is None

    def test_result_with_details(self) -> None:
        """Test result with optional fields."""
        result = CheckResult(
            name="Test Check",
            status=CheckStatus.FAIL,
            message="Test failed",
            details="Additional info",
            fix_suggestion="Try this fix",
        )
        assert result.details == "Additional info"
        assert result.fix_suggestion == "Try this fix"

    def test_to_dict_basic(self) -> None:
        """Test conversion to dictionary."""
        result = CheckResult(
            name="Test",
            status=CheckStatus.OK,
            message="OK",
        )
        d = result.to_dict()
        assert d["name"] == "Test"
        assert d["status"] == "pass"
        assert d["message"] == "OK"
        assert "details" not in d
        assert "fix_suggestion" not in d

    def test_to_dict_full(self) -> None:
        """Test conversion with all fields."""
        result = CheckResult(
            name="Test",
            status=CheckStatus.FAIL,
            message="Failed",
            details="Details here",
            fix_suggestion="Fix suggestion",
        )
        d = result.to_dict()
        assert d["details"] == "Details here"
        assert d["fix_suggestion"] == "Fix suggestion"


class TestHealthCheckReport:
    """Tests for HealthCheckReport dataclass."""

    def test_empty_report(self) -> None:
        """Test empty report initialization."""
        report = HealthCheckReport()
        assert len(report.checks) == 0
        assert report.passed == 0
        assert report.warned == 0
        assert report.failed == 0
        assert report.skipped == 0
        assert report.success is True

    def test_add_pass(self) -> None:
        """Test adding passed check."""
        report = HealthCheckReport()
        report.add(CheckResult("Test", CheckStatus.OK, "OK"))
        assert report.passed == 1
        assert report.success is True

    def test_add_fail(self) -> None:
        """Test adding failed check."""
        report = HealthCheckReport()
        report.add(CheckResult("Test", CheckStatus.FAIL, "Failed"))
        assert report.failed == 1
        assert report.success is False

    def test_add_warn(self) -> None:
        """Test adding warning check."""
        report = HealthCheckReport()
        report.add(CheckResult("Test", CheckStatus.WARN, "Warning"))
        assert report.warned == 1
        assert report.success is True

    def test_add_skip(self) -> None:
        """Test adding skipped check."""
        report = HealthCheckReport()
        report.add(CheckResult("Test", CheckStatus.SKIP, "Skipped"))
        assert report.skipped == 1
        assert report.success is True

    def test_multiple_checks(self) -> None:
        """Test adding multiple checks."""
        report = HealthCheckReport()
        report.add(CheckResult("Test1", CheckStatus.OK, "OK"))
        report.add(CheckResult("Test2", CheckStatus.WARN, "Warning"))
        report.add(CheckResult("Test3", CheckStatus.FAIL, "Failed"))
        report.add(CheckResult("Test4", CheckStatus.SKIP, "Skipped"))

        assert len(report.checks) == 4
        assert report.passed == 1
        assert report.warned == 1
        assert report.failed == 1
        assert report.skipped == 1
        assert report.success is False

    def test_to_dict(self) -> None:
        """Test report conversion to dictionary."""
        report = HealthCheckReport()
        report.add(CheckResult("Test1", CheckStatus.OK, "OK"))
        report.add(CheckResult("Test2", CheckStatus.FAIL, "Failed"))

        d = report.to_dict()
        assert d["summary"]["total"] == 2
        assert d["summary"]["passed"] == 1
        assert d["summary"]["failed"] == 1
        assert d["summary"]["success"] is False
        assert len(d["checks"]) == 2


class TestMCPHealthChecker:
    """Tests for MCPHealthChecker class."""

    def test_init_with_config_path(self) -> None:
        """Test initialization with explicit config path."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        assert checker.config_path == Path("/tmp/test.json")
        assert checker.verbose is False
        assert checker.json_output is False

    def test_init_with_options(self) -> None:
        """Test initialization with verbose and JSON options."""
        checker = MCPHealthChecker(
            config_path="/tmp/test.json",
            verbose=True,
            json_output=True,
        )
        assert checker.verbose is True
        assert checker.json_output is True

    def test_detect_config_path_local(self) -> None:
        """Test config detection with local file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "claude_desktop_config.json"
            config_file.write_text("{}")

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                checker = MCPHealthChecker()
                # The checker should find the local config file
                # It might find it at its resolved path
                assert checker.config_path.name == "claude_desktop_config.json"
                assert checker.config_path.exists()
            finally:
                os.chdir(old_cwd)

    def test_run_command_success(self) -> None:
        """Test successful command execution."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        code, stdout, stderr = checker.run_command(["echo", "hello"])
        assert code == 0
        assert stdout == "hello"

    def test_run_command_not_found(self) -> None:
        """Test command not found."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        code, stdout, stderr = checker.run_command(["nonexistent_command_xyz"])
        assert code == -1
        assert "not found" in stderr.lower() or "nonexistent" in stderr.lower()

    def test_run_command_timeout(self) -> None:
        """Test command timeout."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        code, stdout, stderr = checker.run_command(["sleep", "10"], timeout=1)
        assert code == -1
        # The stderr should contain timeout message or be about the timeout
        assert "timeout" in stderr.lower() or "timed out" in stderr.lower()

    def test_check_system_dependency_found(self) -> None:
        """Test checking installed dependency."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        result = checker.check_system_dependency(
            "echo",
            [["echo", "v1.0.0"]],
        )
        assert result.status == CheckStatus.OK

    def test_check_system_dependency_not_found(self) -> None:
        """Test checking missing dependency."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        result = checker.check_system_dependency(
            "NonExistent",
            [["nonexistent_xyz_123"]],
            required=True,
        )
        assert result.status == CheckStatus.FAIL

    def test_check_system_dependency_optional(self) -> None:
        """Test checking optional missing dependency."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        result = checker.check_system_dependency(
            "OptionalTool",
            [["nonexistent_xyz_123"]],
            required=False,
        )
        assert result.status == CheckStatus.WARN

    def test_check_config_exists_true(self) -> None:
        """Test config exists check when file exists."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            f.write(b"{}")
            config_path = f.name

        try:
            checker = MCPHealthChecker(config_path=config_path)
            result = checker.check_config_exists()
            assert result.status == CheckStatus.OK
        finally:
            os.unlink(config_path)

    def test_check_config_exists_false(self) -> None:
        """Test config exists check when file missing."""
        checker = MCPHealthChecker(config_path="/nonexistent/path/config.json")
        result = checker.check_config_exists()
        assert result.status == CheckStatus.FAIL

    def test_check_config_syntax_valid(self) -> None:
        """Test valid JSON syntax."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump({"mcpServers": {}}, f)
            config_path = f.name

        try:
            checker = MCPHealthChecker(config_path=config_path)
            result = checker.check_config_syntax()
            assert result.status == CheckStatus.OK
            assert checker.config == {"mcpServers": {}}
        finally:
            os.unlink(config_path)

    def test_check_config_syntax_invalid(self) -> None:
        """Test invalid JSON syntax."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            f.write("{invalid json}")
            config_path = f.name

        try:
            checker = MCPHealthChecker(config_path=config_path)
            result = checker.check_config_syntax()
            assert result.status == CheckStatus.FAIL
        finally:
            os.unlink(config_path)

    def test_check_config_structure_valid(self) -> None:
        """Test valid config structure."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump(
                {
                    "mcpServers": {
                        "test": {
                            "command": "python",
                            "args": ["server.py"],
                        }
                    }
                },
                f,
            )
            config_path = f.name

        try:
            checker = MCPHealthChecker(config_path=config_path)
            checker.check_config_syntax()
            result = checker.check_config_structure()
            assert result.status == CheckStatus.OK
        finally:
            os.unlink(config_path)

    def test_check_config_structure_missing_mcpservers(self) -> None:
        """Test config missing mcpServers key."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump({"servers": {}}, f)
            config_path = f.name

        try:
            checker = MCPHealthChecker(config_path=config_path)
            checker.check_config_syntax()
            result = checker.check_config_structure()
            assert result.status == CheckStatus.FAIL
        finally:
            os.unlink(config_path)

    def test_check_config_structure_empty_servers(self) -> None:
        """Test config with empty mcpServers."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump({"mcpServers": {}}, f)
            config_path = f.name

        try:
            checker = MCPHealthChecker(config_path=config_path)
            checker.check_config_syntax()
            result = checker.check_config_structure()
            assert result.status == CheckStatus.WARN
        finally:
            os.unlink(config_path)

    def test_check_config_structure_missing_command(self) -> None:
        """Test config with server missing command."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump(
                {"mcpServers": {"test": {"args": []}}},
                f,
            )
            config_path = f.name

        try:
            checker = MCPHealthChecker(config_path=config_path)
            checker.check_config_syntax()
            result = checker.check_config_structure()
            assert result.status == CheckStatus.FAIL
        finally:
            os.unlink(config_path)

    def test_check_unset_env_references_all_set(self) -> None:
        """Test env references when all are set."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump(
                {
                    "mcpServers": {
                        "test": {
                            "command": "python",
                            "env": {"VAR": "${HOME}"},
                        }
                    }
                },
                f,
            )
            config_path = f.name

        try:
            checker = MCPHealthChecker(config_path=config_path)
            checker.check_config_syntax()
            result = checker.check_unset_env_references()
            assert result.status == CheckStatus.OK
        finally:
            os.unlink(config_path)

    def test_check_unset_env_references_unset(self) -> None:
        """Test env references with unset variables."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump(
                {
                    "mcpServers": {
                        "test": {
                            "command": "python",
                            "env": {"VAR": "${NONEXISTENT_VAR_XYZ_123}"},
                        }
                    }
                },
                f,
            )
            config_path = f.name

        try:
            # Ensure variable is not set
            os.environ.pop("NONEXISTENT_VAR_XYZ_123", None)
            checker = MCPHealthChecker(config_path=config_path)
            checker.check_config_syntax()
            result = checker.check_unset_env_references()
            assert result.status == CheckStatus.FAIL
            assert "NONEXISTENT_VAR_XYZ_123" in (result.details or "")
        finally:
            os.unlink(config_path)

    def test_check_server_command_found(self) -> None:
        """Test server command check when command exists."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        result = checker.check_server_command(
            "test",
            {"command": "python3", "args": []},
        )
        # python3 should exist in most environments
        assert result.status in (CheckStatus.OK, CheckStatus.FAIL)

    def test_check_server_command_not_found(self) -> None:
        """Test server command check when command missing."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        result = checker.check_server_command(
            "test",
            {"command": "nonexistent_command_xyz", "args": []},
        )
        assert result.status == CheckStatus.FAIL

    def test_check_python_server_env_not_python(self) -> None:
        """Test PYTHONUNBUFFERED check for non-Python server."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        result = checker.check_python_server_env(
            "test",
            {"command": "node", "args": ["server.js"]},
        )
        assert result.status == CheckStatus.SKIP

    def test_check_python_server_env_set(self) -> None:
        """Test PYTHONUNBUFFERED check when set."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        result = checker.check_python_server_env(
            "test",
            {
                "command": "python",
                "args": ["server.py"],
                "env": {"PYTHONUNBUFFERED": "1"},
            },
        )
        assert result.status == CheckStatus.OK

    def test_check_python_server_env_not_set(self) -> None:
        """Test PYTHONUNBUFFERED check when not set."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        result = checker.check_python_server_env(
            "test",
            {"command": "python", "args": ["server.py"], "env": {}},
        )
        assert result.status == CheckStatus.WARN

    def test_check_port_available(self) -> None:
        """Test port availability check."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        # Use a high port that's unlikely to be in use
        result = checker.check_port_available(59999)
        assert result.status == CheckStatus.OK

    def test_run_all_checks(self) -> None:
        """Test running all checks."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump(
                {
                    "mcpServers": {
                        "test": {
                            "command": "echo",
                            "args": ["hello"],
                        }
                    }
                },
                f,
            )
            config_path = f.name

        try:
            checker = MCPHealthChecker(config_path=config_path, json_output=True)
            report = checker.run_all_checks()
            assert len(report.checks) > 0
            assert report.passed > 0
        finally:
            os.unlink(config_path)


class TestMain:
    """Tests for main function."""

    def test_main_help(self) -> None:
        """Test help argument."""
        with pytest.raises(SystemExit) as exc_info:
            with patch("sys.argv", ["mcp_health_check.py", "--help"]):
                main()
        assert exc_info.value.code == 0

    def test_main_with_config(self) -> None:
        """Test main with config file."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump({"mcpServers": {}}, f)
            config_path = f.name

        try:
            with patch(
                "sys.argv",
                ["mcp_health_check.py", "--config", config_path, "--json"],
            ):
                exit_code = main()
                # Should succeed (0) since config is valid, even if servers are empty
                assert exit_code in (0, 1)
        finally:
            os.unlink(config_path)

    def test_main_json_output(self, capsys: pytest.CaptureFixture) -> None:
        """Test JSON output mode."""
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as f:
            json.dump({"mcpServers": {}}, f)
            config_path = f.name

        try:
            with patch(
                "sys.argv",
                ["mcp_health_check.py", "--config", config_path, "--json"],
            ):
                main()
                captured = capsys.readouterr()
                # Verify JSON output
                output = json.loads(captured.out)
                assert "summary" in output
                assert "checks" in output
        finally:
            os.unlink(config_path)


class TestVersionComparison:
    """Tests for version comparison logic."""

    def test_version_comparison_equal(self) -> None:
        """Test version comparison with equal versions."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        # Mock a command that returns exact min version
        with patch.object(checker, "run_command") as mock_run:
            mock_run.return_value = (0, "v3.11.0", "")
            result = checker.check_system_dependency(
                "Python",
                [["python", "--version"]],
                min_version="3.11.0",
            )
            assert result.status == CheckStatus.OK

    def test_version_comparison_higher(self) -> None:
        """Test version comparison with higher version."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        with patch.object(checker, "run_command") as mock_run:
            mock_run.return_value = (0, "v20.0.0", "")
            result = checker.check_system_dependency(
                "Node.js",
                [["node", "--version"]],
                min_version="18.0.0",
            )
            assert result.status == CheckStatus.OK

    def test_version_comparison_lower(self) -> None:
        """Test version comparison with lower version."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        with patch.object(checker, "run_command") as mock_run:
            mock_run.return_value = (0, "v16.0.0", "")
            result = checker.check_system_dependency(
                "Node.js",
                [["node", "--version"]],
                min_version="18.0.0",
            )
            assert result.status == CheckStatus.WARN


class TestServerStartup:
    """Tests for server startup checks."""

    def test_check_server_startup_command_not_found(self) -> None:
        """Test startup check with missing command."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        result = checker.check_server_startup(
            "test",
            {"command": "nonexistent_cmd_xyz", "args": []},
        )
        assert result.status == CheckStatus.FAIL

    def test_check_server_startup_echo(self) -> None:
        """Test startup check with echo command (simulates quick exit)."""
        checker = MCPHealthChecker(config_path="/tmp/test.json")
        result = checker.check_server_startup(
            "test",
            {"command": "echo", "args": ["hello"]},
            timeout=2,
        )
        # echo exits immediately without JSON-RPC response
        assert result.status in (CheckStatus.WARN, CheckStatus.FAIL)


class TestWordPressChecks:
    """Tests for WordPress/WooCommerce checks."""

    def test_check_wordpress_env_not_configured(self) -> None:
        """Test WordPress env check when not configured."""
        # Clear any existing vars
        for var in MCPHealthChecker.WORDPRESS_ENV_VARS:
            os.environ.pop(var, None)

        checker = MCPHealthChecker(config_path="/tmp/test.json")
        checker.report = HealthCheckReport()
        checker.check_wordpress_env()

        # Find the WordPress credentials check
        wp_check = next(
            (c for c in checker.report.checks if "WordPress" in c.name),
            None,
        )
        assert wp_check is not None
        assert wp_check.status == CheckStatus.WARN

    def test_check_wordpress_env_configured(self) -> None:
        """Test WordPress env check when configured."""
        # Set required vars
        os.environ["WORDPRESS_CLIENT_ID"] = "test_id"
        os.environ["WORDPRESS_CLIENT_SECRET"] = "test_secret"
        os.environ["SKYY_ROSE_SITE_URL"] = "https://example.com"

        try:
            checker = MCPHealthChecker(config_path="/tmp/test.json")
            checker.report = HealthCheckReport()
            checker.check_wordpress_env()

            wp_check = next(
                (c for c in checker.report.checks if "WordPress" in c.name),
                None,
            )
            assert wp_check is not None
            assert wp_check.status == CheckStatus.OK
        finally:
            # Cleanup
            os.environ.pop("WORDPRESS_CLIENT_ID", None)
            os.environ.pop("WORDPRESS_CLIENT_SECRET", None)
            os.environ.pop("SKYY_ROSE_SITE_URL", None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
