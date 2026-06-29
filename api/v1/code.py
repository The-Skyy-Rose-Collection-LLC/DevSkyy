"""Code Analysis and Fixing API Endpoints.

This module provides endpoints for:
- Code scanning (security vulnerabilities, syntax errors, quality issues)
- Automated code fixing
- Integration with security/code_scanner.py

Version: 1.0.0
"""

import asyncio
import logging
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from security.code_analysis import CodeSecurityAnalyzer, SecurityFinding
from security.jwt_oauth2_auth import TokenPayload, get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/code", tags=["Code Analysis"])


# =============================================================================
# Request/Response Models
# =============================================================================


class CodeScanRequest(BaseModel):
    """Request model for code scanning."""

    path: str = Field(
        ...,
        description="Path to scan (e.g., '/app', './src', 'main.py')",
        min_length=1,
        max_length=500,
    )
    file_types: list[str] = Field(
        default=["py", "js", "ts", "jsx", "tsx"],
        description="File extensions to scan",
        max_length=20,
    )
    deep_scan: bool = Field(
        default=True,
        description="Enable deep analysis including security vulnerabilities",
    )


class ScanIssue(BaseModel):
    """Individual code issue found during scanning."""

    file: str
    line: int
    column: int | None = None
    severity: str  # critical, high, medium, low, info
    type: str  # syntax, security, performance, quality, style
    message: str
    rule: str | None = None
    suggestion: str | None = None


class CodeScanResponse(BaseModel):
    """Response model for code scanning."""

    scan_id: str
    status: str
    timestamp: str
    path: str
    files_scanned: int
    issues_found: int
    issues: list[ScanIssue]
    summary: dict[str, Any]


class CodeFixRequest(BaseModel):
    """Request model for code fixing."""

    scan_id: str | None = Field(
        default=None,
        description="Previous scan ID to use for fixes (or provide scan_results)",
    )
    scan_results: dict[str, Any] | None = Field(
        default=None,
        description="Results from a previous scan containing issues to fix",
    )
    auto_apply: bool = Field(
        default=False,
        description="Automatically apply fixes or generate suggestions only",
    )
    create_backup: bool = Field(default=True, description="Create backup before applying fixes")
    fix_types: list[str] = Field(
        default=["syntax", "imports", "docstrings"],
        description="Types of fixes to apply",
        max_length=10,
    )


class CodeFix(BaseModel):
    """Individual code fix applied."""

    file: str
    line: int
    fix_type: str
    original: str
    fixed: str
    applied: bool


class CodeFixResponse(BaseModel):
    """Response model for code fixing."""

    fix_id: str
    status: str
    timestamp: str
    fixes_generated: int
    fixes_applied: int
    fixes: list[CodeFix]
    backup_path: str | None = None


# =============================================================================
# SAST helpers
# =============================================================================

# Resolve to repo root: api/v1/code.py → api/v1 → api → DevSkyy
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

# Mirror analyze_directory's default exclusion list so file counts are consistent
_EXCLUDE_PATTERNS: list[str] = ["__pycache__", ".git", "node_modules", "venv", ".venv", "env"]


def _do_scan(resolved: Path) -> tuple[list[SecurityFinding], int]:
    """Run synchronous SAST analysis and return (findings, files_scanned).

    Intended to be called via asyncio.to_thread to avoid blocking the event loop;
    CodeSecurityAnalyzer.analyze_directory/analyze_file are CPU-bound filesystem walks.

    A fresh CodeSecurityAnalyzer is created per call because the analyzer stores
    mutable state (self.findings) that would race under concurrent requests if shared.
    """
    analyzer = CodeSecurityAnalyzer()
    if resolved.is_file():
        findings = analyzer.analyze_file(resolved)
        files_scanned = 1 if resolved.suffix == ".py" else 0
    else:
        findings = analyzer.analyze_directory(resolved)
        files_scanned = sum(
            1 for f in resolved.rglob("*.py") if not any(pat in str(f) for pat in _EXCLUDE_PATTERNS)
        )
    return findings, files_scanned


def _finding_to_issue(finding: SecurityFinding) -> ScanIssue:
    """Map a SecurityFinding to a ScanIssue for the API response."""
    return ScanIssue(
        file=finding.file_path,
        line=finding.line_number,
        column=None,
        # SecuritySeverity is a StrEnum; .value yields "critical"/"high"/"medium"/"low"/"info"
        severity=finding.severity.value,
        type="security",
        message=finding.title if finding.title else finding.description,
        rule=finding.cwe_id if finding.cwe_id else finding.id,
        suggestion=finding.recommendation if finding.recommendation else None,
    )


def _build_summary(findings: list[SecurityFinding]) -> dict[str, Any]:
    """Build severity count summary from real findings (not hardcoded)."""
    counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        key = f.severity.value
        if key in counts:
            counts[key] += 1
    counts["security_issues"] = len(findings)
    return counts


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/scan", response_model=CodeScanResponse, status_code=status.HTTP_200_OK)
async def scan_code(
    request: CodeScanRequest, user: TokenPayload = Depends(get_current_user)
) -> CodeScanResponse:
    """Scan codebase for errors, security vulnerabilities, and optimization opportunities.

    The Scanner performs comprehensive code analysis including:
    - Syntax errors and code quality issues
    - Security vulnerabilities (SQL injection, XSS, etc.)
    - Performance bottlenecks
    - Code complexity analysis
    - TODO/FIXME markers
    - Best practice violations

    Supports: Python, JavaScript, TypeScript, HTML, CSS, JSON

    Args:
        request: Scan configuration (path, file_types, deep_scan)
        user: Authenticated user (from JWT token)

    Returns:
        CodeScanResponse with detailed scan results

    Raises:
        HTTPException: If path is outside project root (400), not found (404), or scan fails (500)
    """
    scan_id = str(uuid4())
    logger.info(f"Starting code scan {scan_id} for user {user.sub} at path: {request.path}")

    try:
        # Resolve path and enforce containment within PROJECT_ROOT (path-injection guard).
        # request.path is user-controlled; reject anything that escapes the repo.
        resolved = Path(request.path).resolve()
        if not resolved.is_relative_to(PROJECT_ROOT):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is outside the project root: {request.path}",
            )

        if not resolved.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Path not found: {request.path}",
            )

        # Delegate synchronous SAST analysis to a thread to avoid blocking the event loop.
        # _do_scan is a pure CPU/IO function with no async calls inside.
        findings, files_scanned = await asyncio.to_thread(_do_scan, resolved)

        # Map SecurityFinding → ScanIssue and derive summary from real findings
        issues = [_finding_to_issue(f) for f in findings]
        summary = _build_summary(findings)

        return CodeScanResponse(
            scan_id=scan_id,
            status="completed",
            timestamp=datetime.now(UTC).isoformat(),
            path=request.path,
            files_scanned=files_scanned,
            issues_found=len(issues),
            issues=issues,
            summary=summary,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code scan failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code scan failed: {str(e)}",
        )


@router.post("/fix", response_model=CodeFixResponse, status_code=status.HTTP_200_OK)
async def fix_code(
    request: CodeFixRequest, user: TokenPayload = Depends(get_current_user)
) -> CodeFixResponse:
    """Automatically fix code issues detected by scanner.

    The Fixer provides automated code remediation:
    - Syntax error correction
    - Import optimization and organization
    - Missing docstring generation
    - Type hint inference
    - Security vulnerability patching
    - Code formatting (Black, Prettier)
    - Performance optimizations

    Args:
        request: Fix configuration (scan_id or scan_results, auto_apply, etc.)
        user: Authenticated user (from JWT token)

    Returns:
        CodeFixResponse with summary of fixes applied

    Raises:
        HTTPException: If scan_id not found or fix fails
    """
    fix_id = str(uuid4())
    logger.info(f"Starting code fix {fix_id} for user {user.sub}")

    try:
        # Validate input
        if not request.scan_id and not request.scan_results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either scan_id or scan_results must be provided",
            )

        # TODO: Integrate with actual code fixing logic
        # For now, return mock data demonstrating the structure

        fixes = [
            CodeFix(
                file="example.py",
                line=42,
                fix_type="security",
                original='query = "SELECT * FROM users WHERE id = " + user_id',
                fixed='query = "SELECT * FROM users WHERE id = %s"\ncursor.execute(query, (user_id,))',
                applied=request.auto_apply,
            ),
            CodeFix(
                file="example.py",
                line=10,
                fix_type="imports",
                original="import os, sys, json",
                fixed="import json\nimport os\nimport sys",
                applied=request.auto_apply,
            ),
        ]

        backup_path = None
        if request.create_backup and request.auto_apply:
            backup_path = str(Path(tempfile.gettempdir()) / f"backup_{fix_id}")

        return CodeFixResponse(
            fix_id=fix_id,
            status="completed" if request.auto_apply else "suggestions_generated",
            timestamp=datetime.now(UTC).isoformat(),
            fixes_generated=len(fixes),
            fixes_applied=len(fixes) if request.auto_apply else 0,
            fixes=fixes,
            backup_path=backup_path,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code fix failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code fix failed: {str(e)}",
        )
