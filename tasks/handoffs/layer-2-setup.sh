#!/bin/bash
# Layer 2: New Pipeline Stages — worktree setup
# Run from /Users/theceo/DevSkyy

set -e

echo "Setting up Layer 2 worktree..."
git worktree add ../elite-layer-2 -b elite/layer-2-pipeline-stages

echo ""
echo "Worktree created at: ../elite-layer-2"
echo ""
echo "Next: cd ../elite-layer-2 && claude"
echo "Then paste the contents of tasks/handoffs/layer-2-prompt.md as your first message."
