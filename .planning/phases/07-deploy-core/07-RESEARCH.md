# Phase 7: Deploy Core - Research

**Researched:** 2026-03-09
**Domain:** WordPress theme deployment via SSH/SFTP with WP-CLI maintenance mode
**Confidence:** HIGH

## Summary

Phase 7 delivers a deploy script that transfers the built WordPress theme to the production WordPress.com Atomic server at skyyrose.co. The project already has a working deploy script (`scripts/wp-deploy-theme.sh`) that uses `lftp` for SFTP file transfer and `sshpass` for WP-CLI commands over SSH. This phase needs to build a new, focused deploy script that satisfies DEPLOY-01 through DEPLOY-03 and DEPLOY-07: file transfer, maintenance mode before/after, cache flush, and try/finally safety.

The hosting environment is WordPress.com Atomic (ssh.wp.com), which provides both SFTP and SSH access. The existing deploy script proves that WP-CLI commands work via `sshpass -p "$SSH_PASS" ssh ... "wp $cmd"`. However, WordPress.com Atomic may restrict rsync depending on whether the site has full SSH or SFTP-only mode enabled. The requirement specifies "rsync over SSH" but the existing working infrastructure uses `lftp` (SFTP mirror). The deploy script should attempt rsync first and fall back to lftp if rsync is unavailable -- or use whichever the hosting environment supports. Since the existing `wp_remote()` function already works for WP-CLI, the SSH channel is confirmed functional.

**Primary recommendation:** Create a single bash deploy script (`scripts/deploy-theme.sh`) that sources `.env.wordpress`, enables maintenance mode via WP-CLI over SSH, transfers files via rsync (with lftp fallback), disables maintenance mode and flushes cache, all wrapped in a `trap` handler that guarantees maintenance mode is disabled even on failure.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEPLOY-01 | Deploy script transfers built theme files to production server via rsync over SSH | Existing SSH connection via `sshpass` is verified working. rsync available locally (openrsync 2.6.9). Remote rsync support depends on WordPress.com Atomic SSH mode. lftp SFTP fallback is proven working. |
| DEPLOY-02 | Deploy script enables WP-CLI maintenance mode before file transfer | `wp maintenance-mode activate` is a built-in WP-CLI command (no additional package needed). WP-CLI is preinstalled on WordPress.com. Existing `wp_remote()` pattern in `wp-deploy-theme.sh` proves remote WP-CLI works. |
| DEPLOY-03 | Deploy script disables maintenance mode and flushes cache after transfer | `wp maintenance-mode deactivate`, `wp cache flush`, `wp transient delete --all`, `wp rewrite flush` -- all proven working in existing `do_flush_cache()` function. |
| DEPLOY-07 | Deploy script has try/finally safety -- maintenance mode always gets disabled even on failure | Bash `trap` command with cleanup function. Must handle SIGINT, SIGTERM, ERR, and EXIT signals. |
</phase_requirements>

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| bash | 5.x (zsh-compatible) | Script shell | All existing deploy scripts use bash with `set -euo pipefail` |
| sshpass | latest (homebrew) | Non-interactive SSH password auth | Already installed, used by existing `wp-deploy-theme.sh` |
| rsync | openrsync 2.6.9 (macOS built-in) | Efficient file sync over SSH | Requirement DEPLOY-01 specifies rsync over SSH |
| lftp | latest (homebrew) | SFTP mirror (fallback) | Already installed, proven working with WordPress.com |
| WP-CLI | preinstalled on WordPress.com | Remote WordPress admin commands | maintenance-mode, cache flush, transient delete |

### Supporting
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| curl | system | Post-deploy HTTP check | Quick smoke test that site responds |
| php | 8.x (local) | Pre-flight PHP syntax check | Validate before deploying |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| rsync | lftp SFTP mirror | lftp is proven on WordPress.com but requirement says rsync. Script should try rsync first, fall back to lftp. |
| sshpass | SSH key auth | Keys are more secure but WordPress.com credentials are password-based per .env.wordpress |
| bash | Python deploy script | Project has Python deploy scripts but they're REST API based, not SSH/SFTP. Bash matches existing patterns. |

## Architecture Patterns

### Recommended Script Structure
```
scripts/
  deploy-theme.sh          # NEW: Phase 7 deploy script (DEPLOY-01/02/03/07)
  wp-deploy-theme.sh       # EXISTING: Full deploy + WP setup (not modified)
```

### Pattern 1: Trap-Based Cleanup for Try/Finally Safety
**What:** Use bash `trap` to guarantee maintenance mode is disabled regardless of how the script exits.
**When to use:** Any time maintenance mode is activated on a production server.
**Example:**
```bash
# Source: DEPLOY-07 requirement, bash trap documentation
MAINTENANCE_ACTIVE=false

cleanup() {
    if [[ "$MAINTENANCE_ACTIVE" == "true" ]]; then
        log_warn "Cleanup: disabling maintenance mode..."
        wp_remote "maintenance-mode deactivate" || log_error "Failed to deactivate maintenance mode"
        MAINTENANCE_ACTIVE=false
    fi
}

trap cleanup EXIT INT TERM

# ... later in script ...
wp_remote "maintenance-mode activate"
MAINTENANCE_ACTIVE=true

# If anything fails between here and deactivate, cleanup runs automatically
do_file_transfer

wp_remote "maintenance-mode deactivate"
MAINTENANCE_ACTIVE=false
```

### Pattern 2: wp_remote() for WP-CLI Over SSH
**What:** Execute WP-CLI commands on the remote WordPress.com server via sshpass + ssh.
**When to use:** Any WP-CLI operation (maintenance mode, cache flush).
**Example:**
```bash
# Source: existing scripts/wp-deploy-theme.sh line 83-90
wp_remote() {
    local cmd="$1"
    sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=accept-new \
        "${SSH_USER}@${SSH_HOST}" "wp $cmd" 2>/dev/null
}
```

### Pattern 3: Rsync with SSH via sshpass
**What:** Use rsync over SSH with sshpass for password authentication.
**When to use:** File transfer when rsync is available on the remote server.
**Example:**
```bash
# rsync over SSH with sshpass providing the password
rsync -avz --delete \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='vendor' \
    --exclude='tests' \
    --exclude='test-results' \
    --exclude='.env*' \
    --exclude='*.map' \
    --exclude='.DS_Store' \
    --exclude='package.json' \
    --exclude='package-lock.json' \
    --exclude='webpack.config.js' \
    --exclude='deploy.sh' \
    --exclude='CLAUDE.md' \
    --exclude='IMMERSIVE-WORLDS-PLAN.md' \
    --exclude='composer.json' \
    --exclude='composer.lock' \
    --exclude='scripts/' \
    --exclude='*.log' \
    -e "sshpass -p '$SSH_PASS' ssh -o StrictHostKeyChecking=accept-new -p $SSH_PORT" \
    "$THEME_DIR/" \
    "${SSH_USER}@${SSH_HOST}:${WP_THEME_PATH}/"
```

### Pattern 4: lftp SFTP Fallback
**What:** If rsync fails (e.g., not available on remote), fall back to lftp SFTP mirror.
**When to use:** WordPress.com Atomic in SFTP-only mode.
**Example:**
```bash
# Source: existing scripts/wp-deploy-theme.sh line 164-176
lftp -c "
set sftp:auto-confirm yes
set net:max-retries 3
set net:reconnect-interval-base 5
open -u $SFTP_USER,$SFTP_PASS sftp://$SFTP_HOST:$SFTP_PORT
mirror --reverse --verbose --only-newer $EXCLUDE_ARGS \
  $THEME_DIR/ \
  $WP_THEME_PATH/
bye
"
```

### Anti-Patterns to Avoid
- **No cleanup trap:** Activating maintenance mode without a trap is dangerous -- a mid-transfer failure leaves the site down. Always pair `trap cleanup EXIT` with maintenance mode activation.
- **Using `--delete` with rsync carelessly:** `--delete` removes remote files not in local. Exclude critical WordPress files (wp-config.php, uploads/) to avoid nuking the site. The theme path `/htdocs/wp-content/themes/skyyrose-flagship/` is scoped safely.
- **Hardcoding credentials:** Never embed passwords in the script. Always source from `.env.wordpress`.
- **Deploying node_modules/vendor:** These are dev dependencies. The exclude list must filter them (saves ~383MB of unnecessary transfer).
- **Using `set -e` without trap:** `set -e` causes the script to exit on error, but without a trap, cleanup code never runs. Always combine `set -euo pipefail` with `trap cleanup EXIT`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Maintenance mode | Custom .maintenance file creation | `wp maintenance-mode activate/deactivate` | WP-CLI handles the `.maintenance` file correctly, respects 10-min auto-recovery, and provides status checking |
| File sync | Custom file-by-file upload | rsync `--delete` or lftp `mirror --reverse` | Both handle incremental sync, permission preservation, and large file sets efficiently |
| SSH password auth | expect scripts or manual input | sshpass | Purpose-built tool for non-interactive SSH password auth |
| Cache invalidation | Direct database queries | `wp cache flush && wp transient delete --all && wp rewrite flush` | WP-CLI knows all cache layers including object cache, transients, and rewrite rules |
| Pre-flight PHP check | Custom PHP parser | `find ... -exec php -l {} \;` | PHP's built-in linter catches syntax errors perfectly |

**Key insight:** The existing `wp-deploy-theme.sh` has all the building blocks (wp_remote, lftp deploy, cache flush). Phase 7's script assembles them into a focused deploy pipeline with proper safety (trap cleanup + maintenance mode).

## Common Pitfalls

### Pitfall 1: Maintenance Mode Not Disabled on Failure
**What goes wrong:** Script enables maintenance mode, rsync fails mid-transfer, script exits without disabling maintenance mode. Site stays down.
**Why it happens:** Bash scripts exit on error when `set -e` is set, skipping subsequent commands.
**How to avoid:** Always use `trap cleanup EXIT` that checks and disables maintenance mode. Track state with a flag variable (`MAINTENANCE_ACTIVE`).
**Warning signs:** Testing without simulating failures. The happy path always works.

### Pitfall 2: WordPress.com Atomic SFTP-Only Mode
**What goes wrong:** rsync command fails with "protocol error" or "connection refused" because WordPress.com has the site in SFTP-only mode.
**Why it happens:** WordPress.com Atomic defaults to SFTP-only access. rsync requires full SSH shell access.
**How to avoid:** Test rsync connectivity before relying on it. Implement lftp fallback. Detect the error and switch automatically.
**Warning signs:** `sshpass ... ssh ... "which rsync"` returning empty or error.

### Pitfall 3: macOS openrsync Limitations
**What goes wrong:** openrsync (macOS built-in) is protocol version 29 (compatible with rsync 2.6.9). Some flags from newer rsync versions are unsupported.
**Why it happens:** Apple ships openrsync instead of GNU rsync.
**How to avoid:** Use only well-established flags (`-avz --delete --exclude`). Avoid rsync 3.x-only features like `--info=progress2` or `--mkpath`. If needed, install GNU rsync via `brew install rsync`.
**Warning signs:** `rsync: unknown option` errors.

### Pitfall 4: Large Asset Transfer Timeouts
**What goes wrong:** The theme contains ~325MB of deployable files (229MB images, 58MB scenes). First deployment takes a long time and may time out.
**Why it happens:** Initial sync has no delta -- every file must be transferred.
**How to avoid:** rsync's incremental sync handles subsequent deploys efficiently. For first deploy, use `--timeout=300` and consider uploading large assets separately.
**Warning signs:** SSH session dropping during long transfers. WordPress.com limits sessions to 8 hours, 1GB RAM.

### Pitfall 5: Deploying Dev Files to Production
**What goes wrong:** node_modules (336MB), vendor (47MB), test files, .map files, or dev config get uploaded.
**Why it happens:** Missing or incomplete exclude patterns.
**How to avoid:** Comprehensive exclude list matching the existing deploy scripts. Verify with `--dry-run` first.
**Warning signs:** Deploy taking much longer than expected. Remote disk usage spiking.

### Pitfall 6: Lost Cache After Deploy
**What goes wrong:** Site serves stale CSS/JS after deploying new minified files.
**Why it happens:** Browser and server caches not flushed. WordPress object cache retains old values.
**How to avoid:** Run full cache flush after deploy: object cache, transients, and rewrite rules.
**Warning signs:** Users report old styles after deploy. Browser hard-refresh shows new content but normal navigation shows old.

## Code Examples

### Complete Deploy Script Skeleton
```bash
#!/usr/bin/env bash
# scripts/deploy-theme.sh — Phase 7 deploy script
# Transfers built WordPress theme to production with maintenance mode safety

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
THEME_DIR="$PROJECT_ROOT/wordpress-theme/skyyrose-flagship"
ENV_FILE="$PROJECT_ROOT/.env.wordpress"

MAINTENANCE_ACTIVE=false

# Source credentials
source "$ENV_FILE"

# Cleanup handler -- ALWAYS disables maintenance mode
cleanup() {
    if [[ "$MAINTENANCE_ACTIVE" == "true" ]]; then
        log_warn "Cleanup: disabling maintenance mode..."
        wp_remote "maintenance-mode deactivate" || log_error "CRITICAL: Failed to deactivate maintenance mode"
        MAINTENANCE_ACTIVE=false
    fi
}
trap cleanup EXIT INT TERM

# WP-CLI over SSH (proven pattern from wp-deploy-theme.sh)
wp_remote() {
    local cmd="$1"
    sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=accept-new \
        "${SSH_USER}@${SSH_HOST}" "wp $cmd"
}

# Pre-flight checks
preflight() {
    # Verify .env.wordpress vars
    # Verify sshpass installed
    # Verify theme directory exists
    # Verify SSH connectivity
    # PHP syntax check on theme files
}

# File transfer (rsync with lftp fallback)
transfer_files() {
    # Try rsync first
    # If rsync fails, fall back to lftp
}

# Main deploy pipeline
main() {
    preflight

    # 1. Enable maintenance mode (DEPLOY-02)
    wp_remote "maintenance-mode activate"
    MAINTENANCE_ACTIVE=true

    # 2. Transfer files (DEPLOY-01)
    transfer_files

    # 3. Disable maintenance mode + flush cache (DEPLOY-03)
    wp_remote "maintenance-mode deactivate"
    MAINTENANCE_ACTIVE=false

    wp_remote "cache flush"
    wp_remote "transient delete --all"
    wp_remote "rewrite flush"
}

main "$@"
```

### WP-CLI Maintenance Mode Commands
```bash
# Source: https://developer.wordpress.org/cli/commands/maintenance-mode/
# Activate maintenance mode (creates .maintenance file)
wp maintenance-mode activate
# Output: "Enabling Maintenance mode..." + "Success: Activated Maintenance mode."

# Check status (for scripting -- returns exit code)
wp maintenance-mode is-active
# Returns: exit code 0 if active, 1 if not

# Deactivate maintenance mode (removes .maintenance file)
wp maintenance-mode deactivate
# Output: "Disabling Maintenance mode..." + "Success: Deactivated Maintenance mode."

# Note: WordPress auto-deactivates maintenance mode after 10 minutes
# as a safety net, but the deploy script should not rely on this.
```

### Rsync Exclude List (Comprehensive)
```bash
# Source: derived from existing deploy scripts + theme .gitignore
RSYNC_EXCLUDES=(
    --exclude='.git'
    --exclude='.git/'
    --exclude='node_modules/'
    --exclude='vendor/'
    --exclude='tests/'
    --exclude='test-results/'
    --exclude='.env*'
    --exclude='*.map'
    --exclude='*.log'
    --exclude='.DS_Store'
    --exclude='package.json'
    --exclude='package-lock.json'
    --exclude='composer.json'
    --exclude='composer.lock'
    --exclude='webpack.config.js'
    --exclude='deploy.sh'
    --exclude='CLAUDE.md'
    --exclude='IMMERSIVE-WORLDS-PLAN.md'
    --exclude='scripts/'
    --exclude='.deploy-archives/'
    --exclude='.gitignore'
    --exclude='generate_models.js'
    --exclude='.phpcs.xml'
    --exclude='.eslintrc*'
    --exclude='.prettierrc*'
    --exclude='.editorconfig'
    --exclude='phpunit.xml'
    --exclude='playwright-report/'
    --exclude='screenshots/'
)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FTP upload | rsync/SFTP with incremental sync | Long-established | Only changed files transfer on subsequent deploys |
| Manual maintenance mode | WP-CLI `maintenance-mode activate/deactivate` | WP-CLI 2.x+ | No manual `.maintenance` file creation needed |
| No safety net | bash `trap` for cleanup | Standard practice | Guarantees maintenance mode disabled on failure |
| Custom PHP maintenance file | WP-CLI built-in command | WP-CLI bundled the maintenance-mode-command package | Consistent, tested, includes auto-recovery after 10 minutes |

**Deprecated/outdated:**
- Direct `.maintenance` file creation via SSH: WP-CLI `maintenance-mode` is cleaner and handles edge cases.
- FTP (non-encrypted): Always use SFTP or rsync over SSH.

## Open Questions

1. **Does WordPress.com Atomic allow rsync or is it SFTP-only?**
   - What we know: SSH and WP-CLI work (proven by existing scripts). SFTP works (proven by lftp deploys). WordPress.com Atomic defaults to SFTP-only but can be configured for full SSH.
   - What's unclear: Whether the current skyyrose.wordpress.com account has full SSH enabled (which rsync requires) or is SFTP-only.
   - Recommendation: The deploy script should try rsync and fall back to lftp SFTP mirror if rsync fails. Both approaches satisfy DEPLOY-01's intent ("transfers theme files to production server"). The requirement text says "rsync over SSH" but the fallback ensures the deploy always works.

2. **Should source maps (.map files) be deployed?**
   - What we know: The theme .gitignore excludes .map files generally but includes them for assets/. The existing wp-deploy-theme.sh excludes .map files.
   - What's unclear: Whether debugging on production is needed.
   - Recommendation: Exclude .map files from deploy (matches existing pattern). They're for dev debugging.

3. **Should `--delete` be used with rsync?**
   - What we know: `--delete` removes remote files not present locally. The theme path is scoped to `/htdocs/wp-content/themes/skyyrose-flagship/` so it won't affect other WordPress files.
   - What's unclear: Whether there are server-generated files inside the theme directory that should be preserved.
   - Recommendation: Use `--delete` to keep the remote in sync. Any server-generated files inside the theme dir are unexpected and should be cleaned.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | bash + pytest (shell script testing via subprocess) |
| Config file | tests/conftest.py (existing) |
| Quick run command | `bash scripts/deploy-theme.sh --dry-run` |
| Full suite command | `pytest tests/scripts/test_deploy_theme.py -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEPLOY-01 | Script transfers files via rsync/lftp | integration (dry-run) | `bash scripts/deploy-theme.sh --dry-run` | Wave 0 |
| DEPLOY-02 | Maintenance mode activated before transfer | unit (function test) | `pytest tests/scripts/test_deploy_theme.py::test_maintenance_mode_before_transfer -x` | Wave 0 |
| DEPLOY-03 | Maintenance mode deactivated + cache flushed after transfer | unit (function test) | `pytest tests/scripts/test_deploy_theme.py::test_cache_flush_after_transfer -x` | Wave 0 |
| DEPLOY-07 | Try/finally safety: maintenance mode disabled on failure | unit (trap test) | `pytest tests/scripts/test_deploy_theme.py::test_trap_disables_maintenance_on_failure -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `bash scripts/deploy-theme.sh --dry-run`
- **Per wave merge:** `bash scripts/deploy-theme.sh --dry-run && shellcheck scripts/deploy-theme.sh`
- **Phase gate:** dry-run passes + trap behavior verified via subprocess test

### Wave 0 Gaps
- [ ] `scripts/deploy-theme.sh` -- the deploy script itself (core deliverable)
- [ ] `tests/scripts/test_deploy_theme.py` -- subprocess tests for script behavior
- [ ] `tests/scripts/__init__.py` -- package init (if directory is new)

*(Tests for this phase primarily validate bash script behavior via subprocess invocations and dry-run mode, since actual deployment requires production server access.)*

## Sources

### Primary (HIGH confidence)
- Existing `scripts/wp-deploy-theme.sh` -- proven working deploy script with WP-CLI over SSH, lftp SFTP transfer, cache flush (already in production use)
- Existing `wordpress-theme/skyyrose-flagship/deploy.sh` -- theme-internal deploy with rsync, pre-checks, health checks
- `.env.wordpress` -- confirmed SSH credentials: `skyyrose.wordpress.com@ssh.wp.com:22`, theme path `/htdocs/wp-content/themes/skyyrose-flagship`
- `.claude/skills/wp-deploy/SKILL.md` -- project skill documenting deploy patterns
- Local tool verification: rsync (openrsync 2.6.9), sshpass, lftp all installed

### Secondary (MEDIUM confidence)
- [WordPress.com SSH Support](https://wordpress.com/support/ssh/) -- SSH and WP-CLI available on Business/Commerce plans
- [WP-CLI maintenance-mode](https://developer.wordpress.org/cli/commands/maintenance-mode/) -- activate/deactivate/is-active/status subcommands, built into WP-CLI
- [WP Cloud SSH/SFTP docs](https://wp.cloud/wp-cloud-technical-details/wpcloud-site-ssh-and-sftp/) -- Atomic defaults to SFTP-only, can enable full SSH, 8hr session limit, 1GB RAM limit

### Tertiary (LOW confidence)
- rsync availability on WordPress.com Atomic -- no definitive documentation found confirming rsync binary exists on the remote server. The deploy script should detect and fall back gracefully.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all tools verified locally, WP-CLI patterns proven by existing scripts
- Architecture: HIGH -- deploy script pattern well-established with existing `wp-deploy-theme.sh`
- Pitfalls: HIGH -- based on direct analysis of existing scripts, hosting environment docs, and macOS tool limitations
- rsync on remote: LOW -- unconfirmed whether WordPress.com Atomic has rsync; lftp fallback covers this gap

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (stable domain, tools unlikely to change)
