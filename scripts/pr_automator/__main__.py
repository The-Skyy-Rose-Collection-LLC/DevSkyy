"""CLI entry point — `python -m scripts.pr_automator`."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import time
from pathlib import Path

from scripts.pr_automator.core import GhClient, GhError, RiskPaths, State, setup_logging
from scripts.pr_automator.gates import auto_fix_format, run_gates
from scripts.pr_automator.merge_gate import (
    MAX_CYCLES_PER_SHA,
    NEEDS_HUMAN_LABEL,
    OPT_IN_LABEL,
    evaluate,
    package_root,
)
from scripts.pr_automator.reviewer import ReviewerAgent, fetch_diff

logger = logging.getLogger("pr_automator.cli")

PR_VIEW_FIELDS = [
    "number",
    "headRefName",
    "headRefOid",
    "isDraft",
    "author",
    "labels",
    "mergeable",
    "mergeStateStatus",
    "reviews",
]


def _git(worktree: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=worktree,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def prepare_worktree(repo_root: Path, pr_number: int, head_ref: str, head_sha: str) -> Path:
    """Create or update a worktree at .claude/worktrees/pr-auto-<N> on the PR head SHA."""
    target = repo_root / f".claude/worktrees/pr-auto-{pr_number}"
    if not target.exists():
        # Fetch the PR's head ref then create the worktree.
        _git(repo_root, "fetch", "origin", f"pull/{pr_number}/head:pr-auto-{pr_number}")
        _git(repo_root, "worktree", "add", str(target), f"pr-auto-{pr_number}")
    _git(target, "fetch", "origin", f"pull/{pr_number}/head", check=False)
    _git(target, "checkout", head_sha)
    return target


def run_cycle(
    pr_number: int,
    repo_root: Path,
    *,
    dry_run: bool = False,
    skip_review: bool = False,
    force: bool = False,
) -> int:
    """One full cycle on a single PR. Returns exit code (0=ok, 2=blocked, 3=error)."""
    gh = GhClient(dry_run=dry_run)
    state = State.load()

    if state.paused:
        logger.warning("automator paused (global). Use --resume to clear.")
        return 2

    try:
        pr = gh.pr_view(pr_number, fields=PR_VIEW_FIELDS)
    except GhError as e:
        logger.error("gh pr view failed for #%s: %s", pr_number, e)
        return 3

    head_sha = pr["headRefOid"]
    head_ref = pr["headRefName"]
    labels = {lbl["name"] for lbl in pr.get("labels", [])}

    if OPT_IN_LABEL not in labels and not force:
        logger.info(
            "PR #%s missing `%s` label — skipping (use `gh pr edit %s --add-label %s` to opt in, or pass --force)",
            pr_number,
            OPT_IN_LABEL,
            pr_number,
            OPT_IN_LABEL,
        )
        return 2
    if force and OPT_IN_LABEL not in labels:
        logger.warning("--force: bypassing opt-in label check on PR #%s", pr_number)

    pr_state = state.for_pr(pr_number)
    if pr_state.last_sha == head_sha and pr_state.cycle_count >= MAX_CYCLES_PER_SHA:
        logger.warning(
            "PR #%s hit cycle cap (%d) on SHA %s — labeling needs-human",
            pr_number,
            MAX_CYCLES_PER_SHA,
            head_sha[:8],
        )
        if not dry_run:
            try:
                gh.pr_label_add(pr_number, NEEDS_HUMAN_LABEL)
            except GhError:
                pass
        return 2

    logger.info(
        "PR #%s — head=%s ref=%s cycle=%d",
        pr_number,
        head_sha[:8],
        head_ref,
        pr_state.cycle_count + 1,
    )

    worktree = prepare_worktree(repo_root, pr_number, head_ref, head_sha)
    try:
        changed = gh.pr_changed_files(pr_number)
    except GhError as e:
        logger.error("gh pr diff failed: %s", e)
        return 3

    logger.info("changed files: %d", len(changed))

    # 1. Mechanical auto-fix on format/lint (no judgment).
    fix_changed, fix_summary = auto_fix_format(worktree)
    logger.info("auto-fix: changed=%s | %s", fix_changed, fix_summary)
    if fix_changed and not dry_run:
        _git(worktree, "add", "-A")
        _git(worktree, "commit", "-m", "style(pr-automator): auto-format (ruff/black/isort)")
        _git(worktree, "push", "origin", f"HEAD:{head_ref}")
        logger.info("pushed format-fix; deferring rest of cycle to next pass")
        state.record_cycle(pr_number, head_sha, "FORMAT_FIX")
        return 0

    # 2. Run gates after auto-fix.
    gates = run_gates(worktree, changed)
    logger.info("gates:\n%s", gates.render())

    # 3. Reviewer agent (skippable for fast smoke testing).
    if skip_review:
        from scripts.pr_automator.reviewer import ReviewVerdict

        review = ReviewVerdict(
            verdict="DEFER_HUMAN",
            confidence=0,
            scope_assessment="(reviewer skipped)",
            risk_assessment="unknown",
            defer_reasons=["--skip-review flag set"],
        )
    else:
        diff_text = fetch_diff(worktree, pr_number)
        agent = ReviewerAgent()
        try:
            review = agent.review(pr_number, diff_text)
        except Exception as e:  # pragma: no cover - subprocess failures
            logger.error("reviewer agent failed: %s", e)
            return 3
    logger.info("reviewer verdict: %s (confidence %d)", review.verdict, review.confidence)

    # 4. Post the review on GitHub (unless dry-run or skipped).
    if not skip_review and not dry_run:
        try:
            decision_flag = (
                "APPROVE"
                if review.is_approve and gates.all_pass
                else ("COMMENT" if review.is_defer else "REQUEST_CHANGES")
            )
            gh.pr_review(pr_number, decision_flag, review.to_yaml_body())
        except GhError as e:
            logger.warning("could not post review: %s", e)

    # 5. Evaluate merge predicate.
    risk_paths = RiskPaths.load(package_root() / "RISK_PATHS.txt")
    decision = evaluate(
        pr_number=pr_number,
        pr_view=pr,
        gates=gates,
        review=review,
        risk_paths=risk_paths,
        changed_files=changed,
        state=state,
        head_sha=head_sha,
    )
    logger.info("\n%s", decision.render())

    # 6. Merge if green.
    state.record_cycle(
        pr_number,
        head_sha,
        review.verdict,
        green=gates.all_pass,
        blocked=None if decision.can_merge else "predicate_fail",
    )

    if decision.can_merge:
        logger.info("PR #%s — predicate green, merging (squash --admin)", pr_number)
        if not dry_run:
            try:
                gh.pr_merge(pr_number, method="squash", admin=True)
                logger.info("MERGED #%s", pr_number)
            except GhError as e:
                logger.error("merge failed: %s", e)
                return 3
        return 0

    if review.is_defer and not dry_run:
        try:
            gh.pr_label_add(pr_number, NEEDS_HUMAN_LABEL)
        except GhError:
            pass

    return 2


def watch_loop(repo_root: Path, *, interval: int, dry_run: bool) -> int:
    """Poll open PRs forever, run a cycle on each that has the opt-in label."""
    gh = GhClient(dry_run=dry_run)
    logger.info("watch mode — polling every %ds (Ctrl+C to stop)", interval)
    while True:
        try:
            prs = gh.pr_list_open()
        except GhError as e:
            logger.error("gh pr list failed: %s — sleeping", e)
            time.sleep(interval)
            continue

        for pr in prs:
            labels = {lbl["name"] for lbl in pr.get("labels", [])}
            if OPT_IN_LABEL not in labels or pr.get("isDraft"):
                continue
            try:
                run_cycle(pr["number"], repo_root, dry_run=dry_run)
            except KeyboardInterrupt:
                raise
            except Exception as e:  # pragma: no cover
                logger.exception("cycle on #%s crashed: %s", pr["number"], e)

        time.sleep(interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pr_automator")
    parser.add_argument("--watch", action="store_true", help="daemon mode — poll PRs forever")
    parser.add_argument("--once", action="store_true", help="run one cycle on a single PR")
    parser.add_argument("--pr", type=int, help="PR number (required with --once)")
    parser.add_argument("--dry-run", action="store_true", help="never call mutating gh commands")
    parser.add_argument(
        "--skip-review", action="store_true", help="skip the Claude reviewer agent (smoke testing)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="bypass the opt-in label check (one-off manual cycle on a specific PR)",
    )
    parser.add_argument("--pause", action="store_true", help="set global pause flag")
    parser.add_argument("--resume", action="store_true", help="clear global pause flag")
    parser.add_argument("--status", action="store_true", help="print current state JSON")
    parser.add_argument("--interval", type=int, default=60, help="watch poll interval (seconds)")
    parser.add_argument(
        "--repo-root", type=Path, default=None, help="repo root (default: detect via git rev-parse)"
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    setup_logging(verbose=args.verbose)

    if args.pause:
        s = State.load()
        s.paused = True
        s.save()
        print("automator: PAUSED")
        return 0
    if args.resume:
        s = State.load()
        s.paused = False
        s.save()
        print("automator: RESUMED")
        return 0
    if args.status:
        s = State.load()
        import json as _json

        print(
            _json.dumps(
                {
                    "paused": s.paused,
                    "prs": {k: v.__dict__ for k, v in s.prs.items()},
                },
                indent=2,
            )
        )
        return 0

    if args.repo_root:
        repo_root = args.repo_root.resolve()
    else:
        try:
            out = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            repo_root = Path(out)
        except subprocess.CalledProcessError:
            print("error: not in a git repo (use --repo-root)", file=sys.stderr)
            return 3

    if args.watch:
        return watch_loop(repo_root, interval=args.interval, dry_run=args.dry_run)

    if args.once:
        if not args.pr:
            print("error: --once requires --pr <N>", file=sys.stderr)
            return 3
        return run_cycle(
            args.pr,
            repo_root,
            dry_run=args.dry_run,
            skip_review=args.skip_review,
            force=args.force,
        )

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
