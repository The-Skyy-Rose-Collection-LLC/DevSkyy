#!/usr/bin/env python3
"""Filter .wolf/anatomy.md to entries tracked on git main.

Pipeline: openwolf scan writes the full filesystem anatomy, this script
post-filters it to only files reachable from the `main` ref (canonical branch).
Section headers that lose all their entries are removed.

Source-of-truth ref order:
  1. `origin/main`  -- preferred (remote canonical)
  2. `main`         -- fallback (local tip)

Sandbox-friendly: writes back to .wolf/anatomy.md in place. No network calls.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANATOMY = REPO / ".wolf" / "anatomy.md"

ENTRY_RE = re.compile(r"^- `([^`]+)`")
SECTION_RE = re.compile(r"^## (.+?)/?\s*$")


def _git_ls_tree(ref: str) -> set[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", ref, "--name-only"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def canonical_files() -> tuple[set[str], str]:
    main_files = _git_ls_tree("main")
    origin_files = _git_ls_tree("origin/main")
    union = main_files | origin_files
    if not union:
        raise RuntimeError("Neither main nor origin/main resolved to any files")
    if main_files and origin_files:
        ref = "main ∪ origin/main"
    elif main_files:
        ref = "main"
    else:
        ref = "origin/main"
    return union, ref


def _section_dir(header: str) -> str:
    match = SECTION_RE.match(header)
    if not match:
        return ""
    raw = match.group(1).strip()
    return "" if raw in ("./", ".") else raw


def filter_anatomy(text: str, allowed: set[str]) -> tuple[str, int, int]:
    lines = text.splitlines()
    out: list[str] = []
    section_start: int | None = None
    section_dir = ""
    section_kept_any = False
    kept_entries = 0
    dropped_entries = 0

    def close_section() -> None:
        nonlocal section_start, section_kept_any
        if section_start is not None and not section_kept_any:
            del out[section_start:]
        section_start = None
        section_kept_any = False

    for line in lines:
        if line.startswith("## "):
            close_section()
            section_dir = _section_dir(line)
            section_start = len(out)
            section_kept_any = False
            out.append(line)
            continue

        entry_match = ENTRY_RE.match(line)
        if entry_match and section_start is not None:
            basename = entry_match.group(1)
            rel = f"{section_dir}/{basename}" if section_dir else basename
            if rel not in allowed:
                dropped_entries += 1
                continue
            kept_entries += 1
            section_kept_any = True
            out.append(line)
            continue

        out.append(line)

    close_section()

    while out and out[-1].strip() == "":
        out.pop()

    return "\n".join(out) + "\n", kept_entries, dropped_entries


def update_header_files_count(text: str, count: int, ref: str) -> str:
    return re.sub(
        r"^> Files: \d+ tracked \| Anatomy hits: \d+ \| Misses: \d+$",
        f"> Files: {count} tracked on {ref} | Anatomy hits: 0 | Misses: 0",
        text,
        count=1,
        flags=re.MULTILINE,
    )


def main() -> int:
    if not ANATOMY.exists():
        print(f"anatomy missing: {ANATOMY}", file=sys.stderr)
        return 1

    allowed, ref = canonical_files()
    text = ANATOMY.read_text()
    filtered, kept, dropped = filter_anatomy(text, allowed)
    filtered = update_header_files_count(filtered, kept, ref)
    ANATOMY.write_text(filtered)
    print(f"anatomy filtered to {ref}: kept={kept} dropped={dropped} canonical={len(allowed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
