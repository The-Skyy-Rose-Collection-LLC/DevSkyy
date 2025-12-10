"""
LLM Orchestrator
================

Intelligent model selection and routing based on task requirements.

Features:
- Task-based routing
- Cost optimization
- Speed optimization
- Quality optimization
- Fallback chains
- Load balancing
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field

from .llm_registry import (
    LLMRegistry,
    ModelDefinition,
    ModelCapability,
    ModelProvider,
    ModelTier,
)
from .llm_clients import (
    BaseLLMClient,
    OpenAIClient,
    AnthropicClient,
    GoogleClient,
    MistralClient,
    CohereClient,
    GroqClient,
    Message,
    MessageRole,
    CompletionResponse,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class TaskType(str, Enum):
    """Task types for routing"""
    # General
    CHAT = "chat"
    COMPLETION = "completion"
    
    # Specialized
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_EXPLANATION = "code_explanation"
    
    ANALYSIS = "analysis"
    REASONING = "reasoning"
    MATH = "math"
    
    CREATIVE_WRITING = "creative_writing"
    TECHNICAL_WRITING = "technical_writing"
    SUMMARIZATION = "summarization"
    
    TRANSLATION = "translation"
    
    # Multimodal
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENT_ANALYSIS = "document_analysis"
    
    # Agentic
    TOOL_USE = "tool_use"
    FUNCTION_CALLING = "function_calling"
    
    # Speed-critical
    REAL_TIME = "real_time"
    STREAMING = "streaming"


class RoutingStrategy(str, Enum):
    """Routing strategies"""
    QUALITY = "quality"        # Best quality, ignore cost
    BALANCED = "balanced"      # Balance quality and cost
    COST = "cost"             # Minimize cost
    SPEED = "speed"           # Minimize latency
    SPECIFIC = "specific"     # Use specific model


class Priority(str, Enum):
    """Request priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# Models
# =============================================================================

class RoutingRequest(BaseModel):
    """Request for model routing"""
    task_type: TaskType = TaskType.CHAT
    strategy: RoutingStrategy = RoutingStrategy.BALANCED
    priority: Priority = Priority.NORMAL
    
    # Requirements
    min_context: int = 0
    requires_vision: bool = False
    requires_tools: bool = False
    requires_json: bool = False
    
    # Preferences
    preferred_providers: List[ModelProvider] = []
    excluded_providers: List[ModelProvider] = []
    preferred_model: Optional[str] = None
    
    # Budget
    max_input_price: Optional[float] = None   # Per 1M tokens
    max_output_price: Optional[float] = None  # Per 1M tokens


class CompletionResult(BaseModel):
    """Orchestrator completion result"""
    response: CompletionResponse
    model_used: str
    provider_used: str
    routing_reason: str
    fallback_used: bool = False
    
    # Cost estimation
    estimated_cost_usd: float = 0.0
    
    # Performance
    total_latency_ms: float = 0


# =============================================================================
# Orchestrator
# =============================================================================

class LLMOrchestrator:
    """
    LLM Orchestrator
    
    Intelligently routes requests to optimal models based on requirements.
    
    Usage:
        orchestrator = LLMOrchestrator()
        
        # Simple completion
        result = await orchestrator.complete(
            prompt="Write a Python function to...",
            task_type=TaskType.CODE_GENERATION
        )
        
        # With specific requirements
        result = await orchestrator.complete(
            messages=[...],
            task_type=TaskType.ANALYSIS,
            strategy=RoutingStrategy.QUALITY,
            min_context=100000,
            requires_tools=True
        )
        
        # Streaming
        async for chunk in orchestrator.stream(
            prompt="Tell me a story...",
            task_type=TaskType.CREATIVE_WRITING
        ):
            print(chunk.content, end="")
    """
    
    def __init__(self):
        self.registry = LLMRegistry()
        self._clients: Dict[ModelProvider, BaseLLMClient] = {}
        
        # Task type to capability mapping
        self._task_capabilities: Dict[TaskType, Set[ModelCapability]] = {
            TaskType.CHAT: {ModelCapability.CHAT},
            TaskType.COMPLETION: {ModelCapability.TEXT_GENERATION},
            TaskType.CODE_GENERATION: {ModelCapability.CODE_GENERATION},
            TaskType.CODE_REVIEW: {ModelCapability.CODE_ANALYSIS},
            TaskType.CODE_EXPLANATION: {ModelCapability.CODE_ANALYSIS},
            TaskType.ANALYSIS: {ModelCapability.REASONING},
            TaskType.REASONING: {ModelCapability.REASONING},
            TaskType.MATH: {ModelCapability.MATH},
            TaskType.CREATIVE_WRITING: {ModelCapability.TEXT_GENERATION},
            TaskType.TECHNICAL_WRITING: {ModelCapability.TEXT_GENERATION},
            TaskType.SUMMARIZATION: {ModelCapability.TEXT_GENERATION},
            TaskType.TRANSLATION: {ModelCapability.TEXT_GENERATION},
            TaskType.IMAGE_ANALYSIS: {ModelCapability.VISION},
            TaskType.DOCUMENT_ANALYSIS: {ModelCapability.DOCUMENT_ANALYSIS},
            TaskType.TOOL_USE: {ModelCapability.TOOL_USE},
            TaskType.FUNCTION_CALLING: {ModelCapability.FUNCTION_CALLING},
            TaskType.REAL_TIME: {ModelCapability.FAST_INFERENCE},
            TaskType.STREAMING: {ModelCapability.TEXT_GENERATION},
        }
        
        # Task type to preferred models
        self._task_models: Dict[TaskType, List[str]] = {
            TaskType.CODE_GENERATION: [
                "claude-3-5-sonnet-20241022",
                "gpt-4o",
                "codestral-latest",
            ],
            TaskType.CODE_REVIEW: [
                "claude-3-5-sonnet-20241022",
                "gpt-4o",
            ],
            TaskType.REASONING: [
                "o1-preview",
                "claude-3-opus-20240229",
                "gpt-4o",
            ],
            TaskType.MATH: [
                "o1-preview",
                "claude-3-5-sonnet-20241022",
            ],
            TaskType.CREATIVE_WRITING: [
                "claude-3-5-sonnet-20241022",
                "gpt-4o",
            ],
            TaskType.IMAGE_ANALYSIS: [
                "gpt-4o",
                "gemini-1.5-pro",
                "claude-3-5-sonnet-20241022",
            ],
            TaskType.DOCUMENT_ANALYSIS: [
                "gemini-1.5-pro",  # 2M context
                "claude-3-5-sonnet-20241022",
            ],
            TaskType.REAL_TIME: [
                "llama-3.1-8b-instant",
                "llama-3.1-70b-versatile",
                "gpt-4o-mini",
            ],
            TaskType.TOOL_USE: [
                "claude-3-5-sonnet-20241022",
                "gpt-4o",
                "gemini-2.0-flash-exp",
            ],
        }
    
    def _get_client(self, provider: ModelProvider) -> BaseLLMClient:
        """Get or create client for provider"""
        if provider not in self._clients:
            client_map = {
                ModelProvider.OPENAI: OpenAIClient,
                ModelProvider.ANTHROPIC: AnthropicClient,
                ModelProvider.GOOGLE: GoogleClient,
                ModelProvider.MISTRAL: MistralClient,
                ModelProvider.COHERE: CohereClient,
                ModelProvider.GROQ: GroqClient,
            }
            
            client_class = client_map.get(provider)
            if client_class:
                self._clients[provider] = client_class()
        
        return self._clients.get(provider)
    
    async def close(self):
        """Close all clients"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
    
    # -------------------------------------------------------------------------
    # Model Selection
    # -------------------------------------------------------------------------
    
    def select_model(
        self,
        request: RoutingRequest,
    ) -> tuple[ModelDefinition, str]:
        """
        Select optimal model for request
        
        Returns:
            (ModelDefinition, routing_reason)
        """
        # If specific model requested
        if request.preferred_model:
            model = self.registry.get_model(request.preferred_model)
            if model and self.registry.is_available(request.preferred_model):
                return model, f"User requested model: {request.preferred_model}"
        
        # Build required capabilities
        capabilities: Set[ModelCapability] = set()
        
        # Add task capabilities
        task_caps = self._task_capabilities.get(request.task_type, set())
        capabilities.update(task_caps)
        
        # Add explicit requirements
        if request.requires_vision:
            capabilities.add(ModelCapability.VISION)
        if request.requires_tools:
            capabilities.add(ModelCapability.TOOL_USE)
        if request.requires_json:
            capabilities.add(ModelCapability.JSON_MODE)
        
        # Get available models
        available = self.registry.get_available_models()
        
        # Filter by providers
        if request.preferred_providers:
            available = [
                m for m in available
                if m.provider in request.preferred_providers
            ]
        
        if request.excluded_providers:
            available = [
                m for m in available
                if m.provider not in request.excluded_providers
            ]
        
        # Filter by capabilities
        if capabilities:
            available = [
                m for m in available
                if capabilities.issubset(m.capabilities)
            ]
        
        # Filter by context
        if request.min_context:
            available = [
                m for m in available
                if m.context_window >= request.min_context
            ]
        
        # Filter by price
        if request.max_input_price:
            available = [
                m for m in available
                if m.input_price <= request.max_input_price
            ]
        
        if request.max_output_price:
            available = [
                m for m in available
                if m.output_price <= request.max_output_price
            ]
        
        if not available:
            raise ValueError("No models available matching requirements")
        
        # Apply routing strategy
        if request.strategy == RoutingStrategy.QUALITY:
            # Prefer flagship models
            flagship = [m for m in available if m.tier == ModelTier.FLAGSHIP]
            if flagship:
                available = flagship
            # Sort by price (proxy for quality)
            model = max(available, key=lambda m: m.input_price + m.output_price)
            reason = f"Quality strategy: selected highest-tier model"
            
        elif request.strategy == RoutingStrategy.COST:
            model = min(available, key=lambda m: m.input_price + m.output_price)
            reason = f"Cost strategy: selected cheapest model"
            
        elif request.strategy == RoutingStrategy.SPEED:
            # Prefer fast inference models
            fast = [
                m for m in available
                if ModelCapability.FAST_INFERENCE in m.capabilities
            ]
            if fast:
                available = fast
            model = max(available, key=lambda m: m.tokens_per_second or 0)
            reason = f"Speed strategy: selected fastest model"
            
        else:  # BALANCED
            # Check task-specific recommendations
            preferred = self._task_models.get(request.task_type, [])
            for model_id in preferred:
                model = next((m for m in available if m.id == model_id), None)
                if model:
                    reason = f"Balanced strategy: task-optimized model for {request.task_type.value}"
                    return model, reason
            
            # Fall back to standard tier
            standard = [m for m in available if m.tier == ModelTier.STANDARD]
            if standard:
                model = standard[0]
            else:
                # Pick middle-priced option
                sorted_models = sorted(
                    available,
                    key=lambda m: m.input_price + m.output_price
                )
                model = sorted_models[len(sorted_models) // 2]
            
            reason = f"Balanced strategy: cost-quality optimized"
        
        return model, reason
    
    # -------------------------------------------------------------------------
    # Completion
    # -------------------------------------------------------------------------
    
    async def complete(
        self,
        prompt: str = None,
        messages: List[Message] = None,
        task_type: TaskType = TaskType.CHAT,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        tools: List[Dict] = None,
        system: str = None,
        # Routing options
        min_context: int = 0,
        requires_vision: bool = False,
        requires_tools: bool = False,
        requires_json: bool = False,
        preferred_providers: List[ModelProvider] = None,
        excluded_providers: List[ModelProvider] = None,
        preferred_model: str = None,
        max_input_price: float = None,
        max_output_price: float = None,
        # Fallback
        enable_fallback: bool = True,
        **kwargs,
    ) -> CompletionResult:
        """
        Generate completion with intelligent routing
        
        Args:
            prompt: Simple prompt string (converted to user message)
            messages: List of Message objects
            task_type: Type of task for routing
            strategy: Routing strategy
            temperature: Generation temperature
            max_tokens: Max output tokens
            tools: Tool definitions for function calling
            system: System message
            min_context: Minimum context window required
            requires_vision: Task requires vision capability
            requires_tools: Task requires tool use
            requires_json: Task requires JSON output
            preferred_providers: Prefer these providers
            excluded_providers: Exclude these providers
            preferred_model: Use specific model
            max_input_price: Max input price per 1M tokens
            max_output_price: Max output price per 1M tokens
            enable_fallback: Enable fallback to other models
            
        Returns:
            CompletionResult with response and metadata
        """
        start_time = datetime.now()
        
        # Build messages
        if messages is None:
            messages = []
            if system:
                messages.append(Message(role=MessageRole.SYSTEM, content=system))
            if prompt:
                messages.append(Message(role=MessageRole.USER, content=prompt))
        
        if not messages:
            raise ValueError("Must provide prompt or messages")
        
        # Auto-detect requirements
        if tools:
            requires_tools = True
        
        # Build routing request
        request = RoutingRequest(
            task_type=task_type,
            strategy=strategy,
            min_context=min_context,
            requires_vision=requires_vision,
            requires_tools=requires_tools,
            requires_json=requires_json,
            preferred_providers=preferred_providers or [],
            excluded_providers=excluded_providers or [],
            preferred_model=preferred_model,
            max_input_price=max_input_price,
            max_output_price=max_output_price,
        )
        
        # Select model
        model, routing_reason = self.select_model(request)
        
        # Get client
        client = self._get_client(model.provider)
        if not client:
            raise ValueError(f"No client available for provider: {model.provider}")
        
        # Attempt completion
        fallback_used = False
        
        try:
            response = await client.complete(
                messages=messages,
                model=model.id,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                **kwargs,
            )
            
        except Exception as e:
            logger.error(f"Completion failed with {model.id}: {e}")
            
            if not enable_fallback:
                raise
            
            # Try fallback
            fallback_model = self._get_fallback_model(model, request)
            if fallback_model:
                logger.info(f"Falling back to {fallback_model.id}")
                
                fallback_client = self._get_client(fallback_model.provider)
                response = await fallback_client.complete(
                    messages=messages,
                    model=fallback_model.id,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    **kwargs,
                )
                
                model = fallback_model
                fallback_used = True
                routing_reason += f" (fallback from original)"
            else:
                raise
        
        # Calculate cost
        estimated_cost = self._estimate_cost(
            model,
            response.input_tokens,
            response.output_tokens,
        )
        
        total_latency = (datetime.now() - start_time).total_seconds() * 1000
        
        return CompletionResult(
            response=response,
            model_used=model.id,
            provider_used=model.provider.value,
            routing_reason=routing_reason,
            fallback_used=fallback_used,
            estimated_cost_usd=estimated_cost,
            total_latency_ms=total_latency,
        )
    
    def _get_fallback_model(
        self,
        failed_model: ModelDefinition,
        request: RoutingRequest,
    ) -> Optional[ModelDefinition]:
        """Get fallback model"""
        # Try same provider, different model
        same_provider = [
            m for m in self.registry.find_by_provider(failed_model.provider)
            if m.id != failed_model.id and self.registry.is_available(m.id)
        ]
        
        if same_provider:
            return same_provider[0]
        
        # Try different provider
        other_providers = [
            p for p in ModelProvider
            if p != failed_model.provider
        ]
        
        for provider in other_providers:
            models = [
                m for m in self.registry.find_by_provider(provider)
                if self.registry.is_available(m.id)
            ]
            if models:
                return models[0]
        
        return None
    
    def _estimate_cost(
        self,
        model: ModelDefinition,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost in USD"""
        input_cost = (input_tokens / 1_000_000) * model.input_price
        output_cost = (output_tokens / 1_000_000) * model.output_price
        return input_cost + output_cost
    
    # -------------------------------------------------------------------------
    # Streaming
    # -------------------------------------------------------------------------
    
    async def stream(
        self,
        prompt: str = None,
        messages: List[Message] = None,
        task_type: TaskType = TaskType.CHAT,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system: str = None,
        **kwargs,
    ):
        """
        Stream completion with intelligent routing
        
        Yields:
            StreamChunk objects
        """
        # Build messages
        if messages is None:
            messages = []
            if system:
                messages.append(Message(role=MessageRole.SYSTEM, content=system))
            if prompt:
                messages.append(Message(role=MessageRole.USER, content=prompt))
        
        # Build routing request
        request = RoutingRequest(
            task_type=task_type,
            strategy=strategy,
        )
        
        # Select model
        model, _ = self.select_model(request)
        
        # Get client
        client = self._get_client(model.provider)
        
        # Stream
        async for chunk in client.stream(
            messages=messages,
            model=model.id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield chunk
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available models with details"""
        models = self.registry.get_available_models()
        return [
            {
                "id": m.id,
                "name": m.name,
                "provider": m.provider.value,
                "tier": m.tier.value,
                "context_window": m.context_window,
                "input_price": m.input_price,
                "output_price": m.output_price,
                "capabilities": [c.value for c in m.capabilities],
            }
            for m in models
        ]
    
    def get_recommended_model(
        self,
        task_type: TaskType,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
    ) -> Dict[str, Any]:
        """Get recommended model for task"""
        request = RoutingRequest(
            task_type=task_type,
            strategy=strategy,
        )
        
        model, reason = self.select_model(request)
        
        return {
            "model_id": model.id,
            "model_name": model.name,
            "provider": model.provider.value,
            "reason": reason,
        }
    
    def estimate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Dict[str, float]:
        """Estimate cost for specific model"""
        model = self.registry.get_model(model_id)
        if not model:
            raise ValueError(f"Unknown model: {model_id}")
        
        input_cost = (input_tokens / 1_000_000) * model.input_price
        output_cost = (output_tokens / 1_000_000) * model.output_price
        
        return {
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": input_cost + output_cost,
            "input_price_per_1m": model.input_price,
            "output_price_per_1m": model.output_price,
        }
