#!/bin/bash
# =============================================================================
# DevSkyy — Vercel Full Stack Install
# Installs: CLI, SDKs, AI SDK, Storage, MCP, Edge Config, Monitoring, Functions
# =============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
BOLD='\033[1m'

log()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[!!]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; }
step() { echo -e "\n${BOLD}==> $1${NC}"; }

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

# ── 1. Vercel CLI (global) ──────────────────────────────────────────────────
step "1/6 — Vercel CLI (global)"
if command -v vercel &>/dev/null; then
  CURRENT=$(vercel --version 2>/dev/null | head -1)
  warn "Vercel CLI already installed: $CURRENT — upgrading..."
  npm install -g vercel@latest --legacy-peer-deps 2>&1 | tail -3
else
  npm install -g vercel@latest 2>&1 | tail -3
fi
log "Vercel CLI: $(vercel --version 2>/dev/null | head -1)"

# ── 2. Vercel Platform SDKs (root) ──────────────────────────────────────────
step "2/6 — Vercel Platform SDKs (root: $ROOT_DIR)"
cd "$ROOT_DIR"
npm install --legacy-peer-deps \
  @vercel/sdk@latest \
  @vercel/node@latest \
  @vercel/functions@latest \
  @vercel/analytics@latest \
  @vercel/speed-insights@latest \
  @vercel/og@latest \
  @vercel/toolbar@latest \
  @vercel/blob@latest \
  @vercel/edge-config@latest \
  @vercel/kv@latest \
  @vercel/postgres@latest \
  @vercel/sandbox@latest \
  2>&1 | tail -5
log "Platform SDKs installed in root"

# ── 3. Vercel AI SDK + Providers (root) ─────────────────────────────────────
step "3/6 — Vercel AI SDK + Gateway + Providers (root)"
npm install --legacy-peer-deps \
  ai@latest \
  @ai-sdk/gateway@latest \
  @ai-sdk/anthropic@latest \
  @ai-sdk/openai@latest \
  @ai-sdk/openai-compatible@latest \
  @ai-sdk/google@latest \
  @ai-sdk/google-vertex@latest \
  @ai-sdk/mistral@latest \
  @ai-sdk/cohere@latest \
  @ai-sdk/huggingface@latest \
  @ai-sdk/groq@latest \
  @ai-sdk/xai@latest \
  @ai-sdk/amazon-bedrock@latest \
  @ai-sdk/azure@latest \
  2>&1 | tail -5
log "AI SDK + all providers installed"

# ── 4. Frontend SDKs ────────────────────────────────────────────────────────
step "4/6 — Vercel SDKs (frontend: $FRONTEND_DIR)"
if [ -d "$FRONTEND_DIR" ]; then
  cd "$FRONTEND_DIR"
  npm install --legacy-peer-deps \
    @vercel/analytics@latest \
    @vercel/speed-insights@latest \
    @vercel/og@latest \
    @vercel/toolbar@latest \
    @vercel/blob@latest \
    @vercel/edge-config@latest \
    @vercel/kv@latest \
    @vercel/functions@latest \
    ai@latest \
    @ai-sdk/gateway@latest \
    @ai-sdk/anthropic@latest \
    @ai-sdk/openai@latest \
    2>&1 | tail -5
  log "Frontend Vercel SDKs installed"
else
  warn "No frontend/ directory found — skipping"
fi

# ── 5. Python AI Gateway SDKs ───────────────────────────────────────────────
step "5/6 — Python Vercel AI Gateway SDKs"
cd "$ROOT_DIR"
pip install --quiet \
  llama-index-llms-vercel-ai-gateway \
  2>&1 | tail -3 || warn "llama-index-llms-vercel-ai-gateway failed (optional)"
log "Python Vercel packages installed"

# ── 6. Verify everything ────────────────────────────────────────────────────
step "6/6 — Verification"

echo ""
echo -e "${BOLD}Vercel CLI:${NC}"
vercel --version 2>/dev/null | head -1 || err "CLI not found"

echo ""
echo -e "${BOLD}Root node_modules:${NC}"
cd "$ROOT_DIR"
npm list --depth=0 2>/dev/null | grep -E "@vercel|^ai |@ai-sdk" | head -30

echo ""
echo -e "${BOLD}Frontend node_modules:${NC}"
if [ -d "$FRONTEND_DIR/node_modules" ]; then
  cd "$FRONTEND_DIR"
  npm list --depth=0 2>/dev/null | grep -E "@vercel|^ai |@ai-sdk" | head -20
fi

echo ""
echo -e "${BOLD}Python packages:${NC}"
pip list 2>/dev/null | grep -i -E "vercel|llama.*gateway" || echo "  (none)"

echo ""
echo -e "${GREEN}${BOLD}Done! All Vercel packages installed.${NC}"
echo -e "Run ${BOLD}vercel login${NC} to authenticate the CLI."
