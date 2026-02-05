"""
Security Operations Agent for DevSkyy Platform.

Handles:
- Dependency vulnerability scanning (Python, JavaScript)
- Automated security remediation
- GitHub Dependabot integration
- Compliance reporting and audit trails

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from agents.base_super_agent import BaseSuperAgent
from agents.models import AgentConfig, AgentResponse, ToolDefinition

logger = logging.getLogger(__name__)


class SecurityOpsAgent(BaseSuperAgent):
    """Agent specialized for security operations and vulnerability management."""

    AGENT_NAME = "security_ops_agent"
    AGENT_VERSION = "1.0.0"

    # Agent-specific system prompt
    SYSTEM_PROMPT = """You are the Security Operations Agent for DevSkyy/SkyyRose.

Your mission: Maintain zero security vulnerabilities across all dependencies.

Your capabilities:
- Scan Python (pip-audit, safety) and JavaScript (npm audit, pnpm audit) dependencies
- Detect CVEs via GitHub Dependabot API integration
- Auto-remediate vulnerabilities by upgrading packages to secure versions
- Remove blocking dependencies when necessary for security compliance
- Generate compliance reports with audit trails
- Commit and push security fixes with detailed documentation

Security Philosophy:
- Zero tolerance for HIGH severity vulnerabilities
- MEDIUM vulnerabilities patched within 7 days
- LOW vulnerabilities patched in regular maintenance cycles
- Always verify fixes don't break compatibility
- Document all security decisions for audit compliance

Brand context: SkyyRose - "Where Love Meets Luxury" - Oakland-inspired luxury fashion.
Security protects both the platform and our customers' data.

Always:
- Log all security operations for audit trail
- Create detailed commit messages explaining security fixes
- Update SECURITY-FIXES.md with remediation details
- Verify no new vulnerabilities introduced
- Use systematic approach: audit → analyze → fix → verify → document
"""

    def __init__(
        self,
        config: AgentConfig | None = None,
        repo_path: str | None = None,
        github_token: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize security operations agent.

        Args:
            config: Agent configuration
            repo_path: Path to repository root
            github_token: GitHub API token for Dependabot integration
            **kwargs: Additional arguments passed to base agent
        """
        super().__init__(
            name=self.AGENT_NAME,
            system_prompt=self.SYSTEM_PROMPT,
            config=config,
            **kwargs,
        )
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.github_token = github_token
        self._register_tools()

    def _register_tools(self) -> None:
        """Register security operation tools."""
        # Vulnerability scanning tools
        self.register_tool(
            ToolDefinition(
                name="scan_python_vulnerabilities",
                description="Scan Python dependencies for known vulnerabilities using pip-audit",
                parameters={
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["json", "text"],
                            "description": "Output format for vulnerability report",
                        },
                    },
                    "required": [],
                },
                handler=self._handle_scan_python_vulnerabilities,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="scan_javascript_vulnerabilities",
                description="Scan JavaScript dependencies for vulnerabilities using npm/pnpm audit",
                parameters={
                    "type": "object",
                    "properties": {
                        "package_manager": {
                            "type": "string",
                            "enum": ["npm", "pnpm"],
                            "description": "Package manager to use for audit",
                        },
                    },
                    "required": [],
                },
                handler=self._handle_scan_javascript_vulnerabilities,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="get_dependabot_alerts",
                description="Fetch open Dependabot security alerts from GitHub",
                parameters={
                    "type": "object",
                    "properties": {
                        "severity": {
                            "type": "string",
                            "enum": ["critical", "high", "medium", "low", "all"],
                            "description": "Filter alerts by severity",
                        },
                        "state": {
                            "type": "string",
                            "enum": ["open", "fixed", "dismissed", "all"],
                            "description": "Filter alerts by state",
                        },
                    },
                    "required": [],
                },
                handler=self._handle_get_dependabot_alerts,
            )
        )

        # Remediation tools
        self.register_tool(
            ToolDefinition(
                name="fix_python_vulnerability",
                description="Fix a Python package vulnerability by upgrading to secure version",
                parameters={
                    "type": "object",
                    "properties": {
                        "package": {"type": "string", "description": "Package name"},
                        "current_version": {"type": "string", "description": "Current vulnerable version"},
                        "fixed_version": {"type": "string", "description": "Fixed version to upgrade to"},
                        "remove_if_blocking": {
                            "type": "boolean",
                            "description": "Remove package if it blocks security upgrade",
                        },
                    },
                    "required": ["package", "fixed_version"],
                },
                handler=self._handle_fix_python_vulnerability,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="fix_javascript_vulnerability",
                description="Fix JavaScript package vulnerability by updating lockfile",
                parameters={
                    "type": "object",
                    "properties": {
                        "package": {"type": "string", "description": "Package name"},
                        "fixed_version": {"type": "string", "description": "Fixed version"},
                        "package_manager": {
                            "type": "string",
                            "enum": ["npm", "pnpm"],
                            "description": "Package manager to use",
                        },
                    },
                    "required": ["package", "fixed_version"],
                },
                handler=self._handle_fix_javascript_vulnerability,
            )
        )

        # Documentation and compliance
        self.register_tool(
            ToolDefinition(
                name="generate_security_report",
                description="Generate comprehensive security compliance report",
                parameters={
                    "type": "object",
                    "properties": {
                        "include_fixed": {
                            "type": "boolean",
                            "description": "Include fixed vulnerabilities in report",
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["markdown", "json", "html"],
                            "description": "Report output format",
                        },
                    },
                    "required": [],
                },
                handler=self._handle_generate_security_report,
            )
        )

        self.register_tool(
            ToolDefinition(
                name="commit_security_fixes",
                description="Commit security fixes with detailed audit trail",
                parameters={
                    "type": "object",
                    "properties": {
                        "fixes": {
                            "type": "array",
                            "description": "List of fixes applied",
                            "items": {"type": "object"},
                        },
                        "push": {"type": "boolean", "description": "Auto-push to remote"},
                    },
                    "required": ["fixes"],
                },
                handler=self._handle_commit_security_fixes,
            )
        )

    async def _handle_scan_python_vulnerabilities(
        self,
        format: str = "json",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Scan Python dependencies for vulnerabilities."""
        logger.info(f"{self.AGENT_NAME}: Scanning Python vulnerabilities")
        try:
            result = subprocess.run(
                ["pip-audit", "--format", format],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )

            if format == "json" and result.stdout:
                vulnerabilities = json.loads(result.stdout)
                vuln_count = len([d for d in vulnerabilities.get("dependencies", []) if d.get("vulns")])
                return {
                    "success": True,
                    "vulnerabilities": vulnerabilities,
                    "count": vuln_count,
                    "raw_output": result.stdout,
                }
            else:
                return {
                    "success": True,
                    "output": result.stdout,
                    "has_vulnerabilities": result.returncode != 0,
                }
        except Exception as e:
            logger.error(f"Python vulnerability scan failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_scan_javascript_vulnerabilities(
        self,
        package_manager: str = "pnpm",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Scan JavaScript dependencies for vulnerabilities."""
        logger.info(f"{self.AGENT_NAME}: Scanning JavaScript vulnerabilities with {package_manager}")
        try:
            cmd = [package_manager, "audit", "--json"] if package_manager == "npm" else ["pnpm", "audit", "--json"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )

            if result.stdout:
                try:
                    audit_data = json.loads(result.stdout)
                    return {
                        "success": True,
                        "audit": audit_data,
                        "has_vulnerabilities": result.returncode != 0,
                    }
                except json.JSONDecodeError:
                    return {
                        "success": True,
                        "output": result.stdout,
                        "has_vulnerabilities": result.returncode != 0,
                    }
            return {"success": True, "has_vulnerabilities": False}
        except Exception as e:
            logger.error(f"JavaScript vulnerability scan failed: {e}")
            return {"success": False, "error": str(e)}

    async def _handle_get_dependabot_alerts(
        self,
        severity: str = "all",
        state: str = "open",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Fetch Dependabot alerts from GitHub API."""
        logger.info(f"{self.AGENT_NAME}: Fetching Dependabot alerts (severity={severity}, state={state})")
        try:
            # Use gh CLI for GitHub API access
            cmd = ["gh", "api", "repos/The-Skyy-Rose-Collection-LLC/DevSkyy/dependabot/alerts"]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)

            if result.returncode != 0:
                return {"success": False, "error": result.stderr}

            alerts = json.loads(result.stdout)

            # Filter by state
            if state != "all":
                alerts = [a for a in alerts if a.get("state") == state]

            # Filter by severity
            if severity != "all":
                alerts = [a for a in alerts if a.get("security_advisory", {}).get("severity") == severity]

            return {
                "success": True,
                "alerts": alerts,
                "count": len(alerts),
                "summary": self._summarize_alerts(alerts),
            }
        except Exception as e:
            logger.error(f"Failed to fetch Dependabot alerts: {e}")
            return {"success": False, "error": str(e)}

    def _summarize_alerts(self, alerts: list[dict]) -> dict[str, Any]:
        """Summarize Dependabot alerts by severity and package."""
        summary = {"by_severity": {}, "by_package": {}}

        for alert in alerts:
            severity = alert.get("security_advisory", {}).get("severity", "unknown")
            package = alert.get("dependency", {}).get("package", {}).get("name", "unknown")

            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            if package not in summary["by_package"]:
                summary["by_package"][package] = []
            summary["by_package"][package].append(
                {
                    "number": alert.get("number"),
                    "severity": severity,
                    "cve": alert.get("security_advisory", {}).get("cve_id"),
                }
            )

        return summary

    async def _handle_fix_python_vulnerability(
        self,
        package: str,
        fixed_version: str,
        current_version: str | None = None,
        remove_if_blocking: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Fix Python package vulnerability."""
        logger.info(f"{self.AGENT_NAME}: Fixing {package} vulnerability → {fixed_version}")
        try:
            # Try to upgrade package
            result = subprocess.run(
                ["pip", "install", "--upgrade", f"{package}>={fixed_version}"],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "action": "upgraded",
                    "package": package,
                    "version": fixed_version,
                    "output": result.stdout,
                }

            # If upgrade failed and remove_if_blocking is True, try removing package
            if remove_if_blocking:
                logger.warning(f"Removing blocking package: {package}")
                remove_result = subprocess.run(
                    ["pip", "uninstall", "-y", package],
                    capture_output=True,
                    text=True,
                    cwd=self.repo_path,
                )
                if remove_result.returncode == 0:
                    return {
                        "success": True,
                        "action": "removed",
                        "package": package,
                        "reason": "blocked security upgrade",
                        "output": remove_result.stdout,
                    }

            return {"success": False, "error": result.stderr, "package": package}
        except Exception as e:
            logger.error(f"Failed to fix {package}: {e}")
            return {"success": False, "error": str(e), "package": package}

    async def _handle_fix_javascript_vulnerability(
        self,
        package: str,
        fixed_version: str,
        package_manager: str = "pnpm",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Fix JavaScript package vulnerability."""
        logger.info(f"{self.AGENT_NAME}: Fixing {package} JS vulnerability → {fixed_version}")
        try:
            # Update package.json override
            package_json_path = self.repo_path / "package.json"
            if package_json_path.exists():
                with open(package_json_path) as f:
                    package_data = json.load(f)

                # Add to pnpm overrides
                if "pnpm" not in package_data:
                    package_data["pnpm"] = {}
                if "overrides" not in package_data["pnpm"]:
                    package_data["pnpm"]["overrides"] = {}

                package_data["pnpm"]["overrides"][package] = f">={fixed_version}"

                with open(package_json_path, "w") as f:
                    json.dump(package_data, f, indent=2)
                    f.write("\n")

            # Run install to update lockfile
            result = subprocess.run(
                [package_manager, "install"],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )

            return {
                "success": result.returncode == 0,
                "package": package,
                "version": fixed_version,
                "lockfile_updated": True,
                "output": result.stdout if result.returncode == 0 else result.stderr,
            }
        except Exception as e:
            logger.error(f"Failed to fix {package}: {e}")
            return {"success": False, "error": str(e), "package": package}

    async def _handle_generate_security_report(
        self,
        include_fixed: bool = True,
        output_format: str = "markdown",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate comprehensive security report."""
        logger.info(f"{self.AGENT_NAME}: Generating security report ({output_format})")
        try:
            # Gather data
            python_scan = await self._handle_scan_python_vulnerabilities(format="json")
            js_scan = await self._handle_scan_javascript_vulnerabilities()
            dependabot = await self._handle_get_dependabot_alerts(state="all" if include_fixed else "open")

            timestamp = datetime.now().isoformat()

            if output_format == "markdown":
                report = self._generate_markdown_report(python_scan, js_scan, dependabot, timestamp)
            elif output_format == "json":
                report = json.dumps(
                    {
                        "timestamp": timestamp,
                        "python": python_scan,
                        "javascript": js_scan,
                        "dependabot": dependabot,
                    },
                    indent=2,
                )
            else:
                report = "HTML format not yet implemented"

            return {"success": True, "report": report, "format": output_format, "timestamp": timestamp}
        except Exception as e:
            logger.error(f"Failed to generate security report: {e}")
            return {"success": False, "error": str(e)}

    def _generate_markdown_report(
        self,
        python_scan: dict,
        js_scan: dict,
        dependabot: dict,
        timestamp: str,
    ) -> str:
        """Generate markdown security report."""
        python_count = python_scan.get("count", 0) if python_scan.get("success") else "ERROR"
        js_vulns = "Unknown" if not js_scan.get("success") else ("Yes" if js_scan.get("has_vulnerabilities") else "No")
        dependabot_count = dependabot.get("count", 0) if dependabot.get("success") else "ERROR"

        report = f"""# Security Report - {timestamp}

## Summary

- **Python Vulnerabilities**: {python_count}
- **JavaScript Vulnerabilities**: {js_vulns}
- **Dependabot Alerts**: {dependabot_count}

## Python Dependencies (pip-audit)

{json.dumps(python_scan, indent=2)}

## JavaScript Dependencies

{json.dumps(js_scan, indent=2)}

## GitHub Dependabot

{json.dumps(dependabot.get('summary', {}), indent=2)}

---
Generated by SecurityOpsAgent v{self.AGENT_VERSION}
"""
        return report

    async def _handle_commit_security_fixes(
        self,
        fixes: list[dict],
        push: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Commit security fixes with detailed message."""
        logger.info(f"{self.AGENT_NAME}: Committing {len(fixes)} security fixes")
        try:
            # Stage all changes
            subprocess.run(["git", "add", "-A"], cwd=self.repo_path, check=True)

            # Generate commit message
            commit_msg = self._generate_commit_message(fixes)

            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                capture_output=True,
                text=True,
                cwd=self.repo_path,
            )

            if result.returncode != 0 and "nothing to commit" not in result.stdout:
                return {"success": False, "error": result.stderr}

            # Push if requested
            if push:
                push_result = subprocess.run(
                    ["git", "push", "origin", "main"],
                    capture_output=True,
                    text=True,
                    cwd=self.repo_path,
                )
                if push_result.returncode != 0:
                    return {"success": False, "error": f"Push failed: {push_result.stderr}", "committed": True}

            return {
                "success": True,
                "committed": True,
                "pushed": push,
                "fixes_count": len(fixes),
                "message": commit_msg,
            }
        except Exception as e:
            logger.error(f"Failed to commit fixes: {e}")
            return {"success": False, "error": str(e)}

    def _generate_commit_message(self, fixes: list[dict]) -> str:
        """Generate detailed commit message for security fixes."""
        msg_lines = ["fix(security): automated vulnerability remediation\n"]

        # Group by action type
        upgraded = [f for f in fixes if f.get("action") == "upgraded"]
        removed = [f for f in fixes if f.get("action") == "removed"]

        if upgraded:
            msg_lines.append("UPGRADED PACKAGES:")
            for fix in upgraded:
                msg_lines.append(f"- {fix.get('package')}: → {fix.get('version')}")

        if removed:
            msg_lines.append("\nREMOVED PACKAGES:")
            for fix in removed:
                msg_lines.append(f"- {fix.get('package')}: {fix.get('reason')}")

        msg_lines.append("\nAutomated by SecurityOpsAgent")
        msg_lines.append("Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>")

        return "\n".join(msg_lines)

    async def process(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Process a security operations task.

        Args:
            task: Task description (e.g., "audit dependencies", "fix all vulnerabilities")
            context: Optional context with additional parameters

        Returns:
            AgentResponse with security operation results
        """
        logger.info(f"{self.AGENT_NAME}: Processing security task: {task}")

        # Use base agent's plan-retrieve-execute-validate cycle
        # The reasoning techniques will help determine the best approach
        return await super().process(task, context)
