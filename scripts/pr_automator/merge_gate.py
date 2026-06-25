"""Merge gate — evaluates the 10-check predicate for auto-merge."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.pr_automator.core import PrCycleState, RiskPaths, State
from scripts.pr_automator.gates import GateReport
from scripts.pr_automator.reviewer import ReviewVerdict

logger = logging.getLogger("pr_automator.merge_gate")

OPT_IN_LABEL = "automator:on"
NEEDS_HUMAN_LABEL = "automator:needs-human"
PAUSED_LABEL = "automator:paused"
COOLDOWN_MINUTES = 15
MAX_CYCLES_PER_SHA = 6
BOT_AUTHOR_LOGINS = {
    "dependabot",
    "dependabot[bot]",
    "renovate",
    "renovate[bot]",
    "github-actions[bot]",
}


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str

    def render(self) -> str:
        icon = "OK " if self.passed else "NO "
        return f"  {icon} {self.name}: {self.detail}"


@dataclass
class MergeDecision:
    can_merge: bool
    checks: list[CheckResult] = field(default_factory=list)

    def render(self) -> str:
        head = "MERGE-READY" if self.can_merge else "BLOCKED"
        lines = [f"Merge gate: {head}"]
        lines.extend(c.render() for c in self.checks)
        return "\n".join(lines)


def _check_opt_in_label(labels: set[str]) -> CheckResult:
    return CheckResult(
        name=f"label `{OPT_IN_LABEL}` present",
        passed=OPT_IN_LABEL in labels,
        detail=f"labels={sorted(labels)}",
    )


def _check_mergeable(mergeable: str) -> CheckResult:
    return CheckResult(
        name="mergeable (no conflicts)",
        passed=mergeable == "MERGEABLE",
        detail=f"mergeable={mergeable}",
    )


def _latest_review_per_human_author(reviews: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Group reviews by author login, drop bots, return the latest review per author.

    Why latest-only: a human who posts CHANGES_REQUESTED then later approves
    has only the APPROVED verdict reflected in their *latest* review. Filtering
    by raw `state == CHANGES_REQUESTED` across the full reviews list would
    block forever on the stale CR. GitHub guarantees `submittedAt` is set on
    submitted reviews; reviews with no submittedAt (PENDING) are skipped.
    """
    latest: dict[str, dict[str, Any]] = {}
    for r in reviews:
        author = (r.get("author") or {}).get("login", "")
        if not author or author.endswith("[bot]"):
            continue
        submitted = r.get("submittedAt")
        if not submitted:
            continue
        prior = latest.get(author)
        if prior is None or submitted > prior.get("submittedAt", ""):
            latest[author] = r
    return latest


def _check_human_changes_requested(reviews: list[dict[str, Any]]) -> CheckResult:
    by_author = _latest_review_per_human_author(reviews)
    blockers = [author for author, r in by_author.items() if r.get("state") == "CHANGES_REQUESTED"]
    return CheckResult(
        name="no human CHANGES_REQUESTED",
        passed=len(blockers) == 0,
        detail=(
            f"{len(blockers)} human(s) currently blocking: {', '.join(sorted(blockers))}"
            if blockers
            else f"{len(by_author)} human reviewer(s), none blocking"
        ),
    )


def _check_not_draft_not_bot(is_draft: bool, author_login: str) -> CheckResult:
    is_bot_author = author_login in BOT_AUTHOR_LOGINS or author_login.endswith("[bot]")
    return CheckResult(
        name="not draft, not bot author",
        passed=not is_draft and not is_bot_author,
        detail=f"draft={is_draft}, author={author_login}",
    )


def _check_gates_green(gates: GateReport) -> CheckResult:
    detail = (
        f"{len(gates.failed)} failed: " + ", ".join(g.name for g in gates.failed)
        if gates.failed
        else f"{len(gates.results)} gates passed"
    )
    return CheckResult(name="all local gates green", passed=gates.all_pass, detail=detail)


def _check_cooldown(pr_state: PrCycleState, head_sha: str) -> CheckResult:
    cooldown_ok = False
    detail = "no prior cycle for this SHA"
    if pr_state.last_cycle_at and pr_state.last_sha == head_sha:
        try:
            last = datetime.fromisoformat(pr_state.last_cycle_at)
            elapsed = datetime.now(UTC) - last
            cooldown_ok = elapsed >= timedelta(minutes=COOLDOWN_MINUTES)
            detail = f"elapsed={elapsed}"
        except ValueError:
            detail = "state timestamp unparseable"
    return CheckResult(
        name=f"cooldown ≥ {COOLDOWN_MINUTES} min on this SHA",
        passed=cooldown_ok,
        detail=detail,
    )


def _check_no_risk_paths(risk_paths: RiskPaths, changed_files: list[str]) -> CheckResult:
    """Block auto-merge for any risk-path hit. No label override (see commit 8b98db990)."""
    risk_hits = risk_paths.matches(changed_files)
    detail = (
        "no risk paths touched"
        if not risk_hits
        else f"{len(risk_hits)} risk-path hit(s): "
        + ", ".join(f"{f}~{p}" for f, p in risk_hits[:5])
        + ("..." if len(risk_hits) > 5 else "")
    )
    return CheckResult(name="no risk paths touched", passed=len(risk_hits) == 0, detail=detail)


def _check_prior_green(pr_state: PrCycleState, head_sha: str) -> CheckResult:
    return CheckResult(
        name="prior green cycle exists for head SHA",
        passed=pr_state.last_green_sha == head_sha,
        detail=f"last_green_sha={pr_state.last_green_sha} head_sha={head_sha[:8]}",
    )


def _check_not_paused(state: State, labels: set[str]) -> CheckResult:
    paused = state.paused or PAUSED_LABEL in labels
    return CheckResult(
        name="not paused (global flag or label)",
        passed=not paused,
        detail=f"paused={paused}",
    )


def _check_reviewer_approved(review: ReviewVerdict) -> CheckResult:
    return CheckResult(
        name="reviewer agent APPROVED on head SHA",
        passed=review.is_approve,
        detail=f"verdict={review.verdict} confidence={review.confidence}",
    )


def evaluate(
    pr_number: int,
    pr_view: dict[str, Any],
    gates: GateReport,
    review: ReviewVerdict,
    risk_paths: RiskPaths,
    changed_files: list[str],
    state: State,
    *,
    head_sha: str,
) -> MergeDecision:
    """Evaluate the 10-check predicate. Returns a MergeDecision with per-check results.

    Each check is a small named function so adding/removing a check means
    appending/removing one line in the list below — no behavioural changes
    bury themselves inside this function any more.
    """
    labels = {lbl["name"] for lbl in pr_view.get("labels", [])}
    reviews = pr_view.get("reviews", []) or []
    pr_state = state.for_pr(pr_number)

    checks: list[CheckResult] = [
        _check_opt_in_label(labels),
        _check_mergeable(pr_view.get("mergeable", "UNKNOWN")),
        _check_human_changes_requested(reviews),
        _check_not_draft_not_bot(
            bool(pr_view.get("isDraft", False)),
            (pr_view.get("author") or {}).get("login", "").lower(),
        ),
        _check_gates_green(gates),
        _check_cooldown(pr_state, head_sha),
        _check_no_risk_paths(risk_paths, changed_files),
        _check_prior_green(pr_state, head_sha),
        _check_not_paused(state, labels),
        _check_reviewer_approved(review),
    ]

    return MergeDecision(can_merge=all(c.passed for c in checks), checks=checks)


def package_root() -> Path:
    return Path(__file__).resolve().parent
