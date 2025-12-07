import asyncio
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
from typing import Any

from agent.base_agent import BaseAgent
from agent.content_generator import ContentGeneratorAgent
from agent.ecommerce.analytics_engine import EcommerceAnalyticsEngine
from agent.ecommerce.order_automation import OrderAutomationAgent
from agent.ml_models.forecasting_engine import ForecastingEngine


"""
Enhanced Agent Manager - Enterprise Grade
Advanced agent orchestration with circuit breakers, monitoring, and performance optimization
"""


logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status"""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CIRCUIT_OPEN = "circuit_open"


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker for agent reliability"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED

    def can_execute(self) -> bool:
        """Check if execution is allowed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time and datetime.now() - self.last_failure_time > timedelta(
                seconds=self.recovery_timeout
            ):
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self):
        """Record successful execution"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def record_failure(self):
        """Record failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class AgentMetrics:
    """Agent performance metrics"""

    def __init__(self):
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_execution_time = 0.0
        self.last_execution_time = None
        self.execution_history = deque(maxlen=100)

    def record_execution(self, duration: float, success: bool):
        """Record execution metrics"""
        self.execution_count += 1
        self.total_execution_time += duration
        self.last_execution_time = datetime.now()

        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

        self.execution_history.append(
            {
                "timestamp": self.last_execution_time,
                "duration": duration,
                "success": success,
            }
        )

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count

    @property
    def average_execution_time(self) -> float:
        """Calculate average execution time"""
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_time / self.execution_count


class EnhancedAgentManager:
    """Enhanced agent manager with enterprise features"""

    def __init__(self):
        self.agents: dict[str, BaseAgent] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.metrics: dict[str, AgentMetrics] = {}
        self.active_executions: dict[str, dict] = {}
        self.agent_registry = {
            "content_generator": ContentGeneratorAgent,
            "ecommerce_analytics": EcommerceAnalyticsEngine,
            "order_automation": OrderAutomationAgent,
            "forecasting": ForecastingEngine,
        }

        # Performance monitoring
        self.performance_thresholds = {
            "max_execution_time": 300,  # 5 minutes
            "min_success_rate": 0.95,  # 95%
            "max_concurrent_executions": 10,
        }

        logger.info("Enhanced Agent Manager initialized")

    def register_agent(self, agent_type: str, agent_class: type):
        """Register a new agent type"""
        self.agent_registry[agent_type] = agent_class
        logger.info(f"Registered agent type: {agent_type}")

    def get_or_create_agent(self, agent_type: str) -> BaseAgent:
        """Get existing agent or create new one"""
        if agent_type not in self.agents:
            if agent_type not in self.agent_registry:
                raise ValueError(f"Unknown agent type: {agent_type}")

            agent_class = self.agent_registry[agent_type]
            self.agents[agent_type] = agent_class()
            self.circuit_breakers[agent_type] = CircuitBreaker()
            self.metrics[agent_type] = AgentMetrics()

            logger.info(f"Created new agent: {agent_type}")

        return self.agents[agent_type]

    async def execute_agent(self, agent_type: str, task_data: dict[str, Any], timeout: int = 300) -> dict[str, Any]:
        """Execute agent with enhanced error handling and monitoring"""
        execution_id = f"{agent_type}_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            # Check circuit breaker
            circuit_breaker = self.circuit_breakers.get(agent_type)
            if circuit_breaker and not circuit_breaker.can_execute():
                logger.warning(f"Circuit breaker open for agent: {agent_type}")
                return {
                    "success": False,
                    "error": "Circuit breaker open",
                    "status": AgentStatus.CIRCUIT_OPEN.value,
                    "execution_id": execution_id,
                }

            # Check concurrent execution limit
            if len(self.active_executions) >= self.performance_thresholds["max_concurrent_executions"]:
                logger.warning("Maximum concurrent executions reached")
                return {
                    "success": False,
                    "error": "Maximum concurrent executions reached",
                    "status": AgentStatus.FAILED.value,
                    "execution_id": execution_id,
                }

            # Record active execution
            self.active_executions[execution_id] = {
                "agent_type": agent_type,
                "start_time": start_time,
                "task_data": task_data,
            }

            # Get agent
            agent = self.get_or_create_agent(agent_type)

            # Execute with timeout
            try:
                result = await asyncio.wait_for(agent.execute(task_data), timeout=timeout)

                # Record success
                execution_time = time.time() - start_time
                self.metrics[agent_type].record_execution(execution_time, True)
                if circuit_breaker:
                    circuit_breaker.record_success()

                logger.info(f"Agent {agent_type} executed successfully in {execution_time:.2f}s")

                return {
                    "success": True,
                    "result": result,
                    "status": AgentStatus.COMPLETED.value,
                    "execution_id": execution_id,
                    "execution_time": execution_time,
                }

            except TimeoutError:
                logger.error(f"Agent {agent_type} execution timeout after {timeout}s")
                execution_time = time.time() - start_time
                self.metrics[agent_type].record_execution(execution_time, False)
                if circuit_breaker:
                    circuit_breaker.record_failure()

                return {
                    "success": False,
                    "error": f"Execution timeout after {timeout}s",
                    "status": AgentStatus.TIMEOUT.value,
                    "execution_id": execution_id,
                    "execution_time": execution_time,
                }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Agent {agent_type} execution failed: {e!s}")

            # Record failure
            if agent_type in self.metrics:
                self.metrics[agent_type].record_execution(execution_time, False)
            if circuit_breaker:
                circuit_breaker.record_failure()

            return {
                "success": False,
                "error": str(e),
                "status": AgentStatus.FAILED.value,
                "execution_id": execution_id,
                "execution_time": execution_time,
            }

        finally:
            # Clean up active execution
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]

    def get_agent_metrics(self, agent_type: str) -> dict[str, Any]:
        """Get agent performance metrics"""
        if agent_type not in self.metrics:
            return {"error": f"No metrics available for agent: {agent_type}"}

        metrics = self.metrics[agent_type]
        circuit_breaker = self.circuit_breakers.get(agent_type)

        return {
            "agent_type": agent_type,
            "execution_count": metrics.execution_count,
            "success_count": metrics.success_count,
            "failure_count": metrics.failure_count,
            "success_rate": metrics.success_rate,
            "average_execution_time": metrics.average_execution_time,
            "last_execution_time": (metrics.last_execution_time.isoformat() if metrics.last_execution_time else None),
            "circuit_breaker_state": (circuit_breaker.state.value if circuit_breaker else None),
            "recent_executions": len(metrics.execution_history),
        }

    def get_system_health(self) -> dict[str, Any]:
        """Get overall system health"""
        total_agents = len(self.agents)
        active_executions = len(self.active_executions)

        # Calculate overall metrics
        total_executions = sum(m.execution_count for m in self.metrics.values())
        total_successes = sum(m.success_count for m in self.metrics.values())
        overall_success_rate = total_successes / total_executions if total_executions > 0 else 0

        # Check circuit breaker states
        open_circuits = sum(1 for cb in self.circuit_breakers.values() if cb.state == CircuitBreakerState.OPEN)

        return {
            "timestamp": datetime.now().isoformat(),
            "total_agents": total_agents,
            "active_executions": active_executions,
            "total_executions": total_executions,
            "overall_success_rate": overall_success_rate,
            "open_circuit_breakers": open_circuits,
            "system_status": ("healthy" if open_circuits == 0 and overall_success_rate > 0.9 else "degraded"),
        }

    def list_available_agents(self) -> list[str]:
        """List all available agent types"""
        return list(self.agent_registry.keys())


# Global instance
enhanced_agent_manager = EnhancedAgentManager()
