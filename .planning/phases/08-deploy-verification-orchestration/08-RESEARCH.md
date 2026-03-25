# Phase 8: Deploy Verification & Orchestration - Research

**Researched:** 2026-03-09
**Domain:** Post-deploy health verification, single-command pipeline orchestration, dry-run mode for WordPress theme deployment
**Confidence:** HIGH

## Summary

Phase 8 adds three capabilities to the Phase 7 deploy script (`scripts/deploy-theme.sh`): deep post-deploy health checks that verify page content (DEPLOY-04), a single-command orchestration pipeline that chains build-transfer-verify (DEPLOY-05), and dry-run mode for the full pipeline (DEPLOY-06). The deploy core from Phase 7 already has `--dry-run` for the transfer step; Phase 8 extends dry-run to the full pipeline and adds content verification.

The WordPress site at `https://skyyrose.co` does NOT have `/health`, `/health/ready`, or `/health/live` endpoints -- those are FastAPI backend endpoints defined in `main_enterprise.py`. The success criteria statement "hits health endpoints (/health, /health/ready, /health/live) and verifies page content" should be interpreted as: the deploy verification hits the live WordPress site's key pages and verifies content markers (brand name, theme assets, WooCommerce functionality) rather than just checking HTTP 200 status codes. This is a "deep health check" that confirms the theme deployed correctly and the site is functional.

The existing codebase has three verification scripts (`scripts/smoke-test.sh`, `scripts/wordpress_health_check.py`, `scripts/verify_skyyrose_site.py`) that provide patterns for HTTP-based content verification. However, none of them are integrated into the deploy pipeline. The existing `wordpress-theme/skyyrose-flagship/deploy.sh` also has `run_remote_health_check()` and `run_local_health_check()` functions that check theme activation and file existence. Phase 8 should create a new bash verification function (or script) that checks the live site after deploy, integrated into the orchestration pipeline.

**Primary recommendation:** Create two deliverables: (1) a `scripts/verify-deploy.sh` script that performs deep content verification against the live WordPress site, and (2) a `scripts/deploy-pipeline.sh` orchestration script that chains `npm run build` -> `deploy-theme.sh` -> `verify-deploy.sh` with a unified `--dry-run` mode. The verification script checks HTTP status AND content markers for critical pages. The pipeline script provides the single-command entry point.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DEPLOY-04 | Post-deploy deep health check verifies page content (not just HTTP 200) | curl with content grep is sufficient for bash-based verification. Existing smoke-test.sh has the `test_endpoint()` pattern that checks both status code AND response body content. Key pages: homepage (SkyyRose brand markers), collection pages, REST API discovery endpoint. |
| DEPLOY-05 | Single command runs the full deploy pipeline (build -> transfer -> verify) | A new `scripts/deploy-pipeline.sh` that calls `npm run build` (Phase 5), `deploy-theme.sh` (Phase 7), and `verify-deploy.sh` (Phase 8) sequentially. Each step must succeed before the next runs. |
| DEPLOY-06 | Deploy dry-run mode validates without actually shipping to production | `deploy-theme.sh` already has `--dry-run`. The pipeline script passes `--dry-run` to the deploy step and skips verification (since nothing was deployed). The dry-run shows: what would be built, what would be transferred (rsync file list), and what health checks would run. |
</phase_requirements>

## Standard Stack

### Core
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| bash | 5.x (zsh-compatible) | Script shell | All existing deploy scripts use bash with `set -euo pipefail` |
| curl | system (macOS built-in) | HTTP requests for health checks | Already used in smoke-test.sh pattern, zero dependencies |
| grep | system (macOS built-in) | Content matching in HTTP responses | Used with curl for content verification |
| npm | project-installed | Build trigger (`npm run build`) | Phase 5 build pipeline already configured |

### Supporting
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| shellcheck | latest (homebrew) | Bash script linting | Validation of all new scripts |
| sshpass | latest (homebrew) | SSH password auth (already installed) | Used by deploy-theme.sh (Phase 7) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| bash curl checks | Python httpx (wordpress_health_check.py) | Python scripts exist but add dependency complexity; bash+curl matches Phase 7 patterns and keeps the deploy pipeline self-contained |
| Separate verify script | Functions inside deploy-theme.sh | Separation is better: verification is independently testable and reusable outside the deploy pipeline |
| Single combined script | Three separate scripts (build, deploy, verify) | Three scripts composed by a pipeline script gives maximum flexibility; each can be run independently |

## Architecture Patterns

### Recommended Script Structure
```
scripts/
  deploy-pipeline.sh    # NEW: Phase 8 orchestrator (DEPLOY-05, DEPLOY-06)
  verify-deploy.sh      # NEW: Phase 8 health checks (DEPLOY-04)
  deploy-theme.sh       # EXISTING: Phase 7 core deploy (DEPLOY-01/02/03/07)
```

### Pattern 1: Deep Content Verification via curl + grep
**What:** HTTP request to a page followed by content matching to verify the response contains expected markers (not just HTTP 200).
**When to use:** Post-deploy verification to confirm the theme is serving correctly.
**Example:**
```bash
# Source: adapted from scripts/smoke-test.sh test_endpoint() pattern
verify_page() {
    local name="$1"
    local url="$2"
    local expected_content="$3"
    local timeout="${4:-30}"

    local response http_code body
    response=$(curl -sS -w "\n%{http_code}" --connect-timeout 10 --max-time "$timeout" "$url" 2>/dev/null || echo -e "\n000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" -ne 200 ]]; then
        log_error "$name: HTTP $http_code (expected 200)"
        return 1
    fi

    if ! echo "$body" | grep -qi "$expected_content"; then
        log_error "$name: Content marker not found: '$expected_content'"
        return 1
    fi

    log_success "$name: HTTP 200 + content verified"
    return 0
}
```

### Pattern 2: Pipeline Orchestration with Step Tracking
**What:** A pipeline script that runs build, deploy, and verify as sequential steps with clear logging and failure handling.
**When to use:** Single-command deploy that chains all phases.
**Example:**
```bash
# Source: standard CI/CD pipeline pattern
run_step() {
    local step_num="$1"
    local step_name="$2"
    shift 2

    log_info "[$step_num/3] $step_name..."
    if "$@"; then
        log_success "[$step_num/3] $step_name complete"
    else
        log_error "[$step_num/3] $step_name FAILED"
        return 1
    fi
}

main() {
    run_step 1 "Build assets"    bash -c "cd $THEME_DIR && npm run build"
    run_step 2 "Deploy to production" bash scripts/deploy-theme.sh "${DEPLOY_ARGS[@]}"
    run_step 3 "Verify deployment" bash scripts/verify-deploy.sh
}
```

### Pattern 3: Dry-Run Pipeline Passthrough
**What:** Pipeline's `--dry-run` flag passes through to child scripts and skips steps that require a live deploy.
**When to use:** Previewing the full deploy pipeline without touching production.
**Example:**
```bash
if [[ "$DRY_RUN" == "true" ]]; then
    # Step 1: Show what build would produce
    log_info "[DRY RUN] Would run: cd $THEME_DIR && npm run build"
    # Step 2: Pass --dry-run to deploy script
    bash scripts/deploy-theme.sh --dry-run
    # Step 3: Show what verification would check
    log_info "[DRY RUN] Would verify: homepage, collections, REST API"
    log_info "[DRY RUN] Skipping actual verification (nothing was deployed)"
fi
```

### Anti-Patterns to Avoid
- **Checking only HTTP 200:** The whole point of DEPLOY-04 is content verification. HTTP 200 with a blank page or error page is a false positive. Always check for content markers.
- **Verification that blocks on failure without reporting:** If one page fails verification, continue checking the remaining pages and report all failures at the end. Do not exit on the first failure.
- **Hardcoding the site URL:** Use `WORDPRESS_URL` environment variable (or source from `.env.wordpress`) so the script works for different environments.
- **Running verification in dry-run mode:** Dry-run means nothing was deployed, so hitting the live site would verify the OLD state, not the new deploy. Skip verification in dry-run.
- **Building inside the deploy script:** Build and deploy are separate concerns. The pipeline orchestrator composes them; `deploy-theme.sh` should not also run `npm run build`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP content checking | Custom Python async HTTP client | curl + grep in bash | Zero dependencies, matches existing patterns, trivially testable |
| Pipeline orchestration | Complex DAG/workflow engine | Sequential bash script with step functions | Three linear steps don't need a workflow engine |
| Page content parsing | HTML parser (BeautifulSoup) | Simple string grep on response body | We need brand markers (text strings), not DOM manipulation |
| Retry logic | Custom exponential backoff | curl `--retry 3 --retry-delay 5` | curl has built-in retry support |

**Key insight:** The verification is intentionally simple: hit URL, check status code, grep for content marker. This catches the real failures (theme not deployed, PHP fatal error, maintenance mode stuck) without the complexity of full page rendering validation.

## Common Pitfalls

### Pitfall 1: WordPress.com Caching Returns Stale Content
**What goes wrong:** Verification passes because the CDN/cache serves the old page, but the new theme files are broken.
**Why it happens:** WordPress.com Atomic uses aggressive server-side caching. Even after cache flush via WP-CLI, CDN edge caches may serve stale content briefly.
**How to avoid:** Add cache-busting query parameter (`?nocache=$TIMESTAMP`) to verification URLs. Verify that the `deploy-theme.sh` cache flush runs BEFORE verification starts. Consider a short delay (2-3 seconds) between cache flush and verification to allow propagation.
**Warning signs:** Verification passes immediately after deploy but site shows old content in browser.

### Pitfall 2: Maintenance Mode Still Active During Verification
**What goes wrong:** Verification runs while maintenance mode is still enabled, getting HTTP 503 instead of 200.
**Why it happens:** The pipeline runs verify immediately after deploy, but `deploy-theme.sh` may not have finished deactivating maintenance mode.
**How to avoid:** The pipeline orchestrator calls `deploy-theme.sh` as a blocking subprocess. When it returns, maintenance mode is already deactivated (guaranteed by the script's normal flow or trap cleanup). Verification runs only after `deploy-theme.sh` exits successfully.
**Warning signs:** Intermittent 503 responses during verification.

### Pitfall 3: False Positive on Content Markers
**What goes wrong:** The content marker appears in a WordPress error message or default page, not in the actual theme content.
**Why it happens:** Using too generic a content marker (e.g., "SkyyRose" might appear in an error page title).
**How to avoid:** Use specific markers: CSS class names unique to the theme (`navbar__gradient-text`, `skyyrose-flagship`), specific HTML structures, or the theme version string. Check multiple markers per page.
**Warning signs:** Verification passes but the page is actually showing a WordPress error.

### Pitfall 4: Dry-Run Doesn't Test Build
**What goes wrong:** `--dry-run` skips the build step entirely, so users don't discover build failures until live deploy.
**Why it happens:** Build is treated as a "side effect" and skipped in dry-run.
**How to avoid:** In dry-run mode, STILL run the build step (it only modifies local files, no production impact). Only skip the deploy transfer and live verification. This way, dry-run catches build errors.
**Warning signs:** Dry-run passes but live deploy fails at the build step.

### Pitfall 5: curl Follows Redirects to Different Domain
**What goes wrong:** curl follows a redirect from `skyyrose.co` to `www.skyyrose.co` or vice versa, and the content check passes on the wrong URL.
**Why it happens:** WordPress may redirect based on `siteurl` setting.
**How to avoid:** Use `curl -L` to follow redirects (expected behavior), but log the final URL. The content verification validates the page content regardless of the redirect chain.
**Warning signs:** None typically -- redirects are normal WordPress behavior.

## Code Examples

### Deep Content Verification Script Skeleton
```bash
#!/usr/bin/env bash
# scripts/verify-deploy.sh -- Post-deploy deep health verification for skyyrose.co

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.wordpress}"

# Default site URL (overridable for testing)
SITE_URL="${WORDPRESS_URL:-https://skyyrose.co}"
TIMESTAMP="$(date +%s)"
FAILURES=0
CHECKS=0

# Page definitions: "name|path|content_marker"
HEALTH_CHECKS=(
    "Homepage|/|SkyyRose"
    "REST API|/index.php?rest_route=/|skyyrose"
    "Collection: Black Rose|/collection-black-rose/|Black Rose"
    "Collection: Love Hurts|/collection-love-hurts/|Love Hurts"
    "Collection: Signature|/collection-signature/|Signature"
    "About|/about/|SkyyRose"
)

verify_page() {
    local name="$1" url="$2" marker="$3"
    CHECKS=$((CHECKS + 1))

    local response http_code body
    response=$(curl -sSL -w "\n%{http_code}" \
        --connect-timeout 10 --max-time 30 \
        --retry 2 --retry-delay 3 \
        "${url}?_verify=${TIMESTAMP}" 2>/dev/null || echo -e "\n000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" -ne 200 ]]; then
        log_error "$name: HTTP $http_code (expected 200)"
        FAILURES=$((FAILURES + 1))
        return 1
    fi

    if ! echo "$body" | grep -qi "$marker"; then
        log_error "$name: Content marker '$marker' not found in response"
        FAILURES=$((FAILURES + 1))
        return 1
    fi

    log_success "$name: HTTP 200 + content verified"
    return 0
}
```

### Pipeline Orchestrator Skeleton
```bash
#!/usr/bin/env bash
# scripts/deploy-pipeline.sh -- Full deploy pipeline: build -> transfer -> verify

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
THEME_DIR="$PROJECT_ROOT/wordpress-theme/skyyrose-flagship"

DRY_RUN=false

main() {
    parse_args "$@"

    log_info "=== SkyyRose Deploy Pipeline ==="

    # Step 1: Build (always runs, even in dry-run -- local-only operation)
    log_info "[1/3] Building theme assets..."
    (cd "$THEME_DIR" && npm run build)
    log_success "[1/3] Build complete"

    # Step 2: Deploy (passes --dry-run if set)
    log_info "[2/3] Deploying to production..."
    if [[ "$DRY_RUN" == "true" ]]; then
        bash "$SCRIPT_DIR/deploy-theme.sh" --dry-run
    else
        bash "$SCRIPT_DIR/deploy-theme.sh"
    fi
    log_success "[2/3] Deploy complete"

    # Step 3: Verify (skip in dry-run -- nothing was deployed)
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[3/3] [DRY RUN] Skipping verification (no deploy occurred)"
        log_info "[DRY RUN] Would verify: homepage, collections, REST API, about page"
    else
        log_info "[3/3] Verifying deployment..."
        bash "$SCRIPT_DIR/verify-deploy.sh"
        log_success "[3/3] Verification passed"
    fi

    log_success "=== Pipeline complete ==="
}
```

### WordPress REST API Health Check
```bash
# Source: WordPress REST API discovery endpoint
# WordPress exposes site info at the REST API root.
# Use index.php?rest_route=/ (not /wp-json/) per CLAUDE.md WordPress Rules.
verify_rest_api() {
    local url="${SITE_URL}/index.php?rest_route=/"
    local response
    response=$(curl -sS --connect-timeout 10 --max-time 15 "$url" 2>/dev/null || echo "")

    # Check for WordPress REST API markers
    if echo "$response" | grep -q '"namespaces"'; then
        log_success "REST API: responsive, namespaces present"
        return 0
    fi

    log_error "REST API: no valid response from $url"
    return 1
}
```

### Content Markers for Key Pages
```bash
# Specific, verifiable markers unique to the SkyyRose theme
# These are NOT generic strings -- they come from the theme's HTML output

# Homepage: Check for navbar brand text (from header.php line 48)
# The header outputs "SKYY ROSE" in a span.navbar__gradient-text
HOMEPAGE_MARKER="SKYY ROSE"

# Collection pages: Check for collection-specific content
# template-collection-black-rose.php outputs "Black Rose" in page content
BLACKROSE_MARKER="Black Rose"

# REST API: Check for WordPress REST API namespace list
# index.php?rest_route=/ returns JSON with "namespaces" array
RESTAPI_MARKER="namespaces"

# About page: Check for brand name
ABOUT_MARKER="SkyyRose"

# WooCommerce check: Verify WC REST namespace exists
WC_MARKER="wc/v3"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual browser check after deploy | Automated curl-based content verification | Standard practice | Catches broken deploys immediately without human intervention |
| Separate build + deploy + verify commands | Single orchestrator script | Standard practice | Zero manual steps between build and verification |
| All-or-nothing deploy | Dry-run preview of full pipeline | Standard practice | Operators can validate the pipeline without risk |
| HTTP 200-only health checks | Content-aware deep health checks | Industry evolution | Catches "white screen of death" and partial failures |

**Deprecated/outdated:**
- `scripts/verify_skyyrose_site.py`: Uses `aiohttp` + `BeautifulSoup` which adds Python dependencies. Bash curl approach is simpler for the deploy pipeline.
- `scripts/wordpress_health_check.py`: Comprehensive but uses `httpx` (async Python). Too heavyweight for a post-deploy check integrated into a bash pipeline.

## Open Questions

1. **What content markers reliably identify a functioning SkyyRose theme?**
   - What we know: The header.php outputs "SKYY ROSE" in the navbar. Collection pages output collection names. The REST API root returns JSON with "namespaces".
   - What's unclear: Whether WordPress.com might serve a cached maintenance page or fallback theme that also contains some of these markers.
   - Recommendation: Use multiple markers per critical page (brand name + theme-specific CSS class). The combination makes false positives extremely unlikely.

2. **Should the build step run in dry-run mode?**
   - What we know: `npm run build` only modifies local `.min.js` and `.min.css` files. It has no production side effects.
   - What's unclear: Whether users expect `--dry-run` to be completely side-effect free (not even local changes).
   - Recommendation: Run the build in dry-run mode. It validates the build works and catches errors early. The modified files are local only. Document this behavior in the script's help text.

3. **How long should verification wait after deploy before checking pages?**
   - What we know: `deploy-theme.sh` flushes WP caches (object cache, transients, rewrite rules) before exiting. WordPress.com CDN may have edge cache TTLs.
   - What's unclear: Exact CDN cache invalidation timing on WordPress.com Atomic.
   - Recommendation: Add a configurable delay (default 3 seconds) between deploy completion and verification start. Use cache-busting query parameters on verification URLs. Document that CDN propagation may cause brief stale content.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | bash + pytest (subprocess testing, same as Phase 7) |
| Config file | tests/conftest.py (existing) |
| Quick run command | `bash scripts/deploy-pipeline.sh --dry-run` |
| Full suite command | `pytest tests/scripts/test_verify_deploy.py tests/scripts/test_deploy_pipeline.py -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEPLOY-04 | verify-deploy.sh checks HTTP status AND content markers | unit (subprocess) | `pytest tests/scripts/test_verify_deploy.py -x` | Wave 0 |
| DEPLOY-05 | deploy-pipeline.sh runs build -> deploy -> verify in sequence | unit (subprocess dry-run) | `pytest tests/scripts/test_deploy_pipeline.py -x` | Wave 0 |
| DEPLOY-06 | deploy-pipeline.sh --dry-run shows pipeline without executing | unit (subprocess) | `bash scripts/deploy-pipeline.sh --dry-run` | Wave 0 |

### Sampling Rate
- **Per task commit:** `bash scripts/deploy-pipeline.sh --dry-run`
- **Per wave merge:** `bash scripts/deploy-pipeline.sh --dry-run && shellcheck scripts/verify-deploy.sh scripts/deploy-pipeline.sh`
- **Phase gate:** Full pytest suite green + dry-run passes + shellcheck clean

### Wave 0 Gaps
- [ ] `scripts/verify-deploy.sh` -- post-deploy content verification script
- [ ] `scripts/deploy-pipeline.sh` -- orchestration pipeline script
- [ ] `tests/scripts/test_verify_deploy.py` -- subprocess tests for verification script
- [ ] `tests/scripts/test_deploy_pipeline.py` -- subprocess tests for pipeline script

*(Tests validate script behavior via subprocess invocations and dry-run mode. Actual live site verification requires production access and is manual-only.)*

## Sources

### Primary (HIGH confidence)
- `scripts/deploy-theme.sh` -- Phase 7 deploy script (deploy core, already implemented and human-approved)
- `scripts/smoke-test.sh` -- existing smoke test with `test_endpoint()` pattern: curl + status code + content grep
- `wordpress-theme/skyyrose-flagship/deploy.sh` -- existing deploy script with `run_remote_health_check()` and `run_local_health_check()` patterns
- `wordpress-theme/skyyrose-flagship/header.php` -- confirmed "SKYY ROSE" brand text in navbar (line 48, `navbar__gradient-text`)
- `scripts/wp-deploy-theme.sh` -- existing full deploy script with page creation, menu setup, and cache flush patterns
- `CLAUDE.md` -- WordPress Rules: use `index.php?rest_route=` NOT `/wp-json/` for REST API

### Secondary (MEDIUM confidence)
- `scripts/wordpress_health_check.py` -- comprehensive health check patterns (HTTP checks, version verification, page functionality)
- `scripts/verify_skyyrose_site.py` -- site verification patterns (URL checking, content validation)

### Tertiary (LOW confidence)
- WordPress.com CDN cache invalidation timing -- no definitive documentation on how quickly edge caches clear after WP-CLI cache flush. The 3-second delay + cache-busting parameter is a pragmatic workaround.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all tools are already installed and used in existing scripts (curl, grep, bash, npm)
- Architecture: HIGH -- pipeline pattern is well-established; existing scripts provide proven patterns for every component
- Pitfalls: HIGH -- based on direct analysis of WordPress.com hosting behavior, existing deploy scripts, and theme source code
- Content markers: MEDIUM -- verified from header.php source but not tested against live site response

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (stable domain, tools unlikely to change)
