#!/bin/bash

# Link Vercel Project to "devskyy"
# This script helps link the local project to the Vercel "devskyy" project

echo "🔗 Linking to Vercel project 'devskyy'..."
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm i -g vercel
fi

echo "📋 Current project link:"
if [ -f .vercel/project.json ]; then
    cat .vercel/project.json | python3 -m json.tool
else
    echo "Not linked yet"
fi

echo ""
echo "🔄 To link to 'devskyy' project, run:"
echo "   vercel link --project=devskyy"
echo ""
echo "Or manually link by running:"
echo "   vercel link"
echo "   Then select your team and choose 'devskyy' project"
echo ""

# Option to auto-link if user confirms
read -p "Would you like to auto-link now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Linking..."
    vercel link --yes --project=devskyy

    if [ $? -eq 0 ]; then
        echo "✅ Successfully linked to devskyy project!"
        echo ""
        echo "📋 New project link:"
        cat .vercel/project.json | python3 -m json.tool
    else
        echo "❌ Failed to link. You may need to:"
        echo "   1. Login: vercel login"
        echo "   2. Link manually: vercel link"
    fi
fi
