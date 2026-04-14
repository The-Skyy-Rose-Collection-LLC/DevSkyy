#!/bin/bash
# Layer 6: Virtual Try-On — worktree setup
# Run from /Users/theceo/DevSkyy
# NOTE: Requires Layers 1 + 5 to be merged first

set -e

echo "Setting up Layer 6 worktree..."
git worktree add ../elite-layer-6 -b elite/layer-6-virtual-tryon

echo ""
echo "Worktree created at: ../elite-layer-6"
echo ""
echo "Next: cd ../elite-layer-6 && claude"
echo "Then paste the contents of tasks/handoffs/layer-6-prompt.md as your first message."
