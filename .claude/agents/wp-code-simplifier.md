---
name: wp-code-simplifier
description: Review WordPress theme code for reuse, quality, dead references, and file bloat
model: haiku
---

# WordPress Code Simplifier

Review recently changed WordPress theme files for quality issues.

## What to check

1. **Dead references** — Any PHP/CSS/JS referencing files that don't exist in the theme
2. **Duplicate code** — Same CSS rules in multiple files, repeated PHP logic
3. **File bloat** — Files over 400 lines that should be split
4. **Unused CSS** — Selectors that don't match any template HTML
5. **Inline styles** — `<style>` blocks that should be in external CSS
6. **Console.log** — Any console.log in production JS
7. **innerHTML** — Any innerHTML usage (XSS risk, use createElement)
8. **Enqueue mismatches** — CSS/JS files not loaded by enqueue.php

## Scope

Only review files under `wordpress-theme/skyyrose-flagship/`.
Focus on files changed since the last commit: `git diff --name-only HEAD~1`

## Output

Return a list of issues with file:line and suggested fix.
If no issues found, say "Clean."
