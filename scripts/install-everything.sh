#!/bin/bash
# =============================================================================
# DevSkyy — FULL INSTALL: All SDKs, CLIs, MCPs, APIs, Tools
# =============================================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'; BOLD='\033[1m'
log()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[!!]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; }
step() { echo -e "\n${BOLD}━━━ $1 ━━━${NC}"; }

ROOT="/Users/theceo/DevSkyy"
FRONTEND="$ROOT/frontend"

# ── 1. GLOBAL CLIs ──────────────────────────────────────────────────────────
step "1/8 — Global CLIs"

# Vercel CLI
if ! command -v /Users/theceo/.npm-global/bin/vercel &>/dev/null; then
  npm install -g vercel@latest 2>&1 | tail -2
fi
log "Vercel CLI: $(/Users/theceo/.npm-global/bin/vercel --version 2>/dev/null | head -1)"

# Prisma CLI (via npx, but ensure local)
log "Prisma: available via npx prisma"

# Playwright browsers
if ! python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
  pip install playwright 2>&1 | tail -2
fi
python3 -m playwright install chromium 2>&1 | tail -3 || warn "Playwright browsers already installed"
log "Playwright: $(playwright --version 2>/dev/null)"

# Sentry CLI
if ! command -v sentry-cli &>/dev/null; then
  npm install -g @sentry/cli@latest 2>&1 | tail -2
  log "Sentry CLI installed"
else
  log "Sentry CLI: $(sentry-cli --version 2>/dev/null)"
fi

# WP-CLI (if not installed)
if ! command -v wp &>/dev/null; then
  curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar 2>/dev/null
  chmod +x wp-cli.phar
  mv wp-cli.phar /Users/theceo/.npm-global/bin/wp 2>/dev/null || warn "WP-CLI: move to bin manually"
  log "WP-CLI installed"
else
  log "WP-CLI: $(wp --version 2>/dev/null)"
fi

# Wrangler (Cloudflare Workers)
if ! command -v wrangler &>/dev/null; then
  npm install -g wrangler@latest 2>&1 | tail -2
  log "Wrangler installed"
else
  log "Wrangler: $(wrangler --version 2>/dev/null | head -1)"
fi

# ── 2. ROOT NODE.JS — Missing SDKs ─────────────────────────────────────────
step "2/8 — Root Node.js SDKs (missing packages)"
cd "$ROOT"

npm install --legacy-peer-deps \
  @anthropic-ai/claude-agent-sdk@latest \
  @modelcontextprotocol/sdk@latest \
  @sentry/node@latest \
  @sentry/profiling-node@latest \
  zod@latest \
  drizzle-orm@latest \
  @auth/core@latest \
  bullmq@latest \
  stripe@latest \
  @stripe/stripe-js@latest \
  resend@latest \
  @upstash/redis@latest \
  @upstash/ratelimit@latest \
  @upstash/vector@latest \
  @upstash/qstash@latest \
  @planetscale/database@latest \
  @neondatabase/serverless@latest \
  @t3-oss/env-nextjs@latest \
  next-auth@latest \
  uploadthing@latest \
  @uploadthing/react@latest \
  unstructured-client@latest \
  langchain@latest \
  @langchain/core@latest \
  @langchain/openai@latest \
  @langchain/anthropic@latest \
  @langchain/community@latest \
  llamaindex@latest \
  openai@latest \
  replicate@latest \
  @huggingface/inference@latest \
  @huggingface/hub@latest \
  @pinecone-database/pinecone@latest \
  @qdrant/js-client-rest@latest \
  chromadb@latest \
  weaviate-client@latest \
  2>&1 | tail -10
log "Root SDKs installed"

# ── 3. ROOT NODE.JS — DevOps & Monitoring ──────────────────────────────────
step "3/8 — DevOps, Monitoring & Infra SDKs"
npm install --legacy-peer-deps \
  @opentelemetry/api@latest \
  @opentelemetry/sdk-node@latest \
  @opentelemetry/auto-instrumentations-node@latest \
  @opentelemetry/exporter-trace-otlp-http@latest \
  @opentelemetry/exporter-metrics-otlp-http@latest \
  pino@latest \
  pino-pretty@latest \
  winston@latest \
  helmet@latest \
  cors@latest \
  compression@latest \
  rate-limiter-flexible@latest \
  ioredis@latest \
  kafkajs@latest \
  amqplib@latest \
  2>&1 | tail -5
log "DevOps SDKs installed"

# ── 4. ROOT NODE.JS — Dev Tools ─────────────────────────────────────────────
step "4/8 — Dev Tools & Testing"
npm install --legacy-peer-deps -D \
  @playwright/test@latest \
  vitest@latest \
  @vitest/coverage-v8@latest \
  @vitest/ui@latest \
  msw@latest \
  supertest@latest \
  @types/supertest@latest \
  @types/express@latest \
  @types/cors@latest \
  @types/compression@latest \
  tsx@latest \
  concurrently@latest \
  husky@latest \
  lint-staged@latest \
  commitlint@latest \
  @commitlint/config-conventional@latest \
  knip@latest \
  depcheck@latest \
  npm-check-updates@latest \
  2>&1 | tail -5
log "Dev tools installed"

# ── 5. FRONTEND — Additional SDKs ──────────────────────────────────────────
step "5/8 — Frontend Additional SDKs"
cd "$FRONTEND"

npm install --legacy-peer-deps \
  @modelcontextprotocol/sdk@latest \
  @stripe/stripe-js@latest \
  @upstash/redis@latest \
  @t3-oss/env-nextjs@latest \
  next-auth@latest \
  next-themes@latest \
  @tanstack/react-query@latest \
  @tanstack/react-table@latest \
  zustand@latest \
  jotai@latest \
  nuqs@latest \
  cmdk@latest \
  vaul@latest \
  input-otp@latest \
  @radix-ui/react-dialog@latest \
  @radix-ui/react-dropdown-menu@latest \
  @radix-ui/react-select@latest \
  @radix-ui/react-switch@latest \
  @radix-ui/react-toast@latest \
  @radix-ui/react-tooltip@latest \
  @radix-ui/react-avatar@latest \
  @radix-ui/react-checkbox@latest \
  @radix-ui/react-popover@latest \
  @radix-ui/react-separator@latest \
  @radix-ui/react-scroll-area@latest \
  @radix-ui/react-accordion@latest \
  @radix-ui/react-collapsible@latest \
  @radix-ui/react-navigation-menu@latest \
  @radix-ui/react-hover-card@latest \
  @radix-ui/react-aspect-ratio@latest \
  react-hook-form@latest \
  @hookform/resolvers@latest \
  zod@latest \
  date-fns@latest \
  recharts@latest \
  react-day-picker@latest \
  embla-carousel-react@latest \
  react-resizable-panels@latest \
  sharp@latest \
  2>&1 | tail -5
log "Frontend SDKs installed"

# ── 6. FRONTEND — Dev Tools ─────────────────────────────────────────────────
step "6/8 — Frontend Dev Tools"
npm install --legacy-peer-deps -D \
  @playwright/test@latest \
  @storybook/react@latest \
  @storybook/nextjs@latest \
  @testing-library/react@latest \
  @testing-library/jest-dom@latest \
  @testing-library/user-event@latest \
  2>&1 | tail -5
log "Frontend dev tools installed"

# ── 7. PYTHON — Additional SDKs ────────────────────────────────────────────
step "7/8 — Python Additional SDKs & Tools"
cd "$ROOT"

pip install --quiet \
  pip-audit \
  safety \
  bandit \
  pre-commit \
  httpie \
  rich-cli \
  textual \
  typer[all] \
  click \
  pydantic-ai \
  instructor \
  marvin \
  guardrails-ai \
  litellm \
  lancedb \
  weaviate-client \
  pinecone-client \
  qdrant-client \
  google-cloud-aiplatform \
  boto3 \
  stripe \
  resend \
  twilio \
  sendgrid \
  celery[redis] \
  flower \
  dramatiq[redis] \
  rq \
  locust \
  k6 \
  2>&1 | tail -10 || warn "Some optional Python packages failed (non-critical)"
log "Python additional SDKs installed"

# ── 8. VERIFICATION ─────────────────────────────────────────────────────────
step "8/8 — Verification"

echo ""
echo -e "${BOLD}Global CLIs:${NC}"
for cmd in gh vercel sentry-cli playwright wp wrangler; do
  printf "  %-15s " "$cmd"
  if [ "$cmd" = "vercel" ]; then
    /Users/theceo/.npm-global/bin/vercel --version 2>/dev/null | head -1 || echo "NOT FOUND"
  else
    command -v $cmd &>/dev/null && echo "OK" || echo "NOT FOUND"
  fi
done

echo ""
echo -e "${BOLD}Root Node packages (new):${NC}"
cd "$ROOT"
npm list --depth=0 2>/dev/null | grep -E "@anthropic-ai/claude|@modelcontextprotocol|@sentry|stripe|@upstash|@langchain|openai|@huggingface|@pinecone|bullmq|zod@|drizzle|@opentelemetry" | head -25

echo ""
echo -e "${BOLD}Frontend packages (new):${NC}"
cd "$FRONTEND"
npm list --depth=0 2>/dev/null | grep -E "@tanstack|zustand|next-auth|@radix-ui|react-hook-form|@stripe|cmdk|vaul|nuqs" | head -20

echo ""
echo -e "${BOLD}Python packages (new):${NC}"
pip list 2>/dev/null | grep -iE "litellm|instructor|pydantic-ai|lancedb|pinecone|qdrant|weaviate|stripe|boto3|celery|locust|bandit|pip-audit|safety|guardrails|typer|dramatiq" | head -20

echo ""
echo -e "${GREEN}${BOLD}Installation complete!${NC}"
