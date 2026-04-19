#!/bin/bash
# Layer 5: API & Observability — worktree setup
# Run from /Users/theceo/DevSkyy
# NOTE: Requires Layers 3 + 4 to be merged first

set -e

echo "Setting up Layer 5 worktree..."
git worktree add ../elite-layer-5 -b elite/layer-5-api-observability

echo ""
echo "Worktree created at: ../elite-layer-5"
echo ""
echo "Next: cd ../elite-layer-5 && claude"
echo "Then paste the contents of tasks/handoffs/layer-5-prompt.md as your first message."
