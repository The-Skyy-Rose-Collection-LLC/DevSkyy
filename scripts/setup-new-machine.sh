#!/usr/bin/env bash
# DevSkyy — New Machine Setup
# Sets up the full DevSkyy dev environment: repo, worktrees, venvs, AI peers.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/The-Skyy-Rose-Collection-LLC/DevSkyy/main/scripts/setup-new-machine.sh | bash
#   OR
#   ./scripts/setup-new-machine.sh

set -euo pipefail

REPO_URL="https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git"
TARGET_DIR="${HOME}/DevSkyy"
PYTHON="${PYTHON:-python3}"

cyan() { printf "\033[36m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
yellow() { printf "\033[33m%s\033[0m\n" "$*"; }
red() { printf "\033[31m%s\033[0m\n" "$*"; }

cyan "DevSkyy — New Machine Setup"
echo "============================================"

# 1. Check prerequisites
cyan "[1/7] Checking prerequisites..."
for cmd in git node npm python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        red "Missing: $cmd — install it first"
        exit 1
    fi
done
green "  git, node, npm, python3 — OK"

# 2. Clone repo (or pull if exists)
cyan "[2/7] Cloning repository..."
if [ -d "$TARGET_DIR" ]; then
    yellow "  Directory exists — pulling latest"
    cd "$TARGET_DIR"
    git pull origin main
else
    git clone "$REPO_URL" "$TARGET_DIR"
    cd "$TARGET_DIR"
fi
green "  Repo at: $TARGET_DIR"

# 3. Set up worktrees
cyan "[3/7] Creating worktrees..."
git fetch origin
mkdir -p .claude/worktrees

for branch in wp-theme-work worktree-skyyrose-award; do
    worktree_path=".claude/worktrees/$(echo "$branch" | sed 's/worktree-//; s/-work$//')"
    if [ -d "$worktree_path" ]; then
        yellow "  $worktree_path exists — skipping"
    else
        git worktree add "$worktree_path" "$branch" 2>/dev/null || \
            git worktree add -b "$branch" "$worktree_path" "origin/$branch"
        green "  $worktree_path -> $branch"
    fi
done

# 4. Install AI peers (Claude Code, Codex, Gemini)
cyan "[4/7] Installing AI coding peers..."
npm install -g @anthropic-ai/claude-code@latest @openai/codex@latest @google/gemini-cli@latest 2>&1 | tail -3
green "  claude, codex, gemini installed"

# 5. Set up Python venvs
cyan "[5/7] Setting up Python environments..."
if [ ! -d "$TARGET_DIR/.venv" ]; then
    $PYTHON -m venv "$TARGET_DIR/.venv"
    "$TARGET_DIR/.venv/bin/pip" install -q --upgrade pip
    "$TARGET_DIR/.venv/bin/pip" install -q -e ".[all]" 2>&1 | tail -3 || yellow "  main venv install skipped (errors)"
fi
green "  .venv ready"

IMAGERY_VENV="$TARGET_DIR/.claude/worktrees/wp-theme/.venv-imagery"
REQS="$TARGET_DIR/.claude/worktrees/wp-theme/requirements-imagery.txt"
if [ ! -d "$IMAGERY_VENV" ] && [ -f "$REQS" ]; then
    $PYTHON -m venv "$IMAGERY_VENV"
    "$IMAGERY_VENV/bin/pip" install -q --upgrade pip
    "$IMAGERY_VENV/bin/pip" install -q -r "$REQS"
    green "  .venv-imagery ready (Nano Banana pipeline)"
fi

# 6. Install frontend deps
cyan "[6/7] Installing frontend dependencies..."
if [ -d "$TARGET_DIR/frontend" ]; then
    (cd "$TARGET_DIR/frontend" && npm install --silent 2>&1 | tail -3)
    green "  frontend/node_modules ready"
fi

# 7. API keys reminder
cyan "[7/7] API keys setup required"
yellow "  Copy these files from your other machine manually (they're gitignored):"
yellow "    $TARGET_DIR/.env.secrets         (all API keys)"
yellow "    $TARGET_DIR/.claude/worktrees/wp-theme/.env.hf  (nano-banana keys)"
yellow ""
yellow "  Secure transfer options:"
yellow "    scp user@oldmachine:~/DevSkyy/.env.secrets ~/DevSkyy/.env.secrets"
yellow "    OR 1Password CLI: op document get 'DevSkyy .env.secrets' > ~/DevSkyy/.env.secrets"

echo ""
green "Setup complete."
echo ""
cyan "Next steps:"
echo "  cd $TARGET_DIR/.claude/worktrees/wp-theme"
echo "  claude              # start Claude Code"
echo ""
echo "  # Test Nano Banana pipeline:"
echo "  source .venv-imagery/bin/activate"
echo "  python scripts/nano-banana-run.py dry-run"
