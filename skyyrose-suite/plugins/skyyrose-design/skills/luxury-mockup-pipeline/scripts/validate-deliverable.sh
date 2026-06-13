#!/bin/bash
# validate-deliverable.sh — runs JSON Schema validation against an agent's
# deliverable manifest. Orchestrator calls this AFTER each agent reports DONE
# and BEFORE the deliverable enters Stage 2 synthesis.
#
# Usage:
#   bash validate-deliverable.sh <deliverable-manifest.json>
#
# Exit codes:
#   0 = valid (SaaS Gate clear + schema valid + memory writes ≥ 1)
#   1 = schema invalid
#   2 = SaaS Gate failed
#   3 = memory write protocol violated (zero new entries)

set -uo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCHEMA="$SKILL_ROOT/schemas/deliverable.schema.json"
INPUT="${1:-}"

if [[ -z "$INPUT" || ! -f "$INPUT" ]]; then
  echo "usage: validate-deliverable.sh <deliverable-manifest.json>" >&2
  exit 2
fi

echo "═══════════════════════════════════════════════════════════════════"
echo " Deliverable Validation — $(basename "$INPUT")"
echo "═══════════════════════════════════════════════════════════════════"

# ─── V1: JSON parse ─────────────────────────────────────────────────────────
if ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$INPUT" 2>/dev/null; then
  echo "  ✗ JSON parse: invalid"
  exit 1
fi
echo "  ✓ JSON parse: valid"

# ─── V2: Schema validation (best-effort with jsonschema, fallback to python) ─
python3 - "$INPUT" "$SCHEMA" << 'PY'
import json, sys
data = json.load(open(sys.argv[1]))
schema = json.load(open(sys.argv[2]))

errors = []

# Required top-level fields
for f in schema.get('required', []):
    if f not in data:
        errors.append(f"missing required field: {f}")

# saas_gate sub-validation
sg = data.get('saas_gate', {})
required_gates = ['mobile_verified', 'images_optimized', 'sales_presentation_grade',
                  'accessibility_verified', 'performance_verified',
                  'self_contained_reading', 'conversion_ready_ctas']
for g in required_gates:
    if g not in sg:
        errors.append(f"missing saas_gate.{g}")
    elif not sg[g].get('passed', False):
        errors.append(f"saas_gate.{g} FAILED")

# ROI upgrade required
roi = data.get('roi_upgrade', {})
if not roi.get('proposed', False):
    errors.append("roi_upgrade.proposed must be true (mandate)")
if not roi.get('prefers_reduced_motion_safe', False):
    errors.append("roi_upgrade.prefers_reduced_motion_safe must be true (a11y)")

# Memory writes ≥ 1 (write protocol enforcement)
mw = data.get('memory_writes', [])
if len(mw) < 1:
    errors.append(f"memory_writes count {len(mw)} (mandate: at least 1 per dispatch)")

# Return summary word count
rs = data.get('return_summary', {})
wc = rs.get('word_count', 9999)
if wc > 280:
    errors.append(f"return_summary.word_count {wc} > 280 (token-aware violation)")

if errors:
    print("  ✗ Schema/protocol violations:")
    for e in errors:
        print(f"    - {e}")
    sys.exit(1)
else:
    print("  ✓ Schema valid")
    print(f"  ✓ All 7 SaaS gates passed")
    print(f"  ✓ ROI upgrade proposed + a11y-safe")
    print(f"  ✓ Memory writes: {len(mw)} entries")
    print(f"  ✓ Return summary: {wc} words")
PY

EXIT=$?
if [[ "$EXIT" -ne 0 ]]; then
  echo
  echo "VERDICT: REJECTED — agent re-dispatch required"
  exit "$EXIT"
fi

echo
echo "VERDICT: ACCEPTED — deliverable enters Stage 2 synthesis"
exit 0
