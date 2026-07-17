"""
Regression test: critical .claude/ paths must be both git-tracked and not
gitignored.

Context: `.claude/` was blanket-gitignored (a bare `.claude/` rule) despite
128 files under it already being manually force-added over time. The gap in
that manual process — workflows/, state/, and one agent file were never
force-added — made a real, working 684-line engine
(.claude/workflows/self-healing-theme-loop.js) invisible from a fresh git
worktree and caused a false "this doesn't exist" claim in a live session.
Fixed in commit 5f03516c3 (.gitignore flipped from a blanket `.claude/`
ignore to a short deny-list of personal/ephemeral paths only).

This test uses git itself as the authority (`git check-ignore`, `git
ls-files`) rather than a hand-rolled gitignore parser — git's matching rules
have enough edge cases (anchoring, negation, `**`) that re-implementing them
for a test would just create a second thing that can silently drift from
git's real behavior.

IMPORTANT — why `--no-index` is required, not optional:
`git check-ignore` alone is index-aware. Per its own man page: "By default,
tracked files are not shown at all since they are not subject to exclude
rules." That means a plain `git check-ignore -q <path>` on an
*already-tracked* path always reports "not ignored" (exit 1), regardless of
what the current .gitignore contains. Verified empirically against this
repo's history: two of the five paths below (`.claude/settings.json`,
`.claude/agents/theme-heal-doctor.md`) were already tracked *before* commit
5f03516c3, back when `.gitignore` still had a blanket `.claude/` rule — a
plain `git check-ignore -q` against that old .gitignore, run against the
current (tracked) state of those two files, still reports "not ignored".
Only `git check-ignore --no-index`, which skips the index and tests the raw
pattern match, correctly reports them as ignored under that old rule. `git
status`/`add` in a *fresh* worktree or clone — where the path isn't in the
index yet — uses that same raw pattern match, which is exactly the failure
mode from tonight's incident. So this test uses `--no-index` deliberately;
the naive (index-aware) form would not have caught the regression for any
path that happens to already be tracked.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

CRITICAL_CLAUDE_PATHS = [
    ".claude/workflows/self-healing-theme-loop.js",
    ".claude/agents/theme-heal-doctor.md",
    ".claude/state/theme-health-baseline.json",
    ".claude/state/heal-knowledge.json",
    ".claude/settings.json",
]


@pytest.mark.parametrize("relative_path", CRITICAL_CLAUDE_PATHS)
def test_critical_claude_path_is_not_gitignored(relative_path: str) -> None:
    """The raw gitignore pattern match (not the index-aware one) must not
    match this path — otherwise a fresh worktree or clone would never see
    it, even though the currently-checked-out copy is tracked fine."""
    result = subprocess.run(
        # git -C instead of cwd=: cwd= forces the fork() path on macOS, where
        # fork after Network.framework arming SIGSEGVs the child (bug-263).
        ["git", "-C", str(ROOT), "check-ignore", "--no-index", "-q", relative_path],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1, (
        f"{relative_path} is matched by a .gitignore rule "
        f"(git check-ignore --no-index exit={result.returncode}, want 1 = "
        f"not ignored). A .gitignore edit has re-introduced a rule that "
        f"would hide this path from a fresh clone or new worktree."
    )


@pytest.mark.parametrize("relative_path", CRITICAL_CLAUDE_PATHS)
def test_critical_claude_path_is_tracked(relative_path: str) -> None:
    """The path must actually be committed to git — existing only on disk
    in this worktree is exactly what made the engine invisible elsewhere."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--error-unmatch", relative_path],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"{relative_path} is not tracked by git (git ls-files "
        f"--error-unmatch exit={result.returncode}). It exists only on disk "
        f"and is invisible to any other worktree or fresh clone."
    )
