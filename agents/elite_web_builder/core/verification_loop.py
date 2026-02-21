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
        """True if all gates passed."""
        return all(g.status == GateStatus.PASSED for g in self.gates)

    @property
    def failures(self) -> list[GateResult]:
        """List of failed gates."""
        return [g for g in self.gates if g.status == GateStatus.FAILED]

    @property
    def summary(self) -> dict[str, int]:
        """Count of each status."""
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
    """Extract fenced code blocks as (language, code) pairs."""
    return re.findall(r"```(\w*)\n(.*?)```", content, re.DOTALL)


def _check_build(content: str, context: dict) -> GateResult:
    """BUILD gate — verify code blocks parse without syntax errors."""
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
    """TYPES gate — validate schema/type annotations present in code."""
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
    """LINT gate — detect code quality anti-patterns."""
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
    """TESTS gate — verify test presence when implementation code is present."""
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
    """SECURITY gate — scan for secrets and injection vulnerabilities."""
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
    """A11Y gate — validate accessibility in HTML/template output."""
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
    """PERF gate — detect performance anti-patterns."""
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
    """DIFF gate — compare output against ground truth expectations.

    Uses context["ground_truth"] (expected substrings / regexes) when provided.
    Without ground truth, checks that the output is non-trivial.
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
        self._config = config or {}
        self._gate_configs: dict[str, GateConfig] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load per-gate config from the config dict."""
        gates_raw = self._config.get("gates", {})
        for gate_name in GateName:
            raw = gates_raw.get(gate_name.value, {})
            self._gate_configs[gate_name.value] = GateConfig(
                enabled=raw.get("enabled", True),
                required=raw.get("required", True),
            )

    def get_gate_config(self, gate: str) -> GateConfig:
        """Get config for a gate by name."""
        return self._gate_configs.get(gate, GateConfig())

    async def run(
        self, content: str, *, context: dict | None = None
    ) -> VerificationResult:
        """Run all verification gates on content."""
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
        """Run a single gate through the dispatch table."""
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
