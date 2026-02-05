"""
Integration tests for SecurityOpsAgent.

Tests vulnerability scanning, remediation, and compliance reporting.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agents.security_ops_agent import SecurityOpsAgent


@pytest.fixture
def security_agent():
    """Create SecurityOpsAgent instance for testing."""
    return SecurityOpsAgent(repo_path="/tmp/test_repo")


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for testing."""
    with patch("agents.security_ops_agent.subprocess.run") as mock:
        yield mock


class TestVulnerabilityScanning:
    """Test vulnerability scanning capabilities."""

    @pytest.mark.asyncio
    async def test_scan_python_vulnerabilities_no_vulns(self, security_agent, mock_subprocess):
        """Test Python vulnerability scan with no vulnerabilities."""
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"dependencies": [{"name": "requests", "version": "2.31.0", "vulns": []}]}),
            stderr="",
        )

        result = await security_agent._handle_scan_python_vulnerabilities(format="json")

        assert result["success"] is True
        assert result["count"] == 0
        mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_scan_python_vulnerabilities_found(self, security_agent, mock_subprocess):
        """Test Python vulnerability scan with vulnerabilities found."""
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout=json.dumps(
                {
                    "dependencies": [
                        {
                            "name": "protobuf",
                            "version": "5.29.5",
                            "vulns": [
                                {
                                    "id": "CVE-2026-0994",
                                    "fix_versions": ["6.33.5"],
                                    "description": "JSON recursion depth bypass",
                                }
                            ],
                        }
                    ]
                }
            ),
            stderr="",
        )

        result = await security_agent._handle_scan_python_vulnerabilities(format="json")

        assert result["success"] is True
        assert result["count"] == 1
        assert "CVE-2026-0994" in result["raw_output"]

    @pytest.mark.asyncio
    async def test_scan_javascript_vulnerabilities(self, security_agent, mock_subprocess):
        """Test JavaScript vulnerability scan."""
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"vulnerabilities": {}, "metadata": {"total": 0}}),
            stderr="",
        )

        result = await security_agent._handle_scan_javascript_vulnerabilities(package_manager="pnpm")

        assert result["success"] is True
        assert result["has_vulnerabilities"] is False


class TestDependabotIntegration:
    """Test GitHub Dependabot API integration."""

    @pytest.mark.asyncio
    async def test_get_dependabot_alerts_open(self, security_agent, mock_subprocess):
        """Test fetching open Dependabot alerts."""
        alerts = [
            {
                "number": 255,
                "state": "open",
                "security_advisory": {"severity": "high", "cve_id": "CVE-2025-1234"},
                "dependency": {"package": {"name": "fastify"}},
            }
        ]
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(alerts),
            stderr="",
        )

        result = await security_agent._handle_get_dependabot_alerts(state="open", severity="all")

        assert result["success"] is True
        assert result["count"] == 1
        assert "high" in result["summary"]["by_severity"]

    @pytest.mark.asyncio
    async def test_get_dependabot_alerts_severity_filter(self, security_agent, mock_subprocess):
        """Test filtering Dependabot alerts by severity."""
        alerts = [
            {
                "number": 1,
                "state": "open",
                "security_advisory": {"severity": "high"},
                "dependency": {"package": {"name": "pkg1"}},
            },
            {
                "number": 2,
                "state": "open",
                "security_advisory": {"severity": "medium"},
                "dependency": {"package": {"name": "pkg2"}},
            },
        ]
        mock_subprocess.return_value = MagicMock(returncode=0, stdout=json.dumps(alerts), stderr="")

        result = await security_agent._handle_get_dependabot_alerts(state="open", severity="high")

        assert result["success"] is True
        assert result["count"] == 1


class TestVulnerabilityRemediation:
    """Test vulnerability remediation capabilities."""

    @pytest.mark.asyncio
    async def test_fix_python_vulnerability_upgrade(self, security_agent, mock_subprocess):
        """Test fixing Python vulnerability by upgrading package."""
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="Successfully installed protobuf-6.33.5",
            stderr="",
        )

        result = await security_agent._handle_fix_python_vulnerability(
            package="protobuf",
            fixed_version="6.33.5",
            current_version="5.29.5",
        )

        assert result["success"] is True
        assert result["action"] == "upgraded"
        assert result["package"] == "protobuf"
        assert result["version"] == "6.33.5"

    @pytest.mark.asyncio
    async def test_fix_python_vulnerability_remove_blocking(self, security_agent, mock_subprocess):
        """Test removing blocking package for security upgrade."""
        # First call (upgrade) fails
        # Second call (remove) succeeds
        mock_subprocess.side_effect = [
            MagicMock(returncode=1, stdout="", stderr="Dependency conflict"),
            MagicMock(returncode=0, stdout="Successfully uninstalled stability-sdk", stderr=""),
        ]

        result = await security_agent._handle_fix_python_vulnerability(
            package="stability-sdk",
            fixed_version="1.0.0",
            remove_if_blocking=True,
        )

        assert result["success"] is True
        assert result["action"] == "removed"
        assert result["reason"] == "blocked security upgrade"

    @pytest.mark.asyncio
    async def test_fix_javascript_vulnerability(self, security_agent, mock_subprocess):
        """Test fixing JavaScript vulnerability with lockfile update."""
        # Create mock package.json
        package_json = security_agent.repo_path / "package.json"
        package_json.parent.mkdir(parents=True, exist_ok=True)
        package_json.write_text(json.dumps({"name": "test", "pnpm": {"overrides": {}}}))

        mock_subprocess.return_value = MagicMock(returncode=0, stdout="Lockfile updated", stderr="")

        result = await security_agent._handle_fix_javascript_vulnerability(
            package="fastify",
            fixed_version="5.7.3",
            package_manager="pnpm",
        )

        assert result["success"] is True
        assert result["lockfile_updated"] is True


class TestComplianceReporting:
    """Test compliance reporting and documentation."""

    @pytest.mark.asyncio
    async def test_generate_security_report_markdown(self, security_agent, mock_subprocess):
        """Test generating markdown security report."""
        # Mock all scan results
        with patch.object(security_agent, "_handle_scan_python_vulnerabilities") as mock_py:
            with patch.object(security_agent, "_handle_scan_javascript_vulnerabilities") as mock_js:
                with patch.object(security_agent, "_handle_get_dependabot_alerts") as mock_db:
                    mock_py.return_value = {"success": True, "count": 0}
                    mock_js.return_value = {"success": True, "has_vulnerabilities": False}
                    mock_db.return_value = {"success": True, "count": 0, "summary": {}}

                    result = await security_agent._handle_generate_security_report(output_format="markdown")

                    assert result["success"] is True
                    assert result["format"] == "markdown"
                    assert "Security Report" in result["report"]
                    assert "Python Vulnerabilities: 0" in result["report"]

    @pytest.mark.asyncio
    async def test_commit_security_fixes(self, security_agent, mock_subprocess):
        """Test committing security fixes with audit trail."""
        fixes = [
            {"action": "upgraded", "package": "protobuf", "version": "6.33.5"},
            {"action": "removed", "package": "ecdsa", "reason": "blocked security upgrade"},
        ]

        # Mock git commands
        mock_subprocess.side_effect = [
            MagicMock(returncode=0),  # git add
            MagicMock(returncode=0, stdout="[main abc123] fix(security)"),  # git commit
            MagicMock(returncode=0),  # git push
        ]

        result = await security_agent._handle_commit_security_fixes(fixes=fixes, push=True)

        assert result["success"] is True
        assert result["committed"] is True
        assert result["pushed"] is True
        assert result["fixes_count"] == 2
        assert "UPGRADED PACKAGES" in result["message"]
        assert "REMOVED PACKAGES" in result["message"]


class TestEndToEndScenarios:
    """Test complete end-to-end security workflows."""

    @pytest.mark.asyncio
    async def test_full_vulnerability_remediation_workflow(self, security_agent):
        """Test complete workflow: scan → fix → verify → commit."""
        # This would test the agent's process() method with a full task
        # Requires integration with actual LLM and tools
        pass

    @pytest.mark.asyncio
    async def test_zero_vulnerability_achievement(self, security_agent):
        """Test achieving zero vulnerabilities from 17 initial vulns."""
        # Simulate the exact scenario we just completed manually
        pass


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_scan_with_tool_not_installed(self, security_agent, mock_subprocess):
        """Test graceful handling when security tools not installed."""
        mock_subprocess.side_effect = FileNotFoundError("pip-audit not found")

        result = await security_agent._handle_scan_python_vulnerabilities()

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_github_api_auth_failure(self, security_agent, mock_subprocess):
        """Test handling GitHub API authentication failures."""
        mock_subprocess.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="HTTP 401: Bad credentials",
        )

        result = await security_agent._handle_get_dependabot_alerts()

        assert result["success"] is False
        assert "credentials" in result["error"].lower()


@pytest.mark.integration
class TestRealWorldIntegration:
    """Real integration tests requiring actual tools."""

    @pytest.mark.skipif("not config.getoption('--run-integration')", reason="Requires --run-integration flag")
    @pytest.mark.asyncio
    async def test_real_pip_audit(self):
        """Test with real pip-audit on actual repository."""
        agent = SecurityOpsAgent(repo_path=Path.cwd())
        result = await agent._handle_scan_python_vulnerabilities(format="json")

        assert result["success"] is True
        # Should have 0 vulnerabilities after our fixes
        assert result["count"] == 0

    @pytest.mark.skipif("not config.getoption('--run-integration')", reason="Requires --run-integration flag")
    @pytest.mark.asyncio
    async def test_real_dependabot_check(self):
        """Test with real GitHub Dependabot API."""
        agent = SecurityOpsAgent(repo_path=Path.cwd())
        result = await agent._handle_get_dependabot_alerts(state="open")

        assert result["success"] is True
        # Should have 0 open alerts after our fixes
        assert result["count"] == 0
