#!/bin/bash
# dispatch.sh — orchestrator wrapper that runs the full agent dispatch flow:
#   1. Resolve agent brief (read JSON + inject founder feedback)
#   2. (Caller invokes Agent tool — this script can't dispatch agents itself)
#   3. After agent reports DONE, run validate-deliverable.sh
#   4. If validator REJECTED, surface re-dispatch instruction
#   5. If validator ACCEPTED, run saas-gate.sh against any HTML deliverable
#   6. Print orchestrator status for Stage 2 entry
#
# Usage:
#   bash dispatch.sh <agent-slug> <deliverable-manifest.json> [--html <html-path>]
#
# Example:
#   bash dispatch.sh ux-architect /tmp/ux-deliverable.json --html docs/brand/design-mockups/v2.html

set -uo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT="${1:-}"
MANIFEST="${2:-}"
HTML=""

shift 2 || { echo "usage: dispatch.sh <agent-slug> <manifest> [--html <path>]" >&2; exit 2; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --html) shift; HTML="$1" ;;
    *) ;;
  esac
  shift || true
done

echo "═══════════════════════════════════════════════════════════════════"
echo " Pipeline Dispatch Wrapper — $AGENT"
echo "═══════════════════════════════════════════════════════════════════"

# Verify brief exists
BRIEF="$SKILL_ROOT/prompts/$AGENT.json"
if [[ ! -f "$BRIEF" ]]; then
  echo "✗ Brief not found: $BRIEF"
  exit 2
fi
echo "  ✓ Brief: $BRIEF"

# Verify manifest exists
if [[ ! -f "$MANIFEST" ]]; then
  echo "✗ Manifest not found: $MANIFEST"
  exit 2
fi
echo "  ✓ Manifest: $MANIFEST"

# Phase 1: Validate deliverable manifest
echo
echo "── Phase 1: Validate deliverable manifest ──"
if bash "$SKILL_ROOT/scripts/validate-deliverable.sh" "$MANIFEST"; then
  echo "  ✓ Manifest passed validation"
else
  echo
  echo "✗ DISPATCH REJECTED — re-dispatch with corrections"
  exit 1
fi

# Phase 2: SaaS gate (if HTML target provided)
if [[ -n "$HTML" && -f "$HTML" ]]; then
  echo
  echo "── Phase 2: SaaS Gate on $HTML ──"
  if bash "$SKILL_ROOT/scripts/saas-gate.sh" "$HTML"; then
    echo "  ✓ SaaS Gate passed"
  else
    echo
    echo "⚠ SaaS Gate failed — manifest passed but artifact has gaps"
    echo "  Manifest accepted (agent did its job), but the target file needs follow-up"
  fi
fi

# Phase 3: Memory write verification
echo
echo "── Phase 3: Memory write verification ──"
MEM_DIR="$SKILL_ROOT/memory/$AGENT"
MEM_COUNT_BEFORE=$(ls "$MEM_DIR" 2>/dev/null | grep -v "^INDEX.md$" | wc -l | tr -d ' ')
MEM_FROM_MANIFEST=$(python3 -c "import json; d=json.load(open('$MANIFEST')); print(len(d.get('memory_writes', [])))")
echo "  Memory dir: $MEM_DIR"
echo "  Files (excl INDEX): $MEM_COUNT_BEFORE"
echo "  Manifest claims memory_writes: $MEM_FROM_MANIFEST"

if [[ "$MEM_FROM_MANIFEST" -lt 1 ]]; then
  echo "  ⚠ Memory write mandate violation — agent must write ≥1 entry"
fi

echo
echo "═══════════════════════════════════════════════════════════════════"
echo " DISPATCH COMPLETE — agent output ready for Stage 2 synthesis"
echo "═══════════════════════════════════════════════════════════════════"
exit 0
