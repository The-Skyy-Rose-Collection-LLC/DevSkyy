"""
Verification Loop — 8-gate quality check system.

Every agent output must pass all 8 gates before being marked GREEN.
Gates: BUILD, TYPES, LINT, TESTS, SECURITY, A11Y, PERF, DIFF.
"""

from __future__ import annotations

import ast
import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class GateStatus(str, Enum):
    """Status of a quality gate."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class GateName(str, Enum):
    """Names of the 8 quality gates."""

    BUILD = "build"
    TYPES = "types"
    LINT = "lint"
    TESTS = "tests"
    SECURITY = "security"
    A11Y = "a11y"
    PERF = "perf"
    DIFF = "diff"


@dataclass(frozen=True)
class GateResult:
    """Immutable result from a single gate check."""

    gate: str
    status: GateStatus
    message: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Complete verification result across all gates."""

    gates: list[GateResult] = field(default_factory=list)

    @property
    def all_green(self) -> bool:
        """
        Check whether all recorded gates have status PASSED.
        
        Returns:
            `true` if every gate has status `GateStatus.PASSED`, `false` otherwise.
        """
        return all(g.status == GateStatus.PASSED for g in self.gates)

    @property
    def failures(self) -> list[GateResult]:
        """
        List GateResult entries whose status is GateStatus.FAILED.
        
        Returns:
            list[GateResult]: Failed gate results, empty if there are none.
        """
        return [g for g in self.gates if g.status == GateStatus.FAILED]

    @property
    def summary(self) -> dict[str, int]:
        """
        Map gate status names to counts of gates with each status.
        
        Returns:
            summary (dict[str, int]): Mapping from status string (e.g., "passed", "failed", "skipped") to the number of gates with that status.
        """
        result: dict[str, int] = {}
        for gate in self.gates:
            key = gate.status.value
            result[key] = result.get(key, 0) + 1
        return result


# ─── Gate Configuration ───────────────────────────────────────────────

@dataclass(frozen=True)
class GateConfig:
    """Per-gate configuration."""

    enabled: bool = True
    required: bool = True


DEFAULT_GATE_CONFIG: dict[str, GateConfig] = {
    g.value: GateConfig() for g in GateName
}


# ─── Individual Gate Checks ───────────────────────────────────────────

def _extract_code_blocks(content: str) -> list[tuple[str, str]]:
    """
    Extract fenced Markdown code blocks from the given content.
    
    Returns:
        list[tuple[str, str]]: A list of (language, code) tuples where `language` is the fence language (empty string if unspecified) and `code` is the block content.
    """
    return re.findall(r"```(\w*)\n(.*?)```", content, re.DOTALL)


def _check_build(content: str, context: dict) -> GateResult:
    """
    Validate fenced code blocks for basic syntax and structural correctness.
    
    Parameters:
        content (str): Markdown-like text containing fenced code blocks to validate.
        context (dict): Optional context used by the verification pipeline (not required for this check).
    
    Returns:
        GateResult: A result for the BUILD gate. `status` is `PASSED` when no parse or structural errors are found (or when no code blocks are present), and `FAILED` when one or more errors are detected; on failure `details["errors"]` lists the detected issues.
    """
    blocks = _extract_code_blocks(content)
    if not blocks:
        return GateResult(
            gate=GateName.BUILD.value,
            status=GateStatus.PASSED,
            message="No code blocks to validate",
        )

    errors: list[str] = []
    for lang, code in blocks:
        if lang in ("python", "py", ""):
            try:
                ast.parse(code)
            except SyntaxError as exc:
                errors.append(f"Python syntax error line {exc.lineno}: {exc.msg}")
        if lang in ("json",):
            try:
                json.loads(code)
            except json.JSONDecodeError as exc:
                errors.append(f"JSON parse error: {exc.msg}")
        if lang in ("html", "liquid", "php"):
            opens = code.count("<")
            closes = code.count(">")
            if abs(opens - closes) > 2:
                errors.append(
                    f"Unbalanced angle brackets in {lang}: "
                    f"{opens} opens vs {closes} closes"
                )

    if errors:
        return GateResult(
            gate=GateName.BUILD.value,
            status=GateStatus.FAILED,
            message=f"{len(errors)} build error(s)",
            details={"errors": errors},
        )
    return GateResult(
        gate=GateName.BUILD.value,
        status=GateStatus.PASSED,
        message=f"All {len(blocks)} code block(s) parse OK",
    )


def _check_types(content: str, context: dict) -> GateResult:
    """
    Validate type-related issues found in fenced code blocks within the given content.
    
    Checks include:
    - For JSON blocks: if an object contains a top-level `version` field, verifies a `$schema` field is present.
    - For TypeScript/TSX/TS blocks: detects usage of the `any` type.
    
    Parameters:
    	content (str): Agent output or document text containing fenced code blocks.
    	context (dict): Optional evaluation context (not used by this gate).
    
    Returns:
    	GateResult: Result for the TYPES gate. `status` is `FAILED` with `details["errors"]` when one or more type issues are found, otherwise `PASSED` with a success message.
    """
    blocks = _extract_code_blocks(content)
    if not blocks:
        return GateResult(
            gate=GateName.TYPES.value,
            status=GateStatus.PASSED,
            message="No code blocks to check",
        )

    errors: list[str] = []
    for lang, code in blocks:
        if lang in ("json",):
            try:
                data = json.loads(code)
                if isinstance(data, dict) and "version" in data:
                    if "$schema" not in data:
                        errors.append("JSON config missing $schema field")
            except json.JSONDecodeError:
                pass  # Caught by BUILD gate
        if lang in ("typescript", "ts", "tsx"):
            if re.search(r"\bany\b", code):
                errors.append("TypeScript code uses 'any' type — prefer explicit types")

    if errors:
        return GateResult(
            gate=GateName.TYPES.value,
            status=GateStatus.FAILED,
            message=f"{len(errors)} type issue(s)",
            details={"errors": errors},
        )
    return GateResult(
        gate=GateName.TYPES.value,
        status=GateStatus.PASSED,
        message="Type checks passed",
    )


_LINT_PATTERNS: list[tuple[str, str]] = [
    (r"console\.log\(", "console.log found — use structured logging"),
    (r"debugger\b", "debugger statement found"),
    (r"TODO\b", "TODO comment found — resolve before shipping"),
    (r"var\s+\w+\s*=", "var declaration — use const/let"),
    (r"eval\(", "eval() usage — security risk"),
]


def _check_lint(content: str, context: dict) -> GateResult:
    """
    Detects code-quality anti-patterns in fenced code blocks.
    
    Scans extracted fenced code blocks for known lint anti-patterns. If no code blocks are found the gate passes with a message indicating there are none to lint. If any patterns match the gate fails and the result's details include a "warnings" list with messages for each finding.
    
    Parameters:
        content (str): The text to scan (agent output / document content).
        context (dict): Additional context for the check (unused by this gate but accepted for API consistency).
    
    Returns:
        GateResult: Result for the LINT gate. `FAILED` if any anti-patterns were found (details contain `warnings`), `PASSED` otherwise.
    """
    blocks = _extract_code_blocks(content)
    if not blocks:
        return GateResult(
            gate=GateName.LINT.value,
            status=GateStatus.PASSED,
            message="No code blocks to lint",
        )

    warnings: list[str] = []
    for _lang, code in blocks:
        for pattern, msg in _LINT_PATTERNS:
            if re.search(pattern, code):
                warnings.append(msg)

    if warnings:
        return GateResult(
            gate=GateName.LINT.value,
            status=GateStatus.FAILED,
            message=f"{len(warnings)} lint warning(s)",
            details={"warnings": warnings},
        )
    return GateResult(
        gate=GateName.LINT.value,
        status=GateStatus.PASSED,
        message="Lint checks passed",
    )


def _check_tests(content: str, context: dict) -> GateResult:
    """
    Detects whether implementation code appears in fenced code blocks without accompanying tests.
    
    Scans extracted code blocks for implementation indicators (function or class definitions) and for common test indicators; treats Python and JavaScript/TypeScript blocks specially.
    
    Parameters:
        content (str): Text containing fenced code blocks to analyze.
        context (dict): Optional runtime/contextual data (ignored by this check).
    
    Returns:
        GateResult: Result for the TESTS gate — `status` is `FAILED` if implementation code is detected without accompanying tests, `PASSED` otherwise.
    """
    blocks = _extract_code_blocks(content)
    if not blocks:
        return GateResult(
            gate=GateName.TESTS.value,
            status=GateStatus.PASSED,
            message="No code blocks to check",
        )

    has_implementation = False
    has_tests = False
    for lang, code in blocks:
        if lang in ("python", "py"):
            if re.search(r"^(def |class )\w+", code, re.MULTILINE):
                has_implementation = True
            if re.search(r"(def test_|assert |pytest\.)", code):
                has_tests = True
        if lang in ("javascript", "js", "typescript", "ts", "tsx"):
            if re.search(r"(function |const \w+ ?= ?\(|class )", code):
                has_implementation = True
            if re.search(r"(describe\(|it\(|test\(|expect\()", code):
                has_tests = True

    if has_implementation and not has_tests:
        return GateResult(
            gate=GateName.TESTS.value,
            status=GateStatus.FAILED,
            message="Implementation code found without accompanying tests",
            details={"has_implementation": True, "has_tests": False},
        )
    return GateResult(
        gate=GateName.TESTS.value,
        status=GateStatus.PASSED,
        message="Test coverage check passed",
    )


_SECRET_PATTERNS: list[tuple[str, str]] = [
    (r"(?:api[_-]?key|apikey)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}", "Possible API key"),
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI-style secret key"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub personal access token"),
    (r"(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{4,}", "Hardcoded password"),
    (r"(?:secret|token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}", "Hardcoded secret/token"),
    (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "Private key in content"),
]

_INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"innerHTML\s*=", "innerHTML assignment — XSS risk"),
    (r"document\.write\(", "document.write — XSS risk"),
    (r"dangerouslySetInnerHTML", "dangerouslySetInnerHTML — XSS risk (verify sanitized)"),
    (r"f['\"].*\{.*\}.*(?:SELECT|INSERT|UPDATE|DELETE)", "f-string SQL — injection risk"),
    (r"\$_(?:GET|POST|REQUEST)\[", "Unsanitized PHP superglobal"),
]


def _check_security(content: str, context: dict) -> GateResult:
    """
    Scan the content for exposed secrets and code injection risks.
    
    Searches the entire content for secret patterns and inspects fenced code blocks for injection patterns. Findings are collected in details["findings"] as strings prefixed with "SECRET:" or "INJECTION:".
    
    Returns:
        GateResult: `FAILED` with details {"findings": [...]} when any issues are found, `PASSED` with message "Security scan clean" otherwise.
    """
    findings: list[str] = []

    for pattern, msg in _SECRET_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(f"SECRET: {msg}")

    blocks = _extract_code_blocks(content)
    for _lang, code in blocks:
        for pattern, msg in _INJECTION_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                findings.append(f"INJECTION: {msg}")

    if findings:
        return GateResult(
            gate=GateName.SECURITY.value,
            status=GateStatus.FAILED,
            message=f"{len(findings)} security finding(s)",
            details={"findings": findings},
        )
    return GateResult(
        gate=GateName.SECURITY.value,
        status=GateStatus.PASSED,
        message="Security scan clean",
    )


def _check_a11y(content: str, context: dict) -> GateResult:
    """
    Validate basic accessibility rules in HTML-like code blocks.
    
    Scans fenced code blocks with languages (html, liquid, php, jsx, tsx) and checks for:
    - <img> tags missing an alt attribute
    - empty <a> links without visible text or an aria-label
    - form controls (input/select/textarea) missing an id or aria-label
    - large HTML blocks (>200 chars) without any heading elements
    
    Returns:
        GateResult: Result for the A11Y gate. On failure, `details['violations']` contains a list of detected issues.
    """
    blocks = _extract_code_blocks(content)
    html_blocks = [
        code for lang, code in blocks if lang in ("html", "liquid", "php", "jsx", "tsx")
    ]
    if not html_blocks:
        return GateResult(
            gate=GateName.A11Y.value,
            status=GateStatus.PASSED,
            message="No HTML blocks to check",
        )

    violations: list[str] = []
    for code in html_blocks:
        if re.search(r"<img\b(?![^>]*\balt\s*=)", code):
            violations.append("img tag missing alt attribute")
        if re.search(r"<a\b(?![^>]*\baria-label)", code):
            inner = re.findall(r"<a\b[^>]*>(.*?)</a>", code, re.DOTALL)
            for text in inner:
                stripped = re.sub(r"<[^>]+>", "", text).strip()
                if not stripped:
                    violations.append("Empty link — add text or aria-label")
        if re.search(r"<(input|select|textarea)\b(?![^>]*\bid\s*=)", code):
            if not re.search(r"aria-label", code):
                violations.append("Form input missing id or aria-label")
        if not re.search(r"<(h1|h2|h3|h4|h5|h6)\b", code):
            if len(code) > 200:
                violations.append("Large HTML block with no heading structure")

    if violations:
        return GateResult(
            gate=GateName.A11Y.value,
            status=GateStatus.FAILED,
            message=f"{len(violations)} a11y violation(s)",
            details={"violations": violations},
        )
    return GateResult(
        gate=GateName.A11Y.value,
        status=GateStatus.PASSED,
        message="Accessibility checks passed",
    )


_PERF_PATTERNS: list[tuple[str, str]] = [
    (r"import\s+\*\s+as", "Wildcard import — harms tree-shaking"),
    (r"(?:querySelector|getElementById).*(?:forEach|map)\(", "DOM query in loop — cache reference"),
    (r"(?:loading\s*=\s*['\"]eager['\"])", "Eager loading — use lazy for offscreen images"),
    (r"@import\s+url\(", "CSS @import — use link tags or bundler for performance"),
    (r"(?:setTimeout|setInterval)\(\s*['\"]", "String argument in timer — use function reference"),
]


def _check_perf(content: str, context: dict) -> GateResult:
    """
    Detects performance anti-patterns in fenced code blocks and reports results for the PERF gate.
    
    If no fenced code blocks are present the gate passes with the message "No code blocks to check". If any configured performance patterns are matched the gate fails and the result's details contain an "issues" list with human-readable descriptions of each finding; otherwise the gate passes with the message "Performance checks passed".
    
    Returns:
        GateResult: Result for the PERF gate. `status` is `GateStatus.FAILED` if any issues were found (details contains an "issues" list), otherwise `GateStatus.PASSED`.
    """
    blocks = _extract_code_blocks(content)
    if not blocks:
        return GateResult(
            gate=GateName.PERF.value,
            status=GateStatus.PASSED,
            message="No code blocks to check",
        )

    issues: list[str] = []
    for _lang, code in blocks:
        for pattern, msg in _PERF_PATTERNS:
            if re.search(pattern, code):
                issues.append(msg)

    if issues:
        return GateResult(
            gate=GateName.PERF.value,
            status=GateStatus.FAILED,
            message=f"{len(issues)} performance issue(s)",
            details={"issues": issues},
        )
    return GateResult(
        gate=GateName.PERF.value,
        status=GateStatus.PASSED,
        message="Performance checks passed",
    )


def _check_diff(content: str, context: dict) -> GateResult:
    """
    Compare agent output against optional ground-truth expectations and validate that the output is non-trivial.
    
    Parameters:
        content (str): The agent-produced output to evaluate.
        context (dict): Optional execution context. If present, may contain a "ground_truth" key with a list of expected substrings or regex-like strings to check for in `content`.
    
    Returns:
        GateResult: A result for the DIFF gate.
            - `status` is `FAILED` when expected items from `context["ground_truth"]` are missing, when `content` is empty after trimming, or when `content` is shorter than a minimal threshold.
            - `status` is `PASSED` when all provided expectations are met and the content is non-empty and sufficiently long.
    """
    ground_truth = context.get("ground_truth")

    if ground_truth and isinstance(ground_truth, list):
        missing: list[str] = []
        for expected in ground_truth:
            if isinstance(expected, str):
                if expected not in content:
                    missing.append(f"Missing expected content: {expected!r}")
        if missing:
            return GateResult(
                gate=GateName.DIFF.value,
                status=GateStatus.FAILED,
                message=f"{len(missing)} ground truth mismatch(es)",
                details={"missing": missing},
            )

    stripped = content.strip()
    if not stripped:
        return GateResult(
            gate=GateName.DIFF.value,
            status=GateStatus.FAILED,
            message="Empty output — agent produced no content",
        )
    if len(stripped) < 20:
        return GateResult(
            gate=GateName.DIFF.value,
            status=GateStatus.FAILED,
            message="Output too short — likely incomplete",
            details={"length": len(stripped)},
        )

    return GateResult(
        gate=GateName.DIFF.value,
        status=GateStatus.PASSED,
        message="Ground truth check passed",
    )


# ─── Gate Dispatch ────────────────────────────────────────────────────

_GATE_DISPATCH: dict[GateName, Callable[[str, dict], GateResult]] = {
    GateName.BUILD: _check_build,
    GateName.TYPES: _check_types,
    GateName.LINT: _check_lint,
    GateName.TESTS: _check_tests,
    GateName.SECURITY: _check_security,
    GateName.A11Y: _check_a11y,
    GateName.PERF: _check_perf,
    GateName.DIFF: _check_diff,
}


# ─── Main Loop ────────────────────────────────────────────────────────

class VerificationLoop:
    """Runs all 8 quality gates on agent output."""

    def __init__(self, config: dict | None = None) -> None:
        """
        Initialize the VerificationLoop with an optional configuration and load per-gate settings.
        
        Parameters:
            config (dict | None): Optional configuration mapping. If provided, may contain a "gates" key with per-gate settings; missing or None defaults to an empty configuration.
        """
        self._config = config or {}
        self._gate_configs: dict[str, GateConfig] = {}
        self._load_config()

    def _load_config(self) -> None:
        """
        Populate internal per-gate configurations from the instance config.
        
        Reads the "gates" mapping from self._config (if present) and sets self._gate_configs[gate_name]
        for every GateName value. For each gate, uses the provided "enabled" and "required" boolean flags
        when present; defaults to True for either flag if omitted.
        """
        gates_raw = self._config.get("gates", {})
        for gate_name in GateName:
            raw = gates_raw.get(gate_name.value, {})
            self._gate_configs[gate_name.value] = GateConfig(
                enabled=raw.get("enabled", True),
                required=raw.get("required", True),
            )

    def get_gate_config(self, gate: str) -> GateConfig:
        """
        Retrieve the configuration for a specified gate.
        
        Parameters:
        	gate (str): Gate identifier (should match a GateName value or the key used in the configuration).
        
        Returns:
        	GateConfig: The configuration for the requested gate. If no specific configuration exists, returns a default GateConfig(enabled=True, required=True).
        """
        return self._gate_configs.get(gate, GateConfig())

    async def run(
        self, content: str, *, context: dict | None = None
    ) -> VerificationResult:
        """
        Execute every verification gate against the provided content and collect their results.
        
        Parameters:
            content (str): Agent output or document text to evaluate across gates.
            context (dict | None): Optional mapping of auxiliary data for checkers (e.g., `"ground_truth"` for the DIFF gate).
        
        Returns:
            VerificationResult: Aggregated per-gate results including statuses, messages, and details.
        """
        result = VerificationResult()
        ctx = context or {}

        for gate_name in GateName:
            gate_result = await self._run_gate(gate_name, content, ctx)
            result.gates.append(gate_result)

        if result.all_green:
            logger.info("All 8 gates PASSED")
        else:
            failed = [g.gate for g in result.failures]
            logger.warning("Gates FAILED: %s", ", ".join(failed))

        return result

    async def _run_gate(
        self, gate: GateName, content: str, context: dict
    ) -> GateResult:
        """
        Execute the configured checker for a single gate and return its GateResult.
        
        If the gate is disabled the result will be `SKIPPED`. If no checker is registered the result will be `PASSED` with an explanatory message. If the checker raises an exception the result will be `FAILED` and include the exception text in `details`.
        
        Parameters:
            gate (GateName): The gate to run.
            content (str): The agent output to evaluate.
            context (dict): Additional context used by gate checkers.
        
        Returns:
            GateResult: The outcome of running the gate (status, message, and optional details).
        """
        cfg = self.get_gate_config(gate.value)
        if not cfg.enabled:
            return GateResult(
                gate=gate.value,
                status=GateStatus.SKIPPED,
                message=f"{gate.value} gate disabled",
            )

        checker = _GATE_DISPATCH.get(gate)
        if checker is None:
            return GateResult(
                gate=gate.value,
                status=GateStatus.PASSED,
                message=f"No checker registered for {gate.value}",
            )

        try:
            return checker(content, context)
        except Exception as exc:
            logger.error("Gate %s raised: %s", gate.value, exc)
            return GateResult(
                gate=gate.value,
                status=GateStatus.FAILED,
                message=f"Gate error: {exc}",
                details={"exception": str(exc)},
            )