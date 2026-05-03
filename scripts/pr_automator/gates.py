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

    if py_changed and _have("ruff"):
        rc, out = _run(["ruff", "check", "."], worktree)
        results.append(
            GateResult(
                name="ruff",
                passed=rc == 0,
                summary="clean" if rc == 0 else f"violations (exit {rc})",
                output=out,
            )
        )

    if py_changed and _have("black"):
        rc, out = _run(["black", "--check", "--quiet", "."], worktree)
        results.append(
            GateResult(
                name="black",
                passed=rc == 0,
                summary="formatted" if rc == 0 else "would reformat",
                output=out,
            )
        )

    if py_changed and _have("isort"):
        rc, out = _run(["isort", "--check-only", "--quiet", "."], worktree)
        results.append(
            GateResult(
                name="isort",
                passed=rc == 0,
                summary="sorted" if rc == 0 else "imports unsorted",
                output=out,
            )
        )

    if py_changed and _have("pytest"):
        rc, out = _run(
            ["pytest", "-x", "--timeout=10", "-q", "--no-header", "tests/"],
            worktree,
            timeout=900,
        )
        passed = rc == 0
        results.append(
            GateResult(
                name="pytest-fast",
                passed=passed,
                summary="all tests pass" if passed else f"failures (exit {rc})",
                output=out[-4000:],
            )
        )

    if js_changed and (worktree / "frontend").exists():
        rc, out = _run(["npm", "run", "type-check", "--silent"], worktree / "frontend")
        results.append(
            GateResult(
                name="frontend-type-check",
                passed=rc == 0,
                summary="types ok" if rc == 0 else f"type errors (exit {rc})",
                output=out[-2000:],
            )
        )
        rc, out = _run(["npm", "run", "lint", "--silent"], worktree / "frontend")
        results.append(
            GateResult(
                name="frontend-lint",
                passed=rc == 0,
                summary="lint clean" if rc == 0 else f"lint errors (exit {rc})",
                output=out[-2000:],
            )
        )

    if php_changed:
        theme_dir = worktree / "wordpress-theme/skyyrose-flagship"
        phpcs = theme_dir / "vendor/bin/phpcs"
        phpcs_xml = theme_dir / ".phpcs.xml"
        if phpcs.exists() and phpcs_xml.exists():
            rc, out = _run(
                [str(phpcs), "--standard=.phpcs.xml", "-s", "."],
                theme_dir,
            )
            results.append(
                GateResult(
                    name="phpcs",
                    passed=rc == 0,
                    summary="WPCS clean" if rc == 0 else f"WPCS violations (exit {rc})",
                    output=out[-3000:],
                )
            )

    return GateReport(results=tuple(results))


def auto_fix_format(worktree: Path) -> tuple[bool, str]:
    """Run isort + ruff --fix + black; return (any_changes, summary).

    Lint-format auto-fix is the only thing the automator runs without judgment —
    it's mechanical and reversible via git.
    """
    summary_parts: list[str] = []
    changed = False

    for cmd, label in [
        (["isort", "--quiet", "."], "isort"),
        (["ruff", "check", "--fix", "--quiet", "."], "ruff --fix"),
        (["black", "--quiet", "."], "black"),
    ]:
        if not _have(cmd[0]):
            summary_parts.append(f"{label}: not installed")
            continue
        rc, out = _run(cmd, worktree)
        summary_parts.append(f"{label}: exit={rc}")
        if rc == 0 and out:
            changed = True

    # Authoritative check for actual file changes:
    rc, _ = _run(["git", "diff", "--quiet"], worktree)
    changed = rc != 0
    return changed, " | ".join(summary_parts)
