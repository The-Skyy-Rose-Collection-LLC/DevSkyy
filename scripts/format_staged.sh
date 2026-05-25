#!/usr/bin/env bash
# scripts/format_staged.sh — Pre-format every git-staged file by type.
#
# Designed to run as the FIRST stage of a pre-commit hook so files arrive
# at the validator already normalized. The validator only fails on real
# semantic drift, not on whitespace/format noise.
#
# Usage:
#   bash scripts/format_staged.sh             # format staged files, re-stage
#   bash scripts/format_staged.sh --check     # report only, no writes (CI mode)
#   bash scripts/format_staged.sh --all       # format all tracked files (full repo pass)
#   SKIP_FORMAT=1 bash scripts/format_staged.sh   # bypass — useful for WIP commits
#
# Per-extension formatters (skipped silently if tool not installed):
#   *.py          → black --line-length 100 + ruff check --fix + isort
#   *.json        → python -m json.tool --indent=2 (preserves key order)
#   *.md          → trim trailing whitespace + ensure final newline
#   *.css         → npx --no-install stylelint --fix (from wordpress-theme/)
#   *.js / *.ts   → npx --no-install prettier --write (from project root)
#   *.php         → vendor/bin/phpcbf (from wordpress-theme/skyyrose-flagship/)
#   *.yaml *.yml  → trim trailing whitespace + ensure final newline
#
# Skipped paths (never formatted, even if staged):
#   - *.min.css, *.min.js (generated, do not reformat)
#   - vendor/, node_modules/, .git/, .venv/, .venv-*/
#   - .wolf/designqc-archive/, .wolf/designqc-captures/
#   - tasks/audit-*/ (frozen audit data)
#   - *.bak-* (backup files)
#   - dist/, build/, .next/ (build output)

set -uo pipefail

# ─── Bypass switch ─────────────────────────────────────────────────────
if [[ "${SKIP_FORMAT:-0}" == "1" ]]; then
	echo "[format] SKIP_FORMAT=1 — pre-format step bypassed"
	exit 0
fi

# ─── Flags ─────────────────────────────────────────────────────────────
CHECK_ONLY=false
ALL_TRACKED=false
for arg in "$@"; do
	case "$arg" in
		--check) CHECK_ONLY=true ;;
		--all)   ALL_TRACKED=true ;;
		*) ;;
	esac
done

# ─── Repo root + cd ────────────────────────────────────────────────────
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT" || exit 1

# ─── Color logging ─────────────────────────────────────────────────────
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

log()  { echo -e "${BLUE}[format]${NC} $*"; }
ok()   { echo -e "${GREEN}[format]${NC} $*"; }
warn() { echo -e "${YELLOW}[format]${NC} $*"; }

# ─── Path filter — skip generated / vendored / frozen ─────────────────
should_skip() {
	local f="$1"
	case "$f" in
		*.min.css|*.min.js) return 0 ;;
		vendor/*|*/vendor/*) return 0 ;;
		node_modules/*|*/node_modules/*) return 0 ;;
		.git/*|*/.git/*) return 0 ;;
		.venv/*|.venv-*/*) return 0 ;;
		.wolf/designqc-*/*) return 0 ;;
		tasks/audit-*/*) return 0 ;;
		dist/*|*/dist/*) return 0 ;;
		build/*|*/build/*) return 0 ;;
		.next/*|*/.next/*) return 0 ;;
		*.bak-*) return 0 ;;
	esac
	return 1
}

# ─── Collect targets ───────────────────────────────────────────────────
declare -a STAGED
if $ALL_TRACKED; then
	while IFS= read -r line; do STAGED+=("$line"); done < <(git ls-files)
	log "Mode: --all (every tracked file)"
else
	while IFS= read -r line; do STAGED+=("$line"); done < <(git diff --cached --name-only --diff-filter=ACM)
	log "Mode: staged files only (${#STAGED[@]} file(s))"
fi

if [[ ${#STAGED[@]} -eq 0 ]]; then
	log "Nothing to format."
	exit 0
fi

# ─── Bucket by extension ───────────────────────────────────────────────
declare -a PY=() JSON=() MD=() CSS=() JS=() PHP=() YAML=()
for f in "${STAGED[@]}"; do
	if should_skip "$f"; then continue; fi
	[[ -f "$f" ]] || continue
	case "$f" in
		*.py) PY+=("$f") ;;
		*.json) JSON+=("$f") ;;
		*.md) MD+=("$f") ;;
		*.css) CSS+=("$f") ;;
		*.js|*.ts|*.jsx|*.tsx) JS+=("$f") ;;
		*.php) PHP+=("$f") ;;
		*.yaml|*.yml) YAML+=("$f") ;;
	esac
done

CHANGED_FILES=()

# ─── Helper: track file mtime to detect changes ────────────────────────
record_if_changed() {
	local f="$1" before="$2"
	local after
	after=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null || echo "0")
	[[ "$before" != "$after" ]] && CHANGED_FILES+=("$f")
}

# ─── Python (black + ruff + isort) ─────────────────────────────────────
format_python() {
	[[ ${#PY[@]} -eq 0 ]] && return 0
	command -v black >/dev/null 2>&1 || { warn "black not installed — skipping ${#PY[@]} .py file(s)"; return 0; }
	log "Python: ${#PY[@]} file(s)"
	for f in "${PY[@]}"; do
		local before
		before=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null || echo "0")
		if $CHECK_ONLY; then
			black --check --quiet --line-length 100 "$f" >/dev/null 2>&1 || { warn "would reformat: $f"; }
		else
			black --quiet --line-length 100 "$f" >/dev/null 2>&1 || true
			command -v ruff  >/dev/null 2>&1 && ruff check --fix --quiet "$f" >/dev/null 2>&1 || true
			command -v isort >/dev/null 2>&1 && isort --quiet "$f" >/dev/null 2>&1 || true
			record_if_changed "$f" "$before"
		fi
	done
}

# ─── JSON (python json.tool, preserve order) ───────────────────────────
format_json() {
	[[ ${#JSON[@]} -eq 0 ]] && return 0
	log "JSON: ${#JSON[@]} file(s)"
	for f in "${JSON[@]}"; do
		local before tmp
		before=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null || echo "0")
		tmp="$(mktemp)"
		if python3 -m json.tool --indent=2 "$f" "$tmp" 2>/dev/null; then
			if $CHECK_ONLY; then
				diff -q "$f" "$tmp" >/dev/null 2>&1 || warn "would reformat: $f"
				rm -f "$tmp"
			else
				if ! diff -q "$f" "$tmp" >/dev/null 2>&1; then
					mv "$tmp" "$f"
					record_if_changed "$f" "$before"
				else
					rm -f "$tmp"
				fi
			fi
		else
			rm -f "$tmp"
			warn "invalid JSON, skipping: $f"
		fi
	done
}

# ─── Markdown / YAML (trim trailing ws + ensure final newline) ────────
format_text_normalize() {
	local label="$1"; shift
	local -a files=("$@")
	[[ ${#files[@]} -eq 0 ]] && return 0
	log "$label: ${#files[@]} file(s)"
	for f in "${files[@]}"; do
		local before tmp
		before=$(stat -f %m "$f" 2>/dev/null || stat -c %Y "$f" 2>/dev/null || echo "0")
		tmp="$(mktemp)"
		# Trim trailing whitespace, collapse trailing empty lines, ensure final newline.
		python3 - "$f" "$tmp" <<'PYEOF'
import sys
src, dst = sys.argv[1], sys.argv[2]
with open(src, 'r', encoding='utf-8', errors='replace') as fh:
    lines = [line.rstrip() + '\n' for line in fh]
while lines and lines[-1].strip() == '':
    lines.pop()
if lines:
    lines.append('') if not lines[-1].endswith('\n') else None
with open(dst, 'w', encoding='utf-8') as fh:
    fh.writelines(lines)
PYEOF
		if $CHECK_ONLY; then
			diff -q "$f" "$tmp" >/dev/null 2>&1 || warn "would normalize: $f"
			rm -f "$tmp"
		else
			if ! diff -q "$f" "$tmp" >/dev/null 2>&1; then
				mv "$tmp" "$f"
				record_if_changed "$f" "$before"
			else
				rm -f "$tmp"
			fi
		fi
	done
}

# ─── CSS (stylelint --fix from wordpress-theme/) ──────────────────────
format_css() {
	[[ ${#CSS[@]} -eq 0 ]] && return 0
	if [[ ! -d wordpress-theme/node_modules/stylelint ]]; then
		warn "stylelint not installed (wordpress-theme/node_modules) — skipping ${#CSS[@]} .css file(s)"
		return 0
	fi
	log "CSS: ${#CSS[@]} file(s)"
	local -a rel=()
	for f in "${CSS[@]}"; do
		case "$f" in
			wordpress-theme/*) rel+=("${f#wordpress-theme/}") ;;
			*) rel+=("$f") ;;
		esac
	done
	(cd wordpress-theme && \
		if $CHECK_ONLY; then \
			npx --no-install stylelint "${rel[@]}" 2>&1 | grep -v "^$" || true; \
		else \
			npx --no-install stylelint --fix "${rel[@]}" >/dev/null 2>&1 || true; \
		fi)
	for f in "${CSS[@]}"; do record_if_changed "$f" "0"; done
}

# ─── JS / TS (prettier --write from project root) ─────────────────────
format_js() {
	[[ ${#JS[@]} -eq 0 ]] && return 0
	if [[ ! -d frontend/node_modules/prettier && ! -d wordpress-theme/node_modules/prettier ]]; then
		warn "prettier not installed — skipping ${#JS[@]} .js/.ts file(s)"
		return 0
	fi
	log "JS/TS: ${#JS[@]} file(s)"
	# Run prettier from whichever node_modules has it. Prefer frontend/ for frontend files.
	local frontend_files=() theme_files=()
	for f in "${JS[@]}"; do
		case "$f" in
			frontend/*) frontend_files+=("${f#frontend/}") ;;
			wordpress-theme/*) theme_files+=("${f#wordpress-theme/}") ;;
			*) theme_files+=("$f") ;;
		esac
	done
	if [[ ${#frontend_files[@]} -gt 0 && -d frontend/node_modules/prettier ]]; then
		(cd frontend && \
			if $CHECK_ONLY; then \
				npx --no-install prettier --check "${frontend_files[@]}" >/dev/null 2>&1 || warn "frontend prettier diffs"; \
			else \
				npx --no-install prettier --write "${frontend_files[@]}" >/dev/null 2>&1 || true; \
			fi)
	fi
	if [[ ${#theme_files[@]} -gt 0 && -d wordpress-theme/node_modules/prettier ]]; then
		(cd wordpress-theme && \
			if $CHECK_ONLY; then \
				npx --no-install prettier --check "${theme_files[@]}" >/dev/null 2>&1 || warn "theme prettier diffs"; \
			else \
				npx --no-install prettier --write "${theme_files[@]}" >/dev/null 2>&1 || true; \
			fi)
	fi
	for f in "${JS[@]}"; do record_if_changed "$f" "0"; done
}

# ─── PHP (vendor/bin/phpcbf inside skyyrose-flagship) ─────────────────
format_php() {
	[[ ${#PHP[@]} -eq 0 ]] && return 0
	local phpcbf="wordpress-theme/skyyrose-flagship/vendor/bin/phpcbf"
	if [[ ! -x "$phpcbf" ]]; then
		warn "phpcbf not installed (run composer install) — skipping ${#PHP[@]} .php file(s)"
		return 0
	fi
	log "PHP: ${#PHP[@]} file(s)"
	# phpcbf paths are relative to where the tool sees them — use absolute.
	local -a abs=()
	for f in "${PHP[@]}"; do abs+=("$REPO_ROOT/$f"); done
	if $CHECK_ONLY; then
		(cd wordpress-theme/skyyrose-flagship && ./vendor/bin/phpcs --standard=.phpcs.xml "${abs[@]}" >/dev/null 2>&1) || warn "phpcs diffs in PHP files"
	else
		(cd wordpress-theme/skyyrose-flagship && ./vendor/bin/phpcbf --standard=.phpcs.xml "${abs[@]}" >/dev/null 2>&1) || true
		for f in "${PHP[@]}"; do record_if_changed "$f" "0"; done
	fi
}

# ─── Run all ───────────────────────────────────────────────────────────
format_python
format_json
format_text_normalize "Markdown" "${MD[@]}"
format_text_normalize "YAML"     "${YAML[@]}"
format_css
format_js
format_php

# ─── Re-stage modified files (unless --check or --all) ────────────────
if ! $CHECK_ONLY && ! $ALL_TRACKED && [[ ${#CHANGED_FILES[@]} -gt 0 ]]; then
	log "Re-staging ${#CHANGED_FILES[@]} reformatted file(s):"
	for f in "${CHANGED_FILES[@]}"; do echo "    $f"; done
	git add -- "${CHANGED_FILES[@]}"
fi

if [[ ${#CHANGED_FILES[@]} -eq 0 ]]; then
	ok "All files already clean."
else
	ok "Formatted ${#CHANGED_FILES[@]} file(s)."
fi
