# wordpress-copilot/ — Hardcoded skyyrose.co Claude Code copilot config

Custom Claude Code configuration wiring together agents, commands, hooks, and skills specifically for the skyyrose.co WordPress/WooCommerce production site. Not a generic WP toolkit — every file is tuned for the SkyyRose theme, collections, and deploy pipeline.

## Key files

- `agents/` — Subagent definitions for WP-specific roles (theme reviewer, PHPCS auditor, WC product importer, performance checker).
- `commands/` — Custom slash commands: `/wp-deploy` (wraps `scripts/deploy-theme.sh` with STOP AND SHOW gate), `/wp-lint` (runs PHPCS via Composer on the theme), `/wp-verify` (curls live endpoints and checks HTTP status + size).
- `hooks/` — PreToolUse and PostToolUse hooks: blocks SFTP writes to skyyrose.co without STOP AND SHOW confirmation; post-deploy hook triggers the verify gate automatically.
- `scripts/` — Helper shell scripts consumed by commands: `ssh-check.sh` (validates key at `~/.ssh/skyyrose-deploy` before any transfer), `cache-bust.sh` (bumps `SKYYROSE_VERSION` constant in `functions.php`).
- `skills/` — Reusable skill files: `professor-web-dev.md` (professor-grade HTML/CSS/JS/PHP guidance), `threejs-wordpress.md` (Three.js + WordPress integration patterns for immersive templates), `web-sniper.md` (OSS discovery: search GitHub/npm/Packagist for battle-tested solutions before hand-rolling).
- `TESTING.md` — WP-specific test checklist: PHPCS, PHP syntax, HTTP status verification on 8 canonical URLs, mobile nav, cart, WooCommerce checkout.
- `README.md` — Setup: requires Composer at `~/.local/bin/composer`, SSH key at `~/.ssh/skyyrose-deploy`, `.env.wordpress` with SFTP credentials.

## Conventions

- All WP file writes (theme PHP, CSS, JS) go through the standard Edit/Write tools — no special WP hooks needed for local edits.
- Any SFTP transfer or `deploy-theme.sh` invocation triggers the STOP AND SHOW gate — the hook in `hooks/` enforces this before the Bash tool fires.
- Slash commands in `commands/` are skyyrose.co-specific. Don't add generic WP commands that would apply to other sites.
- Web Sniper (`skills/web-sniper.md`) is always consulted before hand-rolling WP utility code — check GitHub/Packagist first.
- `professor-web-dev.md` skill governs code quality expectations: semantic HTML, progressive enhancement, WCAG AA, zero inline styles in PHP templates.

## Don't

- Don't use this copilot config for any site other than skyyrose.co — paths, SSH keys, and PHPCS rules are hardcoded.
- Don't add a command that bypasses STOP AND SHOW for SFTP or `deploy-theme.sh` — the gate is non-negotiable.
- Don't define WP system prompts here — those live in `prompts/agent_prompts.py` under the E-commerce category.
- Don't commit `.env.wordpress` or credentials to this directory — secrets via `.env.wordpress` in the repo root (gitignored).

## Related

- `wordpress-theme/skyyrose-flagship/` — the theme this copilot governs
- `scripts/deploy-theme.sh` — deploy script wrapped by `/wp-deploy` command
- `prompts/agent_prompts.py` — E-commerce category system prompts used by WP agents
- `inc/enqueue.php` — CSS/JS loading; always check before adding new assets
