import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any

from agent.modules.base_agent import AgentStatus, BaseAgent


"""
Enterprise Multi-Agent Orchestration System
Manages agent lifecycle, dependencies, coordination, and load balancing

Features:
- Agent dependency resolution and execution ordering
- Load balancing and resource management
- Circuit breaker patterns for fault tolerance
- Inter-agent communication and data sharing
- Health monitoring and automatic recovery
- Security and access control
- Performance optimization and caching
"""

logger = logging.getLogger(__name__)


class ExecutionPriority(Enum):
    """Agent execution priority levels"""

    CRITICAL = 1  # Must execute first (security, auth)
    HIGH = 2  # Core business logic (payments, orders)
    MEDIUM = 3  # Standard operations (content, analytics)
    LOW = 4  # Background tasks (learning, optimization)


class TaskStatus(Enum):
    """Multi-agent task status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentCapability:
    """Defines what an agent can do"""

    agent_name: str
    capabilities: list[str]
    required_agents: list[str] = field(default_factory=list)  # Dependencies
    priority: ExecutionPriority = ExecutionPriority.MEDIUM
    max_concurrent: int = 5  # Max concurrent executions
    rate_limit: int = 100  # Requests per minute


@dataclass
class AgentTask:
    """Represents a task to be executed by one or more agents"""

    task_id: str
    task_type: str
    parameters: dict[str, Any]
    required_agents: list[str]
    priority: ExecutionPriority
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class AgentOrchestrator:
    """
    Enterprise-grade multi-agent orchestration system.

    Responsibilities:
    - Agent registration and lifecycle management
    - Dependency resolution and execution ordering
    - Load balancing and resource allocation
    - Inter-agent communication
    - Health monitoring and recovery
    - Security and access control
    """

    def __init__(self, max_concurrent_tasks: int = 50):
        self.agents: dict[str, BaseAgent] = {}
        self.agent_capabilities: dict[str, AgentCapability] = {}
        self.dependency_graph: dict[str, set[str]] = defaultdict(set)
        self.reverse_dependencies: dict[str, set[str]] = defaultdict(set)

        # Task management
        self.tasks: dict[str, AgentTask] = {}
        self.task_queue: deque = deque()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.active_tasks: set[str] = set()

        # Performance tracking
        self.execution_history: list[dict[str, Any]] = []
        self.agent_metrics: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"calls": 0, "errors": 0, "total_time": 0.0, "avg_time": 0.0}
        )

        # Circuit breaker for failing agents
        self.circuit_breakers: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"failures": 0, "opened_at": None, "state": "closed"}
        )

        # Security
        self.access_control: dict[str, set[str]] = defaultdict(set)
        self.api_keys: dict[str, str] = {}

        # Inter-agent data sharing
        self.shared_context: dict[str, Any] = {}

        logger.info("🎭 Enterprise Agent Orchestrator initialized")

    # ============================================================================
    # AGENT REGISTRATION & LIFECYCLE
    # ============================================================================

    async def register_agent(
        self,
        agent: BaseAgent,
        capabilities: list[str],
        dependencies: list[str] | None = None,
        priority: ExecutionPriority = ExecutionPriority.MEDIUM,
    ) -> bool:
        """
        Register an agent with the orchestrator.

        Args:
            agent: BaseAgent instance
            capabilities: List of capabilities this agent provides
            dependencies: List of agent names this agent depends on
            priority: Execution priority

        Returns:
            bool: True if registration successful
        """
        try:
            agent_name = agent.agent_name

            # Initialize agent if not already done
            if agent.status == AgentStatus.INITIALIZING:
                init_success = await agent.initialize()
                if not init_success:
                    logger.error(f"Failed to initialize agent: {agent_name}")
                    return False

            # Register agent
            self.agents[agent_name] = agent

            # Enhance capabilities based on agent type
            enhanced_capabilities = capabilities.copy()

            # Add video generation capabilities if this is a fashion vision agent
            if hasattr(agent, "generate_fashion_runway_video"):
                enhanced_capabilities.extend(
                    [
                        "video_generation",
                        "runway_video_generation",
                        "product_360_video_generation",
                        "video_upscaling",
                        "fashion_image_generation",
                    ]
                )

            # Add brand training capabilities if this is a brand trainer
            if hasattr(agent, "train_lora_model"):
                enhanced_capabilities.extend(
                    [
                        "brand_model_training",
                        "dataset_preparation",
                        "lora_fine_tuning",
                        "brand_consistency_validation",
                        "custom_model_generation",
                    ]
                )

            # Register capabilities
            self.agent_capabilities[agent_name] = AgentCapability(
                agent_name=agent_name,
                capabilities=enhanced_capabilities,
                required_agents=dependencies or [],
                priority=priority,
            )

            # Build dependency graph
            if dependencies:
                self.dependency_graph[agent_name] = set(dependencies)
                for dep in dependencies:
                    self.reverse_dependencies[dep].add(agent_name)

            logger.info(f"✅ Registered agent: {agent_name} with capabilities: {capabilities}")
            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent.agent_name}: {e}")
            return False

    async def unregister_agent(self, agent_name: str) -> bool:
        """Unregister an agent and clean up resources"""
        try:
            if agent_name not in self.agents:
                return False

            # Check if other agents depend on this one
            dependents = self.reverse_dependencies.get(agent_name, set())
            if dependents:
                logger.warning(f"Agent {agent_name} has dependents: {dependents}")

            # Remove from all tracking structures
            del self.agents[agent_name]
            del self.agent_capabilities[agent_name]
            if agent_name in self.dependency_graph:
                del self.dependency_graph[agent_name]
            if agent_name in self.reverse_dependencies:
                del self.reverse_dependencies[agent_name]

            logger.info(f"Unregistered agent: {agent_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_name}: {e}")
            return False

    # ============================================================================
    # TASK EXECUTION & COORDINATION
    # ============================================================================

    async def execute_task(
        self,
        task_type: str,
        parameters: dict[str, Any],
        required_capabilities: list[str],
        priority: ExecutionPriority = ExecutionPriority.MEDIUM,
    ) -> dict[str, Any]:
        """
        Execute a multi-agent task.

        Args:
            task_type: Type of task (e.g., "process_order", "generate_content")
            parameters: Task parameters
            required_capabilities: List of capabilities needed
            priority: Task priority

        Returns:
            Dict with task results from all agents
        """
        task_id = f"task_{datetime.now().timestamp()}_{task_type}"

        # Find agents with required capabilities
        capable_agents = self._find_agents_with_capabilities(required_capabilities)
        if not capable_agents:
            return {"error": f"No agents found with capabilities: {required_capabilities}"}

        # Resolve execution order based on dependencies
        execution_order = self._resolve_dependencies(capable_agents)

        # Create task
        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            parameters=parameters,
            required_agents=execution_order,
            priority=priority,
        )

        self.tasks[task_id] = task
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        results = {}
        errors = []

        try:
            # Execute agents in dependency order
            for agent_name in execution_order:
                if agent_name not in self.agents:
                    errors.append(f"Agent not found: {agent_name}")
                    continue

                agent = self.agents[agent_name]

                # Check circuit breaker
                if self._is_circuit_open(agent_name):
                    errors.append(f"Circuit breaker open for: {agent_name}")
                    continue

                # Check agent health
                if agent.status == AgentStatus.FAILED:
                    errors.append(f"Agent unhealthy: {agent_name}")
                    continue

                # Execute agent
                start_time = datetime.now()
                try:
                    # Pass shared context to agent
                    agent_params = {
                        **parameters,
                        "_shared_context": self.shared_context,
                        "_previous_results": results,
                    }

                    result = await agent.execute_core_function(**agent_params)
                    results[agent_name] = result

                    # Update shared context if agent provides data
                    if result and isinstance(result, dict):
                        self.shared_context.update(result.get("_shared_data", {}))

                    # Track success
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self._record_execution(agent_name, True, execution_time)
                    self._reset_circuit_breaker(agent_name)

                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {e}")
                    errors.append(f"{agent_name}: {e!s}")
                    results[agent_name] = {"error": str(e)}

                    # Track failure
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self._record_execution(agent_name, False, execution_time)
                    self._increment_circuit_breaker(agent_name)

            # Complete task
            task.status = TaskStatus.COMPLETED if not errors else TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.result = results
            if errors:
                task.error = "; ".join(errors)

            return {
                "task_id": task_id,
                "status": task.status.value,
                "results": results,
                "errors": errors if errors else None,
                "execution_time": (task.completed_at - task.started_at).total_seconds(),
            }

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            return {"error": str(e), "task_id": task_id}

    def _find_agents_with_capabilities(self, required_capabilities: list[str]) -> list[str]:
        """Find all agents that have the required capabilities"""
        capable_agents = []

        for agent_name, capability in self.agent_capabilities.items():
            # Check if agent has all required capabilities
            if all(cap in capability.capabilities for cap in required_capabilities):
                capable_agents.append(agent_name)

        # Sort by priority
        capable_agents.sort(key=lambda name: self.agent_capabilities[name].priority.value)

        return capable_agents

    def _resolve_dependencies(self, agent_names: list[str]) -> list[str]:
        """
        Resolve agent dependencies using topological sort.
        Returns agents in execution order.
        """
        # Build subgraph for these agents
        graph = {}
        in_degree = {}

        for agent_name in agent_names:
            dependencies = self.dependency_graph.get(agent_name, set())
            # Only include dependencies that are in our agent list
            relevant_deps = dependencies & set(agent_names)
            graph[agent_name] = relevant_deps
            in_degree[agent_name] = len(relevant_deps)

        # Topological sort (Kahn's algorithm)
        queue = deque([name for name in agent_names if in_degree[name] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            # Update in-degrees for agents that depend on current
            for agent_name in agent_names:
                if current in graph[agent_name]:
                    in_degree[agent_name] -= 1
                    if in_degree[agent_name] == 0:
                        queue.append(agent_name)

        # Check for cycles
        if len(result) != len(agent_names):
            logger.warning("Circular dependency detected, using original order")
            return agent_names

        return result

    # ============================================================================
    # CIRCUIT BREAKER PATTERN
    # ============================================================================

    def _is_circuit_open(self, agent_name: str, threshold: int = 5, timeout: int = 60) -> bool:
        """Check if circuit breaker is open for an agent"""
        breaker = self.circuit_breakers[agent_name]

        if breaker["state"] == "closed":
            return False

        # Check if timeout has passed
        if breaker["opened_at"] and (datetime.now() - breaker["opened_at"]).seconds > timeout:
            # Try to close circuit (half-open state)
            breaker["state"] = "half-open"
            return False

        return breaker["failures"] >= threshold

    def _increment_circuit_breaker(self, agent_name: str, threshold: int = 5):
        """Increment failure count and potentially open circuit"""
        breaker = self.circuit_breakers[agent_name]
        breaker["failures"] += 1

        if breaker["failures"] >= threshold:
            breaker["state"] = "open"
            breaker["opened_at"] = datetime.now()
            logger.warning(f"🔴 Circuit breaker OPENED for agent: {agent_name}")

    def _reset_circuit_breaker(self, agent_name: str):
        """Reset circuit breaker after successful execution"""
        if agent_name in self.circuit_breakers:
            self.circuit_breakers[agent_name] = {
                "failures": 0,
                "opened_at": None,
                "state": "closed",
            }

    # ============================================================================
    # MONITORING & METRICS
    # ============================================================================

    def _record_execution(self, agent_name: str, success: bool, execution_time: float):
        """Record agent execution metrics"""
        metrics = self.agent_metrics[agent_name]
        metrics["calls"] += 1
        metrics["total_time"] += execution_time
        metrics["avg_time"] = metrics["total_time"] / metrics["calls"]

        if not success:
            metrics["errors"] += 1

        # Store in history
        self.execution_history.append(
            {
                "agent": agent_name,
                "success": success,
                "time": execution_time,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Keep only last 1000 records
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

    async def get_orchestrator_health(self) -> dict[str, Any]:
        """Get overall orchestrator health status"""
        agent_health = {}

        for agent_name, agent in self.agents.items():
            health = await agent.health_check()
            agent_health[agent_name] = {
                "status": health.get("status"),
                "metrics": self.agent_metrics[agent_name],
                "circuit_breaker": self.circuit_breakers[agent_name]["state"],
            }

        return {
            "timestamp": datetime.now().isoformat(),
            "registered_agents": len(self.agents),
            "active_tasks": len(self.active_tasks),
            "total_tasks": len(self.tasks),
            "agent_health": agent_health,
            "system_status": (
                "healthy" if all(a.status != AgentStatus.FAILED for a in self.agents.values()) else "degraded"
            ),
        }

    def get_agent_metrics(self, agent_name: str | None = None) -> dict[str, Any]:
        """Get performance metrics for agent(s)"""
        if agent_name:
            return self.agent_metrics.get(agent_name, {})
        return dict(self.agent_metrics)

    def get_dependency_graph(self) -> dict[str, list[str]]:
        """Get the complete dependency graph"""
        return {agent: list(deps) for agent, deps in self.dependency_graph.items()}

    # ============================================================================
    # INTER-AGENT COMMUNICATION
    # ============================================================================

    def share_data(self, key: str, value: Any, ttl: int | None = None):
        """Share data between agents"""
        self.shared_context[key] = {
            "value": value,
            "timestamp": datetime.now(),
            "ttl": ttl,
        }

    def get_shared_data(self, key: str) -> Any | None:
        """Get shared data"""
        data = self.shared_context.get(key)
        if not data:
            return None

        # Check TTL
        if data.get("ttl"):
            age = (datetime.now() - data["timestamp"]).seconds
            if age > data["ttl"]:
                del self.shared_context[key]
                return None

        return data.get("value")

    async def broadcast_to_agents(self, message: dict[str, Any], agent_names: list[str] | None = None):
        """Broadcast a message to multiple agents"""
        target_agents = agent_names if agent_names else list(self.agents.keys())

        for agent_name in target_agents:
            if agent_name in self.agents:
                # Store message in shared context with agent-specific key
                self.share_data(f"message_{agent_name}", message, ttl=300)

    # ============================================================================
    # VIDEO GENERATION TASK HANDLING
    # ============================================================================

    async def create_video_generation_task(
        self, task_type: str, parameters: dict[str, Any], priority: ExecutionPriority = ExecutionPriority.MEDIUM
    ) -> str:
        """
        Create a video generation task.

        Args:
            task_type: Type of video generation ("runway_video", "product_360", etc.)
            parameters: Task parameters
            priority: Task priority

        Returns:
            Task ID
        """
        import uuid

        task_id = str(uuid.uuid4())

        # Determine required agents based on task type
        required_agents = []
        if task_type in ["runway_video", "product_360", "video_upscaling"]:
            required_agents = ["fashion_vision_agent"]
        elif task_type in ["brand_training", "custom_model_generation"]:
            required_agents = ["brand_trainer"]
        elif task_type == "full_brand_pipeline":
            required_agents = ["brand_trainer", "fashion_vision_agent"]

        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            parameters=parameters,
            required_agents=required_agents,
            priority=priority,
        )

        self.tasks[task_id] = task
        self.task_queue.append(task_id)

        logger.info(f"🎬 Created video generation task: {task_type} ({task_id})")

        return task_id

    async def execute_video_generation_task(self, task_id: str) -> dict[str, Any]:
        """
        Execute a video generation task.

        Args:
            task_id: Task ID to execute

        Returns:
            Task execution result
        """
        if task_id not in self.tasks:
            return {"error": f"Task {task_id} not found", "status": "failed"}

        task = self.tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        try:
            result = None

            if task.task_type == "runway_video":
                result = await self._execute_runway_video_task(task)
            elif task.task_type == "product_360":
                result = await self._execute_product_360_task(task)
            elif task.task_type == "brand_training":
                result = await self._execute_brand_training_task(task)
            elif task.task_type == "custom_model_generation":
                result = await self._execute_custom_model_generation_task(task)
            elif task.task_type == "video_upscaling":
                result = await self._execute_video_upscaling_task(task)
            else:
                result = {"error": f"Unknown task type: {task.task_type}", "status": "failed"}

            if result.get("success"):
                task.status = TaskStatus.COMPLETED
                task.result = result
            else:
                task.status = TaskStatus.FAILED
                task.error = result.get("error", "Unknown error")

            task.completed_at = datetime.now()

            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()

            logger.error(f"❌ Video generation task failed: {task_id} - {e}")
            return {"error": str(e), "status": "failed"}

    async def _execute_runway_video_task(self, task: AgentTask) -> dict[str, Any]:
        """Execute runway video generation task."""
        if "fashion_vision_agent" not in self.agents:
            return {"error": "Fashion vision agent not available", "status": "failed"}

        agent = self.agents["fashion_vision_agent"]

        return await agent.generate_fashion_runway_video(
            prompt=task.parameters.get("prompt", "luxury fashion runway"),
            duration=task.parameters.get("duration", 4),
            fps=task.parameters.get("fps", 8),
            width=task.parameters.get("width", 1024),
            height=task.parameters.get("height", 576),
            style=task.parameters.get("style", "luxury fashion runway"),
            upscale=task.parameters.get("upscale", True),
        )

    async def _execute_product_360_task(self, task: AgentTask) -> dict[str, Any]:
        """Execute product 360° video generation task."""
        if "fashion_vision_agent" not in self.agents:
            return {"error": "Fashion vision agent not available", "status": "failed"}

        agent = self.agents["fashion_vision_agent"]

        return await agent.generate_product_360_video(
            product_image_path=task.parameters.get("product_image_path"),
            rotation_steps=task.parameters.get("rotation_steps", 24),
            duration=task.parameters.get("duration", 3),
            upscale=task.parameters.get("upscale", True),
        )

    async def _execute_brand_training_task(self, task: AgentTask) -> dict[str, Any]:
        """Execute brand model training task."""
        if "brand_trainer" not in self.agents:
            return {"error": "Brand trainer not available", "status": "failed"}

        agent = self.agents["brand_trainer"]

        return await agent.train_lora_model(
            dataset_path=task.parameters.get("dataset_path"),
            model_name=task.parameters.get("model_name", "skyy_rose_v1"),
            resume_from_checkpoint=task.parameters.get("resume_from_checkpoint"),
        )

    async def _execute_custom_model_generation_task(self, task: AgentTask) -> dict[str, Any]:
        """Execute custom model generation task."""
        if "brand_trainer" not in self.agents:
            return {"error": "Brand trainer not available", "status": "failed"}

        agent = self.agents["brand_trainer"]

        return await agent.generate_with_brand_model(
            prompt=task.parameters.get("prompt", "luxury fashion item"),
            model_name=task.parameters.get("model_name", "skyy_rose_v1"),
            trigger_word=task.parameters.get("trigger_word", "skyrose_collection"),
            width=task.parameters.get("width", 1024),
            height=task.parameters.get("height", 1024),
        )

    async def _execute_video_upscaling_task(self, task: AgentTask) -> dict[str, Any]:
        """Execute video upscaling task."""
        if "fashion_vision_agent" not in self.agents:
            return {"error": "Fashion vision agent not available", "status": "failed"}

        agent = self.agents["fashion_vision_agent"]

        return await agent.upscale_video(
            video_path=task.parameters.get("video_path"),
            target_resolution=task.parameters.get("target_resolution", (2048, 1152)),
        )


# ============================================================================
# DEMONSTRATION MODE - Mock Agents for Testing
# ============================================================================


class MockAgent(BaseAgent):
    """Mock agent for demonstration purposes"""

    def __init__(self, agent_name: str, version: str = "1.0.0", should_fail: bool = False):
        super().__init__(agent_name, version)
        self.should_fail = should_fail
        self.execution_count = 0

    async def initialize(self) -> bool:
        """Initialize the mock agent"""
        logger.info(f"🚀 Initializing {self.agent_name}...")
        await asyncio.sleep(0.1)
        self.status = AgentStatus.HEALTHY
        return True

    async def execute_core_function(self, **kwargs) -> dict[str, Any]:
        """Execute mock functionality"""
        self.execution_count += 1

        if self.should_fail and self.execution_count % 3 == 0:
            raise Exception(f"Simulated failure in {self.agent_name}")

        await asyncio.sleep(0.2)

        return {
            "agent": self.agent_name,
            "execution_number": self.execution_count,
            "status": "success",
            "message": f"{self.agent_name} executed successfully",
            "parameters_received": kwargs,
        }


async def run_orchestrator_demonstration():
    """
    Comprehensive demonstration of the AgentOrchestrator capabilities.

    Showcases:
    - Agent registration with capabilities and dependencies
    - Dependency resolution and execution ordering
    - Priority-based task execution
    - Health monitoring and metrics
    - Circuit breaker behavior
    - Inter-agent communication
    """

    demo_orchestrator = AgentOrchestrator(max_concurrent_tasks=10)


    # Create mock agents with different capabilities
    auth_agent = MockAgent("auth_agent", "1.0.0")
    data_agent = MockAgent("data_processor", "1.0.0")
    analytics_agent = MockAgent("analytics_agent", "1.0.0")
    notification_agent = MockAgent("notification_agent", "1.0.0")

    # Register agents with capabilities and dependencies
    agents_config = [
        (auth_agent, ["authentication", "authorization"], [], ExecutionPriority.CRITICAL),
        (data_agent, ["data_processing", "validation"], ["auth_agent"], ExecutionPriority.HIGH),
        (
            analytics_agent,
            ["analytics", "reporting"],
            ["data_processor"],
            ExecutionPriority.MEDIUM,
        ),
        (notification_agent, ["notifications", "alerts"], [], ExecutionPriority.LOW),
    ]

    for agent, capabilities, dependencies, priority in agents_config:
        success = await demo_orchestrator.register_agent(
            agent, capabilities=capabilities, dependencies=dependencies, priority=priority
        )
        if success and dependencies:
            pass



    dep_graph = demo_orchestrator.get_dependency_graph()
    if dep_graph:
        for agent in dep_graph:
            pass
    else:
        pass


    task_result = await demo_orchestrator.execute_task(
        task_type="process_user_request",
        parameters={"user_id": "user_123", "action": "analyze_data", "priority": "high"},
        required_capabilities=["authentication", "data_processing", "analytics"],
        priority=ExecutionPriority.HIGH,
    )


    for result in task_result.get("results", {}).values():
        "✅" if result.get("status") == "success" else "❌"


    demo_orchestrator.share_data("global_config", {"theme": "dark", "language": "en"}, ttl=300)
    demo_orchestrator.share_data("user_session", {"user_id": "user_123", "role": "admin"})


    await demo_orchestrator.broadcast_to_agents(
        {"type": "system_announcement", "message": "Maintenance window scheduled"},
        agent_names=["auth_agent", "notification_agent"],
    )


    health = await demo_orchestrator.get_orchestrator_health()

    for agent_health in health["agent_health"].values():
        agent_health["status"]
        agent_health["metrics"]


    all_metrics = demo_orchestrator.get_agent_metrics()
    for _metrics in all_metrics.values():
        pass



    priority_tasks = [
        ("CRITICAL: Security scan", ExecutionPriority.CRITICAL, ["authentication"]),
        ("HIGH: Data backup", ExecutionPriority.HIGH, ["data_processing"]),
        ("MEDIUM: Generate report", ExecutionPriority.MEDIUM, ["analytics"]),
        ("LOW: Send notifications", ExecutionPriority.LOW, ["notifications"]),
    ]

    for task_name, priority, capabilities in priority_tasks:
        result = await demo_orchestrator.execute_task(
            task_type=task_name, parameters={"task": task_name}, required_capabilities=capabilities, priority=priority
        )
        "✅" if result.get("status") == "completed" else "❌"


    await demo_orchestrator.get_orchestrator_health()



# Global orchestrator instance with video generation capabilities
orchestrator = AgentOrchestrator()


# ============================================================================
# MAIN - Run demonstration when executed directly
# ============================================================================

if __name__ == "__main__":
    import sys


    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        asyncio.run(run_orchestrator_demonstration())
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        logger.error(f"Demonstration error: {e}", exc_info=True)
        sys.exit(1)
