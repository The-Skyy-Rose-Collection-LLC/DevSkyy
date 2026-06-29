"""Code Analysis and Fixing API Endpoints.

This module provides endpoints for:
- Code scanning (security vulnerabilities, syntax errors, quality issues)
- Automated code fixing
- Integration with security/code_scanner.py

Version: 1.0.0
"""

import asyncio
import logging
import shutil
import tempfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from security.code_analysis import CodeSecurityAnalyzer, SecurityFinding
from security.jwt_oauth2_auth import TokenPayload, UserRole, get_current_user

if TYPE_CHECKING:  # annotations only — avoids importing the heavy agent module at startup
    from agents.coding_doctor_agent import HealingResult

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
        default=["format", "imports", "lint", "unused"],
        description="Fix types to apply. Supported (real healers): format, imports, lint, unused.",
        max_length=10,
    )


class CodeFixResult(BaseModel):
    """Outcome of one auto-fix action applied to one file (mirrors HealingResult)."""

    file: str
    action: str
    success: bool
    changes_made: list[str]
    error: str | None = None


class CodeFixResponse(BaseModel):
    """Response model for code fixing."""

    fix_id: str
    status: str  # completed | previewed (dry-run) | no_action
    timestamp: str
    dry_run: bool
    files_processed: int
    fixes_applied: int
    results: list[CodeFixResult]
    unsupported_fix_types: list[str] = []
    learning_stats: dict[str, Any] = {}
    backup_path: str | None = None  # dir holding pre-fix copies when create_backup + auto_apply


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


# Map request fix_types to HealingAction names that have a REAL healer in
# SelfHealingEngine (black / isort / ruff --fix / autoflake). Types without a
# real healer (security, docstrings, type_hints, dependency, syntax) are reported
# as unsupported rather than silently faked.
_FIX_TYPE_TO_ACTION: dict[str, str] = {
    "format": "AUTO_FORMAT",
    "imports": "FIX_IMPORTS",
    "lint": "FIX_LINT",
    "unused": "REMOVE_UNUSED",
}


# Persistent self-learning store for code-fix outcomes (success/failure per action).
_LEARNINGS_PATH = PROJECT_ROOT / "data" / "code_fix_learnings.json"

# fix_type that routes to source-level security remediation (SecurityRemediator)
# rather than a tool healer. Opt-in: absent from the default fix_types.
_SECURITY_FIX_TYPE = "security"


def _resolve_repo_py(file_ref: str) -> Path | None:
    """Resolve a scan-result file reference to an absolute .py path inside the repo.

    Returns the resolved path only if it stays within PROJECT_ROOT, exists, and is
    a Python file; otherwise None (path-injection / traversal guard). User-supplied
    paths from scan_results are never trusted.
    """
    candidate = Path(file_ref)
    resolved = (candidate if candidate.is_absolute() else PROJECT_ROOT / candidate).resolve()
    if (
        not resolved.is_relative_to(PROJECT_ROOT)
        or not resolved.exists()
        or resolved.suffix != ".py"
    ):
        return None
    return resolved


def _apply_heals(
    repo_root: Path, issues: list[Any], dry_run: bool
) -> "tuple[list[HealingResult], dict[str, Any]]":
    """Drive SelfHealingEngine over the issues in a worker thread, with learning.

    SelfHealingEngine.heal() shells out to black/isort/ruff/autoflake via blocking
    subprocess.run; running the batch under its own event loop in a thread keeps
    the request's event loop responsive. Agent modules are imported lazily — they
    pull heavy dependencies we do not want at app-import time.

    Self-learning + improving: real (non-dry-run) heal outcomes are recorded in a
    persistent SelfLearningEngine, so the system's per-action success/failure stats
    accumulate across calls (the same loop CodingDoctorAgent.diagnose_and_heal uses).
    Dry-run previews are NOT learned from — a clean check is not a real fix outcome.
    Returns (healing_results, learning_stats).
    """
    from agents.coding_doctor_agent import SelfHealingEngine, SelfLearningEngine

    async def _drive() -> tuple[list[Any], dict[str, Any]]:
        engine = SelfHealingEngine(repo_root)
        await engine.initialize()
        learner = SelfLearningEngine(_LEARNINGS_PATH)
        await learner.initialize()

        results: list[Any] = []
        for issue in issues:
            result = await engine.heal(issue, dry_run=dry_run)
            results.append(result)
            if not dry_run:
                learner.learn(
                    issue.category,
                    result.action.value,
                    "; ".join(result.changes_made) or (result.error or "n/a"),
                    result.success,
                )
        if not dry_run:
            await learner.save()
        return results, learner.get_stats()

    return asyncio.run(_drive())


def _apply_security(
    repo_root: Path, targets_by_file: dict[str, list[Any]], dry_run: bool
) -> "tuple[list[HealingResult], dict[str, Any]]":
    """Drive SecurityRemediator over scan-derived security targets, with learning.

    Runs in a worker thread (CPU/IO-bound file edits) and MUST be invoked BEFORE the
    tool healers: it edits specific lines, so any formatter that reflows the file
    afterwards would invalidate the scan line numbers it relies on. Real (non-dry-run)
    outcomes feed the same persistent SelfLearningEngine the tool healers use.
    Returns (healing_results, learning_stats).
    """
    from agents.code_security_remediator import SecurityRemediator
    from agents.coding_doctor_agent import IssueCategory, SelfLearningEngine

    async def _drive() -> tuple[list[Any], dict[str, Any]]:
        remediator = SecurityRemediator(repo_root)
        learner = SelfLearningEngine(_LEARNINGS_PATH)
        await learner.initialize()

        results: list[Any] = []
        for rel, targets in targets_by_file.items():
            file_results = remediator.remediate_file(rel, targets, dry_run=dry_run)
            results.extend(file_results)
            if not dry_run:
                for r in file_results:
                    learner.learn(
                        IssueCategory.SECURITY,
                        r.action.value,
                        "; ".join(r.changes_made) or (r.error or "n/a"),
                        r.success,
                    )
        if not dry_run:
            await learner.save()
        return results, learner.get_stats()

    return asyncio.run(_drive())


@router.post("/fix", response_model=CodeFixResponse, status_code=status.HTTP_200_OK)
async def fix_code(
    request: CodeFixRequest, user: TokenPayload = Depends(get_current_user)
) -> CodeFixResponse:
    """Auto-fix code by delegating to real healers.

    Two backends, both real:
      * Tool healers — black (``format``), isort (``imports``), ruff --fix
        (``lint``), autoflake (``unused``) — operate on whole files.
      * Security remediation (``security``, opt-in) — SecurityRemediator applies
        SAFE, line-targeted rewrites for the subset of SAST findings that can be
        fixed deterministically (CWE-396 bare ``except:``, CWE-489 ``DEBUG=True``).
        Security findings whose CWE has no safe automated fix (SQL injection,
        eval/exec, hardcoded secrets, ...) are returned as failed results marked
        "manual review required" — never silently dropped, never falsely "fixed".

    ``fix_types`` with no real healer (``docstrings``, ``type_hints``,
    ``dependency``, ``syntax``) are returned in ``unsupported_fix_types`` and never
    fabricated. Tool-healer files come from ``scan_results['issues'][*]['file']``;
    security targets additionally use ``['type'] == 'security'``, ``['rule']`` (CWE)
    and ``['line']``. All paths must resolve inside the project root.

    ``auto_apply=False`` (default) previews without modifying files; ``auto_apply=True``
    applies fixes in place and requires ADMIN. When both run, security fixes are
    applied first (line-preserving) so tool reflows cannot invalidate scan lines.

    Args:
        request: Fix configuration (scan_results, fix_types, auto_apply).
        user: Authenticated user (from JWT token).

    Returns:
        CodeFixResponse with per-file/per-action healer results.

    Raises:
        HTTPException: 400 if scan_results missing; 403 if auto_apply without ADMIN;
        500 if a healer backend is unavailable.
    """
    logger.info("Code fix requested by user %s", user.sub)

    if not request.scan_id and not request.scan_results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either scan_id or scan_results must be provided",
        )
    if not request.scan_results:
        # scan_id-only retrieval needs a scan store, which does not exist yet.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scan_results is required (scan_id lookup is not supported yet)",
        )

    from agents.code_security_remediator import SecurityRemediator, SecurityTarget
    from agents.coding_doctor_agent import (
        CodeIssue,
        HealingAction,
        IssueCategory,
        SeverityLevel,
    )

    # Split requested fix types: tool healers (black/isort/ruff/autoflake), the
    # security remediator (opt-in), and everything else (reported, never faked).
    tool_actions: list[Any] = []
    security_requested = False
    unsupported: list[str] = []
    for fix_type in request.fix_types:
        if fix_type == _SECURITY_FIX_TYPE:
            security_requested = True
            continue
        action_name = _FIX_TYPE_TO_ACTION.get(fix_type)
        if action_name is None:
            unsupported.append(fix_type)
        else:
            tool_actions.append(getattr(HealingAction, action_name))

    raw_issues = request.scan_results.get("issues", [])
    if not isinstance(raw_issues, list):
        raw_issues = []

    # Tool healers operate on whole files: collect unique, path-safe .py files.
    rel_files: list[str] = []
    invalid: list[CodeFixResult] = []
    seen: set[str] = set()
    if tool_actions:
        for item in raw_issues:
            file_ref = item.get("file") if isinstance(item, dict) else None
            if not file_ref or file_ref in seen:
                continue
            seen.add(file_ref)
            resolved = _resolve_repo_py(file_ref)
            if resolved is None:
                invalid.append(
                    CodeFixResult(
                        file=file_ref,
                        action="-",
                        success=False,
                        changes_made=[],
                        error="path outside project root, missing, or not a .py file",
                    )
                )
                continue
            rel_files.append(str(resolved.relative_to(PROJECT_ROOT)))

    # Security remediation is line+CWE targeted: build per-file targets from the
    # security findings, splitting supported CWEs from those needing manual review.
    security_targets: dict[str, list[SecurityTarget]] = defaultdict(list)
    security_manual: list[CodeFixResult] = []
    security_files: set[str] = set()
    if security_requested:
        for item in raw_issues:
            if not isinstance(item, dict) or item.get("type") != "security":
                continue
            file_ref = item.get("file")
            cwe = item.get("rule")
            line = item.get("line")
            resolved = _resolve_repo_py(file_ref) if file_ref else None
            if resolved is None or not isinstance(line, int):
                security_manual.append(
                    CodeFixResult(
                        file=str(file_ref),
                        action=HealingAction.FIX_SECURITY.value,
                        success=False,
                        changes_made=[],
                        error="invalid path or line; manual review required",
                    )
                )
                continue
            if not SecurityRemediator.supports(cwe):
                security_manual.append(
                    CodeFixResult(
                        file=file_ref,
                        action=HealingAction.FIX_SECURITY.value,
                        success=False,
                        changes_made=[],
                        error=f"{cwe or 'unknown CWE'}: no safe automated remediation; "
                        "manual review required",
                    )
                )
                continue
            rel = str(resolved.relative_to(PROJECT_ROOT))
            security_targets[rel].append(SecurityTarget(cwe_id=cwe, line_number=line))
            security_files.add(rel)

    # One CodeIssue per (file, tool action); auto_fixable=True so heal() dispatches.
    issues = [
        CodeIssue(
            file_path=rel,
            line_number=None,
            category=IssueCategory.MAINTAINABILITY,
            severity=SeverityLevel.LOW,
            title=f"auto-fix:{action.value}",
            description=f"Apply {action.value} via SelfHealingEngine",
            auto_fixable=True,
            fix_action=action,
        )
        for rel in rel_files
        for action in tool_actions
    ]

    dry_run = not request.auto_apply

    # In-place mutation requires elevated privileges — an api_user token must not be
    # able to rewrite server-side source files. Dry-run previews stay open.
    if not dry_run and not user.has_any_role({UserRole.ADMIN, UserRole.SUPER_ADMIN}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="auto_apply requires ADMIN role",
        )

    # Honor create_backup: copy each target file into a temp dir BEFORE applying,
    # so a bad fix is recoverable. Covers both tool-healer and security targets.
    backup_files = sorted(set(rel_files) | security_files)
    backup_path: str | None = None
    if not dry_run and request.create_backup and backup_files:
        backup_dir = Path(tempfile.mkdtemp(prefix="codefix-backup-"))
        for rel in backup_files:
            dest = backup_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PROJECT_ROOT / rel, dest)
        backup_path = str(backup_dir)

    if not dry_run:
        logger.info(
            "Code fix APPLYING in place: user=%s files=%s backup=%s",
            user.sub,
            backup_files,
            backup_path,
        )

    healing: list[Any] = []
    learning_stats: dict[str, Any] = {}
    try:
        # Security fixes FIRST: line-targeted and line-count-preserving, so the scan
        # line numbers stay valid. Tool healers (which reflow files) run after.
        if security_targets:
            sec_results, sec_stats = await asyncio.to_thread(
                _apply_security, PROJECT_ROOT, dict(security_targets), dry_run
            )
            healing.extend(sec_results)
            learning_stats = sec_stats
        if issues:
            tool_results, tool_stats = await asyncio.to_thread(
                _apply_heals, PROJECT_ROOT, issues, dry_run
            )
            healing.extend(tool_results)
            learning_stats = tool_stats or learning_stats
    except Exception as exc:  # heavy import or driver failure → backend unavailable
        logger.error("Code fix backend failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Code fix backend is unavailable",
        ) from exc

    results = [
        CodeFixResult(
            file=h.file_path,
            action=h.action.value,
            success=h.success,
            changes_made=h.changes_made,
            error=h.error,
        )
        for h in healing
    ]
    results.extend(security_manual)
    results.extend(invalid)
    fixes_applied = sum(1 for r in results if r.success)

    # "no_action" only when nothing actionable was requested or matched.
    any_action = bool(tool_actions) or bool(security_targets) or bool(security_manual)
    if not any_action:
        run_status = "no_action"
    elif dry_run:
        run_status = "previewed"
    else:
        run_status = "completed"

    return CodeFixResponse(
        fix_id=str(uuid4()),
        status=run_status,
        timestamp=datetime.now(UTC).isoformat(),
        dry_run=dry_run,
        files_processed=len(set(rel_files) | security_files),
        fixes_applied=fixes_applied,
        results=results,
        unsupported_fix_types=unsupported,
        learning_stats=learning_stats,
        backup_path=backup_path,
    )
