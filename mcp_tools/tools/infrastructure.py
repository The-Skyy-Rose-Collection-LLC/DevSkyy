"""Infrastructure & system tools: scan_code, fix_code, self_healing."""

from typing import Any

from pydantic import Field
from utils.logging_utils import get_correlation_id, log_error
from utils.security_utils import (
    SecurityError,
    sanitize_file_types,
    sanitize_path,
    validate_request_params,
)

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import logger, mcp
from mcp_tools.types import BaseAgentInput

# ===========================
# Input Models
# ===========================


class ScanCodeInput(BaseAgentInput):
    """Input for code scanning operations."""

    path: str = Field(
        ...,
        description="Path to scan (e.g., '/app', './src', 'main.py'). Use '.' for current directory",
        min_length=1,
        max_length=500,
    )
    file_types: list[str] | None = Field(
        default=["py", "js", "ts", "jsx", "tsx"],
        description="File extensions to scan (e.g., ['py', 'js', 'html'])",
        max_length=20,
    )
    deep_scan: bool = Field(
        default=True,
        description="Enable deep analysis including security vulnerabilities and performance bottlenecks",
    )


class FixCodeInput(BaseAgentInput):
    """Input for automated code fixing."""

    scan_results: dict[str, Any] = Field(
        ...,
        description="Results from a previous scan operation containing issues to fix",
    )
    auto_apply: bool = Field(
        default=False,
        description="Automatically apply fixes (true) or generate suggestions only (false)",
    )
    create_backup: bool = Field(default=True, description="Create backup before applying fixes")
    fix_types: list[str] | None = Field(
        default=["syntax", "imports", "docstrings"],
        description="Types of fixes to apply: syntax, imports, docstrings, security, performance",
        max_length=10,
    )


class SelfHealingInput(BaseAgentInput):
    """Input for self-healing operations."""

    action: str = Field(
        ...,
        description="Self-healing action: scan (detect issues), heal (auto-fix), status (check health), history (view past fixes)",
    )
    auto_fix: bool = Field(default=True, description="Automatically fix detected issues")
    scope: list[str] | None = Field(
        default=["performance", "errors", "security"],
        description="Areas to check: performance, errors, security, code_quality",
        max_length=10,
    )


# ===========================
# Tool Handlers
# ===========================


@mcp.tool(
    name="devskyy_scan_code",
    annotations={
        "title": "DevSkyy Code Scanner",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
        "defer_loading": True,
        "input_examples": [
            {"path": "./src", "file_types": ["py", "js"], "deep_scan": True},
            {"path": "main.py", "file_types": ["py"], "deep_scan": False},
        ],
    },
)
@secure_tool("scan_code")
async def scan_code(params: ScanCodeInput) -> str:
    """Scan codebase for errors, security vulnerabilities, and optimization opportunities.

    The Scanner Agent (v2.0) performs comprehensive code analysis including:
    - Syntax errors and code quality issues
    - Security vulnerabilities (SQL injection, XSS, etc.)
    - Performance bottlenecks
    - Code complexity analysis
    - TODO/FIXME markers
    - Best practice violations

    Supports: Python, JavaScript, TypeScript, HTML, CSS, JSON

    Args:
        params (ScanCodeInput): Scan configuration containing:
            - path: Directory or file to scan
            - file_types: File extensions to analyze
            - deep_scan: Enable comprehensive analysis
            - response_format: Output format (markdown/json)

    Returns:
        str: Detailed scan results with issues categorized by severity

    Example:
        >>> scan_code({
        ...     "path": "./src",
        ...     "file_types": ["py", "js"],
        ...     "deep_scan": True
        ... })
    """
    # SECURITY: Sanitize inputs to prevent path traversal and injection
    try:
        # Validate and sanitize path
        sanitized_path = str(sanitize_path(params.path))

        # Validate and sanitize file types
        sanitized_file_types = sanitize_file_types(params.file_types or [])

        logger.info(
            "scan_code_invoked",
            path=sanitized_path,
            file_types=sanitized_file_types,
            deep_scan=params.deep_scan,
            correlation_id=get_correlation_id(),
        )

    except SecurityError as e:
        # Log security violation
        await log_error(
            error=e,
            context={
                "tool": "scan_code",
                "path": params.path,
                "file_types": params.file_types,
            },
        )

        return _format_response(
            {"error": f"Security validation failed: {str(e)}"},
            params.response_format,
            "Code Scan Results",
        )

    data = await _make_api_request(
        "scanner/scan",
        method="POST",
        data={
            "path": sanitized_path,
            "file_types": sanitized_file_types,
            "deep_scan": params.deep_scan,
        },
    )

    return _format_response(data, params.response_format, "Code Scan Results")


@mcp.tool(
    name="devskyy_fix_code",
    annotations={
        "title": "DevSkyy Code Fixer",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "input_examples": [
            {
                "scan_results": {"issues": [{"type": "syntax", "file": "main.py"}]},
                "auto_apply": True,
                "fix_types": ["syntax", "imports"],
            },
            {
                "scan_results": {"issues": []},
                "auto_apply": False,
                "create_backup": True,
                "fix_types": ["security"],
            },
        ],
    },
)
@secure_tool("fix_code")
async def fix_code(params: FixCodeInput) -> str:
    """Automatically fix code issues detected by scanner.

    The Fixer Agent (v2.0) provides automated code remediation:
    - Syntax error correction
    - Import optimization and organization
    - Missing docstring generation
    - Type hint inference
    - Security vulnerability patching
    - Code formatting (Black, Prettier)
    - Performance optimizations

    Args:
        params (FixCodeInput): Fix configuration containing:
            - scan_results: Issues from previous scan
            - auto_apply: Apply fixes or generate suggestions
            - create_backup: Backup files before changes
            - fix_types: Categories of fixes to apply
            - response_format: Output format (markdown/json)

    Returns:
        str: Summary of fixes applied with before/after comparisons

    Example:
        >>> fix_code({
        ...     "scan_results": previous_scan_data,
        ...     "auto_apply": True,
        ...     "create_backup": True,
        ...     "fix_types": ["syntax", "security"]
        ... })
    """
    # SECURITY: Sanitize scan_results to prevent injection
    try:
        # Validate scan_results structure
        if params.scan_results and isinstance(params.scan_results, dict):
            sanitized_scan_results = validate_request_params(params.scan_results)
        else:
            sanitized_scan_results = params.scan_results

        logger.info(
            "fix_code_invoked",
            auto_apply=params.auto_apply,
            create_backup=params.create_backup,
            fix_types=params.fix_types,
            correlation_id=get_correlation_id(),
        )

    except SecurityError as e:
        # Log security violation
        await log_error(
            error=e,
            context={
                "tool": "fix_code",
                "auto_apply": params.auto_apply,
            },
        )

        return _format_response(
            {"error": f"Security validation failed: {str(e)}"},
            params.response_format,
            "Code Fix Results",
        )

    data = await _make_api_request(
        "fixer/fix",
        method="POST",
        data={
            "scan_results": sanitized_scan_results,
            "auto_apply": params.auto_apply,
            "create_backup": params.create_backup,
            "fix_types": params.fix_types,
        },
    )

    return _format_response(data, params.response_format, "Code Fix Results")


@mcp.tool(
    name="devskyy_self_healing",
    annotations={
        "title": "DevSkyy Self-Healing System",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "input_examples": [
            {"action": "scan", "auto_fix": False, "scope": ["performance", "errors"]},
            {"action": "heal", "auto_fix": True, "scope": ["security", "performance"]},
            {"action": "status"},
        ],
    },
)
@secure_tool("self_healing")
async def self_healing(params: SelfHealingInput) -> str:
    """Monitor system health and automatically fix issues.

    The Self-Healing Agent continuously monitors the platform and applies
    automated remediation for:
    - Performance degradation (slow APIs, memory leaks)
    - Runtime errors and exceptions
    - Security vulnerabilities
    - Code quality issues
    - Resource exhaustion

    This is a unique DevSkyy feature that enables zero-downtime operation.

    Args:
        params (SelfHealingInput): Self-healing configuration containing:
            - action: scan, heal, status, or history
            - auto_fix: Automatically apply fixes when detected
            - scope: Areas to monitor (performance, errors, security)
            - response_format: Output format (markdown/json)

    Returns:
        str: Health status and automated fixes applied

    Example:
        >>> self_healing({
        ...     "action": "heal",
        ...     "auto_fix": True,
        ...     "scope": ["performance", "errors"]
        ... })
    """
    data = await _make_api_request(
        f"self-healing/{params.action}",
        method="POST",
        data={"auto_fix": params.auto_fix, "scope": params.scope},
    )

    return _format_response(data, params.response_format, "Self-Healing Status")
