"""
CLI entry point for Elite Web Builder.

Usage:
  python -m elite_web_builder "PRD text here"
  python -m elite_web_builder --file prd.md
  python -m elite_web_builder --file prd.md --dry-run
  python -m elite_web_builder --file prd.md --config routing.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .director import Director, DirectorConfig, StoryStatus


def _build_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command-line argument parser for the elite_web_builder tool.
    
    The parser enforces that either inline PRD text or a PRD file is provided (mutually exclusive). It also exposes flags to control planning vs execution, routing configuration, and the maximum number of stories to generate.
    
    Returns:
        argparse.ArgumentParser: Parser configured with:
          - positional `prd` (optional): inline PRD text.
          - `--file` (Path): path to a PRD file (.md or .txt).
          - `--dry-run` (flag): plan stories only; do not execute.
          - `--config` (Path): path to a provider routing JSON override.
          - `--max-stories` (int): maximum number of stories to generate (default 50).
    """
    parser = argparse.ArgumentParser(
        prog="elite_web_builder",
        description="Elite Web Builder — Full-stack AI web development agency",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "prd",
        nargs="?",
        default=None,
        help="Inline PRD text",
    )
    group.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Path to PRD file (.md or .txt)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Plan stories only, do not execute",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to provider routing JSON override",
    )
    parser.add_argument(
        "--max-stories",
        type=int,
        default=50,
        help="Maximum number of stories to generate (default: 50)",
    )

    return parser


def _load_prd(args: argparse.Namespace) -> str:
    """
    Load the product requirements document (PRD) text from parsed CLI arguments.
    
    If a file path is provided in args.file, validate the path exists and return its contents.
    If the file is missing, print an error to stderr and exit the process with code 1.
    If no file is provided, return the inline PRD text from args.prd.
    
    Parameters:
        args (argparse.Namespace): Parsed command-line arguments. Expected attributes:
            - file (pathlib.Path | None): Optional path to a PRD file.
            - prd (str): Inline PRD text.
    
    Returns:
        prd_text (str): The PRD content loaded from the file or from args.prd.
    """
    if args.file:
        if not args.file.exists():
            print(f"Error: PRD file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        return args.file.read_text()
    return args.prd


def _print_report(report: object) -> None:
    """
    Prints a formatted project report for an executed PRD to stdout.
    
    Parameters:
        report (object): A project report with these attributes used for output:
            - stories (Sequence): list of story objects; each must have `id`, `title`, and `status`.
            - status_summary (str): summary string of overall status.
            - all_green (bool): True if all stories succeeded.
            - elapsed_ms (float|int): elapsed execution time in milliseconds.
            - instincts_learned (int): count of "instincts" learned.
            - failures (Sequence[str]): optional list of failure messages.
    
    The function prints counts, overall status, elapsed time, learned instincts, any failures,
    and a per-story line showing a check or cross, story id, title, and status value.
    """
    print("\n" + "=" * 60)
    print("ELITE WEB BUILDER — PROJECT REPORT")
    print("=" * 60)

    print(f"\nStories: {len(report.stories)}")
    print(f"Status: {report.status_summary}")
    print(f"All Green: {report.all_green}")
    print(f"Elapsed: {report.elapsed_ms:.0f}ms")
    print(f"Instincts Learned: {report.instincts_learned}")

    if report.failures:
        print(f"\nFailures ({len(report.failures)}):")
        for failure in report.failures:
            print(f"  - {failure}")

    if report.stories:
        print("\nStory Details:")
        for story in report.stories:
            status_icon = "✓" if story.status == StoryStatus.GREEN else "✗"
            print(f"  {status_icon} {story.id}: {story.title} [{story.status.value}]")

    print("\n" + "=" * 60)


async def _run(args: argparse.Namespace) -> int:
    """
    Run the CLI workflow to plan or execute a PRD and return the process exit code.
    
    Parameters:
        args (argparse.Namespace): Parsed command-line arguments. Expected attributes:
            - prd or file: PRD text or path used to load the PRD.
            - dry_run (bool): If true, plan stories without executing them.
            - config (Optional[str]): Optional routing configuration path.
            - max_stories (int): Maximum number of stories to consider.
    
    Returns:
        int: Process exit code — `0` on success (or successful dry run), `1` on failure or when execution completes with any non-green story.
    """
    prd_text = _load_prd(args)

    # Build config
    config = DirectorConfig(max_stories=args.max_stories)
    if args.config:
        config.routing_config_path = args.config

    director = Director(config=config)

    if args.dry_run:
        # Plan only
        print("DRY RUN — Planning stories only\n")
        try:
            breakdown = await director._plan_stories(prd_text)
        except Exception as exc:
            print(f"Planning failed: {exc}", file=sys.stderr)
            return 1

        print(f"Stories ({len(breakdown.stories)}):")
        for story in breakdown.stories:
            deps = ", ".join(story.depends_on) if story.depends_on else "none"
            print(f"  {story.id}: {story.title}")
            print(f"    Agent: {story.agent_role.value}")
            print(f"    Deps: {deps}")
            print()

        if breakdown.dependency_order:
            print(f"Execution Order: {' → '.join(breakdown.dependency_order)}")
        return 0

    # Full execution
    report = await director.execute_prd(prd_text)
    _print_report(report)
    return 0 if report.all_green else 1


def main() -> None:
    """
    Run the command-line interface: parse command-line arguments, execute the asynchronous CLI workflow, and exit with its status code.
    
    Parses arguments from sys.argv, invokes the async runner `_run` with the parsed arguments, and terminates the process using the integer exit code returned by `_run`.
    """
    parser = _build_parser()
    args = parser.parse_args()
    exit_code = asyncio.run(_run(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()