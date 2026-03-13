"""
SDK Operations Domain Agents
==============================

SDK-powered sub-agents for the Operations core domain.
These agents can actually run commands, read logs, edit files,
and execute deployment scripts — not just generate text about them.

Agents:
    SDKDeployRunnerAgent   — Run deploys, health checks, rollbacks
    SDKCodeDoctorAgent     — Run linters, fix code, type-check
    SDKSecurityScannerAgent — Scan deps, audit files, patch vulns
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.claude_sdk.sdk_sub_agent import SDKSubAgent
from agents.claude_sdk.tool_bridge import ToolProfile
from agents.core.base import CoreAgentType


class SDKDeployRunnerAgent(SDKSubAgent):
    """Deployment specialist with actual shell access.

    Can run deploy scripts, check health endpoints, read logs,
    verify builds, and execute rollbacks — not just plan them.
    """

    name = "sdk_deploy_runner"
    parent_type = CoreAgentType.OPERATIONS
    description = "Run deployments, health probes, rollbacks via shell"
    capabilities = [
        "deploy_run",
        "health_probe",
        "rollback_execute",
        "log_analysis",
        "build_verify",
    ]
    sdk_tools = ToolProfile.OPERATIONS
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/operations/deploy")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy Deployment Runner. You have shell "
            "access to execute real operations.\n\n"
            "Stack:\n"
            "- Python backend: FastAPI on Vercel (serverless)\n"
            "- Frontend: Next.js 16 on Vercel (devskyy.app)\n"
            "- WordPress: skyyrose-flagship theme on shared hosting\n"
            "- MCP server: devskyy_mcp.py\n\n"
            "Health endpoints: /health, /health/ready, /health/live\n\n"
            "Rules:\n"
            "- NEVER force-push or delete production branches\n"
            "- Always check health after deploy actions\n"
            "- Read logs before diagnosing issues\n"
            "- Use git status/diff before any git operations\n"
            "- Report results with concrete data (status codes, "
            "timestamps, error messages)"
        )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """Execute deployment task with real shell access."""
        prompt = self._build_task_prompt(task, **kwargs)
        result = await self._sdk_execute(prompt, label="deploy")

        if result.success:
            return {
                "success": True,
                "result": result.response,
                "agent": self.name,
                "execution_mode": "sdk",
                "metrics": result.metrics,
            }

        # No LLM fallback for deploy — tool access is essential
        return {
            "success": False,
            "result": "",
            "agent": self.name,
            "error": result.error,
            "execution_mode": "failed",
        }


class SDKCodeDoctorAgent(SDKSubAgent):
    """Code quality specialist with actual lint/fix capabilities.

    Can run ruff, mypy, black, ESLint — then read the output,
    edit the files to fix issues, and verify the fixes pass.
    """

    name = "sdk_code_doctor"
    parent_type = CoreAgentType.OPERATIONS
    description = "Run linters, fix code issues, type-check, verify"
    capabilities = [
        "lint_run",
        "lint_fix",
        "type_check",
        "format_code",
        "code_review",
        "auto_fix",
    ]
    sdk_tools = ToolProfile.OPERATIONS
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/operations/code_doctor")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy Code Doctor. You diagnose and fix "
            "code quality issues with real tool access.\n\n"
            "Tools & standards:\n"
            "- Python: ruff check, ruff format, black (100 char line), "
            "mypy --ignore-missing-imports, isort\n"
            "- TypeScript: npm run lint, npm run type-check\n"
            "- Files < 800 lines, functions < 50 lines\n"
            "- All fixes must pass lint after editing\n\n"
            "Workflow:\n"
            "1. Run the linter/checker to identify issues\n"
            "2. Read the affected files\n"
            "3. Edit to fix (use Edit tool for targeted changes)\n"
            "4. Re-run the checker to verify fix\n"
            "5. Report what was fixed with file paths and line numbers"
        )


class SDKSecurityScannerAgent(SDKSubAgent):
    """Security scanner with actual file and dependency access.

    Can read requirements.txt/package.json, run audit commands,
    scan code for OWASP patterns, and apply patches.
    """

    name = "sdk_security_scanner"
    parent_type = CoreAgentType.OPERATIONS
    description = "Scan vulnerabilities, audit deps, patch security issues"
    capabilities = [
        "dep_audit",
        "code_scan",
        "secret_scan",
        "patch_apply",
        "compliance_check",
    ]
    sdk_tools = ToolProfile.OPERATIONS
    sdk_model = "sonnet"
    sdk_output_base = Path("data/sdk_sessions/operations/security")

    def _sdk_default_prompt(self) -> str:
        return (
            "You are the DevSkyy Security Scanner. You have file and "
            "shell access to perform real security audits.\n\n"
            "Checks to perform:\n"
            "- pip audit / npm audit for dependency vulnerabilities\n"
            "- Grep for hardcoded secrets, API keys, passwords\n"
            "- OWASP Top 10: SQL injection, XSS, SSRF patterns\n"
            "- Check .env files are gitignored\n"
            "- Verify CORS, CSP, and auth middleware config\n\n"
            "Rules:\n"
            "- NEVER expose actual secret values in output\n"
            "- Classify findings as CRITICAL/HIGH/MEDIUM/LOW\n"
            "- Include file path + line number for each finding\n"
            "- Suggest specific remediation for each issue\n"
            "- Run fixes only if explicitly asked — default to report"
        )


__all__ = [
    "SDKDeployRunnerAgent",
    "SDKCodeDoctorAgent",
    "SDKSecurityScannerAgent",
]
