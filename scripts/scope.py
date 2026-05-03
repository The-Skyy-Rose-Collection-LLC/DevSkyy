#!/usr/bin/env python3
"""scope - file-to-branch scope router for DevSkyy.

Reads .devskyy/scopes.toml and classifies dirty working-tree files into the
PR/branch they belong to. Prevents kitchen-sink branches by surfacing scope
violations at commit time.

USAGE
    scope status [-v]         Show working tree grouped by scope.
    scope of PATH             Show which scope a single path maps to.
    scope ls [SCOPE]          List scopes (or paths within one scope).
    scope check-staged        Pre-commit hook: fail if staged files span >1 scope.
    scope split --plan        Show the branch split that --execute would perform.
    scope split --execute     Reserved (not implemented; use --plan + manual git).

CONFIG
    .devskyy/scopes.toml at repo root. First-match-wins; declare specific scopes
    before general ones.

EXIT CODES
    0  success / clean
    1  uncategorized files present, or check-staged found cross-scope commit
    2  config error or unimplemented operation
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCOPES_TOML = REPO_ROOT / ".devskyy" / "scopes.toml"
DEFAULT_SCOPE = "_uncategorized"
IGNORE_SCOPE_NAME = "ignore"


@dataclass
class Scope:
    name: str
    description: str = ""
    branch_prefix: str | None = None
    paths: list[str] = field(default_factory=list)
    depends_on_commits: list[str] = field(default_factory=list)
    add_to_gitignore: bool = False


# ---------------------------------------------------------------------------
# Glob matching (stdlib only — no pathspec dep)
# ---------------------------------------------------------------------------


def _expand_braces(pattern: str) -> list[str]:
    """Expand {a,b,c} alternatives to multiple flat patterns."""
    m = re.search(r"\{([^{}]+)\}", pattern)
    if not m:
        return [pattern]
    options = m.group(1).split(",")
    expanded = [pattern[: m.start()] + opt + pattern[m.end() :] for opt in options]
    out: list[str] = []
    for p in expanded:
        out.extend(_expand_braces(p))
    return out


def _glob_to_regex(pattern: str) -> str:
    """Convert gitignore-style glob to a regex anchored at both ends.

    Semantics:
        **      matches anything including /
        *       matches anything except /
        ?       matches one character except /
        [seq]   character class (passed through)
    """
    out: list[str] = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if i + 1 < len(pattern) and pattern[i + 1] == "*":
                out.append(".*")
                i += 2
                if i < len(pattern) and pattern[i] == "/":
                    i += 1
            else:
                out.append("[^/]*")
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        elif c == "[":
            j = pattern.find("]", i)
            if j == -1:
                out.append(re.escape(c))
                i += 1
            else:
                out.append(pattern[i : j + 1])
                i = j + 1
        else:
            out.append(re.escape(c))
            i += 1
    return "^" + "".join(out) + "$"


_compiled: dict[str, re.Pattern[str]] = {}


def _matches(pattern: str, path: str) -> bool:
    for expanded in _expand_braces(pattern):
        if expanded not in _compiled:
            _compiled[expanded] = re.compile(_glob_to_regex(expanded))
        if _compiled[expanded].match(path):
            return True
    return False


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_scopes() -> dict[str, Scope]:
    if not SCOPES_TOML.exists():
        sys.exit(f"error: {SCOPES_TOML.relative_to(REPO_ROOT)} not found")
    try:
        with SCOPES_TOML.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        sys.exit(f"error: {SCOPES_TOML.relative_to(REPO_ROOT)} is not valid TOML: {e}")

    scopes_raw = data.get("scope", {})
    if not scopes_raw:
        sys.exit(f"error: {SCOPES_TOML.relative_to(REPO_ROOT)} has no [scope.*] entries")

    scopes: dict[str, Scope] = {}
    for name, cfg in scopes_raw.items():
        scopes[name] = Scope(
            name=name,
            description=cfg.get("description", ""),
            branch_prefix=cfg.get("branch_prefix"),
            paths=list(cfg.get("paths", [])),
            depends_on_commits=list(cfg.get("depends_on_commits", [])),
            add_to_gitignore=bool(cfg.get("add_to_gitignore", False)),
        )
    return scopes


def classify(path: str, scopes: dict[str, Scope]) -> str:
    for name, scope in scopes.items():
        for pattern in scope.paths:
            if _matches(pattern, path):
                return name
    return DEFAULT_SCOPE


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    return result.stdout


def git_dirty_files() -> list[tuple[str, str]]:
    """Return [(status, path)] for every file that differs from HEAD or is untracked.

    Status codes: M (modified), A (added/untracked), D (deleted), R (renamed).
    """
    files: list[tuple[str, str]] = []
    seen: set[str] = set()

    diff_ns = _git("diff", "HEAD", "--name-status")
    for line in diff_ns.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0][0]
        path = parts[-1]
        if path not in seen:
            seen.add(path)
            files.append((status, path))

    untracked = _git("ls-files", "--others", "--exclude-standard")
    for path in untracked.splitlines():
        if path and path not in seen:
            seen.add(path)
            files.append(("?", path))

    return files


def git_staged_files() -> list[str]:
    return [p for p in _git("diff", "--name-only", "--cached").splitlines() if p]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_status(args: argparse.Namespace) -> int:
    scopes = load_scopes()
    files = git_dirty_files()
    if not files:
        print("Working tree clean.")
        return 0

    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for status, path in files:
        grouped[classify(path, scopes)].append((status, path))

    print(f"Working tree: {len(files)} files\n")

    order = list(scopes.keys()) + [DEFAULT_SCOPE]
    has_uncat = DEFAULT_SCOPE in grouped
    exit_code = 1 if has_uncat else 0

    for scope_name in order:
        if scope_name not in grouped:
            continue
        scope_files = grouped[scope_name]
        scope = scopes.get(scope_name)
        branch = scope.branch_prefix if scope and scope.branch_prefix else "—"
        flag = ""
        if scope_name == DEFAULT_SCOPE:
            flag = "  ⚠️  no matching scope — add to .devskyy/scopes.toml"
        elif scope and scope.add_to_gitignore:
            flag = "  (gitignore — should not commit)"
        print(f"  {scope_name:24} {len(scope_files):4} files  → {branch}{flag}")
        if args.verbose or scope_name == DEFAULT_SCOPE:
            for status, path in sorted(scope_files):
                print(f"      {status} {path}")

    if has_uncat:
        print(
            f"\nexit 1: {len(grouped[DEFAULT_SCOPE])} uncategorized file(s). "
            "Add path globs to .devskyy/scopes.toml."
        )
    return exit_code


def cmd_of(args: argparse.Namespace) -> int:
    scopes = load_scopes()
    name = classify(args.path, scopes)
    if name == DEFAULT_SCOPE:
        print(f"{args.path}\n  → _uncategorized (no matching scope in scopes.toml)")
        return 1
    scope = scopes[name]
    branch = scope.branch_prefix or "no branch"
    print(f"{args.path}\n  → {name} ({branch})")
    if scope.description:
        print(f"     {scope.description}")
    return 0


def cmd_ls(args: argparse.Namespace) -> int:
    scopes = load_scopes()
    if args.scope:
        if args.scope not in scopes:
            sys.exit(f"unknown scope: {args.scope}")
        scope = scopes[args.scope]
        print(f"# scope: {args.scope}")
        print(f"# {scope.description}")
        print(f"# branch_prefix: {scope.branch_prefix or '(none)'}")
        if scope.depends_on_commits:
            print(f"# depends_on_commits: {', '.join(scope.depends_on_commits)}")
        if scope.add_to_gitignore:
            print("# add_to_gitignore: true")
        print()
        for p in scope.paths:
            print(p)
        return 0

    print(f"Configured scopes ({len(scopes)}):\n")
    for name, scope in scopes.items():
        branch = scope.branch_prefix or "—"
        print(f"  {name:24} {len(scope.paths):3} patterns  → {branch}")
        if scope.description:
            print(f"  {' ' * 24}  {scope.description}")
    return 0


def cmd_check_staged(args: argparse.Namespace) -> int:
    scopes = load_scopes()
    staged = git_staged_files()
    if not staged:
        return 0

    found: dict[str, list[str]] = defaultdict(list)
    for path in staged:
        s = classify(path, scopes)
        if s == IGNORE_SCOPE_NAME:
            print(
                f"error: staged file {path!r} is in 'ignore' scope (should not be committed)",
                file=sys.stderr,
            )
            return 1
        found[s].append(path)

    if len(found) <= 1:
        return 0

    print("error: staged files span multiple scopes:\n", file=sys.stderr)
    for s, paths in sorted(found.items()):
        print(f"  [{s}]", file=sys.stderr)
        for p in paths:
            print(f"      {p}", file=sys.stderr)
    print(
        "\nKeep one scope per commit. Either:\n"
        "  - unstage the off-scope files: git restore --staged <file>\n"
        "  - or add --multi-scope to your commit message if intentional",
        file=sys.stderr,
    )
    return 1


def cmd_split(args: argparse.Namespace) -> int:
    scopes = load_scopes()
    files = git_dirty_files()
    if not files:
        print("Working tree clean — nothing to split.")
        return 0

    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for status, path in files:
        grouped[classify(path, scopes)].append((status, path))

    if args.plan:
        print("# scope split --plan")
        print(f"# {len(files)} dirty files across {len(grouped)} scope(s)\n")

        for name, scope in scopes.items():
            if name not in grouped:
                continue
            scope_files = grouped[name]
            if scope.add_to_gitignore:
                print(f"## SKIP [{name}] — {len(scope_files)} files match 'ignore' scope")
                print("  → add to .gitignore, do not commit")
                for status, path in sorted(scope_files):
                    print(f"      {status} {path}")
                print()
                continue
            if not scope.branch_prefix:
                continue
            print(f"## Branch: {scope.branch_prefix}")
            print(f"   ({scope.description})")
            if scope.depends_on_commits:
                for sha in scope.depends_on_commits:
                    print(f"   cherry-pick {sha}")
            for status, path in sorted(scope_files):
                print(f"      {status} {path}")
            print()

        if DEFAULT_SCOPE in grouped:
            uncat = grouped[DEFAULT_SCOPE]
            print(f"## ⚠️  UNCATEGORIZED ({len(uncat)} files) — no branch")
            for status, path in sorted(uncat):
                print(f"      {status} {path}")
            print("\nAdd matching globs to .devskyy/scopes.toml then re-run.")
            return 1
        return 0

    print(
        "scope split --execute is reserved.\n"
        "Use --plan to see the split, then apply commits manually.\n"
        "Auto-execute is intentionally deferred until the system has bedded in.",
        file=sys.stderr,
    )
    return 2


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scope",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_status = sub.add_parser("status", help="show working tree grouped by scope")
    p_status.add_argument("-v", "--verbose", action="store_true", help="list every file")
    p_status.set_defaults(func=cmd_status)

    p_of = sub.add_parser("of", help="show which scope a path belongs to")
    p_of.add_argument("path")
    p_of.set_defaults(func=cmd_of)

    p_ls = sub.add_parser("ls", help="list scopes or paths within a scope")
    p_ls.add_argument("scope", nargs="?")
    p_ls.set_defaults(func=cmd_ls)

    p_check = sub.add_parser(
        "check-staged",
        help="pre-commit: fail if staged files span >1 scope or include ignore-scope files",
    )
    p_check.set_defaults(func=cmd_check_staged)

    p_split = sub.add_parser("split", help="show or execute branch split")
    grp = p_split.add_mutually_exclusive_group(required=True)
    grp.add_argument("--plan", action="store_true", help="show what --execute would do")
    grp.add_argument("--execute", action="store_true", help="(reserved) create branches + commits")
    p_split.set_defaults(func=cmd_split)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
