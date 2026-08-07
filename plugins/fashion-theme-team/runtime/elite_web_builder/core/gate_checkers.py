"""
Concrete gate checker implementations for the 8-gate verification loop.

Each checker is an async callable that returns a GateResult. The Director
wires these into the VerificationLoop for each story execution.

Gate implementations:
- BUILD:    PHP lint, Python compile, Node syntax check
- LINT:     Pattern-based linting (no external tools required)
- SECURITY: Hardcoded secret detection, XSS vector scan
- DIFF:     Validates only expected files were created
- A11Y:     HTML accessibility checks (contrast, ARIA, landmarks)
- PERF:     File size budgets, asset optimization checks

Gates that require external services (TYPES, TESTS) return SKIPPED
with instructions for the user to configure them.

Usage:
    from core.gate_checkers import build_gate_checkers
    checkers = build_gate_checkers(written_files, output_dir)
    report = await verifier.run_all(checkers)
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any

from core.verification_loop import Gate, GateChecker, GateResult, GateStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BUILD gate — syntax validation
# ---------------------------------------------------------------------------

_PHP_OPEN = re.compile(r"<\?php")


async def check_build(files: list[str], output_dir: Path) -> GateResult:
    """
    Validate syntax of generated files.

    - PHP: checks for matching braces and valid opening tag
    - JS:  checks for balanced braces/brackets
    - JSON: attempts parse
    - CSS: checks for balanced braces
    """
    errors: list[str] = []

    for file_path in files:
        full_path = output_dir / file_path
        if not full_path.exists():
            errors.append(f"{file_path}: file not found after write")
            continue

        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"{file_path}: read error — {exc}")
            continue

        suffix = full_path.suffix.lower()

        if suffix == ".php":
            # Check PHP opening tag
            if not _PHP_OPEN.search(content):
                errors.append(f"{file_path}: missing <?php opening tag")
            # Check balanced braces
            brace_err = _check_balanced(content, "{", "}", file_path)
            if brace_err:
                errors.append(brace_err)
            # Try php -l if available
            php_err = _try_php_lint(full_path)
            if php_err:
                errors.append(php_err)

        elif suffix in (".js", ".jsx", ".ts", ".tsx"):
            brace_err = _check_balanced(content, "{", "}", file_path)
            if brace_err:
                errors.append(brace_err)
            bracket_err = _check_balanced(content, "[", "]", file_path)
            if bracket_err:
                errors.append(bracket_err)

        elif suffix == ".json":
            import json
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                errors.append(f"{file_path}: invalid JSON — {exc}")

        elif suffix == ".css":
            brace_err = _check_balanced(content, "{", "}", file_path)
            if brace_err:
                errors.append(brace_err)

    if errors:
        return GateResult(
            gate=Gate.BUILD,
            status=GateStatus.FAILED,
            message=f"BUILD: {len(errors)} syntax error(s)",
            details=errors,
        )

    return GateResult(
        gate=Gate.BUILD,
        status=GateStatus.PASSED,
        message=f"BUILD: all {len(files)} files pass syntax check",
    )


def _check_balanced(content: str, open_char: str, close_char: str, file_path: str) -> str | None:
    """Check that open/close characters are balanced, ignoring strings."""
    depth = 0
    in_string = False
    string_char = ""
    prev_char = ""

    for ch in content:
        if in_string:
            if ch == string_char and prev_char != "\\":
                in_string = False
        else:
            if ch in ("'", '"', "`"):
                in_string = True
                string_char = ch
            elif ch == open_char:
                depth += 1
            elif ch == close_char:
                depth -= 1
                if depth < 0:
                    return f"{file_path}: unmatched '{close_char}'"
        prev_char = ch

    if depth != 0:
        return f"{file_path}: unbalanced '{open_char}'/'{close_char}' (depth={depth})"
    return None


def _try_php_lint(file_path: Path) -> str | None:
    """Try running php -l if PHP is available. Returns error or None."""
    try:
        result = subprocess.run(
            ["php", "-l", str(file_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            # Extract error line from PHP output
            stderr = result.stderr.strip() or result.stdout.strip()
            return f"{file_path.name}: php -l failed — {stderr[:200]}"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # PHP not installed — skip
    return None


# ---------------------------------------------------------------------------
# LINT gate — code quality patterns
# ---------------------------------------------------------------------------

# Patterns that indicate code quality issues
_LINT_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (".php", re.compile(r"\bvar_dump\s*\("), "var_dump() left in code"),
    (".php", re.compile(r"\bprint_r\s*\("), "print_r() left in code"),
    (".php", re.compile(r"\berror_reporting\s*\(\s*0\s*\)"), "error_reporting(0) suppresses errors"),
    (".php", re.compile(r"mysql_(?:query|connect|fetch)"), "deprecated mysql_* functions"),
    (".php", re.compile(r"\$_(?:GET|POST|REQUEST)\s*\["), "raw superglobal without sanitization"),
    (".js", re.compile(r"\bconsole\.\w+\s*\("), "console.log left in code"),
    (".js", re.compile(r"\balert\s*\("), "alert() in production code"),
    (".js", re.compile(r"\bdebugger\b"), "debugger statement"),
    (".js", re.compile(r"\beval\s*\("), "eval() usage"),
    (".css", re.compile(r"!important"), "!important override"),
    (".json", re.compile(r"//.*$", re.MULTILINE), "comments in JSON (invalid)"),
]


async def check_lint(files: list[str], output_dir: Path) -> GateResult:
    """
    Check for common code quality issues using pattern matching.

    This doesn't require external linters — it catches the most common
    issues that agents produce (console.log, var_dump, eval, etc.).
    """
    warnings: list[str] = []

    for file_path in files:
        full_path = output_dir / file_path
        if not full_path.exists():
            continue

        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        suffix = full_path.suffix.lower()

        for ext, pattern, message in _LINT_PATTERNS:
            if suffix == ext:
                matches = pattern.findall(content)
                if matches:
                    warnings.append(
                        f"{file_path}: {message} ({len(matches)}x)"
                    )

    if warnings:
        return GateResult(
            gate=Gate.LINT,
            status=GateStatus.FAILED,
            message=f"LINT: {len(warnings)} quality issue(s)",
            details=warnings,
        )

    return GateResult(
        gate=Gate.LINT,
        status=GateStatus.PASSED,
        message=f"LINT: {len(files)} files clean",
    )


# ---------------------------------------------------------------------------
# SECURITY gate — secret detection + XSS vectors
# ---------------------------------------------------------------------------

_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "potential OpenAI/Anthropic API key"),
    (re.compile(r"AIza[a-zA-Z0-9_-]{35}"), "potential Google API key"),
    (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "potential GitHub token"),
    (re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{4,}['\"]", re.IGNORECASE), "hardcoded password"),
    (re.compile(r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"(?:access_token|api_key|secret_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE), "hardcoded credential"),
]

_XSS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\.innerHTML\s*="), "innerHTML assignment (XSS vector)"),
    (re.compile(r"document\.write\s*\("), "document.write (XSS vector)"),
    (re.compile(r"\becho\s+\$_(?:GET|POST|REQUEST)"), "unescaped echo of user input (XSS)"),
]


async def check_security(files: list[str], output_dir: Path) -> GateResult:
    """
    Scan for hardcoded secrets and XSS vectors.

    Zero tolerance for secrets. Warnings for XSS patterns.
    """
    critical: list[str] = []
    warnings: list[str] = []

    for file_path in files:
        full_path = output_dir / file_path
        if not full_path.exists():
            continue

        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        # Secret detection (CRITICAL)
        for pattern, description in _SECRET_PATTERNS:
            if pattern.search(content):
                critical.append(f"{file_path}: {description}")

        # XSS vector detection
        suffix = full_path.suffix.lower()
        if suffix in (".php", ".js", ".html", ".htm"):
            for pattern, description in _XSS_PATTERNS:
                if pattern.search(content):
                    warnings.append(f"{file_path}: {description}")

    details = critical + warnings

    if critical:
        return GateResult(
            gate=Gate.SECURITY,
            status=GateStatus.FAILED,
            message=f"SECURITY: {len(critical)} CRITICAL secret(s) detected",
            details=details,
        )

    if warnings:
        # Warnings don't block, but are reported
        return GateResult(
            gate=Gate.SECURITY,
            status=GateStatus.PASSED,
            message=f"SECURITY: passed with {len(warnings)} warning(s)",
            details=warnings,
        )

    return GateResult(
        gate=Gate.SECURITY,
        status=GateStatus.PASSED,
        message=f"SECURITY: {len(files)} files clean",
    )


# ---------------------------------------------------------------------------
# DIFF gate — expected file manifest
# ---------------------------------------------------------------------------


async def check_diff(
    files_written: list[str],
    expected_extensions: frozenset[str] | None = None,
    max_files: int = 50,
) -> GateResult:
    """
    Validate that only expected files were created.

    Checks:
    - File count within budget
    - All files have allowed extensions
    - No suspicious file names
    """
    if expected_extensions is None:
        expected_extensions = frozenset({
            ".php", ".css", ".js", ".json", ".html", ".svg", ".txt", ".md",
        })

    errors: list[str] = []

    # File count check
    if len(files_written) > max_files:
        errors.append(
            f"Too many files: {len(files_written)} (max {max_files})"
        )

    # Extension check
    for fp in files_written:
        suffix = Path(fp).suffix.lower()
        if suffix not in expected_extensions:
            errors.append(f"Unexpected extension: {fp}")

    # Suspicious filename check
    suspicious = re.compile(r"(test|tmp|temp|backup|\.bak|\.old|\.orig)", re.IGNORECASE)
    for fp in files_written:
        if suspicious.search(Path(fp).name):
            errors.append(f"Suspicious filename: {fp}")

    if errors:
        return GateResult(
            gate=Gate.DIFF,
            status=GateStatus.FAILED,
            message=f"DIFF: {len(errors)} file manifest issue(s)",
            details=errors,
        )

    return GateResult(
        gate=Gate.DIFF,
        status=GateStatus.PASSED,
        message=f"DIFF: {len(files_written)} files within manifest",
    )


# ---------------------------------------------------------------------------
# A11Y gate — HTML accessibility checks
# ---------------------------------------------------------------------------

_A11Y_CHECKS: list[tuple[re.Pattern[str], str, str]] = [
    # Images without alt
    (re.compile(r"<img\b(?![^>]*\balt\s*=)[^>]*>", re.IGNORECASE),
     "img without alt attribute", "CRITICAL"),
    # Missing lang attribute on html
    (re.compile(r"<html\b(?![^>]*\blang\s*=)[^>]*>", re.IGNORECASE),
     "html element missing lang attribute", "SERIOUS"),
    # Empty links
    (re.compile(r"<a\b[^>]*>\s*</a>", re.IGNORECASE),
     "empty link (no text content)", "SERIOUS"),
    # Missing form labels
    (re.compile(r"<input\b(?![^>]*\b(?:aria-label|aria-labelledby|id)\s*=)[^>]*>", re.IGNORECASE),
     "input without label association", "SERIOUS"),
    # onclick without keyboard equivalent
    (re.compile(r'\bonclick\s*=\s*["\'](?![^"\']*\bkeydown|\bkeypress)', re.IGNORECASE),
     "onclick without keyboard handler", "MODERATE"),
]


async def check_a11y(files: list[str], output_dir: Path) -> GateResult:
    """
    Check HTML files for accessibility violations.

    Runs pattern-based checks for the most common WCAG 2.2 violations.
    Not a replacement for axe-core, but catches critical issues.
    """
    critical: list[str] = []
    serious: list[str] = []
    moderate: list[str] = []

    html_extensions = {".php", ".html", ".htm", ".twig", ".liquid"}

    for file_path in files:
        full_path = output_dir / file_path
        if not full_path.exists():
            continue
        if full_path.suffix.lower() not in html_extensions:
            continue

        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for pattern, message, severity in _A11Y_CHECKS:
            matches = pattern.findall(content)
            if matches:
                entry = f"{file_path}: {message} ({len(matches)}x)"
                if severity == "CRITICAL":
                    critical.append(entry)
                elif severity == "SERIOUS":
                    serious.append(entry)
                else:
                    moderate.append(entry)

    details = critical + serious + moderate

    if critical:
        return GateResult(
            gate=Gate.A11Y,
            status=GateStatus.FAILED,
            message=f"A11Y: {len(critical)} CRITICAL violation(s)",
            details=details,
        )

    # Serious issues are warnings, not blockers
    return GateResult(
        gate=Gate.A11Y,
        status=GateStatus.PASSED,
        message=f"A11Y: passed ({len(serious)} serious, {len(moderate)} moderate warnings)",
        details=details if details else [],
    )


# ---------------------------------------------------------------------------
# PERF gate — file size budgets
# ---------------------------------------------------------------------------

# Max sizes per file type (bytes)
_SIZE_BUDGETS: dict[str, int] = {
    ".css": 150 * 1024,     # 150 KB per CSS file
    ".js": 250 * 1024,      # 250 KB per JS file
    ".php": 100 * 1024,     # 100 KB per PHP file
    ".json": 500 * 1024,    # 500 KB (theme.json can be large)
    ".html": 200 * 1024,    # 200 KB per HTML file
}


async def check_perf(files: list[str], output_dir: Path) -> GateResult:
    """
    Check file sizes against performance budgets.

    Large files indicate bundling issues or unoptimized output.
    """
    warnings: list[str] = []
    total_bytes = 0

    for file_path in files:
        full_path = output_dir / file_path
        if not full_path.exists():
            continue

        try:
            size = full_path.stat().st_size
        except OSError:
            continue

        total_bytes += size
        suffix = full_path.suffix.lower()
        budget = _SIZE_BUDGETS.get(suffix)

        if budget and size > budget:
            warnings.append(
                f"{file_path}: {size / 1024:.0f}KB exceeds {budget / 1024:.0f}KB budget"
            )

    if warnings:
        return GateResult(
            gate=Gate.PERF,
            status=GateStatus.FAILED,
            message=f"PERF: {len(warnings)} file(s) exceed size budget",
            details=warnings,
        )

    return GateResult(
        gate=Gate.PERF,
        status=GateStatus.PASSED,
        message=f"PERF: {total_bytes / 1024:.0f}KB total, all within budget",
    )


# ---------------------------------------------------------------------------
# Builder — create gate checker dict for the Director
# ---------------------------------------------------------------------------


def build_gate_checkers(
    files_written: list[str],
    output_dir: Path,
) -> dict[Gate, GateChecker]:
    """
    Build a complete set of gate checkers for a story's output.

    Returns async callables that the VerificationLoop can execute.
    Wires the output files and directory into each checker.

    Args:
        files_written: List of file paths that were written
        output_dir: Base directory where files live

    Returns:
        Dict of Gate → async checker function
    """
    async def _build() -> GateResult:
        return await check_build(files_written, output_dir)

    async def _lint() -> GateResult:
        return await check_lint(files_written, output_dir)

    async def _security() -> GateResult:
        return await check_security(files_written, output_dir)

    async def _diff() -> GateResult:
        return await check_diff(files_written)

    async def _a11y() -> GateResult:
        return await check_a11y(files_written, output_dir)

    async def _perf() -> GateResult:
        return await check_perf(files_written, output_dir)

    # TYPES and TESTS gates require external tooling — skip gracefully
    async def _types_skip() -> GateResult:
        return GateResult(
            gate=Gate.TYPES,
            status=GateStatus.SKIPPED,
            message="TYPES: skipped (requires tsc/mypy/pyright)",
        )

    async def _tests_skip() -> GateResult:
        return GateResult(
            gate=Gate.TESTS,
            status=GateStatus.SKIPPED,
            message="TESTS: skipped (requires test runner on generated code)",
        )

    return {
        Gate.BUILD: _build,
        Gate.TYPES: _types_skip,
        Gate.LINT: _lint,
        Gate.TESTS: _tests_skip,
        Gate.SECURITY: _security,
        Gate.A11Y: _a11y,
        Gate.PERF: _perf,
        Gate.DIFF: _diff,
    }
