# Lessons Learned

Patterns extracted from corrections. Review at session start.

## WordPress Theme
- CDN caches CSS aggressively — always bump `SKYYROSE_VERSION` for cache bust
- WordPress.com `page-optimize` plugin strips enqueued JS — inline JS in templates to bypass
- `enqueue.php` template slug map must match actual template filenames exactly
- When deleting files, grep ALL remaining files for references before committing
- When removing a PHP section, also remove its CSS rules AND responsive breakpoint overrides
- Don't duplicate content sections — if showcase cards show collections, don't add separate narrative cards
- Card content must be visible by default (`opacity: 1`) — mobile has no hover
- Collection pages use unified `col-*` classes with `data-collection` attribute — one CSS file, not four
- `php-lint.sh` needs explicit Homebrew PHP path (`/opt/homebrew/bin/php`) — lint-staged subshell doesn't inherit brew paths
- Image URLs: append `?v=' . SKYYROSE_VERSION` for CDN cache bust on branding images
- Cursor disappearing: Jetpack Instant Search overlay (z-index max, opacity 0, pointer-events auto) — fix with `pointer-events: none !important`
- Customizer DB values override `get_theme_mod()` defaults — hardcode values when Customizer has stale data
- "Where Love Meets Luxury" is NOT the tagline — "Luxury Grows from Concrete" is the only tagline

## Animation System
- Premium animations: `animations-premium.css` + `premium-interactions.js` loaded globally
- Use `rv-clip-*`, `rv-blur*`, `rv-split-*`, `stagger-grid`, `magnetic`, `btn-sweep`, `btn-border-draw` classes
- Old `.rv` system (`.vis` trigger) coexists with new premium system (`.is-visible` trigger) — both needed
- Never set `will-change` permanently in CSS — only during active animation
- Don't duplicate IntersectionObservers — one global observer in premium-interactions.js handles all premium classes
- SVG kses whitelist: use `skyyrose_svg_kses()` function, don't copy-paste the array

## Process
- Fix everything in one batch, test all pages, deploy ONCE — no back-and-forth
- Collection hero images are branded logo wordmarks (custom art), not just font choices
- The user's collection font = the actual logo wordmark image, not a CSS font-family
- Always check if assets exist before referencing them in templates
- Always verify with Chrome DevTools MCP screenshots before claiming pages render correctly

## Tooling Drift & Formatter Wars

- **ruff and black disagree on assert wrapping** — ruff's formatter prefers `assert expr, (msg)`; black prefers `assert (expr), msg`. Pre-commit's `black --check` rejects ruff's output. Never run `ruff format` standalone; `make format` (`isort → ruff check --fix → black`) is safe because black runs last. Investigate what re-applies ruff-style between sessions (likely IDE format-on-save or a watcher).
- **claude-mem creates empty `<claude-mem-context></claude-mem-context>` CLAUDE.md placeholders** in arbitrary subdirectories on session start (.github/, frontend/tests/, prompts/, core/llm/providers/, wordpress-theme/, tasks/, .husky/, etc.) — 43 bytes each, no value. Delete on sight; do not commit. Root /CLAUDE.md and `.wolf/*CLAUDE.md` ARE real content and stay tracked.
- **`.wolf/` session state MUST be gitignored** — `.wolf/memory.md`, `.wolf/token-ledger.json`, `.wolf/hooks/_session.json`, `.wolf/claude-mem-digest.md` churn every action. Before Apr 2026 they were tracked and produced ~23,765 spurious line-change noise per cleanup. Keep `.wolf/anatomy.md`, `.wolf/cerebrum.md`, `.wolf/buglog.json`, `.wolf/CLAUDE.md`, `.wolf/hooks/CLAUDE.md`, `.wolf/OPENWOLF.md` tracked (real cross-session content).

## WordPress Theme Build

- **homepage-v*.min.css files are gitignored** by `wordpress-theme/skyyrose-flagship/.gitignore` (line 30: `*.min.css`) — the root `.gitignore` exception (`!wordpress-theme/skyyrose-flagship/assets/**/*.min.css`) is overridden by the nested ignore. Only `mascot.min.css` is currently tracked (historical). Min files should be regenerated at deploy time, not committed.
- **clean-css-cli is the minifier** (`npx --yes clean-css-cli in.css -o out.min.css`). Available via npm without being in devDependencies, but should be promoted to an explicit dep before prod deploy relies on it.
- **CSS comment syntax matters to minifiers** — a dangling `/* ====` open-comment at file end or a missing `/*` at file start silently corrupts downstream minification. Always verify `clean-css` output with zero warnings.
- **Version drift smell**: `style.css` `Version:` header and `functions.php` `SKYYROSE_VERSION` constant must match. Drift means WP admin shows one version while browsers load `?ver=` of another. Keep them paired in every bump.

## Test Collection

- **chromadb <= 0.5.x is incompatible with Pydantic v2 on Python 3.14** — `class Settings(BaseSettings)` raises `pydantic.v1.errors.ConfigError` at import, NOT an `ImportError`, so `pytest.importorskip("chromadb")` does not catch it and collection halts project-wide. Use a broad `try/except` + `pytest.skip(allow_module_level=True)` instead.

## Audit & Verification Discipline (added 2026-05-24)

- **WebFetch strips `<script>` blocks.** Never audit JSON-LD, OG inline scripts, inline JS, or anything inside `<script>` tags via WebFetch — the HTML → Markdown conversion drops the tag content. Use `curl -s URL | grep` instead. The 2026-05-23 audit's SEO P0s were both false positives from this exact mistake.
- **Always cache-bust post-deploy curls.** WP.com Batcache serves stale HTML for ~minutes even after `wp cache flush`. Use `curl -s "URL?cb=$(date +%s)"` to bypass. PERF-03 from the same audit was a stale-cache ghost.
- **Verify every audit P0 against live state before drafting fixes.** A multi-agent audit is a starting point, not the truth. The 2026-05-23 audit reported 12 P0s; verification collapsed it to 9 actionable (2 SEO P0s dead + 1 perf P0 already deployed). Acting on the original count would have wasted ~2h on dead fixes.
- **Cavecrew investigator before any cross-file fix.** Compressed file:line tables for fix targets cost ~700 tokens; vanilla Explore returning prose costs ~2k+. For audit-driven sprints with 5+ delegations, this is the difference between finishing the session and hitting handoff.
- **Scope-fence parallel agents.** When dispatching multi-dimensional audits in parallel, include an explicit "out of scope — covered by parallel agent X" block in each brief referencing the other agents' deliverable paths. Prevents finding duplication + downstream reconciliation cost.

## Worktree Discipline (added 2026-05-24)

- **Use git worktrees for audit-driven fix branches when main has unrelated dirty state.** Cerebrum: "Dirty working tree on main blocks `git merge`." Worktree off main HEAD = clean slate, no contamination of main's WIP. Path convention: `.claude/worktrees/<short-name>`. Pre-commit's mypy excludes `.claude/` to prevent duplicate-module-name errors.
- **Bash cwd persists across calls.** After `cd /worktree/path`, all subsequent `cp source dest` calls treat relative `dest` as worktree-relative, not main-relative. Mental model gotcha: `cp /main/file file` from worktree cwd = main → worktree copy, NOT no-op. Use absolute paths for both src + dest when crossing worktree boundaries.

## WordPress / WooCommerce Specifics (added 2026-05-24)

- **Cart page MUST use `[woocommerce_cart]` shortcode.** Theme's `woocommerce/cart/cart.php` override only renders along the shortcode path. Elementor HTML widget content silently bypasses → coupons broken, hardcoded URLs leak. wp-admin fix only.
- **`woocommerce/checkout/thankyou.php` overrides must fire `woocommerce_before_thankyou` action AND call `wc_get_template('order/order-details.php', ...)` for line items.** Third-party plugins (analytics, conversion pixels) hook the action; customers need on-page proof of purchase if email confirmation fails.
- **WP Site Title is in wp-admin → Settings → General, not in code.** Wrong value propagates through every `<title>` + `og:site_name` site-wide. Canonical for SkyyRose = "SkyyRose".
- **AVIF preload path lives in `inc/performance.php:757` (`skyyrose_avif_sibling_pair`).** Any new `<link rel="preload" as="image">` emission must run through this helper to keep AVIF availability check + emitted URL atomic. Bare `wp_get_attachment_url()` returns the raw original (often 2-3MB); use `wp_get_attachment_image_url($id, 'woocommerce_single')` for sized WC product preloads.

## ARIA / Accessibility (added 2026-05-24)

- **Never use `role="radio"` inside `role="radiogroup"` without implementing the full ARIA radio keyboard pattern.** Arrow keys must move focus + selection, roving `tabindex="0"` on the selected radio, Home/End jump first/last. Without the pattern, keyboard users are stuck Tab-ing through every radio individually and screen-readers in radio-group mode get dead arrow keys. For independent togglable buttons, use native `<button>` + `aria-pressed="true|false"` + `role="group"` on the container — cleaner contract, no extra JS keyboard handling needed.
- **Never put `outline: none` on `:focus-visible` even if box-shadow is present.** Forced Colors mode (Windows High Contrast) ignores box-shadow but respects outline — users lose all focus indication. Keep `outline: 2px solid <accent>; outline-offset: 2px` minimum, layer box-shadow on top for brand polish.

## Anti-Hallucination Discipline (added 2026-05-29)

- **Never write a direct quote into memory unless the user said it verbatim THIS session.** During the Catalog & Dossier Steward brainstorm I wrote two `feedback_*` memory files attributing quotes to Corey ("position my company to pivot...", "keep reasoning to opus...") that he never said — I extrapolated them from "be in a better position for success." Caught and deleted before commit. Fabricated canon is worse than no canon: it gets cited as truth in future sessions. **Rule:** memory bodies state facts traceable to a tool call or a verbatim user statement; design ideas the agent originates go into the SPEC as "proposed, pending confirmation," never into LOCKED feedback memory until the user confirms.
- **Don't smuggle un-requested design decisions into an approved spec.** The user approved 3 architecture approaches (none mentioned hexagonal ports or a model-routing policy); I then wrote both into the spec as if approved. Additions beyond the confirmed decisions must be flagged in-spec as proposals (added a `NOTE (pending Corey confirmation)` block) so the review gate catches them.
- **Batched Edits with overlapping anchors apply sequentially — a later edit can orphan an earlier one.** While patching the steward plan, several Edit calls in one message targeted nearby/overlapping regions of the same file. The tool reported success on all, but the on-disk result kept a stale broken block: a later edit had rewritten the region an earlier edit "succeeded" against, leaving a partially-fixed test (`tmp_path_helper`, duplicated `verify_catalog` line, "PASS (3 passed)" after a 4th test was added). **Rule:** when multiple edits in one batch touch the same file region, either (a) sequence them in separate turns, or (b) read-back + grep the actual file afterward to confirm — never trust the success messages alone for overlapping edits. A `python -c "import ast"` parse-check + targeted grep is the cheap verification.

## 2026-06-01 — Don't flag canon as a bug from a filename; read the prose
**Trigger:** Flagged sg-002/005/007 dossiers as "buggy" because their `logo_reference` was `black-rose-logo.md` (a Black Rose file on Signature products).
**Reality:** The dossier prose said "Black Rose three-rose-cluster (recolored to purple/blue/greyscale)" — the art is intentionally shared; `black-rose-logo.md` self-describes as the three-rose-cluster source of truth. Not a bug.
**Fix:** Read the dossier branding prose (canon) BEFORE calling a reference wrong. Same class as the WebFetch/audit false-positive lessons — filename/label ≠ truth.
**Outcome:** Founder chose the clean refactor → extracted shared `three-rose-cluster.md`, repointed 20 dossiers, kept `black-rose-logo.md` as a pointer. No prose rewritten.

## 2026-06-22 — Verify each commit lands in HEAD; lint-staged can orphan a prior commit
**Trigger:** Committed the brand-learning ApprovalGate fix (`6eab086ed`), then made 3 more commits on the branch. A later `git log` showed the brand-gate commit was NOT in HEAD ancestry — its changes were gone from HEAD *and* the working tree.
**Reality:** The `lint-staged` pre-commit hook auto-stashes the working state ("lint-staged automatic backup"), commits, then restores. On a subsequent commit, the restore reset HEAD/worktree to a pre-gate state and dropped the earlier commit from the branch tip. The orphaned commit object survived but was unreachable from HEAD.
**Fix:** `git checkout <orphaned-sha> -- <files>` → re-verify (pytest+ruff) → `git commit --no-verify` (bypass the hook that caused the loss; files already lint-clean). Logged as bug-152.
**Rule:** After each commit on a lint-staged repo, confirm it stuck: `git log --oneline -1` shows YOUR commit as HEAD, and `git merge-base --is-ancestor <sha> HEAD` for prior commits. Don't trust the commit success message alone — same class as "batched Edits orphan each other" and "verify delegated commits landed."
