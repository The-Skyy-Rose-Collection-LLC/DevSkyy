#!/bin/bash
#
# DevSkyy SessionStart Hook - Load Brand DNA & Environment Context
# Executes when Claude Code session starts to inject project context
#

set -euo pipefail

# Read hook input (though we don't need it for SessionStart)
input=$(cat)

# Get project directory
project_dir="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Initialize context message
context_message="🎯 **DevSkyy Production Environment Loaded**\n\n"

# ============================================================================
# 1. LOAD SKYYROSE BRAND DNA
# ============================================================================
context_message+="## SkyyRose Brand Context\n\n"
context_message+="**Brand Name**: SkyyRose\n"
context_message+="**Tagline**: Where Love Meets Luxury\n"
context_message+="**Style**: Premium, Sophisticated, Bold, Elegant\n"
context_message+="**Primary Color**: #B76E79 (Rose Gold)\n"
context_message+="**Secondary Color**: #1A1A1A (Noir)\n"
context_message+="**Tertiary Color**: #FFFFFF (Pure White)\n\n"

context_message+="**Brand Voice**:\n"
context_message+="- Confident yet approachable\n"
context_message+="- Luxury without pretension\n"
context_message+="- Empowering and inclusive\n"
context_message+="- Innovation-driven\n\n"

# ============================================================================
# 2. LOAD ENVIRONMENT CONFIGURATION
# ============================================================================
context_message+="## Environment Configuration\n\n"

# Check for .env file
if [ -f "$project_dir/.env" ]; then
  # Extract non-sensitive config (don't expose actual secrets)
  if grep -q "ENVIRONMENT=" "$project_dir/.env" 2>/dev/null; then
    env_type=$(grep "ENVIRONMENT=" "$project_dir/.env" | cut -d'=' -f2 | tr -d '"')
    context_message+="**Environment**: ${env_type}\n"
  else
    context_message+="**Environment**: production (default)\n"
  fi

  # Check which providers are configured (without exposing keys)
  providers=()
  [ $(grep -c "OPENAI_API_KEY=" "$project_dir/.env" 2>/dev/null) -gt 0 ] && providers+=("OpenAI")
  [ $(grep -c "ANTHROPIC_API_KEY=" "$project_dir/.env" 2>/dev/null) -gt 0 ] && providers+=("Anthropic")
  [ $(grep -c "GOOGLE_AI_API_KEY=" "$project_dir/.env" 2>/dev/null) -gt 0 ] && providers+=("Google")
  [ $(grep -c "TRIPO_API_KEY=" "$project_dir/.env" 2>/dev/null) -gt 0 ] && providers+=("Tripo3D")
  [ $(grep -c "FASHN_API_KEY=" "$project_dir/.env" 2>/dev/null) -gt 0 ] && providers+=("FASHN")

  if [ ${#providers[@]} -gt 0 ]; then
    context_message+="**LLM/AI Providers**: $(IFS=', '; echo "${providers[*]}")\n"
  fi

  # Check for WordPress/WooCommerce config
  if grep -q "WORDPRESS_URL=" "$project_dir/.env" 2>/dev/null; then
    wp_url=$(grep "WORDPRESS_URL=" "$project_dir/.env" | cut -d'=' -f2 | tr -d '"')
    context_message+="**WordPress Site**: ${wp_url}\n"
  fi

  # Check for vector DB config
  if grep -q "VECTOR_DB_PATH=" "$project_dir/.env" 2>/dev/null; then
    context_message+="**RAG System**: Enabled (ChromaDB)\n"
  fi
else
  context_message+="**Environment**: .env file not found (using defaults)\n"
fi

context_message+="\n"

# ============================================================================
# 3. LOAD PROJECT ARCHITECTURE CONTEXT
# ============================================================================
context_message+="## Project Architecture\n\n"
context_message+="**SuperAgents**: Commerce, Creative, Marketing, Support, Operations, Analytics\n"
context_message+="**LLM Providers**: 6 providers (OpenAI, Anthropic, Google, Mistral, Cohere, Groq)\n"
context_message+="**Visual AI**: Tripo3D (3D gen), Imagen/FLUX (images), FASHN (try-on)\n"
context_message+="**Framework**: FastAPI + Next.js 15 + Three.js\n"
context_message+="**Database**: PostgreSQL (asyncpg)\n"
context_message+="**Caching**: Redis\n\n"

# ============================================================================
# 4. LOAD ABSOLUTE RULES REMINDER
# ============================================================================
context_message+="## 🔒 DevSkyy ABSOLUTE RULES (Always Active)\n\n"
context_message+="1. **Correctness > Elegance > Performance** - No magic, explicit contracts\n"
context_message+="2. **No Feature Deletions** - Refactor/harden only, never remove capabilities\n"
context_message+="3. **Truthful Codebase** - No placeholders, stubs, or TODOs\n"
context_message+="4. **TDD Mandatory** - Tests first, then implementation\n"
context_message+="5. **Type Hints Everywhere** - Pydantic validation required\n"
context_message+="6. **Format on Save**: \`isort && ruff --fix && black\`\n\n"

# ============================================================================
# 5. CHECK FOR ACTIVE BRANCH & GIT STATUS
# ============================================================================
if [ -d "$project_dir/.git" ]; then
  current_branch=$(git -C "$project_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  context_message+="## Git Context\n\n"
  context_message+="**Current Branch**: ${current_branch}\n"

  # Count uncommitted changes
  uncommitted=$(git -C "$project_dir" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  if [ "$uncommitted" -gt 0 ]; then
    context_message+="**Uncommitted Changes**: ${uncommitted} files\n"
  fi
  context_message+="\n"
fi

# ============================================================================
# 6. PERSIST ENVIRONMENT VARIABLES (Available to all future bash commands)
# ============================================================================
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo "# DevSkyy Environment Variables"
    echo "export DEVSKYY_PROJECT_ROOT=\"$project_dir\""
    echo "export DEVSKYY_BRAND_NAME=\"SkyyRose\""
    echo "export DEVSKYY_PRIMARY_COLOR=\"#B76E79\""
    echo "export DEVSKYY_ENVIRONMENT=\"production\""

    # Add Python path if not already set
    if [ ! -v PYTHONPATH ]; then
      echo "export PYTHONPATH=\"$project_dir:\${PYTHONPATH:-}\""
    fi
  } >> "$CLAUDE_ENV_FILE"
fi

# ============================================================================
# 7. OUTPUT CONTEXT TO CLAUDE
# ============================================================================
cat <<EOF
{
  "continue": true,
  "suppressOutput": false,
  "systemMessage": "$(echo -e "$context_message" | sed 's/"/\\"/g' | tr '\n' ' ' | sed 's/  */ /g')"
}
EOF

exit 0
