"""
Elite Prompt Intelligence System.

Transforms human-language prompts into expert-level agent briefs.
Includes semantic caching, learning loop, and SkyyRose brand DNA injection.
"""

from skyyrose.elite_studio.prompts.analyzer import PromptAnalysis, PromptAnalyzer
from skyyrose.elite_studio.prompts.cache import PromptCache
from skyyrose.elite_studio.prompts.chain import PromptChain
from skyyrose.elite_studio.prompts.enhancer import EnhancedPrompt, PromptEnhancer
from skyyrose.elite_studio.prompts.history import PromptHistory

# Prompt Library — source of truth for prompts with production impact
# (backed by assets/prompts/registry.yaml). Complements the prompt-intelligence
# modules above (analyzer/cache/chain/enhancer/history/templates).
from skyyrose.elite_studio.prompts.library import (
    Component,
    MissingVariableError,
    Prompt,
    PromptLibrary,
)
from skyyrose.elite_studio.prompts.templates import PromptTemplate, PromptTemplateRegistry

__all__ = [
    "Component",
    "EnhancedPrompt",
    "MissingVariableError",
    "Prompt",
    "PromptAnalysis",
    "PromptAnalyzer",
    "PromptCache",
    "PromptChain",
    "PromptEnhancer",
    "PromptHistory",
    "PromptLibrary",
    "PromptTemplate",
    "PromptTemplateRegistry",
]
