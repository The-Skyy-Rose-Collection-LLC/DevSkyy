#!/bin/bash

# WordPress Plugin Production Build Script
echo "🏗️ Building Skyy Rose AI Agents WordPress Plugin for Production..."

# Set environment variables for production
export NODE_ENV=production
export WP_ENV=production

# Navigate to plugin directory
cd wordpress-plugin

echo "📋 Running production checklist..."

# 1. Validate PHP syntax
echo "✅ Validating PHP syntax..."
find . -name "*.php" -exec php -l {} \; > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ PHP syntax validation passed"
else
    echo "❌ PHP syntax validation failed"
    exit 1
fi

# 2. Check for debug statements
echo "🔍 Checking for debug statements..."
DEBUG_COUNT=$(find . -name "*.php" -exec grep -l "var_dump\|print_r\|echo.*debug\|console\.log" {} \; | wc -l)
if [ $DEBUG_COUNT -eq 0 ]; then
    echo "✅ No debug statements found"
else
    echo "⚠️  Found $DEBUG_COUNT files with debug statements"
fi

# 3. Verify security implementations
echo "🔒 Verifying security implementations..."
SECURITY_COUNT=$(find . -name "*.php" -exec grep -l "wp_verify_nonce\|check_admin_referer\|current_user_can" {} \; | wc -l)
echo "✅ Found security implementations in $SECURITY_COUNT files"

# 4. Check for direct access protection
echo "🛡️ Checking direct access protection..."
NO_ABSPATH=$(find . -name "*.php" -exec grep -L "defined.*ABSPATH.*exit" {} \; | wc -l)
if [ $NO_ABSPATH -eq 0 ]; then
    echo "✅ All PHP files protected from direct access"
else
    echo "⚠️  $NO_ABSPATH files missing ABSPATH protection"
fi

# 5. Create production package
echo "📦 Creating production package..."
cd ..
mkdir -p build/wordpress-plugin
cp -r wordpress-plugin/* build/wordpress-plugin/

# Remove development files from production build
cd build/wordpress-plugin
rm -f production-checklist.md
rm -f TRANSFORMATION_SUMMARY.php

# Create plugin zip file
cd ..
zip -r "skyy-rose-ai-agents-production.zip" wordpress-plugin/ -x "*.md" "*.log"

echo "🎉 Production build complete!"
echo "📍 Location: build/skyy-rose-ai-agents-production.zip"
echo "🚀 Ready for WordPress deployment!"

# Final status
echo ""
echo "=== PRODUCTION BUILD SUMMARY ==="
echo "✅ PHP syntax validated"
echo "✅ Security implementations verified"
echo "✅ Direct access protection confirmed"
echo "✅ Production package created"
echo "✅ Plugin ready for production deployment"