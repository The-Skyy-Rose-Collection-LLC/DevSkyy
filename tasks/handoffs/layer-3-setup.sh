#!/bin/bash
# Layer 3: Production Infrastructure — worktree setup
# Run from /Users/theceo/DevSkyy
# NOTE: Requires Layer 1 to be merged to main first

set -e

echo "Setting up Layer 3 worktree..."
git worktree add ../elite-layer-3 -b elite/layer-3-production-infra

echo ""
echo "Worktree created at: ../elite-layer-3"
echo ""
echo "Next: cd ../elite-layer-3 && claude"
echo "Then paste the contents of tasks/handoffs/layer-3-prompt.md as your first message."
