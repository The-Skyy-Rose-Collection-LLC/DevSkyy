# cli-anything-marvelous — export script template
# Rendered via string.Template; placeholders use $${var} syntax.
#
# Variables:
#   project_path  — absolute path to .zpac or .zprj file to open
#   output_path   — absolute path for the exported file (without extension)
#   export_format — one of: obj, fbx, alembic, usd, zpac, zprj
#
# Run inside Marvelous Designer via:
#   "Marvelous Designer" --script export.py
#
# API reference: https://developer.marvelousdesigner.com/scenario.html

import sys

try:
    import import_api
    import utility_api
    import export_api
    from ApiTypes import ExportType
except ImportError as e:
    print(f"[cli-anything] Failed to import MD API: {e}", file=sys.stderr)
    sys.exit(1)

PROJECT_PATH = r"${project_path}"
OUTPUT_PATH  = r"${output_path}"
EXPORT_FMT   = "${export_format}".lower().strip()

# ── Open project ──────────────────────────────────────────────────────────

print(f"[cli-anything] Opening project: {PROJECT_PATH}")
result = import_api.ImportZpac(PROJECT_PATH)
if not result:
    print(f"[cli-anything] ERROR: Could not open project '{PROJECT_PATH}'", file=sys.stderr)
    sys.exit(2)

# ── Export ────────────────────────────────────────────────────────────────

print(f"[cli-anything] Exporting as {EXPORT_FMT} to {OUTPUT_PATH}")

if EXPORT_FMT == "obj":
    ok = export_api.ExportOBJ(OUTPUT_PATH + ".obj")
elif EXPORT_FMT == "fbx":
    ok = export_api.ExportFBX(OUTPUT_PATH + ".fbx")
elif EXPORT_FMT == "alembic":
    ok = export_api.ExportAlembic(OUTPUT_PATH + ".abc")
elif EXPORT_FMT == "usd":
    ok = export_api.ExportUSD(OUTPUT_PATH + ".usd")
elif EXPORT_FMT == "zpac":
    ok = export_api.ExportZpac(OUTPUT_PATH + ".zpac")
elif EXPORT_FMT == "zprj":
    ok = export_api.ExportZprj(OUTPUT_PATH + ".zprj")
else:
    print(f"[cli-anything] ERROR: Unknown export format '{EXPORT_FMT}'", file=sys.stderr)
    print("[cli-anything] Supported formats: obj, fbx, alembic, usd, zpac, zprj", file=sys.stderr)
    sys.exit(3)

if not ok:
    print(f"[cli-anything] ERROR: Export failed for format '{EXPORT_FMT}'", file=sys.stderr)
    sys.exit(4)

print(f"[cli-anything] Export complete: {OUTPUT_PATH}")
