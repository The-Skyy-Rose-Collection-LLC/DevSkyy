#!/bin/bash

# Jekyll Deployment Test Script
# Tests Jekyll build and serves the site

echo "🔧 Testing Jekyll Deployment for DevSkyy Platform"
echo "================================================="

# Set up environment
export PATH="$HOME/.local/share/gem/ruby/3.2.0/bin:$PATH"

# Check Ruby and Jekyll
echo "📋 Checking prerequisites..."
ruby --version
bundle --version
jekyll --version

echo ""
echo "🧹 Cleaning previous builds..."
bundle exec jekyll clean

echo ""
echo "🏗️ Building Jekyll site..."
bundle exec jekyll build

if [ $? -eq 0 ]; then
    echo "✅ Jekyll build successful!"
    echo ""
    echo "📊 Site structure:"
    ls -la _site/
    
    echo ""
    echo "📄 Generated files:"
    find _site -name "*.html" | head -10
    
    echo ""
    echo "🧪 Testing built site..."
    
    # Check if index.html exists
    if [ -f "_site/index.html" ]; then
        echo "✅ Homepage generated successfully"
    else
        echo "❌ Homepage not found"
        exit 1
    fi
    
    # Check if documentation pages exist
    if [ -f "_site/docs/installation/index.html" ]; then
        echo "✅ Installation guide generated successfully"
    else
        echo "❌ Installation guide not found"
        exit 1
    fi
    
    if [ -f "_site/docs/api-reference/index.html" ]; then
        echo "✅ API reference generated successfully"
    else
        echo "❌ API reference not found"
        exit 1
    fi
    
    # Check CSS
    if [ -f "_site/assets/css/style.css" ]; then
        echo "✅ Luxury styling generated successfully"
    else
        echo "❌ Styling not found"
        exit 1
    fi
    
    echo ""
    echo "🎉 Jekyll deployment test PASSED!"
    echo "🌐 Site ready for GitHub Pages deployment"
    echo ""
    echo "🚀 To deploy:"
    echo "   1. Push to GitHub"
    echo "   2. Enable GitHub Pages in repository settings"
    echo "   3. Set source to 'GitHub Actions'"
    echo ""
    echo "💡 Local development:"
    echo "   bundle exec jekyll serve --host 0.0.0.0 --port 4000"
    
else
    echo "❌ Jekyll build failed!"
    exit 1
fi