#!/bin/bash

# GitHub Actions SHA Updater - Quick Run Script
# Enhanced Security Compliance Tool for DevSkyy Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${PURPLE}🔒 GitHub Actions SHA Updater - DevSkyy Platform${NC}"
echo -e "${PURPLE}===============================================${NC}"
echo ""

# Function to print usage
usage() {
    echo -e "${CYAN}Usage: $0 [OPTIONS]${NC}"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  -d, --dry-run          Preview changes without modifying files"
    echo "  -v, --verbose          Enable verbose logging"
    echo "  -c, --config FILE      Use custom configuration file"
    echo "  -r, --report FILE      Generate report to specified file"
    echo "  -h, --help             Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0                     # Run with default settings"
    echo "  $0 --dry-run           # Preview changes only"
    echo "  $0 --verbose --report update_report.json"
    echo "  $0 --config custom_config.json --dry-run"
    echo ""
    echo -e "${YELLOW}Security Benefits:${NC}"
    echo "  • Pins actions to immutable SHA commits"
    echo "  • Prevents supply chain attacks"
    echo "  • Ensures reproducible builds"
    echo "  • Meets enterprise security requirements"
}

# Parse command line arguments
DRY_RUN=""
VERBOSE=""
CONFIG_FILE="action_sha_config.json"
REPORT_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -r|--report)
            REPORT_FILE="--report $2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Change to project root
cd "$PROJECT_ROOT"

# Check if we're in the right directory
if [[ ! -f "update_action_shas.py" ]]; then
    echo -e "${RED}❌ Error: update_action_shas.py not found in current directory${NC}"
    echo -e "${YELLOW}Please run this script from the repository root${NC}"
    exit 1
fi

# Check Python version
echo -e "${BLUE}🐍 Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "Python version: ${GREEN}$PYTHON_VERSION${NC}"

# Check dependencies
echo -e "${BLUE}📦 Checking dependencies...${NC}"
if ! python3 -c "import requests, yaml" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing missing dependencies...${NC}"
    pip install requests pyyaml
else
    echo -e "${GREEN}✅ Dependencies satisfied${NC}"
fi

# Check configuration file
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo -e "${YELLOW}⚠️  Configuration file '$CONFIG_FILE' not found${NC}"
    echo -e "${YELLOW}Using default configuration${NC}"
    CONFIG_FILE=""
else
    echo -e "${GREEN}✅ Configuration file: $CONFIG_FILE${NC}"
fi

# Check for GitHub token
if [[ -z "$GITHUB_TOKEN" ]]; then
    echo -e "${YELLOW}⚠️  GITHUB_TOKEN not set${NC}"
    echo -e "${YELLOW}API rate limiting may occur. Consider setting:${NC}"
    echo -e "${CYAN}export GITHUB_TOKEN='your_token_here'${NC}"
else
    echo -e "${GREEN}✅ GitHub token configured${NC}"
fi

echo ""

# Show what will be executed
if [[ -n "$DRY_RUN" ]]; then
    echo -e "${CYAN}🔍 DRY RUN MODE: No files will be modified${NC}"
fi

if [[ -n "$VERBOSE" ]]; then
    echo -e "${CYAN}📝 Verbose logging enabled${NC}"
fi

echo -e "${BLUE}🚀 Starting GitHub Actions SHA update process...${NC}"
echo ""

# Build command
CMD="python3 update_action_shas.py"
if [[ -n "$CONFIG_FILE" ]]; then
    CMD="$CMD --config $CONFIG_FILE"
fi
if [[ -n "$DRY_RUN" ]]; then
    CMD="$CMD $DRY_RUN"
fi
if [[ -n "$VERBOSE" ]]; then
    CMD="$CMD $VERBOSE"
fi
if [[ -n "$REPORT_FILE" ]]; then
    CMD="$CMD $REPORT_FILE"
fi

echo -e "${CYAN}Executing: $CMD${NC}"
echo ""

# Execute the command
if eval "$CMD"; then
    echo ""
    echo -e "${GREEN}✅ SHA update process completed successfully!${NC}"
    
    # Check if files were modified (only in non-dry-run mode)
    if [[ -z "$DRY_RUN" ]] && git diff --quiet; then
        echo -e "${BLUE}📝 No changes made to workflow files${NC}"
    elif [[ -z "$DRY_RUN" ]]; then
        echo -e "${YELLOW}📝 Changes made to workflow files:${NC}"
        git diff --name-only | head -10
        echo ""
        echo -e "${YELLOW}💡 Next steps:${NC}"
        echo "  1. Review the changes: git diff"
        echo "  2. Test updated workflows in a branch"
        echo "  3. Commit changes: git add . && git commit -m 'Update action SHAs for security'"
        echo "  4. Push changes: git push"
    fi
    
    # Show report file if generated
    if [[ -n "$REPORT_FILE" ]]; then
        REPORT_FILE_NAME=$(echo "$REPORT_FILE" | sed 's/--report //')
        if [[ -f "$REPORT_FILE_NAME" ]]; then
            echo -e "${BLUE}📊 Update report generated: $REPORT_FILE_NAME${NC}"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}🛡️  Security compliance enhanced!${NC}"
    
else
    echo ""
    echo -e "${RED}❌ SHA update process failed${NC}"
    echo -e "${YELLOW}💡 Troubleshooting:${NC}"
    echo "  1. Check network connectivity"
    echo "  2. Verify GITHUB_TOKEN if rate-limited"
    echo "  3. Review error messages above"
    echo "  4. Try dry-run mode: $0 --dry-run"
    exit 1
fi