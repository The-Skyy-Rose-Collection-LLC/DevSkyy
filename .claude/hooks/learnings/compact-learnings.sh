#!/bin/bash
# compact-learnings.sh — cap + archive: when a CLAUDE.md Learnings subsection
# has more than N bullets, move the oldest chunk to docs/learnings-archive/.
#
# Invoked by /promote-learnings after insertion (not as a PostToolUse hook —
# we don't want it running on every edit).
#
# Usage: compact-learnings.sh [threshold]
#   threshold: max bullets per subsection (default 75)
set -eu

THRESHOLD="${1:-75}"
ARCHIVE_BATCH=25

repo=$(git rev-parse --show-toplevel 2>/dev/null || { echo "not in a repo" >&2; exit 1; })
claude_md="$repo/CLAUDE.md"
archive_dir="$repo/docs/learnings-archive"
mkdir -p "$archive_dir"

if [ ! -f "$claude_md" ]; then
  echo "[compact-learnings] CLAUDE.md not found" >&2
  exit 1
fi

# Extract every marker-wrapped subsection and count bullets
python3 - "$claude_md" "$THRESHOLD" "$ARCHIVE_BATCH" "$archive_dir" <<'PY'
import sys, re, pathlib, datetime

claude_md = pathlib.Path(sys.argv[1])
threshold = int(sys.argv[2])
batch = int(sys.argv[3])
archive_dir = pathlib.Path(sys.argv[4])

text = claude_md.read_text(encoding="utf-8")

# Find all <!-- learnings:NAME --> ... <!-- /learnings:NAME --> blocks
pattern = re.compile(
    r"<!--\s*learnings:([a-z0-9\-]+)\s*-->(.*?)<!--\s*/learnings:\1\s*-->",
    re.DOTALL
)

q = (datetime.date.today().month - 1) // 3 + 1
year = datetime.date.today().year
quarter_tag = f"{year}-Q{q}"
today = datetime.date.today().isoformat()

changed = False
new_text = text

for m in list(pattern.finditer(text)):
    name, body = m.group(1), m.group(2)
    bullets = [ln for ln in body.splitlines() if ln.lstrip().startswith("- ")]
    if len(bullets) <= threshold:
        continue

    # Move oldest `batch` bullets to archive. "Oldest" = first in subsection.
    move = bullets[:batch]
    keep = bullets[batch:]

    # Archive file path
    archive_path = archive_dir / f"{quarter_tag}-{name}.md"
    header = (
        f"# {name.replace('-', ' ').title()} Learnings — {quarter_tag}\n\n"
        f"<!-- archived:{today} -->\n"
        f"<!-- source: CLAUDE.md learnings:{name} -->\n\n"
    )
    if not archive_path.exists():
        archive_path.write_text(header, encoding="utf-8")
    # Append with date prefix
    with archive_path.open("a", encoding="utf-8") as f:
        for ln in move:
            stripped = ln.lstrip()[2:].rstrip()
            f.write(f"- {today} · {stripped}\n")

    # Rebuild the subsection body: keep non-bullet lines + surviving bullets
    non_bullets = []
    in_header = True
    for ln in body.splitlines():
        if ln.lstrip().startswith("- "):
            in_header = False
            continue
        if in_header or ln.strip() == "":
            non_bullets.append(ln)
    # Put the kept bullets back in order
    new_body_lines = []
    # start with leading blank + heading lines (non_bullets until first blank run)
    new_body_lines.extend(non_bullets)
    if keep and (not new_body_lines or new_body_lines[-1].strip() != ""):
        pass
    new_body_lines.extend(keep)
    # Add archive pointer if first-time archived
    pointer = f"> Older learnings: [{archive_path.relative_to(claude_md.parent)}](./{archive_path.relative_to(claude_md.parent)})"
    if pointer not in new_body_lines:
        new_body_lines.append("")
        new_body_lines.append(pointer)
    new_body = "\n".join(new_body_lines) + "\n"

    replacement = f"<!-- learnings:{name} -->{new_body}<!-- /learnings:{name} -->"
    new_text = new_text.replace(m.group(0), replacement, 1)
    changed = True
    print(f"[compact-learnings] archived {len(move)} bullets from {name} to {archive_path.name}", file=sys.stderr)

if changed:
    claude_md.write_text(new_text, encoding="utf-8")
    print("[compact-learnings] CLAUDE.md updated", file=sys.stderr)
else:
    print(f"[compact-learnings] no subsection exceeded {threshold} bullets", file=sys.stderr)
PY
