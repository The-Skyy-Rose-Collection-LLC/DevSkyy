"""Local quality gates — scoped to file types touched by a PR diff."""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("pr_automator.gates")


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    summary: str
    output: str = ""

    def render(self) -> str:
        icon = "PASS" if self.passed else "FAIL"
        return f"[{icon}] {self.name}: {self.summary}"


@dataclass(frozen=True)
class GateReport:
    results: tuple[GateResult, ...]

    @property
    def all_pass(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failed(self) -> tuple[GateResult, ...]:
        return tuple(r for r in self.results if not r.passed)

    def render(self) -> str:
        return "\n".join(r.render() for r in self.results) or "(no gates ran)"


def _run(cmd: list[str], cwd: Path, timeout: int = 600) -> tuple[int, str]:
    logger.debug("gate: %s", " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout}s"
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def _have(binary: str) -> bool:
    return shutil.which(binary) is not None


def _gate(name: str, rc: int, out: str, ok: str, fail: str, *, tail: int = 4000) -> GateResult:
    return GateResult(
        name=name,
        passed=rc == 0,
        summary=ok if rc == 0 else f"{fail} (exit {rc})",
        output=out[-tail:] if tail else out,
    )


def _python_gates(worktree: Path) -> list[GateResult]:
    results: list[GateResult] = []
    if _have("ruff"):
        rc, out = _run(["ruff", "check", "."], worktree)
        results.append(_gate("ruff", rc, out, "clean", "violations"))
    if _have("black"):
        rc, out = _run(["black", "--check", "--quiet", "."], worktree)
        results.append(_gate("black", rc, out, "formatted", "would reformat"))
    if _have("isort"):
        rc, out = _run(["isort", "--check-only", "--quiet", "."], worktree)
        results.append(_gate("isort", rc, out, "sorted", "imports unsorted"))
    if _have("pytest"):
        rc, out = _run(
            ["pytest", "-x", "--timeout=10", "-q", "--no-header", "tests/"],
            worktree,
            timeout=900,
        )
        results.append(_gate("pytest-fast", rc, out, "all tests pass", "failures"))
    return results


def _frontend_gates(worktree: Path) -> list[GateResult]:
    fe = worktree / "frontend"
    if not fe.exists():
        return []
    if not _have("npm"):
        return []
    results: list[GateResult] = []
    rc, out = _run(["npm", "run", "type-check", "--silent"], fe)
    results.append(_gate("frontend-type-check", rc, out, "types ok", "type errors", tail=2000))
    rc, out = _run(["npm", "run", "lint", "--silent"], fe)
    results.append(_gate("frontend-lint", rc, out, "lint clean", "lint errors", tail=2000))
    return results


def _php_gates(worktree: Path) -> list[GateResult]:
    theme_dir = worktree / "wordpress-theme/skyyrose-flagship"
    phpcs = theme_dir / "vendor/bin/phpcs"
    phpcs_xml = theme_dir / ".phpcs.xml"
    if not (phpcs.exists() and phpcs_xml.exists()):
        return []
    rc, out = _run([str(phpcs), "--standard=.phpcs.xml", "-s", "."], theme_dir)
    return [_gate("phpcs", rc, out, "WPCS clean", "WPCS violations", tail=3000)]


def run_gates(worktree: Path, changed_files: list[str]) -> GateReport:
    """Run only the gates whose tooling exists AND whose scope was touched."""
    py_changed = any(f.endswith(".py") for f in changed_files)
    js_changed = any(
        f.startswith("frontend/") and f.endswith((".ts", ".tsx", ".js", ".jsx"))
        for f in changed_files
    )
    php_changed = any(
        f.startswith("wordpress-theme/") and f.endswith(".php") for f in changed_files
    )

    results: list[GateResult] = []
    if py_changed:
        results.extend(_python_gates(worktree))
    if js_changed:
        results.extend(_frontend_gates(worktree))
    if php_changed:
        results.extend(_php_gates(worktree))
    return GateReport(results=tuple(results))
