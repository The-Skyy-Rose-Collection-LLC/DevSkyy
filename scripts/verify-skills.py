#!/usr/bin/env python3
"""Conformance gate for SKILL.md files — see docs/skill-authoring-standard.md.

Fails CLOSED by design: an unreadable, unparseable, or absent SKILL.md is a FAIL, never a skip.
A gate that quietly passes when its input is missing is the fail-open defect this repo has hit
six times (bug-230), and a skills gate is exactly where it would hide.

Usage:
    python3 scripts/verify-skills.py [--root DIR ...] [--only NAME] [--json] [--self-test]

Exit codes: 0 = every skill conforms · 1 = at least one FAIL · 2 = the gate itself is broken.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

DEFAULT_ROOTS = [
    REPO / ".claude" / "skills",
    Path.home() / ".claude" / "skills",
]

# Section -> regex that must match a heading line. Tolerant of wording so the gate checks for the
# CONTRACT, not for one blessed phrasing ("## Verify" and "## Verification" both count).
REQUIRED_SECTIONS = {
    "when-to-use": r"^#+\s*.*\bwhen\s+to\s+use\b",
    "inputs": r"^#+\s*.*\b(inputs?|prerequisites?|required\s+before)\b",
    "procedure": r"^#+\s*.*\b(procedure|steps|workflow|how\s+to)\b",
    "verification": r"^#+\s*.*\b(verif\w*|acceptance|proof)\b",
    "example": r"^#+\s*.*\bexamples?\b",
    "failure-modes": r"^#+\s*.*\b(failure\s+modes?|anti-?patterns?|gotchas?|common\s+mistakes?)\b",
}

# A Verification section must contain a command that can actually be run...
COMMAND_RE = re.compile(
    r"```[a-z]*\n.*?(?:curl|npm|npx|python3?|pytest|php|git|grep|bash|node|composer|vendor/bin|"
    r"rtk|wp |make |stylelint|phpstan|phpcs|vitest|playwright)\b.*?```",
    re.S | re.I,
)
# ...and state what counts as passing. Without this a command block is a suggestion, not a gate.
PASS_COND_RE = re.compile(
    r"\b(PASS|expect(?:ed)?|must (?:be|equal|return|exit)|exits? 0|→)\b", re.I
)

# Unfalsifiable phrasing: reads like a check, cannot return "no".
VAGUE_RE = re.compile(
    r"\b(?:make sure|ensure|confirm|check) (?:it|that )?(?:everything|it all|the code|things)?\s*"
    r"(?:works|is (?:clean|correct|good|fine|production[- ]ready)|looks (?:right|good|premium))",
    re.I,
)

TRIGGER_RE = re.compile(r"\buse (?:this )?(?:skill )?when\b", re.I)
EVIDENCE_TAGS = ("[live]", "[repo]", "[repro]", "[test]", "[docs]", "[inferred]")


@dataclass
class Result:
    name: str
    path: str
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Minimal YAML-ish frontmatter reader. No PyYAML dependency — this gate must run anywhere."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw, body = text[3:end], text[end + 4 :]
    meta: dict[str, str] = {}
    key = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            meta[key] = m.group(2).strip()
        elif key and line.startswith((" ", "\t", ">")):
            meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta, body


def strip_code_blocks(body: str) -> str:
    """Headings inside fenced examples are illustrations, not this skill's own sections."""
    return re.sub(r"```.*?```", "", body, flags=re.S)


def check_skill(d: Path) -> Result:
    r = Result(name=d.name, path=str(d))
    f = d / "SKILL.md"

    if not f.is_file():
        r.failures.append("no SKILL.md")
        return r
    try:
        text = f.read_text(encoding="utf-8")
    except Exception as e:  # unreadable == FAIL, never skip
        r.failures.append(f"unreadable: {e.__class__.__name__}: {e}")
        return r
    if not text.strip():
        r.failures.append("SKILL.md is empty")
        return r

    meta, body = split_frontmatter(text)
    if not meta:
        r.failures.append("missing YAML frontmatter")
    else:
        declared = meta.get("name", "")
        if not declared:
            r.failures.append("frontmatter has no `name`")
        elif declared != d.name:
            # Real instance: high-end-visual-design declared name: luxury-design-taste.
            r.failures.append(f"name mismatch: declares `{declared}`, directory is `{d.name}`")
        desc = meta.get("description", "")
        if not desc:
            r.failures.append("frontmatter has no `description`")
        else:
            if not TRIGGER_RE.search(desc):
                r.failures.append("description states no dispatch trigger (needs 'Use when …')")
            if not re.search(r"\b(do not use|don't use|not for|skip (?:this )?for)\b", desc, re.I):
                r.warnings.append("description has no 'Do NOT use for …' clause")

    scan = strip_code_blocks(body)
    for label, pattern in REQUIRED_SECTIONS.items():
        if not re.search(pattern, scan, re.I | re.M):
            r.failures.append(f"missing section: {label}")

    # Verification section is the load-bearing one — inspect its contents, not just its heading.
    m = re.search(REQUIRED_SECTIONS["verification"], body, re.I | re.M)
    if m:
        start = m.start()
        nxt = re.search(r"^#{1,3}\s", body[start + 1 :], re.M)
        section = body[start : start + 1 + nxt.start()] if nxt else body[start:]
        if not COMMAND_RE.search(section):
            r.failures.append("verification section has no runnable command block")
        if not PASS_COND_RE.search(section):
            r.failures.append("verification section states no pass condition")
        if not any(t in section for t in EVIDENCE_TAGS):
            r.warnings.append("verification section carries no evidence-scope tag")

    for bad in VAGUE_RE.findall(scan):
        r.failures.append(f"unfalsifiable criterion: {bad!r}")

    if "```" not in body:
        r.failures.append("no code/command block anywhere — example cannot be concrete")

    return r


def iter_skills(roots: list[Path], only: str | None):
    seen: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for d in sorted(p for p in root.iterdir() if p.is_dir()):
            if only and d.name != only:
                continue
            key = f"{root}:{d.name}"
            if key in seen:
                continue
            seen.add(key)
            yield d


SELF_TEST_CASES = [
    ("no-frontmatter", "# Just a heading\n", "missing YAML frontmatter"),
    (
        "name-mismatch",
        "---\nname: something-else\ndescription: Does things. Use when asked.\n---\n# X\n```sh\ntrue\n```\n",
        "name mismatch",
    ),
    (
        "vague-criterion",
        "---\nname: vague-criterion\ndescription: Does things. Use when asked.\n---\n"
        "## When to use\nx\n## Inputs\nx\n## Procedure\nx\n"
        "## Verification\nMake sure everything works.\n## Example\nx\n## Failure modes\nx\n```sh\ntrue\n```\n",
        "unfalsifiable criterion",
    ),
    (
        "no-pass-condition",
        "---\nname: no-pass-condition\ndescription: Does things. Use when asked.\n---\n"
        "## When to use\nx\n## Inputs\nx\n## Procedure\nx\n"
        "## Verification\n```sh\nnpm run build\n```\n## Example\nx\n## Failure modes\nx\n",
        "states no pass condition",
    ),
]


def self_test() -> int:
    """Rule 3 applied to this gate: prove it still returns NO for known-bad input."""
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, content, expect in SELF_TEST_CASES:
            d = root / name
            d.mkdir()
            (d / "SKILL.md").write_text(content)
            res = check_skill(d)
            if res.ok:
                problems.append(f"{name}: expected FAIL, got PASS")
            elif not any(expect in f for f in res.failures):
                problems.append(f"{name}: expected {expect!r}, got {res.failures}")
        # A missing SKILL.md must fail, not skip.
        (root / "empty-dir").mkdir()
        if check_skill(root / "empty-dir").ok:
            problems.append("empty-dir: expected FAIL (fail-closed), got PASS")

    for p in problems:
        print(f"SELF-TEST BROKEN: {p}", file=sys.stderr)
    if problems:
        return 2
    print(f"self-test: {len(SELF_TEST_CASES) + 1} known-bad fixtures all correctly FAILED")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", action="append", type=Path, help="skills dir (repeatable)")
    ap.add_argument("--only", help="check a single skill by name")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()

    roots = a.root or DEFAULT_ROOTS
    if not any(r.is_dir() for r in roots):
        print(f"ERROR: no skills root exists among {[str(r) for r in roots]}", file=sys.stderr)
        return 2  # absent input is a broken gate, not a pass

    results = [check_skill(d) for d in iter_skills(roots, a.only)]
    if not results:
        print("ERROR: zero skills found — refusing to report success", file=sys.stderr)
        return 2

    failed = [r for r in results if not r.ok]
    warned = [r for r in results if r.ok and r.warnings]

    if a.json:
        print(
            json.dumps(
                {
                    "total": len(results),
                    "passed": len(results) - len(failed),
                    "failed": len(failed),
                    "results": [
                        {
                            "name": r.name,
                            "path": r.path,
                            "ok": r.ok,
                            "failures": r.failures,
                            "warnings": r.warnings,
                        }
                        for r in results
                    ],
                },
                indent=2,
            )
        )
        return 1 if failed else 0

    for r in failed:
        print(f"FAIL  {r.name}")
        for f in r.failures:
            print(f"        - {f}")
    for r in warned:
        print(f"WARN  {r.name}: {'; '.join(r.warnings)}")

    print(
        f"\n{len(results) - len(failed)}/{len(results)} skills conform to "
        f"docs/skill-authoring-standard.md"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
