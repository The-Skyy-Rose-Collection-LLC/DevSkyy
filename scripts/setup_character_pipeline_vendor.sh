#!/usr/bin/env bash
# Fetch the vendored assets skyyrose/character_pipeline needs: the FBX2glTF
# v0.9.7 binaries and the pinned three.js r128 UMD build. Idempotent — safe
# to re-run; skips any file that already exists and verifies.
#
# Every file is sha256-pinned: GitHub release assets can be replaced under an
# existing tag and raw.githubusercontent tag refs are movable, so a bare URL
# pin is not an integrity guarantee for binaries we chmod +x and execute.
# Pins were derived from the official upstream URLs on 2026-07-10 (FBX2glTF
# is archived upstream and publishes no official checksums).
#
# Usage:
#   bash scripts/setup_character_pipeline_vendor.sh
#   bash scripts/setup_character_pipeline_vendor.sh --force   # re-fetch everything

set -euo pipefail

VENDOR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/skyyrose/character_pipeline/vendor"
FORCE=false
[[ "${1:-}" == "--force" ]] && FORCE=true

mkdir -p "$VENDOR_DIR"
cd "$VENDOR_DIR"

verify_sha256() {
  local name="$1" expected="$2"
  local actual
  actual="$(shasum -a 256 "$name" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "CHECKSUM MISMATCH for $name" >&2
    echo "  expected: $expected" >&2
    echo "  actual:   $actual" >&2
    rm -f "$name"
    exit 1
  fi
}

fetch() {
  local name="$1" url="$2" sha256="$3"
  if [[ -f "$name" && "$FORCE" != true ]]; then
    verify_sha256 "$name" "$sha256"
    echo "skip (exists, checksum OK): $name"
    return
  fi
  echo "fetching: $name"
  curl -fsSL -o "$name" "$url"
  verify_sha256 "$name" "$sha256"
}

fetch "three.r128.min.js" \
  "https://raw.githubusercontent.com/mrdoob/three.js/r128/build/three.min.js" \
  "9274bbcec8d96168626c732b5d31c775aa8cfb7eaa0599bec0c175908a2c1ce2"
fetch "GLTFLoader.r128.js" \
  "https://raw.githubusercontent.com/mrdoob/three.js/r128/examples/js/loaders/GLTFLoader.js" \
  "5c15967ba830918a9caea6338712c994c354bccd4edc4569bde411c3ec06a3e6"
fetch "OrbitControls.r128.js" \
  "https://raw.githubusercontent.com/mrdoob/three.js/r128/examples/js/controls/OrbitControls.js" \
  "02bb4ade710f3e607329e37a21f098bc3ac70eb6e33daf8a65e79f4db785e7b2"
fetch "FBX2glTF-linux-x64" \
  "https://github.com/facebookincubator/FBX2glTF/releases/download/v0.9.7/FBX2glTF-linux-x64" \
  "b38210352fdd29d50ba53a6514c3ff05ccbb5d1e0a6442db7a49834bf34a3145"
fetch "FBX2glTF-darwin-x64" \
  "https://github.com/facebookincubator/FBX2glTF/releases/download/v0.9.7/FBX2glTF-darwin-x64" \
  "f82383ae4185c39f991b479b04ecce104f02e70c12a035ed31fc469e6f74a3fd"

chmod +x FBX2glTF-linux-x64 FBX2glTF-darwin-x64
echo "done: $VENDOR_DIR"
ls -la "$VENDOR_DIR"
