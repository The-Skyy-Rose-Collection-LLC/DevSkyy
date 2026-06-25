#!/usr/bin/env bash
# =============================================================================
# ci-env/setup.sh — Build the isolated Python toolchain that scripts/ci-local.sh
# runs its lint / security / python-tests jobs against.
# =============================================================================
# Why a dedicated venv: ci-local.sh auto-activates ci-env/.venv if present, so
# the CI checks run against a pinned, reproducible toolchain instead of whatever
# happens to be on PATH (which on this machine is Python 3.14 — CI targets 3.11).
# This keeps the offline mirror honest while GitHub Actions billing is blocked.
#
# Tool versions mirror .github/workflows/ci.yml, which installs the tool layer
# UNPINNED (`pip install ruff black isort mypy` / `bandit pip-audit` /
# `pytest ...`). We install the same set so behaviour matches the cloud runner.
#
# Usage:
#   bash ci-env/setup.sh               # full: tools + project (editable) for pytest
#   bash ci-env/setup.sh --tools-only  # fast: lint/format/security tools only
#   PYTHON_BIN=python3.11 bash ci-env/setup.sh   # pin interpreter for exact parity
#
# After setup, run the mirror:
#   bash scripts/ci-local.sh           # all gating jobs
#   bash scripts/ci-local.sh lint      # one job
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
VENV="$HERE/.venv"
TOOLS_ONLY=0
[ "${1:-}" = "--tools-only" ] && TOOLS_ONLY=1

# CI uses Python 3.11. Prefer an exact match if available; fall back to python3.
PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if command -v python3.11 >/dev/null 2>&1; then PYTHON_BIN="python3.11"; else PYTHON_BIN="python3"; fi
fi

echo "── ci-env setup ────────────────────────────────────────────"
echo "interpreter : $PYTHON_BIN ($("$PYTHON_BIN" --version 2>&1))"
echo "venv        : $VENV"
echo "mode        : $([ "$TOOLS_ONLY" = 1 ] && echo 'tools-only' || echo 'full (tools + editable project)')"
case "$("$PYTHON_BIN" --version 2>&1)" in
  *3.11*) ;;
  *) echo "note        : CI runs Python 3.11 — this interpreter differs. For exact"
     echo "              parity use act/Docker (see ci-env/README.md) or install"
     echo "              python3.11 and re-run." ;;
esac
echo

[ -d "$VENV" ] || "$PYTHON_BIN" -m venv "$VENV"
# shellcheck disable=SC1091
. "$VENV/bin/activate"

python -m pip install --upgrade pip --quiet

echo "→ installing lint + format + security tools (mirrors ci.yml)"
pip install --quiet ruff black isort mypy bandit pip-audit

echo "→ installing pytest layer (mirrors ci.yml python-tests)"
pip install --quiet pytest pytest-asyncio pytest-cov pytest-xdist httpx

if [ "$TOOLS_ONLY" = 0 ]; then
  echo "→ installing project (editable, '.[dev]') so pytest can import it"
  if ! pip install --quiet -e "$ROOT/.[dev]"; then
    echo "  WARN: 'pip install -e .[dev]' failed (likely a 3.11-vs-$("$PYTHON_BIN" -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")') dep gap)."
    echo "  Lint/security/format still work. For python-tests parity, use act/Docker."
  fi
fi

echo
echo "✓ ci-env ready. Run:  bash scripts/ci-local.sh"
