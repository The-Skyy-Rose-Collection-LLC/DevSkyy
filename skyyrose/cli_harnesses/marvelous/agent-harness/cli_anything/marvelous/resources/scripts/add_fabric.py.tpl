# cli-anything-marvelous — add_fabric script template
# Rendered via string.Template; placeholders use $${var} syntax.
#
# Variables:
#   project_path   — absolute path to .zpac or .zprj file to open
#   pattern_name   — name of the pattern piece to assign fabric to
#   fabric_name    — display name for the new fabric
#   texture_path   — absolute path to fabric texture image (png/jpg)
#   output_path    — absolute path to save modified .zpac
#
# Run inside Marvelous Designer via:
#   "Marvelous Designer" --script add_fabric.py
#
# API reference: https://developer.marvelousdesigner.com/scenario.html

import sys

try:
    import import_api
    import fabric_api
    import export_api
except ImportError as e:
    print(f"[cli-anything] Failed to import MD API: {e}", file=sys.stderr)
    sys.exit(1)

PROJECT_PATH = r"${project_path}"
PATTERN_NAME = "${pattern_name}"
FABRIC_NAME  = "${fabric_name}"
TEXTURE_PATH = r"${texture_path}"
OUTPUT_PATH  = r"${output_path}"

# ── Open project ──────────────────────────────────────────────────────────

print(f"[cli-anything] Opening project: {PROJECT_PATH}")
result = import_api.ImportZpac(PROJECT_PATH)
if not result:
    print(f"[cli-anything] ERROR: Could not open project '{PROJECT_PATH}'", file=sys.stderr)
    sys.exit(2)

# ── Check current fabric count ────────────────────────────────────────────

before_count = fabric_api.GetFabricCount()
print(f"[cli-anything] Current fabric count: {before_count}")

# ── Assign fabric to pattern ──────────────────────────────────────────────

print(f"[cli-anything] Assigning fabric '{FABRIC_NAME}' to pattern '{PATTERN_NAME}'")
print(f"[cli-anything] Texture: {TEXTURE_PATH}")

ok = fabric_api.AssignFabricToPattern(
    patternName=PATTERN_NAME,
    fabricName=FABRIC_NAME,
    texturePath=TEXTURE_PATH,
)

if not ok:
    print(
        f"[cli-anything] ERROR: AssignFabricToPattern failed for "
        f"pattern='{PATTERN_NAME}' fabric='{FABRIC_NAME}'",
        file=sys.stderr,
    )
    sys.exit(3)

after_count = fabric_api.GetFabricCount()
print(f"[cli-anything] Fabric count after assignment: {after_count}")

# ── Save result ───────────────────────────────────────────────────────────

print(f"[cli-anything] Saving to: {OUTPUT_PATH}")
saved = export_api.ExportZpac(OUTPUT_PATH)
if not saved:
    print(f"[cli-anything] ERROR: Could not save to '{OUTPUT_PATH}'", file=sys.stderr)
    sys.exit(4)

print(f"[cli-anything] Saved: {OUTPUT_PATH}")
