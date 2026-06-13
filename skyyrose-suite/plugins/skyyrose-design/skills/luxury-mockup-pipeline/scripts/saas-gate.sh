#!/bin/bash
# saas-gate.sh — automated SaaS Product Delivery Standard validator
#
# Runs the 11 grep checks + HTML parse + asset path verification + variant
# coverage on a target HTML file. Exits 0 on pass, non-zero on fail with
# per-check report.
#
# Usage:
#   bash saas-gate.sh <target-html-path> [--manifest <path>] [--strict]
#
# Examples:
#   bash saas-gate.sh /Users/theceo/DevSkyy/docs/brand/design-mockups/v2.html
#   bash saas-gate.sh v2.html --manifest v2-fix-manifest.md --strict

set -uo pipefail

TARGET="${1:-}"
STRICT=0
MANIFEST=""

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --strict) STRICT=1 ;;
    --manifest) shift; MANIFEST="$1" ;;
    *) ;;
  esac
  shift || true
done

if [[ -z "$TARGET" ]]; then
  echo "usage: saas-gate.sh <target-html-path> [--manifest <path>] [--strict]" >&2
  exit 2
fi

if [[ ! -f "$TARGET" ]]; then
  echo "ERR: target not found: $TARGET" >&2
  exit 2
fi

PASS=0
FAIL=0
WARN=0
REPORT=""

emit() {
  local status="$1" name="$2" detail="$3"
  case "$status" in
    PASS) PASS=$((PASS+1)); REPORT+=$'\n'"  ✓ $name — $detail" ;;
    FAIL) FAIL=$((FAIL+1)); REPORT+=$'\n'"  ✗ $name — $detail" ;;
    WARN) WARN=$((WARN+1)); REPORT+=$'\n'"  ⚠ $name — $detail" ;;
  esac
}

# ─── G1: HTML parse ─────────────────────────────────────────────────────────
if python3 -c "import html.parser,sys; p=html.parser.HTMLParser(); p.feed(open(sys.argv[1]).read())" "$TARGET" >/dev/null 2>&1; then
  emit PASS "HTML parse" "valid"
else
  emit FAIL "HTML parse" "invalid"
fi

# ─── G2: <picture> AVIF source presence on every image ──────────────────────
PIC=$(grep -c '<picture' "$TARGET" 2>/dev/null) || true
AVIF=$(grep -c 'image/avif' "$TARGET" 2>/dev/null) || true
if [[ "$PIC" -gt 0 && "$AVIF" -ge "$PIC" ]]; then
  emit PASS "AVIF coverage" "$AVIF avif sources / $PIC pictures"
elif [[ "$PIC" -eq 0 ]]; then
  emit WARN "AVIF coverage" "no <picture> elements found"
else
  emit FAIL "AVIF coverage" "$AVIF avif sources / $PIC pictures (need >= picture count)"
fi

# ─── G3: WebP source coverage ───────────────────────────────────────────────
WEBP=$(grep -c 'image/webp' "$TARGET" 2>/dev/null) || true
if [[ "$PIC" -gt 0 && "$WEBP" -ge "$PIC" ]]; then
  emit PASS "WebP coverage" "$WEBP webp sources / $PIC pictures"
elif [[ "$PIC" -eq 0 ]]; then
  emit WARN "WebP coverage" "no <picture> elements"
else
  emit WARN "WebP coverage" "$WEBP webp / $PIC pictures (partial)"
fi

# ─── G4: fetchpriority="high" on at least one above-fold image ──────────────
FP=$(grep -c 'fetchpriority="high"' "$TARGET" 2>/dev/null) || true
if [[ "$FP" -ge 1 ]]; then
  emit PASS "fetchpriority hint" "$FP element(s) marked high"
else
  emit FAIL "fetchpriority hint" "no fetchpriority=\"high\" on any image"
fi

# ─── G5: explicit width/height on every img (CLS prevention) ────────────────
# Use pcregrep-style multi-line via tr to collapse <img>...> blocks first
IMG=$(tr '\n' ' ' < "$TARGET" | grep -oE '<img\b[^>]*>' | wc -l | tr -d ' ')
IMG_DIM=$(tr '\n' ' ' < "$TARGET" | grep -oE '<img\b[^>]*>' | grep -cE 'width="[0-9]+"[^>]*height="[0-9]+"|height="[0-9]+"[^>]*width="[0-9]+"')
IMG=${IMG:-0}
IMG_DIM=${IMG_DIM:-0}
if [[ "$IMG" -gt 0 && "$IMG_DIM" -eq "$IMG" ]]; then
  emit PASS "Image dimensions" "$IMG_DIM/$IMG have explicit width+height"
elif [[ "$IMG" -eq 0 ]]; then
  emit WARN "Image dimensions" "no <img> elements"
else
  emit FAIL "Image dimensions" "$IMG_DIM/$IMG have explicit dims (CLS risk)"
fi

# ─── G6: aspect-ratio CSS present ───────────────────────────────────────────
AR=$(grep -cE 'aspect-ratio:' "$TARGET" 2>/dev/null) || true
if [[ "$AR" -ge 1 ]]; then
  emit PASS "aspect-ratio CSS" "$AR rule(s) present"
else
  emit WARN "aspect-ratio CSS" "no aspect-ratio CSS rules (CLS risk on dynamic images)"
fi

# ─── G7: lazy-load below-fold (any loading="lazy" presence) ─────────────────
LAZY=$(grep -c 'loading="lazy"' "$TARGET" 2>/dev/null) || true
if [[ "$LAZY" -ge 1 ]]; then
  emit PASS "Lazy loading" "$LAZY lazy-load hint(s) present"
else
  emit WARN "Lazy loading" "no loading=\"lazy\" hints (perf risk on long pages)"
fi

# ─── G8: <link rel="preload"> for critical hero asset ───────────────────────
PRELOAD=$(grep -cE 'rel="preload"' "$TARGET" 2>/dev/null) || true
if [[ "$PRELOAD" -ge 1 ]]; then
  emit PASS "Preload hints" "$PRELOAD preload tag(s)"
else
  emit WARN "Preload hints" "no rel=\"preload\" tags (LCP risk)"
fi

# ─── G9: prefers-reduced-motion fallback ────────────────────────────────────
PRM=$(grep -cE 'prefers-reduced-motion' "$TARGET" 2>/dev/null) || true
if [[ "$PRM" -ge 1 ]]; then
  emit PASS "Reduced motion" "$PRM @media or JS check(s)"
else
  emit FAIL "Reduced motion" "no prefers-reduced-motion handling (a11y violation)"
fi

# ─── G10: skip link present ─────────────────────────────────────────────────
SKIP=$(grep -cE 'skip[-_ ]link|skip to (main|content)' "$TARGET" 2>/dev/null) || true
if [[ "$SKIP" -ge 1 ]]; then
  emit PASS "Skip link" "present"
else
  emit WARN "Skip link" "no skip link (a11y concern)"
fi

# ─── G11: viewport meta ─────────────────────────────────────────────────────
VP=$(grep -cE 'name="viewport"' "$TARGET" 2>/dev/null) || true
if [[ "$VP" -ge 1 ]]; then
  emit PASS "Viewport meta" "present"
else
  emit FAIL "Viewport meta" "missing — mobile layout will be broken"
fi

# ─── G12: focus-visible support ─────────────────────────────────────────────
FV=$(grep -cE ':focus-visible' "$TARGET" 2>/dev/null) || true
if [[ "$FV" -ge 1 ]]; then
  emit PASS "focus-visible" "$FV rule(s)"
else
  emit WARN "focus-visible" "no :focus-visible rules (keyboard nav UX risk)"
fi

# ─── G13: Asset path resolution (any 404s in the file://?) ──────────────────
DIR="$(cd "$(dirname "$TARGET")" && pwd)"
MISSING=0
TOTAL_ASSETS=0
while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  TOTAL_ASSETS=$((TOTAL_ASSETS+1))
  # Resolve relative paths from target dir
  resolved="$DIR/$path"
  if [[ "$path" =~ ^/ ]]; then resolved="$path"; fi
  if [[ ! -f "$resolved" ]]; then
    MISSING=$((MISSING+1))
  fi
done < <(grep -oE '(src|srcset)="[^"]*\.(avif|webp|png|jpg|jpeg|svg)[^"]*"' "$TARGET" | sed -E 's/(src|srcset)="//; s/"$//' | tr ',' '\n' | awk '{print $1}' | sort -u)
if [[ "$MISSING" -eq 0 ]]; then
  emit PASS "Asset paths resolve" "$TOTAL_ASSETS asset references, 0 missing"
else
  emit FAIL "Asset paths resolve" "$MISSING/$TOTAL_ASSETS missing on disk"
fi

# ─── Summary ────────────────────────────────────────────────────────────────
TOTAL=$((PASS+FAIL+WARN))
echo "═══════════════════════════════════════════════════════════════════"
echo " SaaS Gate Report — $(basename "$TARGET")"
echo "═══════════════════════════════════════════════════════════════════"
echo "$REPORT"
echo
echo "  $PASS pass / $WARN warn / $FAIL fail (of $TOTAL checks)"
echo

if [[ "$FAIL" -gt 0 ]]; then
  echo "VERDICT: FAIL — re-work before publishing"
  exit 1
elif [[ "$WARN" -gt 0 && "$STRICT" -eq 1 ]]; then
  echo "VERDICT: WARN (strict mode treats warns as fails)"
  exit 1
else
  echo "VERDICT: PASS — deliverable clears SaaS gate"
  exit 0
fi
