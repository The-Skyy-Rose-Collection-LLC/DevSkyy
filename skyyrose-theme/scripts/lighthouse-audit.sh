#!/bin/bash

###############################################################################
# Lighthouse Audit Script
#
# Runs comprehensive Lighthouse audits on all 4 3D collection pages
# and static archive pages for performance, accessibility, best practices, SEO
#
# Usage: bash scripts/lighthouse-audit.sh
#
# Requirements:
# - Node.js 14+
# - Lighthouse CLI: npm install -g lighthouse
# - Chrome/Chromium browser
#
# @package SkyyRose_Flagship
# @since 1.0.0
###############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${1:-http://skyyroselocal.local}"
OUTPUT_DIR="tests/lighthouse"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}SkyyRose Lighthouse Audit Suite${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "Base URL: ${GREEN}$BASE_URL${NC}"
echo -e "Output Directory: ${GREEN}$OUTPUT_DIR${NC}"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# 3D Collection Pages
declare -a pages_3d=(
  "signature-collection-3d"
  "love-hurts-3d"
  "black-rose-3d"
  "preorder-gateway-3d"
)

# Static Archive Pages
declare -a pages_archive=(
  "product-category/signature-collection"
  "product-category/love-hurts"
  "product-category/black-rose"
  "product-category/preorder"
)

# Target scores
TARGET_PERFORMANCE=85
TARGET_ACCESSIBILITY=95
TARGET_BEST_PRACTICES=95
TARGET_SEO=95

# Counters
total_tests=0
passed_tests=0
failed_tests=0

###############################################################################
# Function: Run Lighthouse Audit
###############################################################################
run_lighthouse() {
  local url=$1
  local name=$2
  local preset=$3  # "desktop" or "mobile"

  echo -e "${YELLOW}Testing: $name ($preset)${NC}"

  local output_file="${OUTPUT_DIR}/${name}-${preset}-${TIMESTAMP}.json"
  local html_file="${OUTPUT_DIR}/${name}-${preset}-${TIMESTAMP}.html"

  # Run Lighthouse
  if [ "$preset" = "mobile" ]; then
    npx lighthouse "$url" \
      --only-categories=performance,accessibility,best-practices,seo \
      --output=json \
      --output=html \
      --output-path="${OUTPUT_DIR}/${name}-${preset}-${TIMESTAMP}" \
      --preset=mobile \
      --chrome-flags="--headless --no-sandbox --disable-gpu" \
      --quiet \
      2>/dev/null
  else
    npx lighthouse "$url" \
      --only-categories=performance,accessibility,best-practices,seo \
      --output=json \
      --output=html \
      --output-path="${OUTPUT_DIR}/${name}-${preset}-${TIMESTAMP}" \
      --chrome-flags="--headless --no-sandbox --disable-gpu" \
      --quiet \
      2>/dev/null
  fi

  # Check if audit succeeded
  if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Audit failed for $name ($preset)${NC}"
    ((failed_tests++))
    return 1
  fi

  # Parse scores from JSON
  local perf=$(jq -r '.categories.performance.score * 100' "${output_file}.json" 2>/dev/null)
  local a11y=$(jq -r '.categories.accessibility.score * 100' "${output_file}.json" 2>/dev/null)
  local bp=$(jq -r '.categories["best-practices"].score * 100' "${output_file}.json" 2>/dev/null)
  local seo=$(jq -r '.categories.seo.score * 100' "${output_file}.json" 2>/dev/null)

  # Round scores
  perf=$(printf "%.0f" "$perf")
  a11y=$(printf "%.0f" "$a11y")
  bp=$(printf "%.0f" "$bp")
  seo=$(printf "%.0f" "$seo")

  echo -e "  Performance:    ${perf}/100"
  echo -e "  Accessibility:  ${a11y}/100"
  echo -e "  Best Practices: ${bp}/100"
  echo -e "  SEO:            ${seo}/100"

  # Check if scores meet targets
  local pass=true
  if [ "$perf" -lt "$TARGET_PERFORMANCE" ]; then
    echo -e "  ${RED}⚠ Performance below target ($TARGET_PERFORMANCE)${NC}"
    pass=false
  fi
  if [ "$a11y" -lt "$TARGET_ACCESSIBILITY" ]; then
    echo -e "  ${RED}⚠ Accessibility below target ($TARGET_ACCESSIBILITY)${NC}"
    pass=false
  fi
  if [ "$bp" -lt "$TARGET_BEST_PRACTICES" ]; then
    echo -e "  ${RED}⚠ Best Practices below target ($TARGET_BEST_PRACTICES)${NC}"
    pass=false
  fi
  if [ "$seo" -lt "$TARGET_SEO" ]; then
    echo -e "  ${RED}⚠ SEO below target ($TARGET_SEO)${NC}"
    pass=false
  fi

  if [ "$pass" = true ]; then
    echo -e "  ${GREEN}✓ All scores above targets${NC}"
    ((passed_tests++))
  else
    ((failed_tests++))
  fi

  echo -e "  Report: ${BLUE}${html_file}.html${NC}"
  echo ""

  ((total_tests++))
}

###############################################################################
# Test 3D Collection Pages
###############################################################################
echo -e "${GREEN}Testing 3D Collection Pages...${NC}"
echo ""

for page in "${pages_3d[@]}"; do
  url="$BASE_URL/$page/"
  name=$(echo "$page" | sed 's/-3d$//')

  # Desktop
  run_lighthouse "$url" "${name}-3d" "desktop"

  # Mobile
  run_lighthouse "$url" "${name}-3d" "mobile"
done

###############################################################################
# Test Static Archive Pages
###############################################################################
echo -e "${GREEN}Testing Static Archive Pages...${NC}"
echo ""

for page in "${pages_archive[@]}"; do
  url="$BASE_URL/$page/"
  name=$(echo "$page" | sed 's/product-category\///' | sed 's/-$//')

  # Desktop
  run_lighthouse "$url" "${name}-archive" "desktop"

  # Mobile
  run_lighthouse "$url" "${name}-archive" "mobile"
done

###############################################################################
# Summary
###############################################################################
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Audit Summary${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "Total Tests:  ${total_tests}"
echo -e "Passed:       ${GREEN}${passed_tests}${NC}"
echo -e "Failed:       ${RED}${failed_tests}${NC}"
echo ""

if [ $failed_tests -eq 0 ]; then
  echo -e "${GREEN}✓ All Lighthouse audits passed!${NC}"
  exit 0
else
  echo -e "${RED}✗ Some audits failed. Check reports in $OUTPUT_DIR${NC}"
  exit 1
fi
