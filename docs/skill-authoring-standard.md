# Skill Authoring Standard

Every `SKILL.md` in this project conforms to this contract. `scripts/verify-skills.py` enforces it
and **fails closed** — a skill that cannot be parsed is a FAIL, never a skip.

The problem this solves: a skill that says *"design a beautiful hero"* cannot be graded, so an agent
declares success and moves on. A skill that says *"the hero passes when `curl -sI` returns 200, the
LCP element is the hero image, and axe reports 0 serious violations"* can be **wrong**, and that is
the whole point. **A criterion that cannot fail is decoration.**

---

## 1. Required frontmatter

```yaml
---
name: <exactly the directory name>
description: <what it does> — Use when <concrete trigger>. Do NOT use for <the nearest wrong fit>.
---
```

- `name` **must equal the directory name.** A mismatch silently breaks invocation.
  (Real instance found 2026-07-28: `high-end-visual-design/SKILL.md` declared `name: luxury-design-taste`.)
- `description` carries the dispatch trigger. "Use when the user asks to check the design" is a
  trigger; "design skill" is not. The `Do NOT use for` clause is what stops a skill being loaded
  into every unrelated task.

## 2. Required sections

| Section | Must contain |
|---|---|
| `## When to use` | Concrete observable events, and an explicit **when NOT to** |
| `## Inputs` | What must exist before starting, and what to do when it is absent (**never proceed**) |
| `## Procedure` | Numbered, executable steps — each an action, not an intention |
| `## Verification` | ≥1 runnable command in a fenced block **and** a stated pass condition |
| `## Worked example` | A real invocation with real paths and real observed output |
| `## Failure modes` | What going wrong looks like, plus the `bug-NNN` id where one exists |

## 3. What makes a Verification section acceptable

It must be possible to **fail**. Each check states the command, the pass condition, and the evidence
tag it earns.

```bash
# GOOD — can return "no"
npx stylelint 'assets/css/**/*.css'          # PASS: exits 0, "0 problems"
curl -sI "https://skyyrose.co/?cb=$(date +%s)" | head -1   # PASS: HTTP/2 200
```

```
BAD — cannot return "no"
- "Confirm the design looks premium"
- "Ensure the code is production-ready"
- "Check that everything works"
```

**Evidence-scope tags are mandatory on every claim** (founder-mandated, bug-287):

| Tag | Means |
|---|---|
| `[live]` | probed production this session |
| `[repo]` | read the source / working tree |
| `[repro]` | ran it and observed the result |
| `[test]` | a check executed that could have failed |
| `[docs]` | Context7 / vendor documentation |
| `[inferred]` | reasoned, NOT observed — **never carries severity** |

Evidence scope must cover claim scope. These jumps are banned without their own probe:
repo state → live behavior · static finding → runtime behavior · tool output → filesystem truth ·
an audit doc → current state.

## 4. The four rules every skill inherits

1. **A gate that dies is not a gate that passed.** If a check errors, times out, or hits a session
   limit, its zero-findings output is an *artifact*. Re-verify by hand. (bug-230, ×6)
2. **A SKIP is not a PASS.** Skills that cannot execute an aspect must say so explicitly and name who
   closes it. Silent omission reads as success.
3. **Prove the check can fail.** Before trusting a new gate, break its input once and confirm it goes
   red, then restore. A gate never observed failing is a guess with a citation.
4. **Attribute before claiming a finding is yours.** Run the same gate against a pristine tree:
   `git archive HEAD <path> | tar -x -C <scratch>`. **Never `git stash`** — the stack is shared
   across worktrees. When a check fails, diff its *contents*, not its state: a new violation hides as
   one more line inside an already-red check.

## 5. Worked example — upgrading a weak criterion

**Before** (unfalsifiable):

```markdown
## Verification
Make sure the CSS is clean and the page looks right.
```

**After** (executable, and it caught a real defect):

```markdown
## Verification

1. Lint the source, not the build:
   `cd wordpress-theme && npx stylelint 'skyyrose-flagship/assets/css/**/*.css'`
   **PASS:** exits 0. `[repro]`

2. Rebuild and prove the shipped bytes match:
   `npm run build && bash skyyrose-flagship/scripts/verify-theme.sh --only min-sync`
   **PASS:** "every .min css/js byte-identical to a fresh build". `[test]`
   Production serves `.min` — a source-only edit ships nothing.

3. Confirm live: `curl -s "https://skyyrose.co/...style.css?cb=$(date +%s)" | grep -i '^Version'`
   **PASS:** matches `SKYYROSE_VERSION`. `[live]`
   Cache-bust is required — Batcache serves stale.

**Found by check 1 on 2026-07-28:** `single-product.css:24` contains `data/collections/*/sot.json`
inside a comment. The `*/` closes the comment early, and the corruption reached production —
`single-product.min.css` ships an invalid selector list, so browsers drop the rule entirely.
Harmless only because every consumer carries a `#000` fallback.
```

The second version is longer and worth it: it names *what* to run, *what* counts as passing, *what
scope* the evidence covers, and *why* each step exists. It also found a production bug.

## 6. Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| "Ensure quality" / "verify it works" | Cannot return no |
| Verification that only greps the skill's own output | Circular; the tool grading itself |
| A check requiring a browser in a headless skill | Always skips → always "passes" |
| Absent input → proceed with a default | Fail-open (bug-230). Absent input = **stop** |
| Severity asserted from `[repo]` alone | "Production bug" requires `[live]` |
| Example with invented paths | Teaches hallucination; use real, existing paths |

## 7. Enforcement

```bash
python3 scripts/verify-skills.py                 # all skill roots, exits 1 on any FAIL
python3 scripts/verify-skills.py --json          # machine-readable
python3 scripts/verify-skills.py --only <name>   # single skill
python3 scripts/verify-skills.py --root <dir>    # a specific skills directory
```

The checker is itself subject to rule 3: `--self-test` runs it against fixtures that are *known bad*
and fails if they pass.
