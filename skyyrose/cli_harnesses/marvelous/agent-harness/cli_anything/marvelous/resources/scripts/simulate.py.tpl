# cli-anything-marvelous — simulate script template
# Rendered via string.Template; placeholders use $${var} syntax.
#
# Variables:
#   project_path  — absolute path to .zpac or .zprj file to open
#   frames        — number of simulation frames (integer)
#   output_path   — absolute path to write resulting .zpac (after sim)
#
# Run inside Marvelous Designer via:
#   "Marvelous Designer" --script simulate.py
#
# API reference: https://developer.marvelousdesigner.com/scenario.html

import sys

try:
    import import_api
    import utility_api
    import export_api
except ImportError as e:
    print(f"[cli-anything] Failed to import MD API: {e}", file=sys.stderr)
    sys.exit(1)

PROJECT_PATH = r"${project_path}"
FRAMES       = int("${frames}")
OUTPUT_PATH  = r"${output_path}"

# ── Open project ──────────────────────────────────────────────────────────

print(f"[cli-anything] Opening project: {PROJECT_PATH}")
result = import_api.ImportZpac(PROJECT_PATH)
if not result:
    print(f"[cli-anything] ERROR: Could not open project '{PROJECT_PATH}'", file=sys.stderr)
    sys.exit(2)

# ── Simulate ──────────────────────────────────────────────────────────────

print(f"[cli-anything] Running simulation for {FRAMES} frames...")
utility_api.Simulate(FRAMES)
print(f"[cli-anything] Simulation complete.")

# ── Save result ───────────────────────────────────────────────────────────

print(f"[cli-anything] Saving result to: {OUTPUT_PATH}")
ok = export_api.ExportZpac(OUTPUT_PATH)
if not ok:
    print(f"[cli-anything] ERROR: Could not save simulated project to '{OUTPUT_PATH}'", file=sys.stderr)
    sys.exit(3)

print(f"[cli-anything] Saved: {OUTPUT_PATH}")
