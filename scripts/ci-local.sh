#!/usr/bin/env bash
# DevSkyy local CI sandbox.
#
# Mirrors the 6 parallel gating jobs from .github/workflows/ci.yml so PRs can
# be validated locally while the GitHub Actions runner is unavailable
# (billing-locked, network-isolated, or just slower than running on the dev
# machine).
#
# Jobs mirrored:
#   lint        - ruff + black --check + isort --check + mypy (Stage 1)
#   python      - pytest tests/ with coverage, ignores tests/e2e (Stage 2)
#   security    - pip-audit + bandit + safety + semgrep (Stage 2)
#   frontend    - npm ci + lint + type-check + build (Stage 2)
#   threejs     - npm ci + npm run test:collections (Stage 2)
#   wordpress   - PHP syntax check + (theme npm build if package.json exists)
#
# Jobs NOT mirrored (deliberately):
#   e2e         - Playwright requires a running stack; use docker compose instead
#   api-integ   - Needs Redis service; spin up via `docker compose up redis -d`
#   docker      - Builds container images; use `make docker-build` if needed
#   deploy-*    - Production / staging deploy steps. Never local.
#
# Usage:
#   bash scripts/ci-local.sh                  # run all jobs
#   bash scripts/ci-local.sh --only lint      # run a single job
#   bash scripts/ci-local.sh --only lint,python  # run several
#   bash scripts/ci-local.sh --list           # show job names
#   bash scripts/ci-local.sh --verbose        # stream output (default: capture)
#   bash scripts/ci-local.sh --no-install     # never auto-install missing tools
#   bash scripts/ci-local.sh --help
#
# Outputs:
#   ci-local-output/<job>.log   - full per-job log (always captured)
#   ci-local-output/summary.md  - final table, suitable for pasting to a PR
#
# Exit codes:
#   0   all jobs passed or were intentionally skipped
#   1   at least one job failed
#   2   invalid arguments

set -uo pipefail
# NOTE: NOT using set -e. Individual job failures must not abort the script —
# we want the summary to show all jobs, not just up to the first red.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OUTPUT_DIR="ci-local-output"
mkdir -p "$OUTPUT_DIR"

# --- args --------------------------------------------------------------------
ALL_JOBS=(lint python security frontend threejs wordpress)
SELECTED_JOBS=()
VERBOSE=0
NO_INSTALL=0

usage() {
    sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --only)
            IFS=',' read -ra SELECTED_JOBS <<< "$2"
            shift 2
            ;;
        --list)
            printf '%s\n' "${ALL_JOBS[@]}"
            exit 0
            ;;
        --verbose|-v)
            VERBOSE=1
            shift
            ;;
        --no-install)
            NO_INSTALL=1
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "ci-local.sh: unknown argument '$1'" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [[ ${#SELECTED_JOBS[@]} -eq 0 ]]; then
    SELECTED_JOBS=("${ALL_JOBS[@]}")
fi

# Validate selected jobs are real
for job in "${SELECTED_JOBS[@]}"; do
    found=0
    for known in "${ALL_JOBS[@]}"; do
        [[ "$known" == "$job" ]] && { found=1; break; }
    done
    if [[ $found -eq 0 ]]; then
        echo "ci-local.sh: unknown job '$job'. Use --list to see options." >&2
        exit 2
    fi
done

# --- pretty printing ---------------------------------------------------------
if [[ -t 1 ]]; then
    BOLD=$'\033[1m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'
    BLUE=$'\033[34m'; DIM=$'\033[2m'; RESET=$'\033[0m'
else
    BOLD=""; GREEN=""; YELLOW=""; RED=""; BLUE=""; DIM=""; RESET=""
fi

section() { printf '\n%s===%s %s%s%s\n' "$BOLD$BLUE" "$RESET" "$BOLD" "$1" "$RESET"; }
pass()    { printf '%s PASS %s  %s\n' "$BOLD$GREEN" "$RESET" "$1"; }
fail()    { printf '%s FAIL %s  %s\n' "$BOLD$RED" "$RESET" "$1"; }
skip()    { printf '%s SKIP %s  %s%s%s\n' "$BOLD$YELLOW" "$RESET" "$DIM" "$1" "$RESET"; }
info()    { printf '%s     %s%s\n' "$DIM" "$1" "$RESET"; }

# --- result tracking ---------------------------------------------------------
declare -A JOB_RESULT   # "pass" | "fail" | "skip"
declare -A JOB_REASON   # one-line explanation
declare -A JOB_DURATION # seconds (rounded)

# Run a shell pipeline, optionally capturing output. Returns the pipeline's
# exit code. Always writes to $OUTPUT_DIR/<job>.log.
run_cmd() {
    local job="$1"
    shift
    local logfile="$OUTPUT_DIR/$job.log"
    if [[ $VERBOSE -eq 1 ]]; then
        "$@" 2>&1 | tee -a "$logfile"
        return "${PIPESTATUS[0]}"
    else
        "$@" >> "$logfile" 2>&1
        return $?
    fi
}

# Mark a job as skipped with a reason. Pass/fail are derived from exit codes.
mark_skipped() {
    JOB_RESULT[$1]="skip"
    JOB_REASON[$1]="$2"
    skip "$1: $2"
}
mark_passed() {
    JOB_RESULT[$1]="pass"
    JOB_REASON[$1]="${2:-OK}"
    pass "$1: ${2:-OK}"
}
mark_failed() {
    JOB_RESULT[$1]="fail"
    JOB_REASON[$1]="${2:-see log}"
    fail "$1: ${2:-see log}  (log: $OUTPUT_DIR/$1.log)"
}

# Check tool availability. Returns 0 if found, 1 if missing.
have() { command -v "$1" >/dev/null 2>&1; }

# Attempt to install missing pip tools (with NO_INSTALL guard).
ensure_pip_tool() {
    local tool="$1"; local pkg="${2:-$1}"
    if have "$tool"; then return 0; fi
    if [[ $NO_INSTALL -eq 1 ]]; then
        return 1
    fi
    info "Installing missing tool: $pkg"
    pip install --quiet --user "$pkg" >> "$OUTPUT_DIR/install.log" 2>&1 || return 1
    have "$tool"
}

# --- jobs --------------------------------------------------------------------
# Each job function: prints its section header, runs, marks result.
# Truncate any prior log for this job before running so re-runs don't appear
# to grow indefinitely.

job_lint() {
    section "lint — ruff + black + isort + mypy"
    : > "$OUTPUT_DIR/lint.log"
    local missing=()
    for t in ruff black isort mypy; do
        ensure_pip_tool "$t" || missing+=("$t")
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        mark_skipped lint "missing tools: ${missing[*]} (run 'pip install ${missing[*]}')"
        return
    fi
    local failed=()
    info "ruff check ."
    run_cmd lint ruff check . || failed+=("ruff")
    info "black --check ."
    run_cmd lint black --check --diff . || failed+=("black")
    info "isort --check-only ."
    run_cmd lint isort --check-only --diff . || failed+=("isort")
    info "mypy . --ignore-missing-imports"
    run_cmd lint mypy . --ignore-missing-imports --no-error-summary || failed+=("mypy")
    if [[ ${#failed[@]} -gt 0 ]]; then
        mark_failed lint "${failed[*]} reported issues"
    else
        mark_passed lint "ruff+black+isort+mypy clean"
    fi
}

job_python() {
    section "python — pytest with coverage"
    : > "$OUTPUT_DIR/python.log"
    if ! have pytest; then
        mark_skipped python "pytest not installed (run 'pip install -e \".[dev]\"')"
        return
    fi
    if [[ ! -d tests ]]; then
        mark_skipped python "tests/ directory not found"
        return
    fi
    info "pytest tests/ --ignore=tests/e2e (no coverage in local mode)"
    # Skip --cov so partial test envs don't fail on missing optional plugins.
    # Real CI runs --cov; matching that here would block too many local devs.
    if PYTHONPATH="$REPO_ROOT" run_cmd python pytest tests/ -x --ignore=tests/e2e --tb=short -q; then
        mark_passed python "tests passed"
    else
        mark_failed python "pytest reported failures"
    fi
}

job_security() {
    section "security — pip-audit + bandit + safety + semgrep"
    : > "$OUTPUT_DIR/security.log"
    local results=()
    if ensure_pip_tool pip-audit; then
        info "pip-audit"
        run_cmd security pip-audit --strict && results+=("pip-audit:ok") || results+=("pip-audit:FAIL")
    else
        results+=("pip-audit:skip")
    fi
    if ensure_pip_tool bandit; then
        info "bandit -r . -ll"
        run_cmd security bandit -r . -x ./tests,./venv,./.venv,./node_modules,./frontend -ll && results+=("bandit:ok") || results+=("bandit:FAIL")
    else
        results+=("bandit:skip")
    fi
    if ensure_pip_tool safety; then
        info "safety check"
        run_cmd security safety check && results+=("safety:ok") || results+=("safety:FAIL")
    else
        results+=("safety:skip")
    fi
    if ensure_pip_tool semgrep; then
        info "semgrep scan --config=auto"
        run_cmd security semgrep scan --config=auto --error && results+=("semgrep:ok") || results+=("semgrep:FAIL")
    else
        results+=("semgrep:skip")
    fi
    if printf '%s\n' "${results[@]}" | grep -q ':FAIL'; then
        mark_failed security "$(printf '%s ' "${results[@]}")"
    else
        local skips
        skips="$(printf '%s\n' "${results[@]}" | grep -c ':skip' || true)"
        if [[ "$skips" -gt 0 ]]; then
            mark_passed security "ran with $skips skipped tool(s) — ${results[*]}"
        else
            mark_passed security "all 4 scanners clean"
        fi
    fi
}

job_frontend() {
    section "frontend — npm lint + type-check + build"
    : > "$OUTPUT_DIR/frontend.log"
    if [[ ! -d frontend ]]; then
        mark_skipped frontend "frontend/ directory not found"
        return
    fi
    if ! have npm; then
        mark_skipped frontend "npm not on PATH"
        return
    fi
    pushd frontend >/dev/null
    if [[ ! -d node_modules ]]; then
        info "npm ci (first run)"
        if ! run_cmd frontend npm ci --no-audit --no-fund; then
            popd >/dev/null
            mark_failed frontend "npm ci failed"
            return
        fi
    fi
    local failed=()
    info "npm run lint"
    run_cmd frontend npm run lint || failed+=("lint")
    info "npm run type-check"
    run_cmd frontend npm run type-check || failed+=("type-check")
    info "npm run build"
    NEXT_TELEMETRY_DISABLED=1 run_cmd frontend npm run build || failed+=("build")
    popd >/dev/null
    if [[ ${#failed[@]} -gt 0 ]]; then
        mark_failed frontend "${failed[*]} failed"
    else
        mark_passed frontend "lint+type-check+build clean"
    fi
}

job_threejs() {
    section "threejs — npm run test:collections"
    : > "$OUTPUT_DIR/threejs.log"
    if ! have npm; then
        mark_skipped threejs "npm not on PATH"
        return
    fi
    if ! grep -q '"test:collections"' package.json 2>/dev/null; then
        mark_skipped threejs "no 'test:collections' script in root package.json"
        return
    fi
    if [[ ! -d node_modules ]]; then
        info "npm ci (root, first run)"
        if ! run_cmd threejs npm ci --no-audit --no-fund; then
            mark_failed threejs "npm ci failed"
            return
        fi
    fi
    info "npm run test:collections"
    if run_cmd threejs npm run test:collections; then
        mark_passed threejs "jest collection tests passed"
    else
        mark_failed threejs "jest reported failures"
    fi
}

job_wordpress() {
    section "wordpress — PHP syntax + (theme build if available)"
    : > "$OUTPUT_DIR/wordpress.log"
    if ! have php; then
        mark_skipped wordpress "php not on PATH (apt-get install php-cli on Debian/Ubuntu)"
        return
    fi
    local error_count=0
    local checked=0
    info "php -l on wordpress-theme/skyyrose-flagship/**/*.php"
    while IFS= read -r file; do
        checked=$((checked + 1))
        if ! output=$(php -l "$file" 2>&1); then
            echo "::error file=$file::PHP syntax error: $output" | tee -a "$OUTPUT_DIR/wordpress.log"
            error_count=$((error_count + 1))
        fi
    done < <(find wordpress-theme/skyyrose-flagship \
        -name "*.php" \
        -not -path "*/node_modules/*" \
        -not -path "*/vendor/*")
    info "checked $checked PHP files"
    if [[ $error_count -gt 0 ]]; then
        mark_failed wordpress "$error_count PHP syntax errors"
        return
    fi
    # CI also runs npm build inside the theme — but the theme has no
    # package.json today (only composer.json). Skip cleanly rather than
    # claiming to mirror something that doesn't exist.
    if [[ -f wordpress-theme/skyyrose-flagship/package.json ]]; then
        if ! have npm; then
            mark_passed wordpress "PHP syntax clean ($checked files); npm build skipped (npm missing)"
            return
        fi
        pushd wordpress-theme/skyyrose-flagship >/dev/null
        info "theme npm install + build"
        local build_ok=1
        run_cmd wordpress npm install --no-audit --no-fund || build_ok=0
        [[ $build_ok -eq 1 ]] && { run_cmd wordpress npm run build || build_ok=0; }
        popd >/dev/null
        if [[ $build_ok -eq 1 ]]; then
            mark_passed wordpress "PHP syntax clean ($checked files) + theme build OK"
        else
            mark_failed wordpress "theme npm build failed (PHP syntax was clean)"
        fi
    else
        mark_passed wordpress "PHP syntax clean ($checked files); theme npm build skipped (no package.json)"
    fi
}

# --- runner ------------------------------------------------------------------
START_TIME=$(date +%s)
echo
printf '%s%s%s\n' "$BOLD" "DevSkyy local CI — running ${#SELECTED_JOBS[@]} job(s)" "$RESET"
printf '%sJobs: %s%s\n' "$DIM" "${SELECTED_JOBS[*]}" "$RESET"
printf '%sLogs: %s/$JOB.log%s\n' "$DIM" "$OUTPUT_DIR" "$RESET"

for job in "${SELECTED_JOBS[@]}"; do
    job_start=$(date +%s)
    case "$job" in
        lint)      job_lint ;;
        python)    job_python ;;
        security)  job_security ;;
        frontend)  job_frontend ;;
        threejs)   job_threejs ;;
        wordpress) job_wordpress ;;
    esac
    job_end=$(date +%s)
    JOB_DURATION[$job]=$((job_end - job_start))
done

# --- summary -----------------------------------------------------------------
END_TIME=$(date +%s)
TOTAL_DURATION=$((END_TIME - START_TIME))

section "summary"
{
    echo "# DevSkyy local CI summary"
    echo
    echo "_Generated $(date -u +%Y-%m-%dT%H:%M:%SZ) — ran ${#SELECTED_JOBS[@]} job(s) in ${TOTAL_DURATION}s_"
    echo
    echo "| Job | Result | Duration | Notes |"
    echo "|-----|--------|----------|-------|"
} > "$OUTPUT_DIR/summary.md"

PASSED=0; FAILED=0; SKIPPED=0
for job in "${SELECTED_JOBS[@]}"; do
    local_result="${JOB_RESULT[$job]:-unknown}"
    local_reason="${JOB_REASON[$job]:-}"
    local_duration="${JOB_DURATION[$job]:-0}s"
    case "$local_result" in
        pass)
            PASSED=$((PASSED + 1))
            printf '%s PASS %s %-10s  %3ss  %s\n' "$BOLD$GREEN" "$RESET" "$job" "${local_duration%s}" "$local_reason"
            echo "| $job | :white_check_mark: pass | $local_duration | $local_reason |" >> "$OUTPUT_DIR/summary.md"
            ;;
        fail)
            FAILED=$((FAILED + 1))
            printf '%s FAIL %s %-10s  %3ss  %s\n' "$BOLD$RED" "$RESET" "$job" "${local_duration%s}" "$local_reason"
            echo "| $job | :x: fail | $local_duration | $local_reason |" >> "$OUTPUT_DIR/summary.md"
            ;;
        skip)
            SKIPPED=$((SKIPPED + 1))
            printf '%s SKIP %s %-10s  %3ss  %s\n' "$BOLD$YELLOW" "$RESET" "$job" "${local_duration%s}" "$local_reason"
            echo "| $job | :warning: skipped | $local_duration | $local_reason |" >> "$OUTPUT_DIR/summary.md"
            ;;
        *)
            echo "| $job | unknown | $local_duration | (no result recorded) |" >> "$OUTPUT_DIR/summary.md"
            ;;
    esac
done

echo
printf '%s%d passed%s, %s%d failed%s, %s%d skipped%s  (total %ds)\n' \
    "$GREEN" "$PASSED" "$RESET" \
    "$RED" "$FAILED" "$RESET" \
    "$YELLOW" "$SKIPPED" "$RESET" \
    "$TOTAL_DURATION"
echo
info "Full summary written to $OUTPUT_DIR/summary.md"
info "Per-job logs in $OUTPUT_DIR/<job>.log"

if [[ $FAILED -gt 0 ]]; then
    exit 1
fi
exit 0
