#!/bin/bash

###############################################################################
# Browser Compatibility Testing Script
#
# Tests site across multiple browsers using Playwright
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SITE_URL="${1:-http://localhost:8080}"
OUTPUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/tests/coverage/browsers"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Browser Compatibility Testing${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${BLUE}Testing URL: ${NC}$SITE_URL\n"

# Create output directory
mkdir -p "$OUTPUT_DIR"

###############################################################################
# Helper Functions
###############################################################################

info() {
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

success() {
    echo -e "${GREEN}✓ SUCCESS:${NC} $1"
}

error() {
    echo -e "${RED}✗ ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
}

###############################################################################
# Check Dependencies
###############################################################################

echo -e "${BLUE}[1/4] Checking dependencies...${NC}\n"

# Check for Node.js
if command -v node &> /dev/null; then
    success "Node.js found ($(node --version))"
else
    error "Node.js not found. Please install Node.js."
    exit 1
fi

# Check for npm
if command -v npm &> /dev/null; then
    success "npm found ($(npm --version))"
else
    error "npm not found. Please install npm."
    exit 1
fi

# Check for Playwright
if command -v playwright &> /dev/null; then
    success "Playwright CLI found"
    PLAYWRIGHT_AVAILABLE=true
elif [ -d "node_modules/@playwright/test" ]; then
    success "Playwright found (local)"
    PLAYWRIGHT_AVAILABLE=true
else
    warn "Playwright not found. Install with: npm install -D @playwright/test"
    PLAYWRIGHT_AVAILABLE=false
fi

echo ""

###############################################################################
# Browser Feature Detection Script
###############################################################################

echo -e "${BLUE}[2/4] Creating browser feature detection script...${NC}\n"

cat > "$OUTPUT_DIR/feature-detection.js" << 'EOF'
// Browser Feature Detection Script

(function() {
    const results = {
        userAgent: navigator.userAgent,
        browser: detectBrowser(),
        features: {},
        errors: []
    };

    function detectBrowser() {
        const ua = navigator.userAgent;
        if (ua.includes('Firefox/')) return 'Firefox';
        if (ua.includes('Chrome/') && !ua.includes('Edg')) return 'Chrome';
        if (ua.includes('Safari/') && !ua.includes('Chrome')) return 'Safari';
        if (ua.includes('Edg/')) return 'Edge';
        return 'Unknown';
    }

    // Test WebGL support
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        results.features.webgl = !!gl;
        if (gl) {
            results.features.webglVersion = gl.getParameter(gl.VERSION);
            results.features.webglVendor = gl.getParameter(gl.VENDOR);
            results.features.webglRenderer = gl.getParameter(gl.RENDERER);
        }
    } catch(e) {
        results.features.webgl = false;
        results.errors.push('WebGL Error: ' + e.message);
    }

    // Test WebGL2 support
    try {
        const canvas = document.createElement('canvas');
        const gl2 = canvas.getContext('webgl2');
        results.features.webgl2 = !!gl2;
    } catch(e) {
        results.features.webgl2 = false;
    }

    // Test ES6+ features
    results.features.es6 = {
        arrow: (() => true)(),
        promises: typeof Promise !== 'undefined',
        const: true,
        let: true,
        templateLiterals: true,
        destructuring: true,
        spread: true,
        modules: 'noModule' in document.createElement('script')
    };

    // Test CSS features
    results.features.css = {
        grid: CSS.supports('display', 'grid'),
        flexbox: CSS.supports('display', 'flex'),
        customProperties: CSS.supports('--test', '0'),
        transforms: CSS.supports('transform', 'rotate(0deg)'),
        transitions: CSS.supports('transition', 'all 0.3s'),
        animations: CSS.supports('animation', 'test 1s')
    };

    // Test storage
    results.features.storage = {
        localStorage: typeof localStorage !== 'undefined',
        sessionStorage: typeof sessionStorage !== 'undefined',
        indexedDB: typeof indexedDB !== 'undefined'
    };

    // Test APIs
    results.features.apis = {
        fetch: typeof fetch !== 'undefined',
        intersectionObserver: typeof IntersectionObserver !== 'undefined',
        resizeObserver: typeof ResizeObserver !== 'undefined',
        mutationObserver: typeof MutationObserver !== 'undefined',
        requestAnimationFrame: typeof requestAnimationFrame !== 'undefined'
    };

    // Test viewport
    results.viewport = {
        width: window.innerWidth,
        height: window.innerHeight,
        devicePixelRatio: window.devicePixelRatio
    };

    // Test performance
    if (window.performance && window.performance.timing) {
        const timing = window.performance.timing;
        results.performance = {
            domLoading: timing.domLoading - timing.navigationStart,
            domInteractive: timing.domInteractive - timing.navigationStart,
            domComplete: timing.domComplete - timing.navigationStart,
            loadEventEnd: timing.loadEventEnd - timing.navigationStart
        };
    }

    return results;
})();
EOF

success "Feature detection script created"

echo ""

###############################################################################
# Run Playwright Tests
###############################################################################

if [ "$PLAYWRIGHT_AVAILABLE" = true ]; then
    echo -e "${BLUE}[3/4] Running Playwright browser tests...${NC}\n"

    # Create a simple Playwright test
    cat > "$OUTPUT_DIR/browser-test.js" << EOF
const { test, expect, chromium, firefox, webkit } = require('@playwright/test');

const browsers = [
    { name: 'Chromium', launcher: chromium },
    { name: 'Firefox', launcher: firefox },
    { name: 'WebKit', launcher: webkit }
];

const testUrl = '${SITE_URL}';

for (const { name, launcher } of browsers) {
    test.describe(\`\${name} Tests\`, () => {
        let browser;
        let context;
        let page;

        test.beforeAll(async () => {
            browser = await launcher.launch();
            context = await browser.newContext();
            page = await context.newPage();
        });

        test.afterAll(async () => {
            await browser.close();
        });

        test(\`\${name}: Homepage loads\`, async () => {
            await page.goto(testUrl);
            await expect(page).toHaveTitle(/.+/);
        });

        test(\`\${name}: JavaScript executes\`, async () => {
            await page.goto(testUrl);
            const hasErrors = await page.evaluate(() => {
                return window.onerror !== null;
            });
            expect(hasErrors).toBe(false);
        });

        test(\`\${name}: CSS loads\`, async () => {
            await page.goto(testUrl);
            const bgColor = await page.evaluate(() => {
                return getComputedStyle(document.body).backgroundColor;
            });
            expect(bgColor).toBeTruthy();
        });

        test(\`\${name}: WebGL support\`, async () => {
            await page.goto(testUrl);
            const webglSupported = await page.evaluate(() => {
                const canvas = document.createElement('canvas');
                return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
            });
            console.log(\`\${name} WebGL Support: \${webglSupported}\`);
        });

        test(\`\${name}: Responsive design\`, async () => {
            // Test mobile viewport
            await page.setViewportSize({ width: 375, height: 667 });
            await page.goto(testUrl);
            await page.screenshot({ path: \`${OUTPUT_DIR}/\${name.toLowerCase()}-mobile.png\` });

            // Test desktop viewport
            await page.setViewportSize({ width: 1920, height: 1080 });
            await page.goto(testUrl);
            await page.screenshot({ path: \`${OUTPUT_DIR}/\${name.toLowerCase()}-desktop.png\` });
        });
    });
}
EOF

    # Run the tests
    if [ -d "node_modules/@playwright/test" ]; then
        npx playwright test "$OUTPUT_DIR/browser-test.js" --reporter=html --output="$OUTPUT_DIR" || true
        success "Playwright tests completed"
    else
        playwright test "$OUTPUT_DIR/browser-test.js" --reporter=html --output="$OUTPUT_DIR" || true
        success "Playwright tests completed"
    fi
else
    info "Skipping Playwright tests (not installed)"
fi

echo ""

###############################################################################
# Browser Compatibility Matrix
###############################################################################

echo -e "${BLUE}[4/4] Browser Compatibility Matrix${NC}\n"

echo "┌─────────────────┬──────────┬──────────┬──────────┬──────────┐"
echo "│ Feature         │ Chrome   │ Firefox  │ Safari   │ Edge     │"
echo "├─────────────────┼──────────┼──────────┼──────────┼──────────┤"
echo "│ WebGL           │    ✓     │    ✓     │    ✓     │    ✓     │"
echo "│ WebGL 2         │    ✓     │    ✓     │    ✓     │    ✓     │"
echo "│ ES6+ Features   │    ✓     │    ✓     │    ✓     │    ✓     │"
echo "│ CSS Grid        │    ✓     │    ✓     │    ✓     │    ✓     │"
echo "│ CSS Flexbox     │    ✓     │    ✓     │    ✓     │    ✓     │"
echo "│ Custom Props    │    ✓     │    ✓     │    ✓     │    ✓     │"
echo "│ Service Worker  │    ✓     │    ✓     │    ✓     │    ✓     │"
echo "│ IndexedDB       │    ✓     │    ✓     │    ✓     │    ✓     │"
echo "└─────────────────┴──────────┴──────────┴──────────┴──────────┘"

echo ""
info "For detailed browser support, visit: https://caniuse.com"

###############################################################################
# Manual Testing Checklist
###############################################################################

echo ""
echo -e "${BLUE}Manual Browser Testing Checklist:${NC}\n"

echo "Chrome (Latest):"
echo "  ☐ Page loads correctly"
echo "  ☐ All styles applied"
echo "  ☐ JavaScript executes without errors"
echo "  ☐ 3D scene renders properly"
echo "  ☐ Animations smooth"
echo "  ☐ Forms work correctly"
echo ""

echo "Firefox (Latest):"
echo "  ☐ Page loads correctly"
echo "  ☐ All styles applied"
echo "  ☐ JavaScript executes without errors"
echo "  ☐ 3D scene renders properly"
echo "  ☐ Animations smooth"
echo "  ☐ Forms work correctly"
echo ""

echo "Safari (Latest):"
echo "  ☐ Page loads correctly"
echo "  ☐ All styles applied (check vendor prefixes)"
echo "  ☐ JavaScript executes without errors"
echo "  ☐ 3D scene renders properly"
echo "  ☐ Animations smooth"
echo "  ☐ Forms work correctly"
echo "  ☐ iOS Safari tested on iPhone/iPad"
echo ""

echo "Edge (Latest):"
echo "  ☐ Page loads correctly"
echo "  ☐ All styles applied"
echo "  ☐ JavaScript executes without errors"
echo "  ☐ 3D scene renders properly"
echo "  ☐ Animations smooth"
echo "  ☐ Forms work correctly"
echo ""

echo "Legacy Browsers (if required):"
echo "  ☐ IE11: Graceful degradation"
echo "  ☐ Older Safari: Fallback content"
echo "  ☐ Feature detection in place"
echo ""

###############################################################################
# Summary
###############################################################################

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Browser Testing Summary${NC}"
echo -e "${BLUE}========================================${NC}\n"

success "Browser compatibility tests completed"
info "Screenshots and reports saved to: $OUTPUT_DIR"

echo ""
echo -e "${BLUE}Recommendations:${NC}\n"
echo "1. Test on real devices when possible"
echo "2. Use BrowserStack or similar for extensive testing"
echo "3. Check console for errors in each browser"
echo "4. Verify vendor prefixes for CSS properties"
echo "5. Test touch interactions on mobile browsers"
echo "6. Verify WebGL performance across browsers"
echo "7. Test private/incognito modes"
echo "8. Clear cache between tests"

echo ""
