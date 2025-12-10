"""
LLM Registry
============

Comprehensive registry of LLM models with capabilities, pricing, and routing metadata.

Features:
- 18 model definitions across 6 providers
- Capability tagging for intelligent routing
- Token limits and pricing information
- Performance benchmarks

References:
- OpenAI: https://platform.openai.com/docs/models
- Anthropic: https://docs.anthropic.com/claude/docs/models-overview
- Google: https://ai.google.dev/models/gemini
- Mistral: https://docs.mistral.ai/getting-started/models/
- Cohere: https://docs.cohere.com/docs/models
- Groq: https://console.groq.com/docs/models
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class ModelProvider(str, Enum):
    """LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MISTRAL = "mistral"
    COHERE = "cohere"
    GROQ = "groq"


class ModelTier(str, Enum):
    """Model performance tiers"""
    FLAGSHIP = "flagship"      # Best quality, highest cost
    STANDARD = "standard"      # Good balance
    EFFICIENT = "efficient"    # Fast and cheap
    SPECIALIZED = "specialized"  # Task-specific


class ModelCapability(str, Enum):
    """Model capabilities"""
    # Core capabilities
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    COMPLETION = "completion"
    
    # Advanced capabilities
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    REASONING = "reasoning"
    MATH = "math"
    
    # Multimodal
    VISION = "vision"
    IMAGE_UNDERSTANDING = "image_understanding"
    DOCUMENT_ANALYSIS = "document_analysis"
    
    # Specialized
    FUNCTION_CALLING = "function_calling"
    TOOL_USE = "tool_use"
    JSON_MODE = "json_mode"
    STRUCTURED_OUTPUT = "structured_output"
    
    # Performance
    LONG_CONTEXT = "long_context"
    FAST_INFERENCE = "fast_inference"
    LOW_LATENCY = "low_latency"
    
    # Safety
    SAFETY_FILTERS = "safety_filters"
    CONTENT_MODERATION = "content_moderation"


# =============================================================================
# Models
# =============================================================================

class ModelDefinition(BaseModel):
    """LLM model definition"""
    id: str                           # Model identifier
    name: str                         # Display name
    provider: ModelProvider
    tier: ModelTier
    
    # Token limits
    context_window: int               # Max input tokens
    max_output_tokens: int            # Max output tokens
    
    # Capabilities
    capabilities: Set[ModelCapability] = set()
    
    # Pricing (per 1M tokens, USD)
    input_price: float = 0.0
    output_price: float = 0.0
    
    # Performance
    tokens_per_second: Optional[float] = None  # Approximate TPS
    latency_ms: Optional[float] = None         # First token latency
    
    # Metadata
    release_date: Optional[str] = None
    deprecated: bool = False
    description: str = ""
    
    # Routing hints
    best_for: List[str] = []          # Task types this excels at
    avoid_for: List[str] = []         # Task types to avoid
    
    class Config:
        use_enum_values = True


class ProviderConfig(BaseModel):
    """Provider configuration"""
    provider: ModelProvider
    api_key_env: str                  # Environment variable for API key
    base_url: Optional[str] = None    # Custom base URL
    default_model: str                # Default model ID
    rate_limit_rpm: int = 60          # Requests per minute
    rate_limit_tpm: int = 100000      # Tokens per minute


# =============================================================================
# Model Definitions
# =============================================================================

# OpenAI Models
GPT4O = ModelDefinition(
    id="gpt-4o",
    name="GPT-4o",
    provider=ModelProvider.OPENAI,
    tier=ModelTier.FLAGSHIP,
    context_window=128000,
    max_output_tokens=16384,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.REASONING,
        ModelCapability.VISION,
        ModelCapability.FUNCTION_CALLING,
        ModelCapability.JSON_MODE,
        ModelCapability.LONG_CONTEXT,
    },
    input_price=2.50,
    output_price=10.00,
    tokens_per_second=80,
    latency_ms=500,
    release_date="2024-05-13",
    description="Most capable GPT-4 model with vision",
    best_for=["complex_reasoning", "multimodal", "code", "analysis"],
)

GPT4O_MINI = ModelDefinition(
    id="gpt-4o-mini",
    name="GPT-4o Mini",
    provider=ModelProvider.OPENAI,
    tier=ModelTier.EFFICIENT,
    context_window=128000,
    max_output_tokens=16384,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.VISION,
        ModelCapability.FUNCTION_CALLING,
        ModelCapability.JSON_MODE,
        ModelCapability.FAST_INFERENCE,
    },
    input_price=0.15,
    output_price=0.60,
    tokens_per_second=150,
    latency_ms=200,
    release_date="2024-07-18",
    description="Fast and affordable GPT-4 class model",
    best_for=["simple_tasks", "high_volume", "quick_responses"],
)

O1_PREVIEW = ModelDefinition(
    id="o1-preview",
    name="o1-preview",
    provider=ModelProvider.OPENAI,
    tier=ModelTier.FLAGSHIP,
    context_window=128000,
    max_output_tokens=32768,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.REASONING,
        ModelCapability.MATH,
        ModelCapability.CODE_GENERATION,
        ModelCapability.CODE_ANALYSIS,
    },
    input_price=15.00,
    output_price=60.00,
    tokens_per_second=30,
    latency_ms=2000,
    release_date="2024-09-12",
    description="Advanced reasoning model for complex tasks",
    best_for=["complex_reasoning", "math", "science", "code_review"],
    avoid_for=["simple_chat", "high_volume"],
)

# Anthropic Models
CLAUDE_35_SONNET = ModelDefinition(
    id="claude-3-5-sonnet-20241022",
    name="Claude 3.5 Sonnet",
    provider=ModelProvider.ANTHROPIC,
    tier=ModelTier.FLAGSHIP,
    context_window=200000,
    max_output_tokens=8192,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.CODE_ANALYSIS,
        ModelCapability.REASONING,
        ModelCapability.VISION,
        ModelCapability.TOOL_USE,
        ModelCapability.LONG_CONTEXT,
        ModelCapability.STRUCTURED_OUTPUT,
    },
    input_price=3.00,
    output_price=15.00,
    tokens_per_second=100,
    latency_ms=400,
    release_date="2024-10-22",
    description="Most intelligent Claude model, excellent for coding",
    best_for=["coding", "analysis", "writing", "reasoning"],
)

CLAUDE_3_OPUS = ModelDefinition(
    id="claude-3-opus-20240229",
    name="Claude 3 Opus",
    provider=ModelProvider.ANTHROPIC,
    tier=ModelTier.FLAGSHIP,
    context_window=200000,
    max_output_tokens=4096,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.REASONING,
        ModelCapability.VISION,
        ModelCapability.TOOL_USE,
        ModelCapability.LONG_CONTEXT,
    },
    input_price=15.00,
    output_price=75.00,
    tokens_per_second=50,
    latency_ms=800,
    release_date="2024-02-29",
    description="Most powerful Claude for complex tasks",
    best_for=["complex_analysis", "research", "nuanced_writing"],
    avoid_for=["simple_tasks", "high_volume"],
)

CLAUDE_3_HAIKU = ModelDefinition(
    id="claude-3-haiku-20240307",
    name="Claude 3 Haiku",
    provider=ModelProvider.ANTHROPIC,
    tier=ModelTier.EFFICIENT,
    context_window=200000,
    max_output_tokens=4096,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.VISION,
        ModelCapability.TOOL_USE,
        ModelCapability.FAST_INFERENCE,
        ModelCapability.LOW_LATENCY,
    },
    input_price=0.25,
    output_price=1.25,
    tokens_per_second=200,
    latency_ms=150,
    release_date="2024-03-07",
    description="Fast and efficient Claude model",
    best_for=["quick_tasks", "high_volume", "simple_chat"],
)

# Google Models
GEMINI_15_PRO = ModelDefinition(
    id="gemini-1.5-pro",
    name="Gemini 1.5 Pro",
    provider=ModelProvider.GOOGLE,
    tier=ModelTier.FLAGSHIP,
    context_window=2000000,  # 2M tokens!
    max_output_tokens=8192,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.REASONING,
        ModelCapability.VISION,
        ModelCapability.DOCUMENT_ANALYSIS,
        ModelCapability.LONG_CONTEXT,
        ModelCapability.FUNCTION_CALLING,
    },
    input_price=1.25,
    output_price=5.00,
    tokens_per_second=70,
    latency_ms=600,
    release_date="2024-02-15",
    description="Google's flagship with 2M context window",
    best_for=["long_documents", "multimodal", "research"],
)

GEMINI_15_FLASH = ModelDefinition(
    id="gemini-1.5-flash",
    name="Gemini 1.5 Flash",
    provider=ModelProvider.GOOGLE,
    tier=ModelTier.EFFICIENT,
    context_window=1000000,
    max_output_tokens=8192,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.VISION,
        ModelCapability.FAST_INFERENCE,
        ModelCapability.FUNCTION_CALLING,
    },
    input_price=0.075,
    output_price=0.30,
    tokens_per_second=200,
    latency_ms=200,
    release_date="2024-05-14",
    description="Fast Gemini with 1M context",
    best_for=["quick_tasks", "long_context_fast", "high_volume"],
)

GEMINI_20_FLASH = ModelDefinition(
    id="gemini-2.0-flash-exp",
    name="Gemini 2.0 Flash",
    provider=ModelProvider.GOOGLE,
    tier=ModelTier.STANDARD,
    context_window=1000000,
    max_output_tokens=8192,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.REASONING,
        ModelCapability.VISION,
        ModelCapability.FUNCTION_CALLING,
        ModelCapability.TOOL_USE,
    },
    input_price=0.10,
    output_price=0.40,
    tokens_per_second=180,
    latency_ms=250,
    release_date="2024-12-11",
    description="Next-gen Gemini with improved reasoning",
    best_for=["balanced_tasks", "tool_use", "multimodal"],
)

# Mistral Models
MISTRAL_LARGE = ModelDefinition(
    id="mistral-large-latest",
    name="Mistral Large",
    provider=ModelProvider.MISTRAL,
    tier=ModelTier.FLAGSHIP,
    context_window=128000,
    max_output_tokens=8192,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.REASONING,
        ModelCapability.FUNCTION_CALLING,
        ModelCapability.JSON_MODE,
    },
    input_price=2.00,
    output_price=6.00,
    tokens_per_second=90,
    latency_ms=400,
    release_date="2024-02-26",
    description="Mistral's most capable model",
    best_for=["european_languages", "reasoning", "code"],
)

MISTRAL_MEDIUM = ModelDefinition(
    id="mistral-medium-latest",
    name="Mistral Medium",
    provider=ModelProvider.MISTRAL,
    tier=ModelTier.STANDARD,
    context_window=32000,
    max_output_tokens=8192,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.FUNCTION_CALLING,
    },
    input_price=2.70,
    output_price=8.10,
    tokens_per_second=100,
    latency_ms=350,
    description="Balanced Mistral model",
    best_for=["general_tasks", "multilingual"],
)

MISTRAL_SMALL = ModelDefinition(
    id="mistral-small-latest",
    name="Mistral Small",
    provider=ModelProvider.MISTRAL,
    tier=ModelTier.EFFICIENT,
    context_window=32000,
    max_output_tokens=8192,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.FAST_INFERENCE,
        ModelCapability.FUNCTION_CALLING,
    },
    input_price=0.20,
    output_price=0.60,
    tokens_per_second=150,
    latency_ms=200,
    description="Fast and efficient Mistral",
    best_for=["simple_tasks", "high_volume"],
)

CODESTRAL = ModelDefinition(
    id="codestral-latest",
    name="Codestral",
    provider=ModelProvider.MISTRAL,
    tier=ModelTier.SPECIALIZED,
    context_window=32000,
    max_output_tokens=8192,
    capabilities={
        ModelCapability.CODE_GENERATION,
        ModelCapability.CODE_ANALYSIS,
        ModelCapability.COMPLETION,
        ModelCapability.FAST_INFERENCE,
    },
    input_price=0.20,
    output_price=0.60,
    tokens_per_second=200,
    latency_ms=150,
    description="Specialized for code generation",
    best_for=["code_generation", "code_completion", "refactoring"],
    avoid_for=["general_chat", "creative_writing"],
)

# Cohere Models
COMMAND_R_PLUS = ModelDefinition(
    id="command-r-plus",
    name="Command R+",
    provider=ModelProvider.COHERE,
    tier=ModelTier.FLAGSHIP,
    context_window=128000,
    max_output_tokens=4096,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.REASONING,
        ModelCapability.TOOL_USE,
        ModelCapability.LONG_CONTEXT,
    },
    input_price=2.50,
    output_price=10.00,
    tokens_per_second=80,
    latency_ms=500,
    description="Cohere's flagship RAG-optimized model",
    best_for=["rag", "enterprise", "multilingual"],
)

COMMAND_R = ModelDefinition(
    id="command-r",
    name="Command R",
    provider=ModelProvider.COHERE,
    tier=ModelTier.STANDARD,
    context_window=128000,
    max_output_tokens=4096,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.TOOL_USE,
        ModelCapability.LONG_CONTEXT,
    },
    input_price=0.15,
    output_price=0.60,
    tokens_per_second=120,
    latency_ms=300,
    description="Efficient RAG model",
    best_for=["rag", "search", "retrieval"],
)

# Groq Models (Fast inference)
LLAMA_31_70B = ModelDefinition(
    id="llama-3.1-70b-versatile",
    name="Llama 3.1 70B (Groq)",
    provider=ModelProvider.GROQ,
    tier=ModelTier.STANDARD,
    context_window=131072,
    max_output_tokens=8192,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.REASONING,
        ModelCapability.FAST_INFERENCE,
        ModelCapability.LOW_LATENCY,
        ModelCapability.TOOL_USE,
    },
    input_price=0.59,
    output_price=0.79,
    tokens_per_second=300,  # Groq is FAST
    latency_ms=100,
    description="Llama 3.1 70B on Groq's fast inference",
    best_for=["fast_responses", "high_volume", "real_time"],
)

LLAMA_31_8B = ModelDefinition(
    id="llama-3.1-8b-instant",
    name="Llama 3.1 8B (Groq)",
    provider=ModelProvider.GROQ,
    tier=ModelTier.EFFICIENT,
    context_window=131072,
    max_output_tokens=8192,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.FAST_INFERENCE,
        ModelCapability.LOW_LATENCY,
    },
    input_price=0.05,
    output_price=0.08,
    tokens_per_second=750,  # Extremely fast
    latency_ms=50,
    description="Ultra-fast small model on Groq",
    best_for=["instant_responses", "simple_tasks", "real_time_chat"],
)

MIXTRAL_8X7B = ModelDefinition(
    id="mixtral-8x7b-32768",
    name="Mixtral 8x7B (Groq)",
    provider=ModelProvider.GROQ,
    tier=ModelTier.EFFICIENT,
    context_window=32768,
    max_output_tokens=8192,
    capabilities={
        ModelCapability.TEXT_GENERATION,
        ModelCapability.CHAT,
        ModelCapability.CODE_GENERATION,
        ModelCapability.FAST_INFERENCE,
        ModelCapability.LOW_LATENCY,
    },
    input_price=0.24,
    output_price=0.24,
    tokens_per_second=500,
    latency_ms=75,
    description="Fast MoE model on Groq",
    best_for=["fast_inference", "balanced_quality_speed"],
)


# =============================================================================
# Registry
# =============================================================================

class LLMRegistry:
    """
    LLM Model Registry
    
    Manages model definitions and provides intelligent selection.
    
    Usage:
        registry = LLMRegistry()
        
        # Get model by ID
        model = registry.get_model("gpt-4o")
        
        # Find models by capability
        vision_models = registry.find_by_capability(ModelCapability.VISION)
        
        # Get cheapest model for task
        cheap_model = registry.get_cheapest(capabilities={ModelCapability.CODE_GENERATION})
        
        # Get fastest model
        fast_model = registry.get_fastest(min_context=50000)
    """
    
    # All registered models
    _models: Dict[str, ModelDefinition] = {
        # OpenAI
        "gpt-4o": GPT4O,
        "gpt-4o-mini": GPT4O_MINI,
        "o1-preview": O1_PREVIEW,
        
        # Anthropic
        "claude-3-5-sonnet-20241022": CLAUDE_35_SONNET,
        "claude-3-opus-20240229": CLAUDE_3_OPUS,
        "claude-3-haiku-20240307": CLAUDE_3_HAIKU,
        
        # Google
        "gemini-1.5-pro": GEMINI_15_PRO,
        "gemini-1.5-flash": GEMINI_15_FLASH,
        "gemini-2.0-flash-exp": GEMINI_20_FLASH,
        
        # Mistral
        "mistral-large-latest": MISTRAL_LARGE,
        "mistral-medium-latest": MISTRAL_MEDIUM,
        "mistral-small-latest": MISTRAL_SMALL,
        "codestral-latest": CODESTRAL,
        
        # Cohere
        "command-r-plus": COMMAND_R_PLUS,
        "command-r": COMMAND_R,
        
        # Groq
        "llama-3.1-70b-versatile": LLAMA_31_70B,
        "llama-3.1-8b-instant": LLAMA_31_8B,
        "mixtral-8x7b-32768": MIXTRAL_8X7B,
    }
    
    # Provider configurations
    _providers: Dict[ModelProvider, ProviderConfig] = {
        ModelProvider.OPENAI: ProviderConfig(
            provider=ModelProvider.OPENAI,
            api_key_env="OPENAI_API_KEY",
            base_url="https://api.openai.com/v1",
            default_model="gpt-4o-mini",
            rate_limit_rpm=500,
            rate_limit_tpm=200000,
        ),
        ModelProvider.ANTHROPIC: ProviderConfig(
            provider=ModelProvider.ANTHROPIC,
            api_key_env="ANTHROPIC_API_KEY",
            base_url="https://api.anthropic.com",
            default_model="claude-3-5-sonnet-20241022",
            rate_limit_rpm=60,
            rate_limit_tpm=100000,
        ),
        ModelProvider.GOOGLE: ProviderConfig(
            provider=ModelProvider.GOOGLE,
            api_key_env="GOOGLE_API_KEY",
            default_model="gemini-1.5-flash",
            rate_limit_rpm=60,
            rate_limit_tpm=100000,
        ),
        ModelProvider.MISTRAL: ProviderConfig(
            provider=ModelProvider.MISTRAL,
            api_key_env="MISTRAL_API_KEY",
            base_url="https://api.mistral.ai/v1",
            default_model="mistral-small-latest",
            rate_limit_rpm=60,
            rate_limit_tpm=100000,
        ),
        ModelProvider.COHERE: ProviderConfig(
            provider=ModelProvider.COHERE,
            api_key_env="COHERE_API_KEY",
            base_url="https://api.cohere.ai/v1",
            default_model="command-r",
            rate_limit_rpm=60,
            rate_limit_tpm=100000,
        ),
        ModelProvider.GROQ: ProviderConfig(
            provider=ModelProvider.GROQ,
            api_key_env="GROQ_API_KEY",
            base_url="https://api.groq.com/openai/v1",
            default_model="llama-3.1-70b-versatile",
            rate_limit_rpm=30,
            rate_limit_tpm=50000,
        ),
    }
    
    def __init__(self):
        self.models = self._models.copy()
        self.providers = self._providers.copy()
    
    # -------------------------------------------------------------------------
    # Basic Operations
    # -------------------------------------------------------------------------
    
    def get_model(self, model_id: str) -> Optional[ModelDefinition]:
        """Get model by ID"""
        return self.models.get(model_id)
    
    def get_provider(self, provider: ModelProvider) -> Optional[ProviderConfig]:
        """Get provider configuration"""
        return self.providers.get(provider)
    
    def list_models(self) -> List[ModelDefinition]:
        """List all models"""
        return list(self.models.values())
    
    def list_providers(self) -> List[ModelProvider]:
        """List available providers"""
        return list(self.providers.keys())
    
    # -------------------------------------------------------------------------
    # Filtering
    # -------------------------------------------------------------------------
    
    def find_by_provider(self, provider: ModelProvider) -> List[ModelDefinition]:
        """Find models by provider"""
        return [m for m in self.models.values() if m.provider == provider]
    
    def find_by_tier(self, tier: ModelTier) -> List[ModelDefinition]:
        """Find models by tier"""
        return [m for m in self.models.values() if m.tier == tier]
    
    def find_by_capability(
        self,
        capability: ModelCapability,
    ) -> List[ModelDefinition]:
        """Find models with specific capability"""
        return [
            m for m in self.models.values()
            if capability in m.capabilities
        ]
    
    def find_by_capabilities(
        self,
        capabilities: Set[ModelCapability],
        require_all: bool = True,
    ) -> List[ModelDefinition]:
        """Find models with multiple capabilities"""
        results = []
        for model in self.models.values():
            if require_all:
                if capabilities.issubset(model.capabilities):
                    results.append(model)
            else:
                if capabilities.intersection(model.capabilities):
                    results.append(model)
        return results
    
    def find_by_context(self, min_context: int) -> List[ModelDefinition]:
        """Find models with minimum context window"""
        return [
            m for m in self.models.values()
            if m.context_window >= min_context
        ]
    
    # -------------------------------------------------------------------------
    # Optimization Queries
    # -------------------------------------------------------------------------
    
    def get_cheapest(
        self,
        capabilities: Set[ModelCapability] = None,
        min_context: int = None,
    ) -> Optional[ModelDefinition]:
        """Get cheapest model matching requirements"""
        candidates = list(self.models.values())
        
        if capabilities:
            candidates = [
                m for m in candidates
                if capabilities.issubset(m.capabilities)
            ]
        
        if min_context:
            candidates = [
                m for m in candidates
                if m.context_window >= min_context
            ]
        
        if not candidates:
            return None
        
        # Sort by total cost (input + output)
        return min(candidates, key=lambda m: m.input_price + m.output_price)
    
    def get_fastest(
        self,
        capabilities: Set[ModelCapability] = None,
        min_context: int = None,
    ) -> Optional[ModelDefinition]:
        """Get fastest model matching requirements"""
        candidates = list(self.models.values())
        
        if capabilities:
            candidates = [
                m for m in candidates
                if capabilities.issubset(m.capabilities)
            ]
        
        if min_context:
            candidates = [
                m for m in candidates
                if m.context_window >= min_context
            ]
        
        # Filter to models with TPS data
        candidates = [m for m in candidates if m.tokens_per_second]
        
        if not candidates:
            return None
        
        return max(candidates, key=lambda m: m.tokens_per_second or 0)
    
    def get_best_quality(
        self,
        capabilities: Set[ModelCapability] = None,
        min_context: int = None,
    ) -> Optional[ModelDefinition]:
        """Get highest quality model matching requirements"""
        candidates = list(self.models.values())
        
        if capabilities:
            candidates = [
                m for m in candidates
                if capabilities.issubset(m.capabilities)
            ]
        
        if min_context:
            candidates = [
                m for m in candidates
                if m.context_window >= min_context
            ]
        
        # Filter to flagship tier first
        flagship = [m for m in candidates if m.tier == ModelTier.FLAGSHIP]
        if flagship:
            candidates = flagship
        
        if not candidates:
            return None
        
        # Sort by price as proxy for quality
        return max(candidates, key=lambda m: m.input_price + m.output_price)
    
    def get_balanced(
        self,
        capabilities: Set[ModelCapability] = None,
        min_context: int = None,
    ) -> Optional[ModelDefinition]:
        """Get balanced model (good quality, reasonable cost)"""
        candidates = list(self.models.values())
        
        if capabilities:
            candidates = [
                m for m in candidates
                if capabilities.issubset(m.capabilities)
            ]
        
        if min_context:
            candidates = [
                m for m in candidates
                if m.context_window >= min_context
            ]
        
        # Prefer standard tier
        standard = [m for m in candidates if m.tier == ModelTier.STANDARD]
        if standard:
            candidates = standard
        
        if not candidates:
            return None
        
        # Return middle-priced option
        sorted_candidates = sorted(
            candidates,
            key=lambda m: m.input_price + m.output_price
        )
        return sorted_candidates[len(sorted_candidates) // 2]
    
    # -------------------------------------------------------------------------
    # Task-Based Selection
    # -------------------------------------------------------------------------
    
    def get_for_task(self, task_type: str) -> Optional[ModelDefinition]:
        """Get recommended model for task type"""
        task_mappings = {
            "code": "claude-3-5-sonnet-20241022",
            "coding": "claude-3-5-sonnet-20241022",
            "analysis": "gpt-4o",
            "reasoning": "o1-preview",
            "math": "o1-preview",
            "vision": "gpt-4o",
            "multimodal": "gemini-1.5-pro",
            "long_document": "gemini-1.5-pro",
            "fast": "llama-3.1-8b-instant",
            "real_time": "llama-3.1-8b-instant",
            "chat": "gpt-4o-mini",
            "simple": "gpt-4o-mini",
            "rag": "command-r-plus",
            "search": "command-r",
            "creative": "claude-3-5-sonnet-20241022",
            "writing": "claude-3-5-sonnet-20241022",
        }
        
        model_id = task_mappings.get(task_type.lower())
        if model_id:
            return self.get_model(model_id)
        
        # Default to balanced option
        return self.get_balanced()
    
    # -------------------------------------------------------------------------
    # Provider Availability
    # -------------------------------------------------------------------------
    
    def get_available_providers(self) -> List[ModelProvider]:
        """Get providers with API keys configured"""
        available = []
        for provider, config in self.providers.items():
            if os.getenv(config.api_key_env):
                available.append(provider)
        return available
    
    def get_available_models(self) -> List[ModelDefinition]:
        """Get models from providers with API keys"""
        available_providers = self.get_available_providers()
        return [
            m for m in self.models.values()
            if m.provider in available_providers
        ]
    
    def is_available(self, model_id: str) -> bool:
        """Check if model is available (provider has API key)"""
        model = self.get_model(model_id)
        if not model:
            return False
        
        config = self.get_provider(model.provider)
        if not config:
            return False
        
        return bool(os.getenv(config.api_key_env))
