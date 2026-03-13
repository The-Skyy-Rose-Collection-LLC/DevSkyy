#!/usr/bin/env bash
set -euo pipefail

# Build Verification Script for SkyyRose Flagship Theme
# Validates that npm run build produced correct output for all source files.
#
# Usage: bash scripts/verify-build.sh
# Exit 0: all checks pass
# Exit 1: one or more checks failed

THEME_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0
TOTAL=0

check() {
  local name="$1"
  local result="$2"  # "pass" or "fail"
  local detail="$3"
  TOTAL=$((TOTAL + 1))
  if [ "$result" = "pass" ]; then
    PASS=$((PASS + 1))
    echo "  PASS: $name -- $detail"
  else
    FAIL=$((FAIL + 1))
    echo "  FAIL: $name -- $detail"
  fi
}

echo "=== SkyyRose Build Verification ==="
echo ""

# ---------------------------------------------------------------
# a. JS count match (BUILD-01)
# ---------------------------------------------------------------
JS_SRC=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.js" ! -name "*.min.js" | wc -l | tr -d ' ')
JS_MIN=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.min.js" | wc -l | tr -d ' ')
if [ "$JS_SRC" -eq "$JS_MIN" ] && [ "$JS_SRC" -gt 0 ]; then
  check "JS count match (BUILD-01)" "pass" "$JS_SRC source = $JS_MIN minified"
else
  check "JS count match (BUILD-01)" "fail" "$JS_SRC source != $JS_MIN minified"
fi

# ---------------------------------------------------------------
# b. CSS count match (BUILD-02)
# ---------------------------------------------------------------
CSS_SRC=$(find "$THEME_DIR/assets/css" -name "*.css" ! -name "*.min.css" | wc -l | tr -d ' ')
CSS_MIN=$(find "$THEME_DIR/assets/css" -name "*.min.css" | wc -l | tr -d ' ')
ROOT_MIN=0
[ -f "$THEME_DIR/style.min.css" ] && ROOT_MIN=1
# Total CSS: assets/ files + root style.css
TOTAL_SRC=$((CSS_SRC + 1))
TOTAL_MIN=$((CSS_MIN + ROOT_MIN))
if [ "$TOTAL_SRC" -eq "$TOTAL_MIN" ] && [ "$TOTAL_SRC" -gt 0 ]; then
  check "CSS count match (BUILD-02)" "pass" "$TOTAL_SRC source = $TOTAL_MIN minified (including root style.css)"
else
  check "CSS count match (BUILD-02)" "fail" "$TOTAL_SRC source != $TOTAL_MIN minified"
fi

# ---------------------------------------------------------------
# c. Source maps exist (BUILD-03)
# ---------------------------------------------------------------
JS_MAPS=$(find "$THEME_DIR/assets/js" -name "*.map" | wc -l | tr -d ' ')
CSS_MAPS=$(find "$THEME_DIR/assets/css" -name "*.map" | wc -l | tr -d ' ')
ROOT_MAP=0
[ -f "$THEME_DIR/style.min.css.map" ] && ROOT_MAP=1
TOTAL_MAPS=$((JS_MAPS + CSS_MAPS + ROOT_MAP))
if [ "$TOTAL_MAPS" -gt 0 ]; then
  check "Source maps exist (BUILD-03)" "pass" "$TOTAL_MAPS .map files ($JS_MAPS JS, $CSS_MAPS CSS, $ROOT_MAP root)"
else
  check "Source maps exist (BUILD-03)" "fail" "0 .map files found"
fi

# ---------------------------------------------------------------
# d. JS source map pairing
# ---------------------------------------------------------------
JS_MAP_MISSING=0
JS_MAP_CHECKED=0
for minfile in "$THEME_DIR"/assets/js/*.min.js; do
  [ -f "$minfile" ] || continue
  JS_MAP_CHECKED=$((JS_MAP_CHECKED + 1))
  mapfile="${minfile}.map"
  if [ ! -f "$mapfile" ]; then
    echo "    Missing: $mapfile"
    JS_MAP_MISSING=$((JS_MAP_MISSING + 1))
  fi
done
if [ "$JS_MAP_MISSING" -eq 0 ] && [ "$JS_MAP_CHECKED" -gt 0 ]; then
  check "JS source map pairing" "pass" "$JS_MAP_CHECKED .min.js files all have .map"
else
  check "JS source map pairing" "fail" "$JS_MAP_MISSING of $JS_MAP_CHECKED missing .map"
fi

# ---------------------------------------------------------------
# e. CSS source map pairing
# ---------------------------------------------------------------
CSS_MAP_MISSING=0
CSS_MAP_CHECKED=0
while IFS= read -r minfile; do
  [ -f "$minfile" ] || continue
  CSS_MAP_CHECKED=$((CSS_MAP_CHECKED + 1))
  mapfile="${minfile}.map"
  if [ ! -f "$mapfile" ]; then
    echo "    Missing: $mapfile"
    CSS_MAP_MISSING=$((CSS_MAP_MISSING + 1))
  fi
done < <(find "$THEME_DIR/assets/css" -name "*.min.css")
# Also check root style.min.css
if [ -f "$THEME_DIR/style.min.css" ]; then
  CSS_MAP_CHECKED=$((CSS_MAP_CHECKED + 1))
  if [ ! -f "$THEME_DIR/style.min.css.map" ]; then
    echo "    Missing: style.min.css.map"
    CSS_MAP_MISSING=$((CSS_MAP_MISSING + 1))
  fi
fi
if [ "$CSS_MAP_MISSING" -eq 0 ] && [ "$CSS_MAP_CHECKED" -gt 0 ]; then
  check "CSS source map pairing" "pass" "$CSS_MAP_CHECKED .min.css files all have .map"
else
  check "CSS source map pairing" "fail" "$CSS_MAP_MISSING of $CSS_MAP_CHECKED missing .map"
fi

# ---------------------------------------------------------------
# f. WordPress theme header preserved
# ---------------------------------------------------------------
if [ -f "$THEME_DIR/style.min.css" ]; then
  if head -5 "$THEME_DIR/style.min.css" | grep -q "Theme Name"; then
    check "WordPress theme header preserved" "pass" "style.min.css contains 'Theme Name' in first 5 lines"
  else
    check "WordPress theme header preserved" "fail" "style.min.css missing 'Theme Name' in first 5 lines"
  fi
else
  check "WordPress theme header preserved" "fail" "style.min.css does not exist"
fi

# ---------------------------------------------------------------
# g. Minified files are smaller (spot check)
# ---------------------------------------------------------------
SIZE_PASS=0
SIZE_FAIL=0
SIZE_CHECKED=0

spot_check_size() {
  local src="$1"
  local min="$2"
  if [ -f "$src" ] && [ -f "$min" ]; then
    SIZE_CHECKED=$((SIZE_CHECKED + 1))
    local src_size min_size
    src_size=$(wc -c < "$src" | tr -d ' ')
    min_size=$(wc -c < "$min" | tr -d ' ')
    if [ "$min_size" -lt "$src_size" ]; then
      SIZE_PASS=$((SIZE_PASS + 1))
    else
      echo "    Not smaller: $min ($min_size >= $src_size)"
      SIZE_FAIL=$((SIZE_FAIL + 1))
    fi
  fi
}

# 3 JS spot checks
spot_check_size "$THEME_DIR/assets/js/navigation.js" "$THEME_DIR/assets/js/navigation.min.js"
spot_check_size "$THEME_DIR/assets/js/woocommerce.js" "$THEME_DIR/assets/js/woocommerce.min.js"
spot_check_size "$THEME_DIR/assets/js/immersive-world.js" "$THEME_DIR/assets/js/immersive-world.min.js"

# 3 CSS spot checks
spot_check_size "$THEME_DIR/assets/css/woocommerce.css" "$THEME_DIR/assets/css/woocommerce.min.css"
spot_check_size "$THEME_DIR/assets/css/main.css" "$THEME_DIR/assets/css/main.min.css"
spot_check_size "$THEME_DIR/style.css" "$THEME_DIR/style.min.css"

if [ "$SIZE_FAIL" -eq 0 ] && [ "$SIZE_CHECKED" -gt 0 ]; then
  check "Minified files smaller (spot check)" "pass" "$SIZE_PASS of $SIZE_CHECKED spot checks: minified < source"
else
  check "Minified files smaller (spot check)" "fail" "$SIZE_FAIL of $SIZE_CHECKED not smaller"
fi

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
echo ""
echo "=== $PASS/$TOTAL checks passed ==="

if [ "$FAIL" -gt 0 ]; then
  echo "RESULT: FAILED ($FAIL check(s) failed)"
  exit 1
else
  echo "RESULT: PASSED"
  exit 0
fi
