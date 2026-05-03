"""Merge gate — evaluates the 10-check predicate for auto-merge."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from scripts.pr_automator.core import RiskPaths, State
from scripts.pr_automator.gates import GateReport
from scripts.pr_automator.reviewer import ReviewVerdict

logger = logging.getLogger("pr_automator.merge_gate")

OPT_IN_LABEL = "automator:on"
RISK_OK_LABEL = "automator:risk-ok"
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
    checks: list[CheckResult] = []
    labels = {lbl["name"] for lbl in pr_view.get("labels", [])}
    reviews = pr_view.get("reviews", []) or []
    is_draft = bool(pr_view.get("isDraft", False))
    author_login = (pr_view.get("author") or {}).get("login", "").lower()
    mergeable = pr_view.get("mergeable", "UNKNOWN")
    pr_state = state.for_pr(pr_number)

    # 1. opt-in label
    checks.append(
        CheckResult(
            name=f"label `{OPT_IN_LABEL}` present",
            passed=OPT_IN_LABEL in labels,
            detail=f"labels={sorted(labels)}",
        )
    )

    # 2. mergeable
    checks.append(
        CheckResult(
            name="mergeable (no conflicts)",
            passed=mergeable == "MERGEABLE",
            detail=f"mergeable={mergeable}",
        )
    )

    # 3. no human CHANGES_REQUESTED
    human_blocks = [
        r
        for r in reviews
        if r.get("state") == "CHANGES_REQUESTED"
        and not (r.get("author") or {}).get("login", "").endswith("[bot]")
    ]
    checks.append(
        CheckResult(
            name="no human CHANGES_REQUESTED",
            passed=len(human_blocks) == 0,
            detail=f"{len(human_blocks)} human change-request review(s)",
        )
    )

    # 4. not draft, not bot author
    is_bot_author = author_login in BOT_AUTHOR_LOGINS or author_login.endswith("[bot]")
    checks.append(
        CheckResult(
            name="not draft, not bot author",
            passed=not is_draft and not is_bot_author,
            detail=f"draft={is_draft}, author={author_login}",
        )
    )

    # 5. local gates green
    checks.append(
        CheckResult(
            name="all local gates green",
            passed=gates.all_pass,
            detail=(
                f"{len(gates.failed)} failed: " + ", ".join(g.name for g in gates.failed)
                if gates.failed
                else f"{len(gates.results)} gates passed"
            ),
        )
    )

    # 6. cooldown — head SHA stable for COOLDOWN_MINUTES
    cooldown_ok = False
    cooldown_detail = "no prior cycle for this SHA"
    if pr_state.last_cycle_at and pr_state.last_sha == head_sha:
        try:
            last = datetime.fromisoformat(pr_state.last_cycle_at)
            elapsed = datetime.now(UTC) - last
            cooldown_ok = elapsed >= timedelta(minutes=COOLDOWN_MINUTES)
            cooldown_detail = f"elapsed={elapsed}"
        except ValueError:
            cooldown_detail = "state timestamp unparseable"
    checks.append(
        CheckResult(
            name=f"cooldown ≥ {COOLDOWN_MINUTES} min on this SHA",
            passed=cooldown_ok,
            detail=cooldown_detail,
        )
    )

    # 7. no risk paths touched (NO label override — see security review:
    # `automator:risk-ok` was self-applicable by any write-access user, which
    # collapsed this check to a single label. PRs that touch risk paths now
    # require a manual human merge regardless of labels.)
    risk_hits = risk_paths.matches(changed_files)
    risk_detail = (
        "no risk paths touched"
        if not risk_hits
        else f"{len(risk_hits)} risk-path hit(s): "
        + ", ".join(f"{f}~{p}" for f, p in risk_hits[:5])
        + ("..." if len(risk_hits) > 5 else "")
    )
    checks.append(
        CheckResult(
            name="no risk paths touched",
            passed=len(risk_hits) == 0,
            detail=risk_detail,
        )
    )

    # 8. ≥1 prior green cycle on this SHA
    green_on_sha = pr_state.last_green_sha == head_sha
    checks.append(
        CheckResult(
            name="prior green cycle exists for head SHA",
            passed=green_on_sha,
            detail=f"last_green_sha={pr_state.last_green_sha} head_sha={head_sha[:8]}",
        )
    )

    # 9. not paused (global or per-PR)
    paused = state.paused or PAUSED_LABEL in labels
    checks.append(
        CheckResult(
            name="not paused (global flag or label)",
            passed=not paused,
            detail=f"paused={paused}",
        )
    )

    # 10. reviewer approved on this exact head SHA
    checks.append(
        CheckResult(
            name="reviewer agent APPROVED on head SHA",
            passed=review.is_approve,
            detail=f"verdict={review.verdict} confidence={review.confidence}",
        )
    )

    # Cycle-cap enforcement happens earlier in __main__.run_cycle (the cycle
    # short-circuits before evaluate is even called when the cap is hit),
    # so there's no second check here.
    can_merge = all(c.passed for c in checks)
    return MergeDecision(can_merge=can_merge, checks=checks)


def package_root() -> Path:
    return Path(__file__).resolve().parent
