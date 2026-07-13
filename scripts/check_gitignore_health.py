#!/usr/bin/env python3
"""check_gitignore_health.py — Read-only .gitignore redundancy/duplication linter.

Flags two classes of drift that let .gitignore grow through session-by-session,
reactive edits with no check against existing coverage (see the .gitignore's
own 2026-07-09 changelog comment for the incident this guards against — a
blanket `.claude/` ignore rule made a real engine invisible in a worktree):

  1. Exact-duplicate content lines — the same pattern added twice, verbatim.
  2. Redundant `**/X` (or `**/X/`) lines where a bare `X` (or `X/`) pattern
     already exists elsewhere in the file. Per gitignore(5), a pattern with
     no leading slash and no interior slash already matches at any depth in
     the tree — prefixing it with `**/` changes nothing. A pattern WITH a
     leading `/` or an interior `/` (other than a single trailing one) is
     anchored to the .gitignore's own directory and is NOT equivalent to the
     recursive form, so those are never flagged as redundant.

Exit codes:
  0 — clean, no issues found
  1 — one or more issues found (see report)
  2 — usage / argument error (e.g. .gitignore not found)

Usage:
  python scripts/check_gitignore_health.py
  python scripts/check_gitignore_health.py --gitignore /path/to/.gitignore
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GITIGNORE = ROOT / ".gitignore"


@dataclass(frozen=True)
class ContentLine:
    """A single non-comment, non-blank .gitignore line."""

    number: int  # 1-indexed line number in the source file
    text: str  # line content with surrounding whitespace stripped


def _content_lines(raw_lines: list[str]) -> list[ContentLine]:
    """Return every non-blank, non-comment line, preserving original numbering."""
    lines = []
    for i, raw in enumerate(raw_lines, start=1):
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        lines.append(ContentLine(number=i, text=text))
    return lines


def _normalize(pattern: str) -> str:
    """Strip a single trailing slash so `foo` and `foo/` compare equal."""
    return pattern[:-1] if pattern.endswith("/") else pattern


def find_duplicate_lines(lines: list[ContentLine]) -> dict[str, list[int]]:
    """Return {pattern_text: [line_numbers]} for every pattern appearing 2+ times."""
    seen: dict[str, list[int]] = defaultdict(list)
    for line in lines:
        seen[line.text].append(line.number)
    return {text: nums for text, nums in seen.items() if len(nums) > 1}


def find_redundant_recursive_patterns(
    lines: list[ContentLine],
) -> list[tuple[ContentLine, ContentLine]]:
    """Return (recursive_line, bare_line) pairs where `**/X` is redundant.

    A `**/X` (or `**/X/`) line is redundant when a bare `X` (or `X/`) pattern —
    no leading slash, no interior slash before a single trailing one — already
    exists elsewhere in the file, since that bare pattern already matches at
    any depth.
    """
    # Index every bare, unanchored pattern that could make a `**/X` line moot.
    bare_by_normalized: dict[str, ContentLine] = {}
    for line in lines:
        if line.text.startswith(("!", "/", "**/")):
            continue  # negation / anchored / already-recursive — not a bare candidate
        normalized = _normalize(line.text)
        if "/" in normalized:
            continue  # interior slash -> anchored to this directory, not bare-recursive
        bare_by_normalized.setdefault(normalized, line)

    redundant: list[tuple[ContentLine, ContentLine]] = []
    for line in lines:
        if not line.text.startswith("**/") or line.text == "**/":
            continue
        remainder = line.text[len("**/") :]
        normalized_remainder = _normalize(remainder)
        if "/" in normalized_remainder:
            continue  # **/foo/bar — no anchored bare form is ever equivalent to this
        bare_match = bare_by_normalized.get(normalized_remainder)
        if bare_match is not None:
            redundant.append((line, bare_match))
    return redundant


def build_report(gitignore_path: Path) -> tuple[str, bool]:
    """Return (report_text, is_clean) for the given .gitignore file."""
    raw_lines = gitignore_path.read_text().splitlines()
    lines = _content_lines(raw_lines)

    duplicates = find_duplicate_lines(lines)
    redundant = find_redundant_recursive_patterns(lines)

    if not duplicates and not redundant:
        return f"gitignore health check: clean ({gitignore_path})\n", True

    parts = [f"gitignore health check: ISSUES FOUND ({gitignore_path})"]

    if duplicates:
        parts.append("\nExact-duplicate lines:")
        for text, nums in sorted(duplicates.items(), key=lambda kv: kv[1][0]):
            line_list = ", ".join(f"line {n}" for n in nums)
            parts.append(f'  {line_list}: "{text}"')

    if redundant:
        parts.append("\nRedundant `**/X` patterns (bare pattern already covers recursion):")
        for recursive_line, bare_line in sorted(redundant, key=lambda pair: pair[0].number):
            parts.append(
                f'  line {recursive_line.number}: "{recursive_line.text}" — redundant; '
                f'bare "{bare_line.text}" already present at line {bare_line.number}'
            )

    total_duplicates = sum(len(nums) - 1 for nums in duplicates.values())
    total = total_duplicates + len(redundant)
    parts.append(f"\n{total} issue(s) found.")
    return "\n".join(parts) + "\n", False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint .gitignore for exact duplicates and redundant **/X patterns"
    )
    parser.add_argument(
        "--gitignore",
        type=Path,
        default=DEFAULT_GITIGNORE,
        help="Path to the .gitignore file to check (default: repo root .gitignore)",
    )
    args = parser.parse_args(argv)

    if not args.gitignore.is_file():
        print(f"error: {args.gitignore} not found", file=sys.stderr)
        return 2

    report, is_clean = build_report(args.gitignore)
    print(report)
    return 0 if is_clean else 1


if __name__ == "__main__":
    sys.exit(main())
