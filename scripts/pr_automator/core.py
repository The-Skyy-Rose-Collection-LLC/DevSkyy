"""Core utilities — gh CLI wrapper, persistent state, risk-path matcher, logging."""

from __future__ import annotations

import dataclasses
import fnmatch
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("pr_automator")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# git wrapper — single timeout policy shared by every git invocation
# ---------------------------------------------------------------------------


class GitError(RuntimeError):
    """Raised when ``git`` exits non-zero or times out.

    Subclasses ``RuntimeError`` so existing callers that catch ``RuntimeError``
    continue to work without modification.
    """


def git_run(
    cwd: Path,
    *args: str,
    check: bool = True,
    timeout: int = 120,
) -> str:
    """Run ``git`` in ``cwd`` with a uniform timeout. Returns stripped stdout.

    Centralised here so ``__main__`` and ``reviewer`` share one timeout
    policy and one error shape — the previous design had three separate
    ``subprocess.run([git, ...])`` paths with drift potential.

    Raises ``GitError`` on non-zero exit (when ``check=True``) or on timeout.
    Callers should catch ``GitError`` — no need to also catch
    ``subprocess.TimeoutExpired`` separately.
    """
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        raise GitError(f"git {' '.join(args)} timed out after {timeout}s") from e
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


# ---------------------------------------------------------------------------
# gh CLI wrapper
# ---------------------------------------------------------------------------


class GhError(RuntimeError):
    """Raised when `gh` exits non-zero or returns malformed JSON."""


@dataclass(frozen=True)
class GhClient:
    """Thin wrapper around `gh` CLI. All methods raise GhError on failure."""

    repo: str | None = None
    dry_run: bool = False

    def _run(self, args: list[str], *, capture: bool = True, mutating: bool = False) -> str:
        cmd = ["gh", *args]
        if self.repo and "--repo" not in args and args[0] != "auth":
            cmd.extend(["--repo", self.repo])
        if mutating and self.dry_run:
            logger.info("[dry-run] would run: %s", " ".join(cmd))
            return ""
        logger.debug("gh: %s", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                check=False,
                capture_output=capture,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired as e:
            raise GhError(f"gh timed out after 120s: {' '.join(cmd)}") from e
        if proc.returncode != 0:
            raise GhError(
                f"gh exited {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}"
            )
        return proc.stdout

    def pr_view(self, pr: int, *, fields: list[str]) -> dict[str, Any]:
        out = self._run(["pr", "view", str(pr), "--json", ",".join(fields)])
        try:
            return json.loads(out)
        except json.JSONDecodeError as e:
            raise GhError(f"gh pr view returned invalid JSON: {e}") from e

    def pr_changed_files(self, pr: int) -> list[str]:
        out = self._run(["pr", "diff", str(pr), "--name-only"])
        return [line.strip() for line in out.splitlines() if line.strip()]

    def pr_list_open(self) -> list[dict[str, Any]]:
        out = self._run(
            [
                "pr",
                "list",
                "--state",
                "open",
                "--json",
                "number,headRefName,headRefOid,isDraft,author,labels",
                "--limit",
                "200",
            ]
        )
        try:
            return json.loads(out)
        except json.JSONDecodeError as e:
            raise GhError(f"gh pr list returned invalid JSON: {e}") from e

    def pr_review(self, pr: int, decision: str, body: str) -> None:
        flag = {
            "APPROVE": "--approve",
            "REQUEST_CHANGES": "--request-changes",
            "COMMENT": "--comment",
        }[decision]
        self._run(["pr", "review", str(pr), flag, "--body", body], mutating=True)

    def pr_comment(self, pr: int, body: str) -> None:
        self._run(["pr", "comment", str(pr), "--body", body], mutating=True)

    def pr_label_add(self, pr: int, label: str) -> None:
        self._run(["pr", "edit", str(pr), "--add-label", label], mutating=True)

    def pr_label_remove(self, pr: int, label: str) -> None:
        self._run(["pr", "edit", str(pr), "--remove-label", label], mutating=True)

    def pr_merge(self, pr: int, *, method: str = "squash", admin: bool = False) -> None:
        """Merge a PR.

        ``admin=False`` (the default) respects branch protection — required checks,
        CODEOWNERS, and reviewer counts apply. Pass ``admin=True`` only when the
        operator has explicitly opted into bypassing branch protection (the
        ``--admin`` CLI flag); a warning is logged so the bypass is auditable in
        the daemon log.
        """
        args = ["pr", "merge", str(pr), f"--{method}", "--delete-branch"]
        if admin:
            logger.warning("merging PR #%s with --admin (branch protection bypassed)", pr)
            args.append("--admin")
        self._run(args, mutating=True)


# ---------------------------------------------------------------------------
# Persistent state
# ---------------------------------------------------------------------------


def state_path() -> Path:
    base = Path(os.environ.get("PR_AUTOMATOR_HOME", Path.home() / ".cache/pr-automator"))
    base.mkdir(parents=True, exist_ok=True)
    return base / "state.json"


@dataclass
class PrCycleState:
    cycle_count: int = 0
    last_sha: str | None = None
    last_verdict: str | None = None
    last_cycle_at: str | None = None
    last_green_sha: str | None = None
    blocked_reason: str | None = None


@dataclass
class State:
    """Persistent automator state.

    Deliberate exception to the project's "create new objects, never mutate"
    rule. ``State`` is a single-writer persistence object: every mutation
    flows through ``record_cycle`` / ``for_pr`` and is immediately serialised
    to disk via ``save()``. A copy-on-write pattern would either force every
    caller to reassign the State instance after each update (verbose, error-
    prone in long-running loops) or require a global pointer indirection.
    The single-writer invariant is enforced operationally — only one
    ``--watch`` daemon and ``--once`` invocation should run concurrently —
    backed by atomic writes (tmp + os.replace) so concurrent readers are
    safe.
    """

    paused: bool = False
    prs: dict[str, PrCycleState] = field(default_factory=dict)

    @classmethod
    def load(cls) -> State:
        path = state_path()
        if not path.exists():
            return cls()
        raw = json.loads(path.read_text())
        # Filter to known fields so adding/removing PrCycleState fields
        # doesn't break loading an older state.json.
        known = set(PrCycleState.__dataclass_fields__)
        prs = {
            k: PrCycleState(**{kk: vv for kk, vv in v.items() if kk in known})
            for k, v in raw.get("prs", {}).items()
        }
        return cls(paused=raw.get("paused", False), prs=prs)

    def save(self) -> None:
        """Atomic write — temp file + os.replace.

        A crash mid-write would otherwise leave a truncated state.json that
        raises JSONDecodeError on next load. os.replace is atomic on POSIX, so
        readers see either the old file or the new file, never a half-written
        one.
        """
        path = state_path()
        payload = {
            "paused": self.paused,
            "prs": {k: dataclasses.asdict(v) for k, v in self.prs.items()},
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        os.replace(tmp, path)

    def for_pr(self, pr: int) -> PrCycleState:
        key = str(pr)
        if key not in self.prs:
            self.prs[key] = PrCycleState()
        return self.prs[key]

    def record_cycle(
        self,
        pr: int,
        head_sha: str,
        verdict: str,
        *,
        green: bool = False,
        blocked: str | None = None,
    ) -> None:
        s = self.for_pr(pr)
        if s.last_sha != head_sha:
            s.cycle_count = 0
        s.cycle_count += 1
        s.last_sha = head_sha
        s.last_verdict = verdict
        s.last_cycle_at = datetime.now(UTC).isoformat()
        s.blocked_reason = blocked
        if green:
            s.last_green_sha = head_sha
        self.save()


# ---------------------------------------------------------------------------
# Risk paths
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RiskPaths:
    patterns: tuple[str, ...]

    @classmethod
    def load(cls, source: Path) -> RiskPaths:
        if not source.exists():
            return cls(patterns=())
        lines = source.read_text().splitlines()
        patterns = tuple(
            line.strip() for line in lines if line.strip() and not line.strip().startswith("#")
        )
        return cls(patterns=patterns)

    def matches(self, files: list[str]) -> list[tuple[str, str]]:
        """Return (file, pattern) tuples for every risk-path hit."""
        hits: list[tuple[str, str]] = []
        for f in files:
            for pat in self.patterns:
                if fnmatch.fnmatch(f, pat):
                    hits.append((f, pat))
                    break
        return hits
