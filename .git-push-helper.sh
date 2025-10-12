#!/bin/bash
# Git Push Helper - Prevents push conflicts by always pulling first

echo "🔄 Checking for remote changes..."
git fetch origin

# Check if there are remote changes
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "📥 Remote changes detected. Pulling and rebasing..."
    git pull origin main --rebase

    if [ $? -ne 0 ]; then
        echo "❌ Rebase failed. Please resolve conflicts manually."
        exit 1
    fi
fi

echo "🚀 Pushing to remote..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Push successful!"
else
    echo "❌ Push failed. Running automatic fix..."
    git pull origin main --rebase
    git push origin main
fi