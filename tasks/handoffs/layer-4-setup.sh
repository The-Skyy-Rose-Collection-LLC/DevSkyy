#!/bin/bash
# Layer 4: Quality System — worktree setup
# Run from /Users/theceo/DevSkyy
# NOTE: Requires Layers 2 + 3 to be merged first

set -e

echo "Setting up Layer 4 worktree..."
git worktree add ../elite-layer-4 -b elite/layer-4-quality-system

echo ""
echo "Worktree created at: ../elite-layer-4"
echo ""
echo "Next: cd ../elite-layer-4 && claude"
echo "Then paste the contents of tasks/handoffs/layer-4-prompt.md as your first message."
