#!/bin/bash

###############################################################################
# Accessibility Audit Script
#
# Runs pa11y accessibility tests on all pages for WCAG 2.1 AA compliance
#
# Usage: bash scripts/accessibility-audit.sh
#
# Requirements:
# - Node.js 14+
# - pa11y: npm install -g pa11y
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
OUTPUT_DIR="tests/accessibility"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}SkyyRose Accessibility Audit Suite${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "Base URL: ${GREEN}$BASE_URL${NC}"
echo -e "Output Directory: ${GREEN}$OUTPUT_DIR${NC}"
echo -e "Standard: ${GREEN}WCAG 2.1 AA${NC}"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Pages to test
declare -a pages=(
  "signature-collection-3d"
  "love-hurts-3d"
  "black-rose-3d"
  "preorder-gateway-3d"
  "product-category/signature-collection"
  "product-category/love-hurts"
  "product-category/black-rose"
  "product-category/preorder"
)

# Counters
total_pages=0
passed_pages=0
failed_pages=0
total_issues=0

###############################################################################
# Function: Run pa11y Test
###############################################################################
run_pa11y() {
  local url=$1
  local name=$2

  echo -e "${YELLOW}Testing: $name${NC}"

  local output_file="${OUTPUT_DIR}/${name}-${TIMESTAMP}.json"
  local report_file="${OUTPUT_DIR}/${name}-${TIMESTAMP}.txt"

  # Run pa11y
  npx pa11y "$url" \
    --standard WCAG2AA \
    --reporter json \
    --timeout 30000 \
    --wait 5000 \
    --ignore "warning;notice" \
    > "$output_file" 2>/dev/null

  # Check if test succeeded
  if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Test failed for $name${NC}"
    ((failed_pages++))
    ((total_pages++))
    return 1
  fi

  # Count issues
  local issue_count=$(jq 'length' "$output_file" 2>/dev/null || echo "0")

  echo -e "  Issues found: ${issue_count}"

  # Create human-readable report
  if [ "$issue_count" -gt 0 ]; then
    echo "Accessibility Issues for: $name" > "$report_file"
    echo "URL: $url" >> "$report_file"
    echo "Standard: WCAG 2.1 AA" >> "$report_file"
    echo "Date: $(date)" >> "$report_file"
    echo "" >> "$report_file"

    jq -r '.[] | "[\(.type | ascii_upcase)] \(.message)\n  Code: \(.code)\n  Context: \(.context)\n  Selector: \(.selector)\n"' "$output_file" >> "$report_file"

    echo -e "  ${YELLOW}⚠ Issues found - see report${NC}"
    echo -e "  Report: ${BLUE}${report_file}${NC}"
    ((failed_pages++))
    total_issues=$((total_issues + issue_count))
  else
    echo -e "  ${GREEN}✓ No accessibility issues${NC}"
    ((passed_pages++))
  fi

  echo ""
  ((total_pages++))
}

###############################################################################
# Run Tests
###############################################################################
echo -e "${GREEN}Running accessibility tests...${NC}"
echo ""

for page in "${pages[@]}"; do
  url="$BASE_URL/$page/"
  name=$(echo "$page" | sed 's/\//-/g')

  run_pa11y "$url" "$name"
done

###############################################################################
# Summary
###############################################################################
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Accessibility Audit Summary${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo -e "Pages Tested:    ${total_pages}"
echo -e "Passed:          ${GREEN}${passed_pages}${NC}"
echo -e "Failed:          ${RED}${failed_pages}${NC}"
echo -e "Total Issues:    ${total_issues}"
echo ""

if [ $failed_pages -eq 0 ]; then
  echo -e "${GREEN}✓ All accessibility tests passed (WCAG 2.1 AA)!${NC}"
  exit 0
else
  echo -e "${RED}✗ Some pages have accessibility issues. Check reports in $OUTPUT_DIR${NC}"
  echo ""
  echo -e "${YELLOW}Common Issues to Fix:${NC}"
  echo "  - Missing alt text on images"
  echo "  - Insufficient color contrast"
  echo "  - Missing ARIA labels"
  echo "  - Incorrect heading hierarchy"
  echo "  - Missing form labels"
  exit 1
fi
