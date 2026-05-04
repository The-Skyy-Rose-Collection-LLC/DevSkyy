"""Canonical LLM model IDs — single source of truth for model strings.

Importers across the codebase (`agents/`, `skyyrose/`, `orchestration/`,
service code) MUST pull model strings from this module rather than
hardcoding inline. When a model is rolled forward (e.g. Claude Sonnet
4.6 → 4.7), updating the constant here updates every caller in one shot.

Conventions:
- ``*_MODEL`` constants hold the literal API model identifier as the
  provider expects it.
- Aliases group by use case (``COMPOSITOR_*``, ``VISION_*``, ``QC_*``)
  so callers express intent, not the concrete model.

If you add a new model:
1. Add the literal ID near the top, grouped by provider.
2. If it's used for a specific pipeline role, add an alias below.
3. Update any caller that referenced an older string.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Anthropic (Claude 4.x family)
# ---------------------------------------------------------------------------

CLAUDE_OPUS_MODEL = "claude-opus-4-7"  # deepest reasoning, frontier intelligence
CLAUDE_SONNET_MODEL = "claude-sonnet-4-6"  # workhorse, best speed/intelligence
CLAUDE_HAIKU_MODEL = "claude-haiku-4-5"  # fast classification + simple tasks
CLAUDE_MYTHOS_PREVIEW_MODEL = (
    "claude-mythos-preview"  # new class — strongest at coding + cybersecurity (preview)
)

# ---------------------------------------------------------------------------
# Google Gemini (3.x family)
# ---------------------------------------------------------------------------

GEMINI_VISION_MODEL = "gemini-3-flash-preview"  # text-output vision (cheap)
GEMINI_PRO_MODEL = "gemini-3-pro-preview"  # text-only deep reasoning
GEMINI_PRO_IMAGE_MODEL = "gemini-3-pro-image-preview"  # image gen, deep
GEMINI_FLASH_IMAGE_MODEL = "gemini-3.1-flash-image-preview"  # image gen w/ refs

# "Nano Banana" branded aliases (Google's marketing names for the
# Gemini native image-generation models). Per Context7 verification of
# Google's docs (2026-05-03):
#   - Nano Banana     = gemini-2.5-flash-image       (original)
#   - Nano Banana 2   = gemini-3.1-flash-image-preview  (new flash w/ thinking)
#   - Nano Banana Pro = gemini-3-pro-image-preview     (4K, deep reasoning)
# Sources:
#   https://ai.google.dev/gemini-api/docs/video       ("Step 1: Nano Banana 2")
#   https://ai.google.dev/gemini-api/docs/gemini-3    (gemini-3-pro-image-preview)
#   agents/visual_generation/gemini_native.py docstring (Nano Banana Pro = pro)
NANO_BANANA_MODEL = "gemini-2.5-flash-image"  # original
NANO_BANANA_2_MODEL = GEMINI_FLASH_IMAGE_MODEL  # gemini-3.1-flash-image-preview
NANO_BANANA_PRO_MODEL = GEMINI_PRO_IMAGE_MODEL  # gemini-3-pro-image-preview, 4K

# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------

OPENAI_VISION_MODEL = "gpt-4o"  # multimodal flagship
OPENAI_MINI_MODEL = "gpt-4o-mini"  # cheap text + vision

# Image generation lineage (verified against Context7 OpenAI docs 2026-05-03):
#   gpt-image-1       → original GPT image model
#   gpt-image-1-mini  → mini variant of v1 (cheaper, lower fidelity)
#   gpt-image-1.5     → 1.5 generation (improved quality)
#   gpt-image-2       → latest, current default per OpenAI docs guide
OPENAI_IMAGE_MODEL = "gpt-image-1"  # default — original (kept for back-compat)
OPENAI_IMAGE_MINI_MODEL = "gpt-image-1-mini"  # cheap variant
OPENAI_IMAGE_15_MODEL = "gpt-image-1.5"  # 1.5 generation
OPENAI_IMAGE_2_MODEL = "gpt-image-2"  # latest GPT image model

# ---------------------------------------------------------------------------
# xAI
# ---------------------------------------------------------------------------

XAI_GROK_MODEL = "grok-3"

# ---------------------------------------------------------------------------
# 3D
# ---------------------------------------------------------------------------

MESHY_AI_MODEL = "meshy-5"  # mirrored in ai_3d/providers/meshy.py

# ---------------------------------------------------------------------------
# Pipeline-role aliases — express intent, not concrete model.
# Update the constants above to roll forward; callers stay the same.
# ---------------------------------------------------------------------------

VISION_CLAUDE_MODEL = CLAUDE_OPUS_MODEL  # vision_agent / claude vision calls
QC_CLAUDE_MODEL = CLAUDE_SONNET_MODEL  # quality_agent.verify
COMPOSITOR_CLAUDE_MODEL = CLAUDE_OPUS_MODEL  # compositor_agent prompt synth
RAS_GENERATION_MODEL = GEMINI_FLASH_IMAGE_MODEL  # 3D + generator agents
GENERATION_MODEL = GEMINI_FLASH_IMAGE_MODEL  # default image generation
QC_MODEL = QC_CLAUDE_MODEL

# Specialist roles — mythos-preview is strongest for these per Anthropic docs
SECURITY_AUDIT_MODEL = CLAUDE_MYTHOS_PREVIEW_MODEL  # security_ops_agent — cybersecurity
CODE_REVIEW_MODEL = CLAUDE_MYTHOS_PREVIEW_MODEL  # coding_doctor_agent — coding

# Multi-agent orchestrator roles (skyyrose/multi_agent)
ORCHESTRATOR_MODEL = CLAUDE_OPUS_MODEL  # planning, decomposition
SUBAGENT_MODEL = CLAUDE_SONNET_MODEL  # cost-efficient subagents
FAST_MODEL = CLAUDE_HAIKU_MODEL  # classification, simple tasks

# Compositor stage models (legacy names kept for back-compat)
COMPOSITOR_OPUS_MODEL = COMPOSITOR_CLAUDE_MODEL
COMPOSITOR_QA_MODEL = GEMINI_FLASH_IMAGE_MODEL  # visual QA via Gemini

__all__ = [
    "CLAUDE_HAIKU_MODEL",
    "CLAUDE_MYTHOS_PREVIEW_MODEL",
    "CLAUDE_OPUS_MODEL",
    "CLAUDE_SONNET_MODEL",
    "CODE_REVIEW_MODEL",
    "COMPOSITOR_CLAUDE_MODEL",
    "COMPOSITOR_OPUS_MODEL",
    "COMPOSITOR_QA_MODEL",
    "FAST_MODEL",
    "GEMINI_FLASH_IMAGE_MODEL",
    "GEMINI_PRO_IMAGE_MODEL",
    "GEMINI_PRO_MODEL",
    "GEMINI_VISION_MODEL",
    "GENERATION_MODEL",
    "MESHY_AI_MODEL",
    "NANO_BANANA_2_MODEL",
    "NANO_BANANA_MODEL",
    "NANO_BANANA_PRO_MODEL",
    "OPENAI_IMAGE_15_MODEL",
    "OPENAI_IMAGE_2_MODEL",
    "OPENAI_IMAGE_MINI_MODEL",
    "OPENAI_IMAGE_MODEL",
    "OPENAI_MINI_MODEL",
    "OPENAI_VISION_MODEL",
    "ORCHESTRATOR_MODEL",
    "QC_CLAUDE_MODEL",
    "QC_MODEL",
    "RAS_GENERATION_MODEL",
    "SECURITY_AUDIT_MODEL",
    "SUBAGENT_MODEL",
    "VISION_CLAUDE_MODEL",
    "XAI_GROK_MODEL",
]
