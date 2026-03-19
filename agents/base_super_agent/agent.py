"""
Enhanced Base Super Agent
==========================

The main EnhancedSuperAgent class that integrates all modules:
- 17 Prompt Engineering Techniques (auto-selection)
- ML Capabilities Module
- Self-Learning Module
- LLM Round Table Interface
- LLM Router for intelligent provider selection
- Enterprise Intelligence Modules

All 6 SuperAgents inherit from this class.
"""

import logging
import time
from abc import abstractmethod
from typing import Any

import structlog

# Import existing components
from adk.base import ADKProvider, AgentConfig, AgentResult, AgentStatus, BaseDevSkyyAgent
from core.structured_logging import bind_contextvars, unbind_contextvars
from orchestration.prompt_engineering import PromptTechnique

# Import LLM Router for intelligent provider selection
try:
    from llm.base import Message, ModelProvider
    from llm.router import LLMRouter, RoutingStrategy

    LLM_ROUTER_AVAILABLE = True
except ImportError:
    LLMRouter = None
    RoutingStrategy = None
    ModelProvider = None
    Message = None
    LLM_ROUTER_AVAILABLE = False

from .learning_module import SelfLearningModule
from .ml_module import MLCapabilitiesModule
from .prompt_module import PromptEngineeringModule, get_task_analyzer
from .round_table_module import LLMRoundTableInterface
from .types import (
    AGENT_PROVIDER_PREFERENCES,
    HIGH_STAKES_AGENT_TYPES,
    HIGH_STAKES_TASK_TYPES,
    ROUND_TABLE_QUALITY_THRESHOLD,
    TASK_PROVIDER_PREFERENCES,
    LLMProvider,
    PromptTechniqueResult,
    SuperAgentType,
    TaskCategory,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Enhanced Base Super Agent
# =============================================================================


class EnhancedSuperAgent(BaseDevSkyyAgent):  # Implements ISuperAgent via duck typing
    """
    Enhanced Base Super Agent with all modules integrated.

    Features:
    - 17 Prompt Engineering Techniques
    - ML Capabilities
    - Self-Learning
    - LLM Round Table Integration

    All 6 SuperAgents inherit from this class.
    """

    agent_type: SuperAgentType = None
    sub_capabilities: list[str] = []

    def __init__(
        self,
        config: AgentConfig,
        *,
        rag_manager: Any | None = None,
        ml_pipeline: Any | None = None,
        llm_client: Any | None = None,
        cache: Any | None = None,
    ):
        """
        Initialize Enhanced Super Agent with optional dependency injection.

        Args:
            config: Agent configuration
            rag_manager: Optional RAG manager (IRAGManager)
            ml_pipeline: Optional ML pipeline (IMLPipeline)
            llm_client: Optional LLM client
            cache: Optional cache provider (ICacheProvider)
        """
        super().__init__(config)

        # Store injected dependencies or fetch from registry
        self._rag_manager = rag_manager
        self._ml_pipeline = ml_pipeline
        self._llm_client = llm_client
        self._cache = cache

        # Initialize modules
        self.prompt_module = PromptEngineeringModule()
        self.ml_module: MLCapabilitiesModule | None = None
        self.learning_module: SelfLearningModule | None = None
        self.round_table: LLMRoundTableInterface | None = None

        # LLM Router for intelligent provider selection
        self._router: Any = None  # Type: LLMRouter | None
        self._router_available = LLM_ROUTER_AVAILABLE

        # Enterprise Intelligence Modules (NEW)
        self.enterprise_index: Any = None  # Type: EnterpriseIndex | None
        self.semantic_analyzer: Any = None  # Type: SemanticCodeAnalyzer | None
        self.verification_engine: Any = None  # Type: LLMVerificationEngine | None

        # State
        self._initialized = False
        self._execution_count = 0
        self._active_provider = ADKProvider.PYDANTIC
        self._current_model_provider: str | None = None  # Track routed provider

    async def initialize(self) -> None:
        """Initialize all modules"""
        logger.info(f"Initializing Enhanced Super Agent: {self.agent_type}")

        # Initialize ML module
        if self.agent_type:
            self.ml_module = MLCapabilitiesModule(self.agent_type)
            await self.ml_module.initialize()

            # Initialize learning module
            self.learning_module = SelfLearningModule(self.agent_type)

            # Initialize Round Table
            self.round_table = LLMRoundTableInterface()

        # Initialize LLM Router for intelligent provider selection
        if self._router_available and LLMRouter is not None and RoutingStrategy is not None:
            try:
                # Use COST strategy for low-temperature (deterministic) tasks
                # Use PRIORITY strategy for higher-temperature (creative) tasks
                strategy = (
                    RoutingStrategy.COST
                    if self.config.temperature < 0.5
                    else RoutingStrategy.PRIORITY
                )
                self._router = LLMRouter(strategy=strategy)
                logger.info(
                    f"LLM Router initialized for {self.agent_type} with {strategy.value} strategy"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize LLM Router: {e}")
                self._router = None

        # Initialize Enterprise Intelligence Modules (NEW)
        await self._init_enterprise_intelligence()

        # Initialize backend
        try:
            await self._init_pydantic_backend()
        except ImportError:
            try:
                await self._init_langchain_backend()
            except ImportError:
                logger.warning("No ADK backend available, using fallback")

        self._initialized = True
        logger.info(f"Enhanced Super Agent {self.agent_type} initialized")

    async def _init_pydantic_backend(self) -> None:
        """Initialize with PydanticAI backend"""
        from pydantic_ai import Agent

        self._backend_agent = Agent(
            self._get_model_string(),
            system_prompt=self.config.system_prompt,
        )
        self._active_provider = ADKProvider.PYDANTIC

    async def _init_langchain_backend(self) -> None:
        """Initialize with LangChain/LangGraph backend"""
        from langchain_openai import ChatOpenAI

        self._backend_llm = ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
        )
        self._active_provider = ADKProvider.LANGGRAPH

    def _get_model_string(self) -> str:
        """Get model string for current provider"""
        model = self.config.model.lower()
        if "gpt" in model:
            return f"openai:{self.config.model}"
        elif "claude" in model:
            return f"anthropic:{self.config.model}"
        elif "gemini" in model:
            return f"google-gla:{self.config.model}"
        return f"openai:{self.config.model}"

    def _get_preferred_provider(self, task_category: TaskCategory | None = None) -> str:
        """
        Get the preferred LLM provider based on agent type and task category.

        Uses AGENT_PROVIDER_PREFERENCES and TASK_PROVIDER_PREFERENCES to determine
        the optimal provider for each agent/task combination.

        Args:
            task_category: Optional task category for task-specific routing

        Returns:
            Provider name (e.g., 'anthropic', 'openai', 'google')
        """
        # Get agent-type preferences
        agent_key = self.agent_type.value if self.agent_type else "commerce"
        agent_prefs = AGENT_PROVIDER_PREFERENCES.get(agent_key, ["openai", "anthropic"])

        # Get task-specific preferences if task category is provided
        if task_category:
            task_key = task_category.value
            task_prefs = TASK_PROVIDER_PREFERENCES.get(task_key)

            if task_prefs:
                # Find intersection that maintains agent preference order
                common_providers = [p for p in agent_prefs if p in task_prefs]
                if common_providers:
                    return common_providers[0]

        # Fall back to first agent preference
        return agent_prefs[0] if agent_prefs else "openai"

    async def _route_to_provider(
        self, prompt: str, task_category: TaskCategory | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Route request through LLM Router for intelligent provider selection.

        Args:
            prompt: The prompt to send
            task_category: Optional task category for routing decisions
            **kwargs: Additional parameters for the LLM call

        Returns:
            Response dict with 'text', 'provider', 'model', 'usage' keys
        """
        preferred_provider = self._get_preferred_provider(task_category)
        self._current_model_provider = preferred_provider

        # If router is available, use it for intelligent routing
        if self._router is not None and Message is not None and ModelProvider is not None:
            try:
                # Convert string provider to ModelProvider enum
                provider_map = {
                    "openai": ModelProvider.OPENAI,
                    "anthropic": ModelProvider.ANTHROPIC,
                    "google": ModelProvider.GOOGLE,
                    "groq": ModelProvider.GROQ,
                    "mistral": ModelProvider.MISTRAL,
                    "cohere": ModelProvider.COHERE,
                }

                # Build preferred providers list (model_provider used for fallback)
                agent_key = self.agent_type.value if self.agent_type else "commerce"
                pref_list = AGENT_PROVIDER_PREFERENCES.get(agent_key, ["openai"])
                model_providers = [provider_map[p] for p in pref_list if p in provider_map]

                # Create message from prompt
                messages = [Message.user(prompt)]

                # Add system prompt if configured
                if self.config.system_prompt:
                    messages.insert(0, Message.system(self.config.system_prompt))

                # Route through LLM Router with fallback
                response = await self._router.complete_with_fallback(
                    messages=messages,
                    providers=model_providers,
                    temperature=kwargs.get("temperature", self.config.temperature),
                    max_tokens=kwargs.get("max_tokens", 2000),
                )

                # Get the actual provider used from response
                actual_provider = preferred_provider
                if hasattr(response, "model"):
                    # Infer provider from model name
                    model_lower = response.model.lower()
                    if "claude" in model_lower:
                        actual_provider = "anthropic"
                    elif "gpt" in model_lower:
                        actual_provider = "openai"
                    elif "gemini" in model_lower:
                        actual_provider = "google"
                    elif "llama" in model_lower:
                        actual_provider = "groq"
                    elif "mistral" in model_lower:
                        actual_provider = "mistral"

                self._current_model_provider = actual_provider
                logger.debug(f"Routed to {actual_provider} for {self.agent_type}")

                return {
                    "text": response.content if hasattr(response, "content") else str(response),
                    "provider": actual_provider,
                    "model": response.model if hasattr(response, "model") else self.config.model,
                    "usage": {
                        "input_tokens": (
                            response.usage.input_tokens
                            if hasattr(response, "usage") and response.usage
                            else 0
                        ),
                        "output_tokens": (
                            response.usage.output_tokens
                            if hasattr(response, "usage") and response.usage
                            else 0
                        ),
                        "cost_usd": (
                            response.usage.cost
                            if hasattr(response, "usage")
                            and response.usage
                            and hasattr(response.usage, "cost")
                            else 0.0
                        ),
                    },
                }

            except Exception as e:
                logger.warning(f"Router failed, falling back to direct call: {e}")

        # Fallback: Direct execution without router
        return await self._execute_direct(prompt, preferred_provider, **kwargs)

    async def _execute_direct(
        self,
        prompt: str,
        provider: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute directly without router when router is unavailable.

        Attempts multiple fallback strategies:
        1. Use existing backend agent
        2. Try direct LLM provider calls
        3. Raise error if no provider available (no silent failures)

        Args:
            prompt: The prompt to execute
            provider: Preferred provider name
            **kwargs: Additional execution arguments

        Returns:
            Dict with text, provider, model, and usage info

        Raises:
            RuntimeError: If no execution backend is available
        """
        # Strategy 1: Use existing backend if available
        if hasattr(self, "_backend_agent") and self._backend_agent:
            try:
                result = await self._backend_agent.run(prompt)
                return {
                    "text": str(result.data) if hasattr(result, "data") else str(result),
                    "provider": provider,
                    "model": self.config.model,
                    "usage": {"tokens": 0, "cost_usd": 0.0},
                }
            except Exception as e:
                logger.error(f"Backend execution failed: {e}")

        # Strategy 2: Try direct LLM provider calls
        try:
            from llm.router import get_llm_router

            router = get_llm_router()
            if router:
                # Get first available provider
                available = router.list_available_providers()
                if available:
                    fallback_provider = available[0]
                    logger.info(f"Using fallback provider: {fallback_provider}")

                    response = await router.route_and_execute(
                        prompt=prompt,
                        preferred_provider=fallback_provider,
                        task_type=(
                            self.agent_type.value
                            if hasattr(self.agent_type, "value")
                            else str(self.agent_type)
                        ),
                    )

                    return {
                        "text": response.content if hasattr(response, "content") else str(response),
                        "provider": fallback_provider,
                        "model": response.model if hasattr(response, "model") else "unknown",
                        "usage": {"tokens": 0, "cost_usd": 0.0},
                    }
        except ImportError:
            logger.debug("LLM router not available for fallback")
        except Exception as e:
            logger.warning(f"Direct LLM fallback failed: {e}")

        # Strategy 3: Raise error - no silent failures in production
        raise RuntimeError(
            f"No execution backend available for provider '{provider}'. "
            f"Configure at least one LLM provider (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.) "
            f"or ensure the backend agent is properly initialized."
        )

    def select_technique(
        self,
        task_category: TaskCategory,
        context: dict[str, Any] | None = None,
        prompt: str | None = None,
    ) -> PromptTechnique:
        """
        Select the best prompt technique for a task.

        Selection priority:
        1. RAG-based recommendation (similar prompt analysis)
        2. Learning module history
        3. Prompt module auto-selection
        """
        # Priority 1: Query RAG/knowledge base for similar prompts
        if self.learning_module and prompt:
            rag_technique, confidence = self.learning_module.get_technique_recommendation(
                prompt=prompt, task_type=task_category.value
            )
            if rag_technique and confidence > 0.6:  # High confidence threshold
                logger.debug(
                    f"RAG recommended technique {rag_technique.value} "
                    f"with {confidence:.1%} confidence"
                )
                return rag_technique

        # Priority 2: Check if learning module has a better suggestion from history
        if self.learning_module:
            learned_technique = self.learning_module.get_best_technique(task_category.value)
            if learned_technique:
                return learned_technique

        # Priority 3: Fall back to prompt module auto-selection
        return self.prompt_module.auto_select_technique(task_category, context)

    def apply_technique(
        self, technique: PromptTechnique, prompt: str, **kwargs
    ) -> PromptTechniqueResult:
        """Apply a prompt engineering technique"""
        return self.prompt_module.apply_technique(technique, prompt, **kwargs)

    async def predict(self, model_name: str, input_data: Any, **kwargs):
        """Run ML prediction"""
        if not self.ml_module:
            return None
        return await self.ml_module.predict(model_name, input_data, **kwargs)

    async def run_round_table(
        self,
        prompt: str,
        providers: list[LLMProvider] | None = None,
        context: dict[str, Any] | None = None,
    ):
        """Run LLM Round Table competition"""
        if not self.round_table:
            return None
        return await self.round_table.compete(prompt, providers, context)

    @abstractmethod
    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute agent task - must be implemented by subclasses"""
        pass

    async def execute_auto(
        self,
        prompt: str,
        task_type: str | None = None,
        correlation_id: str | None = None,
        use_router: bool = True,
        use_round_table: bool = False,
        **kwargs,
    ) -> AgentResult:
        """
        Execute with AUTOMATIC prompt technique selection.

        This is the recommended entry point for all agent executions.
        It automatically:
        1. Generates a correlation_id for tracing
        2. Analyzes the prompt to determine TaskCategory
        3. Selects the optimal PromptTechnique from 17 available
        4. Applies the technique to enhance the prompt
        5. Routes to optimal LLM provider
        6. Logs all decisions for observability and A/B testing
        7. Records outcomes for self-learning optimization

        Args:
            prompt: The task prompt
            task_type: Optional task type for learning (auto-inferred if not provided)
            correlation_id: Optional correlation ID (auto-generated if not provided)
            use_router: Whether to use LLM Router for provider selection
            use_round_table: Whether to use Round Table for high-stakes tasks
            **kwargs: Additional execution parameters

        Returns:
            AgentResult with execution outcome and technique metadata
        """
        import uuid

        # Generate correlation_id for tracing
        correlation_id = correlation_id or str(uuid.uuid4())
        task_id = correlation_id[:16]
        start_time = time.time()

        # Use TaskCategoryAnalyzer for intelligent category inference
        analyzer = get_task_analyzer()
        task_category, confidence, analysis_reason = analyzer.analyze(
            prompt=prompt,
            agent_type=self.agent_type,
            correlation_id=correlation_id,
        )

        # Auto-infer task_type if not provided
        if task_type is None:
            task_type = (
                f"{self.agent_type.value if self.agent_type else 'general'}_{task_category.value}"
            )

        # Select optimal technique
        technique, selection_reason = analyzer.select_technique(
            category=task_category,
            confidence=confidence,
            correlation_id=correlation_id,
        )

        # Log the automatic selection for observability
        log = structlog.get_logger(__name__)

        # Bind execution-scoped context
        bind_contextvars(
            correlation_id=correlation_id,
            agent_id=str(
                getattr(self, "agent_id", self.agent_type.value if self.agent_type else "unknown")
            ),
        )

        log.info(
            "agent_technique_selection",
            agent_type=self.agent_type.value if self.agent_type else "unknown",
            task_category=task_category.value,
            technique=technique.value,
            confidence=round(confidence, 2),
        )

        # Auto-fetch docs context when RAG is selected and no context was provided.
        # Silently degrades — agents function normally if the collection is absent.
        if technique == PromptTechnique.RAG and "context" not in kwargs:
            try:
                from orchestration.docs_context import get_docs_context

                docs_ctx = await get_docs_context(prompt)
                if docs_ctx:
                    kwargs = {**kwargs, "context": docs_ctx}
                    log.info("docs_rag_injected", chunks=len(docs_ctx))
            except Exception:
                pass

        # Apply technique to enhance prompt
        enhanced = self.apply_technique(technique, prompt, **kwargs)

        # Add correlation metadata to result
        enhanced_with_meta = PromptTechniqueResult(
            technique=enhanced.technique,
            original_prompt=enhanced.original_prompt,
            enhanced_prompt=enhanced.enhanced_prompt,
            metadata={
                **enhanced.metadata,
                "correlation_id": correlation_id,
                "task_category": task_category.value,
                "confidence": confidence,
                "selection_reason": selection_reason,
            },
            correlation_id=correlation_id,
            task_category=task_category,
            selection_reason=selection_reason,
        )

        # Determine if Round Table should be used
        should_use_round_table = use_round_table or self._is_high_stakes_task(task_type, prompt)

        # Execute with appropriate method
        if should_use_round_table and self.round_table:
            result = await self._execute_with_round_table_internal(
                enhanced_with_meta, task_type, task_category, correlation_id, **kwargs
            )
        elif use_router and self._router is not None:
            result = await self._execute_with_router_internal(
                enhanced_with_meta, task_category, correlation_id, **kwargs
            )
        else:
            # Direct execution
            result = await self.execute(enhanced_with_meta.enhanced_prompt, **kwargs)

        # Calculate metrics
        latency_ms = (time.time() - start_time) * 1000
        success = result.status == AgentStatus.COMPLETED
        cost_usd = result.cost_usd

        # Record for learning
        if self.learning_module:
            self.learning_module.record_execution(
                task_id=task_id,
                task_type=task_type,
                prompt=prompt,
                technique=technique,
                llm_provider=self._current_model_provider or self._active_provider.value,
                success=success,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
            )

        # Update technique stats
        self.prompt_module.record_outcome(technique, success)

        # Enrich result metadata with technique selection info
        if result.metadata is None:
            result.metadata = {}
        result.metadata.update(
            {
                "correlation_id": correlation_id,
                "task_category": task_category.value,
                "technique": technique.value,
                "technique_confidence": confidence,
                "selection_reason": selection_reason,
                "auto_selected": True,
            }
        )

        self._execution_count += 1

        log.info(
            "agent_execution_complete",
            status=result.status.value,
            latency_ms=round(latency_ms, 0),
            technique=technique.value,
            success=success,
        )

        # Unbind execution-scoped context
        unbind_contextvars("correlation_id", "agent_id")

        return result

    async def _execute_with_router_internal(
        self,
        enhanced: PromptTechniqueResult,
        task_category: TaskCategory,
        correlation_id: str,
        **kwargs,
    ) -> AgentResult:
        """Internal method for router-based execution."""
        try:
            routed_response = await self._route_to_provider(
                enhanced.enhanced_prompt, task_category=task_category, **kwargs
            )
            provider_used = routed_response.get("provider", self._active_provider.value)
            self._current_model_provider = provider_used

            return AgentResult(
                status=AgentStatus.COMPLETED,
                output=routed_response.get("text", ""),
                usage=routed_response.get("usage", {}),
                metadata={
                    "provider": provider_used,
                    "model": routed_response.get("model", self.config.model),
                    "routed": True,
                    "correlation_id": correlation_id,
                },
            )
        except Exception as e:
            logger.warning(f"[{correlation_id}] Routed execution failed: {e}")
            return await self.execute(enhanced.enhanced_prompt, **kwargs)

    async def _execute_with_round_table_internal(
        self,
        enhanced: PromptTechniqueResult,
        task_type: str,
        task_category: TaskCategory,
        correlation_id: str,
        **kwargs,
    ) -> AgentResult:
        """Internal method for Round Table execution."""
        if not self.round_table:
            return await self.execute(enhanced.enhanced_prompt, **kwargs)

        try:
            round_table_result = await self.round_table.compete(
                enhanced.enhanced_prompt,
                providers=None,  # Use all available
                context={
                    "task_type": task_type,
                    "task_category": task_category.value,
                    "agent_type": self.agent_type.value if self.agent_type else None,
                    "correlation_id": correlation_id,
                },
            )

            winner = round_table_result.winner
            success = winner is not None and winner.response

            return AgentResult(
                status=AgentStatus.COMPLETED if success else AgentStatus.FAILED,
                output=winner.response if winner else "",
                usage={
                    "cost_usd": winner.cost_usd if winner else 0.0,
                    "latency_ms": winner.latency_ms if winner else 0.0,
                    "round_table_entries": len(round_table_result.entries),
                },
                metadata={
                    "round_table": True,
                    "task_id": round_table_result.task_id,
                    "winning_provider": winner.provider.value if winner else None,
                    "winner_score": winner.total_score if winner else 0.0,
                    "judge_reasoning": round_table_result.judge_reasoning,
                    "correlation_id": correlation_id,
                },
            )
        except Exception as e:
            logger.warning(f"[{correlation_id}] Round Table failed: {e}")
            return await self.execute(enhanced.enhanced_prompt, **kwargs)

    async def execute_with_learning(
        self,
        prompt: str,
        task_type: str,
        technique: PromptTechnique | None = None,
        use_router: bool = True,
        **kwargs,
    ) -> AgentResult:
        """
        Execute with automatic learning, optimization, and intelligent routing.

        This method:
        1. Infers task category from prompt
        2. Selects the best technique if not specified
        3. Applies the technique to enhance the prompt
        4. Routes to optimal LLM provider based on agent type and task
        5. Executes the task
        6. Records the outcome for learning
        7. Updates technique and provider stats

        Args:
            prompt: The task prompt
            task_type: Type of task for learning categorization
            technique: Optional specific technique to use
            use_router: Whether to use LLM Router for provider selection
            **kwargs: Additional execution parameters

        Returns:
            AgentResult with execution outcome
        """
        import uuid

        task_id = str(uuid.uuid4())[:16]
        start_time = time.time()

        # Infer task category for routing and technique selection
        task_category = self._infer_task_category(prompt)

        # Select technique if not specified
        if technique is None:
            technique = self.select_technique(task_category)

        # Apply technique to enhance prompt
        enhanced = self.apply_technique(technique, prompt, **kwargs)

        # Track which provider was used
        provider_used = self._active_provider.value

        # Execute with intelligent routing if enabled and router available
        if use_router and self._router is not None:
            try:
                routed_response = await self._route_to_provider(
                    enhanced.enhanced_prompt, task_category=task_category, **kwargs
                )
                provider_used = routed_response.get("provider", provider_used)
                self._current_model_provider = provider_used

                # Build result from routed response
                result = AgentResult(
                    status=AgentStatus.COMPLETED,
                    output=routed_response.get("text", ""),
                    usage=routed_response.get("usage", {}),
                    metadata={
                        "provider": provider_used,
                        "model": routed_response.get("model", self.config.model),
                        "routed": True,
                        "task_category": task_category.value,
                        "technique": technique.value,
                    },
                )
            except Exception as e:
                logger.warning(f"Routed execution failed, falling back: {e}")
                result = await self.execute(enhanced.enhanced_prompt, **kwargs)
        else:
            # Direct execution without router
            result = await self.execute(enhanced.enhanced_prompt, **kwargs)

        # Calculate metrics
        latency_ms = (time.time() - start_time) * 1000
        success = result.status == AgentStatus.COMPLETED
        cost_usd = result.cost_usd

        # Record for learning with actual provider used
        if self.learning_module:
            self.learning_module.record_execution(
                task_id=task_id,
                task_type=task_type,
                prompt=prompt,
                technique=technique,
                llm_provider=provider_used,
                success=success,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
            )

        # Update technique stats
        self.prompt_module.record_outcome(technique, success)

        self._execution_count += 1
        return result

    def _infer_task_category(self, prompt: str) -> TaskCategory:
        """Infer task category from prompt"""
        prompt_lower = prompt.lower()

        category_keywords = {
            TaskCategory.REASONING: ["why", "explain", "analyze", "reason"],
            TaskCategory.CLASSIFICATION: ["classify", "categorize", "label", "type"],
            TaskCategory.CREATIVE: ["create", "design", "generate", "imagine"],
            TaskCategory.SEARCH: ["find", "search", "locate", "look for"],
            TaskCategory.QA: ["what", "who", "when", "where", "how"],
            TaskCategory.EXTRACTION: ["extract", "parse", "get", "pull"],
            TaskCategory.MODERATION: ["review", "check", "validate", "moderate"],
            TaskCategory.GENERATION: ["write", "compose", "draft", "produce"],
            TaskCategory.ANALYSIS: ["analyze", "examine", "study", "investigate"],
            TaskCategory.PLANNING: ["plan", "schedule", "organize", "strategy"],
            TaskCategory.DEBUGGING: ["fix", "debug", "error", "issue", "bug"],
            TaskCategory.OPTIMIZATION: ["optimize", "improve", "enhance", "better"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                return category

        return TaskCategory.GENERATION  # Default

    def _is_high_stakes_task(self, task_type: str, prompt: str | None = None) -> bool:
        """
        Determine if a task should use Round Table for quality assurance.

        High-stakes tasks include:
        - Tasks in HIGH_STAKES_TASK_TYPES
        - Tasks from HIGH_STAKES_AGENT_TYPES agents
        - Tasks with keywords indicating financial/security operations

        Args:
            task_type: The task type string
            prompt: Optional prompt to analyze for high-stakes keywords

        Returns:
            True if Round Table should be used
        """
        # Check if task type is explicitly high-stakes
        if task_type.lower() in HIGH_STAKES_TASK_TYPES:
            return True

        # Check if this agent type defaults to high-stakes
        agent_type = self.agent_type.value if self.agent_type else ""
        if agent_type in HIGH_STAKES_AGENT_TYPES:
            # Check for transaction-related keywords
            high_stakes_keywords = [
                "order",
                "payment",
                "refund",
                "transaction",
                "checkout",
                "purchase",
                "invoice",
                "charge",
                "deploy",
                "delete",
                "remove",
                "production",
            ]
            task_lower = task_type.lower()
            if any(kw in task_lower for kw in high_stakes_keywords):
                return True

        # Check prompt for high-stakes indicators
        if prompt:
            prompt_lower = prompt.lower()
            critical_keywords = [
                "process payment",
                "charge customer",
                "refund order",
                "delete",
                "remove permanently",
                "deploy to production",
                "update inventory",
                "change price",
                "modify stock",
                "authenticate user",
                "verify identity",
            ]
            if any(kw in prompt_lower for kw in critical_keywords):
                return True

        return False

    async def execute_with_round_table(
        self,
        prompt: str,
        task_type: str,
        technique: PromptTechnique | None = None,
        providers: list[LLMProvider] | None = None,
        **kwargs,
    ) -> AgentResult:
        """
        Execute task using LLM Round Table for quality assurance.

        Multiple LLMs compete, top 2 are A/B tested, winner is returned.
        Use for high-stakes tasks or when maximum quality is required.

        Args:
            prompt: The task prompt
            task_type: Type of task for categorization
            technique: Optional prompt technique to apply
            providers: Optional list of LLM providers to include
            **kwargs: Additional execution parameters

        Returns:
            AgentResult with winning response and metadata
        """
        import uuid

        task_id = str(uuid.uuid4())[:16]
        start_time = time.time()

        # Infer task category and select technique
        task_category = self._infer_task_category(prompt)
        if technique is None:
            technique = self.select_technique(task_category)

        # Apply technique to enhance prompt
        enhanced = self.apply_technique(technique, prompt, **kwargs)

        # Run Round Table competition
        if not self.round_table:
            logger.warning("Round Table not initialized, falling back to standard execution")
            return await self.execute_with_learning(
                prompt, task_type, technique, use_router=True, **kwargs
            )

        try:
            round_table_result = await self.round_table.compete(
                enhanced.enhanced_prompt,
                providers=providers,
                context={
                    "task_type": task_type,
                    "task_category": task_category.value,
                    "agent_type": self.agent_type.value if self.agent_type else None,
                },
            )

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            winner = round_table_result.winner
            success = winner is not None and winner.response

            # Build result from winner
            result = AgentResult(
                status=AgentStatus.COMPLETED if success else AgentStatus.FAILED,
                output=winner.response if winner else "",
                usage={
                    "cost_usd": winner.cost_usd if winner else 0.0,
                    "latency_ms": winner.latency_ms if winner else 0.0,
                    "round_table_entries": len(round_table_result.entries),
                },
                metadata={
                    "round_table": True,
                    "task_id": round_table_result.task_id,
                    "winning_provider": winner.provider.value if winner else None,
                    "winner_score": winner.total_score if winner else 0.0,
                    "judge_reasoning": round_table_result.judge_reasoning,
                    "technique": technique.value,
                    "task_category": task_category.value,
                },
            )

            # Record for learning
            if self.learning_module:
                self.learning_module.record_execution(
                    task_id=task_id,
                    task_type=task_type,
                    prompt=prompt,
                    technique=technique,
                    llm_provider=(
                        f"round_table:{winner.provider.value}" if winner else "round_table"
                    ),
                    success=success,
                    latency_ms=latency_ms,
                    cost_usd=winner.cost_usd if winner else 0.0,
                    user_feedback=winner.total_score if winner else None,
                )

                # Auto-ingest successful responses to RAG for future retrieval
                if success and winner and winner.total_score >= ROUND_TABLE_QUALITY_THRESHOLD:
                    await self.learning_module.ingest_successful_response(
                        prompt=prompt,
                        response=winner.response,
                        task_type=task_type,
                        technique=technique,
                        score=winner.total_score,
                        provider=winner.provider.value,
                        metadata={
                            "round_table_entries": len(round_table_result.entries),
                            "judge_reasoning": round_table_result.judge_reasoning[:200],
                            "task_category": task_category.value,
                        },
                    )

            # Update technique stats
            self.prompt_module.record_outcome(
                technique, success, winner.total_score if winner else 0.0
            )

            self._execution_count += 1
            logger.info(
                f"Round Table completed: winner={winner.provider.value if winner else 'none'}, "
                f"score={winner.total_score:.2f if winner else 0}, entries={len(round_table_result.entries)}"
            )

            return result

        except Exception as e:
            logger.error(f"Round Table execution failed: {e}")
            # Fall back to standard execution
            return await self.execute_with_learning(
                prompt, task_type, technique, use_router=True, **kwargs
            )

    async def execute_smart(
        self,
        prompt: str,
        task_type: str,
        technique: PromptTechnique | None = None,
        force_round_table: bool = False,
        **kwargs,
    ) -> AgentResult:
        """
        Smart execution that auto-selects execution mode based on task stakes.

        Automatically uses Round Table for:
        - High-stakes tasks (transactions, security, etc.)
        - Force round table flag
        - Commerce/Operations agents for important decisions

        Uses standard routing execution for lower-stakes tasks.

        Args:
            prompt: The task prompt
            task_type: Type of task for categorization
            technique: Optional prompt technique to apply
            force_round_table: Force Round Table usage
            **kwargs: Additional execution parameters

        Returns:
            AgentResult with execution outcome
        """
        # Check if this is a high-stakes task
        use_round_table = force_round_table or self._is_high_stakes_task(task_type, prompt)

        if use_round_table and self.round_table:
            logger.info(f"High-stakes task detected, using Round Table: {task_type}")
            return await self.execute_with_round_table(prompt, task_type, technique, **kwargs)
        else:
            return await self.execute_with_learning(
                prompt, task_type, technique, use_router=True, **kwargs
            )

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive agent statistics"""
        stats = {
            "agent_type": self.agent_type.value if self.agent_type else None,
            "execution_count": self._execution_count,
            "initialized": self._initialized,
            "active_provider": self._active_provider.value,
            "current_model_provider": self._current_model_provider,
        }

        # Router status
        stats["router"] = {
            "available": self._router_available,
            "initialized": self._router is not None,
            "preferred_providers": AGENT_PROVIDER_PREFERENCES.get(
                self.agent_type.value if self.agent_type else "commerce", []
            ),
        }

        if self.prompt_module:
            stats["technique_stats"] = self.prompt_module.get_technique_stats()

        if self.learning_module:
            stats["learning"] = self.learning_module.get_optimization_report()

        if self.ml_module:
            stats["ml_models"] = self.ml_module.list_available_models()

        if self.round_table:
            stats["round_table"] = self.round_table.get_provider_stats()

        return stats

    def get_provider_recommendation(self, task_type: str | None = None) -> dict[str, Any]:
        """
        Get provider recommendation for this agent and optional task type.

        Returns:
            Dict with recommended provider and reasoning
        """
        agent_type = self.agent_type.value if self.agent_type else "commerce"
        agent_prefs = AGENT_PROVIDER_PREFERENCES.get(agent_type, ["openai"])

        task_category = None
        if task_type:
            try:  # noqa: SIM105 - simple pattern, no need to import contextlib
                task_category = TaskCategory(task_type)
            except ValueError:
                pass

        recommended = self._get_preferred_provider(task_category)

        return {
            "recommended_provider": recommended,
            "agent_type": agent_type,
            "agent_preferences": agent_prefs,
            "task_category": task_category.value if task_category else None,
            "reasoning": f"Based on {agent_type} agent preferences and task requirements",
        }

    async def _init_enterprise_intelligence(self) -> None:
        """
        Initialize Enterprise Intelligence Modules.

        Sets up:
        1. EnterpriseIndex - Multi-provider code search
        2. SemanticCodeAnalyzer - Pattern detection
        3. LLMVerificationEngine - DeepSeek + Claude verification
        """
        try:
            # Import enterprise modules
            from llm.providers.anthropic import AnthropicClient
            from llm.providers.deepseek import DeepSeekClient
            from llm.verification import LLMVerificationEngine, VerificationConfig
            from orchestration.enterprise_index import create_enterprise_index
            from orchestration.semantic_analyzer import SemanticCodeAnalyzer

            # Initialize Enterprise Index
            self.enterprise_index = create_enterprise_index()
            await self.enterprise_index.initialize()
            logger.info("EnterpriseIndex initialized with all configured providers")

            # Initialize Semantic Analyzer
            self.semantic_analyzer = SemanticCodeAnalyzer()
            logger.info("SemanticCodeAnalyzer initialized")

            # Initialize Verification Engine (DeepSeek + Claude)
            generator_client = DeepSeekClient()
            verifier_client = AnthropicClient()
            verification_config = VerificationConfig(
                generator_provider="deepseek",
                generator_model="deepseek-chat",
                verifier_provider="anthropic",
                verifier_model="claude-3-5-sonnet-20241022",
            )
            self.verification_engine = LLMVerificationEngine(
                generator_client=generator_client,
                verifier_client=verifier_client,
                config=verification_config,
            )
            logger.info("LLMVerificationEngine initialized (DeepSeek + Claude)")

        except ImportError as e:
            logger.warning(f"Enterprise intelligence modules not available: {e}")
            self.enterprise_index = None
            self.semantic_analyzer = None
            self.verification_engine = None
        except Exception as e:
            logger.error(f"Failed to initialize enterprise intelligence: {e}")
            self.enterprise_index = None
            self.semantic_analyzer = None
            self.verification_engine = None

    async def gather_enterprise_context(
        self,
        task_description: str,
        language: str = "python",
    ) -> dict[str, Any]:
        """
        Gather enterprise context BEFORE code generation (Context-First Pattern).

        This is the pre-flight phase that searches:
        1. Enterprise code indexes (GitHub, GitLab, Sourcegraph)
        2. Semantic patterns in existing codebase
        3. Similar implementations for reference

        Args:
            task_description: What code needs to be generated
            language: Programming language filter

        Returns:
            Context dict with:
            - similar_code: List of similar implementations
            - patterns: Detected patterns from semantic analysis
            - recommendations: Best practices from existing code
            - metadata: Search metadata
        """
        context = {
            "similar_code": [],
            "patterns": [],
            "recommendations": [],
            "metadata": {},
        }

        if not self.enterprise_index or not self.semantic_analyzer:
            logger.warning("Enterprise intelligence not initialized, skipping context gathering")
            return context

        try:
            # Import search types
            from orchestration.enterprise_index import SearchLanguage

            # Map string to enum
            lang_map = {
                "python": SearchLanguage.PYTHON,
                "typescript": SearchLanguage.TYPESCRIPT,
                "javascript": SearchLanguage.JAVASCRIPT,
                "go": SearchLanguage.GO,
                "rust": SearchLanguage.RUST,
                "java": SearchLanguage.JAVA,
            }
            search_lang = lang_map.get(language.lower(), SearchLanguage.PYTHON)

            # Phase 1: Search enterprise indexes
            logger.info(f"Searching enterprise indexes for: {task_description[:50]}...")
            search_results = await self.enterprise_index.search_code(
                query=task_description,
                language=search_lang,
                max_results_per_provider=3,
            )

            context["similar_code"] = [
                {
                    "repository": r.repository,
                    "file_path": r.file_path,
                    "snippet": r.code_snippet[:200],  # Truncate for context
                    "url": r.url,
                    "provider": r.provider,
                    "score": r.score,
                }
                for r in search_results[:5]  # Top 5 results
            ]

            # Phase 2: Semantic analysis of found code
            if search_results:
                logger.info(f"Analyzing {len(search_results)} code samples for patterns...")
                patterns_found = set()

                for result in search_results[:3]:  # Analyze top 3
                    try:
                        # Detect patterns in the code snippet
                        if len(result.code_snippet) > 50:
                            if "class " in result.code_snippet:
                                patterns_found.add("object_oriented")
                            if "async " in result.code_snippet:
                                patterns_found.add("async_await")
                            if "def test" in result.code_snippet:
                                patterns_found.add("test_driven")
                    except Exception as e:
                        logger.warning(f"Pattern analysis failed for {result.file_path}: {e}")

                context["patterns"] = list(patterns_found)

            # Phase 3: Generate recommendations
            if context["similar_code"]:
                context["recommendations"] = [
                    f"Found {len(context['similar_code'])} similar implementations across enterprise codebases",
                    f"Common patterns: {', '.join(context['patterns']) if context['patterns'] else 'none detected'}",
                    "Consider following established patterns for consistency",
                ]

            context["metadata"] = {
                "search_query": task_description,
                "language": language,
                "results_count": len(search_results),
                "providers_used": list({r.provider for r in search_results}),
            }

            logger.info(
                f"Enterprise context gathered: {len(context['similar_code'])} examples, "
                f"{len(context['patterns'])} patterns"
            )

        except Exception as e:
            logger.error(f"Failed to gather enterprise context: {e}")

        return context


__all__ = [
    "EnhancedSuperAgent",
    "LLM_ROUTER_AVAILABLE",
]
