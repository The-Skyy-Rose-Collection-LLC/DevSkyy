#!/usr/bin/env python3
"""
.wolf/hooks/memory-audit.py — Memory-decay detector.

Scans load-bearing memory files, extracts factual claims, verifies them against
the filesystem. Purpose: catch drift between what memory says exists and what
actually does — the failure mode that wasted a session on 2026-04-20 when stale
"7 pose sprites" and "immersive-world.js" claims shaped a wrong plan.

What it checks
--------------
1. Backtick-quoted paths: does the file/dir exist at repo root?
2. Line-count claims of the form `(NNNL)` or `(NNN lines)`: does `wc -l` match ±10%?
3. `verified YYYY-MM-DD` stamps: are they within the freshness window (30d default)?
4. Entries that reference a path but have NO verification stamp → flagged as unverified.

Input files
-----------
- <repo>/.wolf/cerebrum.md
- <repo>/.wolf/anatomy.md
- <repo>/CLAUDE.md
- ~/.claude/projects/<encoded-repo-path>/memory/MEMORY.md  (if present)

Output
------
- <repo>/.wolf/memory-audit.json     (detailed report)
- stderr: one-line summary + worst-offender bullets (this lands in session context)

Exit code: 0 always (non-blocking — informational signal only).
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

REPO_ROOT = Path(os.environ.get("SKYYROSE_REPO_ROOT") or "/Users/theceo/DevSkyy")
FRESHNESS_DAYS = 30
LINE_COUNT_TOLERANCE = 0.10  # ±10%

# Dirs we skip when building the path index (noise, huge vendor trees, build output).
INDEX_SKIP_DIRS = {
    "node_modules",
    "__pycache__",
    ".venv",
    ".venv-agents",
    ".venv-imagery",
    ".git",
    "vendor",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".cache",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
}

# Section-level retired markers — if any of these appears on the same line as a
# path claim, OR in the nearest preceding header, the path is treated as
# "documented-missing" rather than "decayed missing".
RETIRED_MARKERS = re.compile(
    r"\b(retired|deprecated|historical|do not resurrect|removed|deleted)\b",
    re.IGNORECASE,
)

# Paths that are CLI examples, generic placeholders, or external — skip these.
SKIP_PREFIXES = (
    "http://",
    "https://",
    "file://",
    "ftp://",
    "~/",
    "$HOME/",
    "/Users/",  # absolute paths handled separately if needed
    "foo",
    "bar",
    "baz",
    "example.com",
    "your-",
)
SKIP_EXACT = {"path/to/file", "N/A", "TBD"}

# Substrings that mark a claim as a template/placeholder, not a real path.
SKIP_SUBSTRINGS = ("...", "YYYY", "MM-DD", "HH:MM", "<", ">", "{", "}", "*")

# Binary/asset extensions — skip line-count checks (wc -l is meaningless for these).
BINARY_EXTS = {
    ".glb",
    ".gltf",
    ".fbx",
    ".obj",
    ".usd",
    ".usdz",
    ".jpeg",
    ".jpg",
    ".png",
    ".webp",
    ".gif",
    ".avif",
    ".bmp",
    ".svg",
    ".mp3",
    ".mp4",
    ".wav",
    ".ogg",
    ".webm",
    ".mov",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".ico",
    ".icns",
}

# Extract backtick-quoted things that look like file paths.
# Must contain / OR end with a known extension (2-4 alphanumeric chars after final .).
PATH_RE = re.compile(
    r"`([A-Za-z0-9_\-./]*?"
    r"(?:/[A-Za-z0-9_\-.]+"
    r"|\.[a-zA-Z0-9]{2,4}))`"
)
LINECOUNT_RE = re.compile(r"\(\s*(\d+)\s*(?:L|lines?)\b", re.IGNORECASE)
VERIFIED_RE = re.compile(r"verified\s+(\d{4}-\d{2}-\d{2})", re.IGNORECASE)


def project_memory_dir(repo: Path) -> Path | None:
    """Return ~/.claude/projects/<encoded>/memory/ for this repo, if it exists."""
    home = Path.home()
    encoded = "-" + str(repo).replace("/", "-").lstrip("-")
    candidate = home / ".claude" / "projects" / encoded / "memory"
    return candidate if candidate.is_dir() else None


def target_files(repo: Path) -> list[Path]:
    files: list[Path] = []
    for rel in (".wolf/cerebrum.md", ".wolf/anatomy.md", "CLAUDE.md"):
        p = repo / rel
        if p.is_file():
            files.append(p)
    pmd = project_memory_dir(repo)
    if pmd:
        files.extend(sorted(pmd.glob("*.md")))
    return files


def should_skip_path(p: str) -> bool:
    if p in SKIP_EXACT:
        return True
    if any(p.startswith(pref) for pref in SKIP_PREFIXES):
        return True
    if any(s in p for s in SKIP_SUBSTRINGS):
        return True
    # Bare extensions like ".py" or "./x" aren't real claims.
    if p.startswith(".") and "/" not in p and len(p) < 5:
        return True
    return False


def wc_l(p: Path) -> int:
    try:
        with p.open("rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return -1


def build_path_index(repo: Path) -> dict[str, list[str]]:
    """Build a basename -> [rel_path, ...] index of the repo for suffix matching.

    Lets us resolve `inc/product-catalog.php` when the actual location is
    `wordpress-theme/skyyrose-flagship/inc/product-catalog.php` — a memory
    claim made in-context is still valid.
    """
    index: dict[str, list[str]] = {}
    for root, dirs, files in os.walk(repo):
        dirs[:] = [
            d
            for d in dirs
            if d not in INDEX_SKIP_DIRS
            and not d.startswith(".")
            or d in (".wolf", ".claude", ".planning", ".ralph")
        ]
        rel_root = os.path.relpath(root, repo)
        for name in files + dirs:
            rel = name if rel_root == "." else f"{rel_root}/{name}"
            index.setdefault(name, []).append(rel)
    return index


def resolve_claim(claim: str, repo: Path, index: dict[str, list[str]]) -> str | None:
    """Return a real relative path if the claim resolves, else None.

    Strategy:
      1. Exact match at repo root.
      2. Suffix match anywhere in the index (path mentioned in a sub-context).
      3. Basename-only match if claim has no slashes.
    """
    target = repo / claim
    if target.exists():
        return claim

    basename = claim.rsplit("/", 1)[-1]
    candidates = index.get(basename, [])
    # Prefer paths that end with the full claim (handles suffix match).
    for c in candidates:
        if c == claim or c.endswith("/" + claim):
            return c
    # If claim had no slashes, any basename hit is good enough.
    if "/" not in claim and candidates:
        return candidates[0]
    return None


def audit_file(src: Path, repo: Path, index: dict[str, list[str]]) -> dict:
    """Audit one memory file. Return structured findings."""
    text = src.read_text(encoding="utf-8", errors="replace")
    in_fence = False
    fence_re = re.compile(r"^```")

    missing_paths: list[dict] = []
    verified_paths: list[dict] = []
    linecount_mismatches: list[dict] = []
    stale_stamps: list[dict] = []
    fresh_stamps: list[dict] = []
    documented_missing: list[dict] = []  # path doesn't exist BUT line says "retired" etc.

    for lineno, line in enumerate(text.splitlines(), start=1):
        # Skip inside fenced code blocks — those are examples, not claims.
        if fence_re.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        # Freshness stamps.
        for m in VERIFIED_RE.finditer(line):
            try:
                stamp = datetime.strptime(m.group(1), "%Y-%m-%d").date()
            except ValueError:
                continue
            age_days = (date.today() - stamp).days
            record = {
                "file": str(src.relative_to(repo)) if src.is_relative_to(repo) else str(src),
                "line": lineno,
                "stamp": m.group(1),
                "age_days": age_days,
            }
            (fresh_stamps if age_days <= FRESHNESS_DAYS else stale_stamps).append(record)

        # Path claims — only in backticks, only if they look like a real path.
        claimed_line_count: int | None = None
        lcmatch = LINECOUNT_RE.search(line)
        if lcmatch:
            claimed_line_count = int(lcmatch.group(1))

        line_is_retired_context = bool(RETIRED_MARKERS.search(line))
        file_rel = str(src.relative_to(repo)) if src.is_relative_to(repo) else str(src)

        for m in PATH_RE.finditer(line):
            claim = m.group(1).strip()
            if should_skip_path(claim):
                continue
            if claim.startswith("/"):
                continue  # absolute external path — skip for this audit

            resolved = resolve_claim(claim, repo, index)
            entry = {"file": file_rel, "line": lineno, "claim": claim}

            if resolved is None:
                # Decayed claim — UNLESS the line explicitly documents removal.
                if line_is_retired_context:
                    documented_missing.append(entry)
                else:
                    missing_paths.append(entry)
                continue

            # Resolved — record and optionally check line count.
            entry["resolved"] = resolved
            resolved_path = repo / resolved
            is_binary = resolved_path.suffix.lower() in BINARY_EXTS
            if claimed_line_count is not None and resolved_path.is_file() and not is_binary:
                actual = wc_l(resolved_path)
                if actual > 0:
                    drift = abs(actual - claimed_line_count) / actual
                    if drift > LINE_COUNT_TOLERANCE:
                        linecount_mismatches.append(
                            {
                                **entry,
                                "claimed": claimed_line_count,
                                "actual": actual,
                                "drift_pct": round(drift * 100, 1),
                            }
                        )
            verified_paths.append(entry)

    return {
        "missing_paths": missing_paths,
        "verified_paths": verified_paths,
        "linecount_mismatches": linecount_mismatches,
        "stale_stamps": stale_stamps,
        "fresh_stamps": fresh_stamps,
        "documented_missing": documented_missing,
    }


def main() -> int:
    sources = target_files(REPO_ROOT)
    index = build_path_index(REPO_ROOT)
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "repo_root": str(REPO_ROOT),
        "freshness_days": FRESHNESS_DAYS,
        "files_scanned": len(sources),
        "indexed_basenames": len(index),
        "missing_paths": [],
        "linecount_mismatches": [],
        "stale_stamps": [],
        "fresh_stamps": [],
        "documented_missing_count": 0,
        "verified_count": 0,
    }

    for src in sources:
        try:
            findings = audit_file(src, REPO_ROOT, index)
        except Exception as exc:  # noqa: BLE001 — audit must never crash the session
            findings = {"error": f"{type(exc).__name__}: {exc}"}
        if "error" in findings:
            continue
        report["missing_paths"].extend(findings["missing_paths"])
        report["linecount_mismatches"].extend(findings["linecount_mismatches"])
        report["stale_stamps"].extend(findings["stale_stamps"])
        report["fresh_stamps"].extend(findings["fresh_stamps"])
        report["verified_count"] += len(findings["verified_paths"])
        report["documented_missing_count"] += len(findings["documented_missing"])

    # Write detailed report.
    out_path = REPO_ROOT / ".wolf" / "memory-audit.json"
    out_path.write_text(json.dumps(report, indent=2))

    # Short stderr summary — this is what lands in the session context.
    issues = (
        len(report["missing_paths"])
        + len(report["linecount_mismatches"])
        + len(report["stale_stamps"])
    )
    summary = (
        f"[memory-audit] {report['generated_at']} — "
        f"scanned {report['files_scanned']} files, {report['verified_count']} path claims verified"
    )
    print(summary, file=sys.stderr)
    if issues == 0:
        print("  OK — no decay detected.", file=sys.stderr)
    else:
        for item in report["missing_paths"][:5]:
            print(
                f"  MISSING  {item['file']}:{item['line']}  `{item['claim']}` does not exist",
                file=sys.stderr,
            )
        for item in report["linecount_mismatches"][:5]:
            print(
                f"  DRIFT    {item['file']}:{item['line']}  `{item['claim']}` "
                f"claims {item['claimed']}L, actual {item['actual']}L ({item['drift_pct']}%)",
                file=sys.stderr,
            )
        for item in report["stale_stamps"][:3]:
            print(
                f"  STALE    {item['file']}:{item['line']}  "
                f"verified {item['stamp']} ({item['age_days']}d ago) — re-verify",
                file=sys.stderr,
            )
        if issues > 13:
            print(f"  ... +{issues - 13} more issues in .wolf/memory-audit.json", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
