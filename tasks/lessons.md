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
