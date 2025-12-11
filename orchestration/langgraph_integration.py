"""
DevSkyy LangGraph Integration
=============================

Multi-agent workflow orchestration using LangGraph patterns.

Features:
- Agent nodes for specialized tasks
- Conditional routing
- State management
- Workflow persistence
- Error handling and recovery

References:
- LangGraph: https://langchain-ai.github.io/langgraph/
- State Machines: https://en.wikipedia.org/wiki/Finite-state_machine
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Type variable for state
S = TypeVar("S", bound="WorkflowState")


# =============================================================================
# Enums
# =============================================================================


class NodeType(str, Enum):
    """Node types in workflow"""

    AGENT = "agent"
    TOOL = "tool"
    ROUTER = "router"
    AGGREGATOR = "aggregator"
    CHECKPOINT = "checkpoint"
    END = "end"


class EdgeType(str, Enum):
    """Edge types"""

    SEQUENTIAL = "sequential"
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"


class WorkflowStatus(str, Enum):
    """Workflow execution status"""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# State Management
# =============================================================================


class WorkflowState(BaseModel):
    """
    Base workflow state.

    All workflow state classes should inherit from this.
    """

    # Core state
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_node: str | None = None

    # Execution tracking
    started_at: str | None = None
    completed_at: str | None = None
    node_history: list[str] = []

    # Data passing
    inputs: dict[str, Any] = {}
    outputs: dict[str, Any] = {}
    context: dict[str, Any] = {}

    # Error handling
    errors: list[dict[str, Any]] = []
    retry_count: int = 0
    max_retries: int = 3

    # Messages for agent communication
    messages: list[dict[str, Any]] = []

    def add_message(self, role: str, content: str, metadata: dict = None):
        """Add message to state"""
        self.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": metadata or {},
            }
        )

    def get_last_output(self, node_name: str = None) -> Any:
        """Get output from last or specific node"""
        if node_name and node_name in self.outputs:
            return self.outputs[node_name]
        # Return last output
        if self.node_history:
            last_node = self.node_history[-1]
            return self.outputs.get(last_node)
        return None

    def record_error(self, node: str, error: str, details: dict = None):
        """Record error in state"""
        self.errors.append(
            {
                "node": node,
                "error": error,
                "details": details or {},
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

    def to_checkpoint(self) -> dict[str, Any]:
        """Create checkpoint for persistence"""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "current_node": self.current_node,
            "node_history": self.node_history,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "context": self.context,
            "errors": self.errors,
            "messages": self.messages,
            "checkpoint_time": datetime.now(UTC).isoformat(),
        }

    @classmethod
    def from_checkpoint(cls, data: dict[str, Any]) -> "WorkflowState":
        """Restore from checkpoint"""
        data["status"] = WorkflowStatus(data.get("status", "pending"))
        return cls(**data)


class SkyyRoseWorkflowState(WorkflowState):
    """SkyyRose-specific workflow state"""

    # Product context
    product_id: int | None = None
    product_name: str | None = None
    collection: str | None = None

    # Asset tracking
    images: list[str] = []
    model_3d: str | None = None
    tryon_images: list[str] = []

    # Content
    description: str | None = None
    social_posts: dict[str, str] = {}

    # Analytics
    pricing_recommendation: float | None = None
    demand_forecast: dict[str, Any] | None = None


# =============================================================================
# Node Definitions
# =============================================================================


class AgentNode(ABC):
    """
    Base class for workflow agent nodes.

    Each node processes state and returns updated state.
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        timeout: float = 30.0,
    ):
        self.name = name
        self.description = description
        self.timeout = timeout
        self.node_type = NodeType.AGENT

    @abstractmethod
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute node and return updated state"""
        pass

    async def run(self, state: WorkflowState) -> WorkflowState:
        """Run node with error handling"""
        try:
            state.current_node = self.name
            state.node_history.append(self.name)

            # Execute with timeout
            result = await asyncio.wait_for(self.execute(state), timeout=self.timeout)

            return result

        except TimeoutError:
            state.record_error(self.name, "Timeout exceeded")
            raise
        except Exception as e:
            state.record_error(self.name, str(e))
            raise


class ToolNode(AgentNode):
    """Node that executes a specific tool"""

    def __init__(
        self,
        name: str,
        tool_name: str,
        tool_params: dict[str, Any] = None,
        description: str = "",
    ):
        super().__init__(name, description)
        self.tool_name = tool_name
        self.tool_params = tool_params or {}
        self.node_type = NodeType.TOOL

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute tool and store result"""
        # Get params from state context if needed
        params = {**self.tool_params}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to state variable
                state_key = value[1:]
                if state_key in state.context:
                    params[key] = state.context[state_key]

        # Here you would call the actual tool
        # For now, we'll simulate
        result = {
            "tool": self.tool_name,
            "params": params,
            "status": "success",
        }

        state.outputs[self.name] = result
        return state


class RouterNode(AgentNode):
    """Node that routes to different paths based on conditions"""

    def __init__(
        self,
        name: str,
        routes: dict[str, Callable[[WorkflowState], bool]],
        default_route: str = None,
    ):
        super().__init__(name, "Router node")
        self.routes = routes
        self.default_route = default_route
        self.node_type = NodeType.ROUTER

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Determine next route"""
        for route_name, condition in self.routes.items():
            try:
                if condition(state):
                    state.context["_next_node"] = route_name
                    return state
            except Exception as e:
                logger.warning(f"Route condition error: {e}")

        if self.default_route:
            state.context["_next_node"] = self.default_route

        return state


class AggregatorNode(AgentNode):
    """Node that aggregates results from parallel branches"""

    def __init__(
        self,
        name: str,
        source_nodes: list[str],
        aggregation_fn: Callable[[list[Any]], Any] = None,
    ):
        super().__init__(name, "Aggregator node")
        self.source_nodes = source_nodes
        self.aggregation_fn = aggregation_fn or self._default_aggregate
        self.node_type = NodeType.AGGREGATOR

    def _default_aggregate(self, results: list[Any]) -> dict[str, Any]:
        """Default aggregation: combine into dict"""
        return {"aggregated": results}

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Aggregate outputs from source nodes"""
        results = []
        for node_name in self.source_nodes:
            if node_name in state.outputs:
                results.append(state.outputs[node_name])

        aggregated = self.aggregation_fn(results)
        state.outputs[self.name] = aggregated

        return state


# =============================================================================
# Edge Definitions
# =============================================================================


class WorkflowEdge(BaseModel):
    """Edge connecting two nodes"""

    source: str
    target: str
    edge_type: EdgeType = EdgeType.SEQUENTIAL
    condition: str | None = None  # For conditional edges

    def __hash__(self):
        return hash((self.source, self.target))


class ConditionalEdge(WorkflowEdge):
    """Conditional edge with routing logic"""

    edge_type: EdgeType = EdgeType.CONDITIONAL
    conditions: dict[str, str] = {}  # target -> condition expression
    default_target: str | None = None


# =============================================================================
# Workflow Graph
# =============================================================================


class WorkflowGraph:
    """
    Directed graph representing workflow structure.

    Usage:
        graph = WorkflowGraph()

        graph.add_node(ContentAgent("generate_content"))
        graph.add_node(ImageAgent("generate_images"))
        graph.add_node(UploadAgent("upload_assets"))

        graph.add_edge("generate_content", "generate_images")
        graph.add_edge("generate_images", "upload_assets")

        graph.set_entry_point("generate_content")
        graph.set_finish_point("upload_assets")
    """

    def __init__(self, name: str = "workflow"):
        self.name = name
        self.nodes: dict[str, AgentNode] = {}
        self.edges: list[WorkflowEdge] = []
        self.entry_point: str | None = None
        self.finish_points: list[str] = []

    def add_node(self, node: AgentNode):
        """Add node to graph"""
        self.nodes[node.name] = node
        logger.debug(f"Added node: {node.name}")

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: EdgeType = EdgeType.SEQUENTIAL,
        condition: str = None,
    ):
        """Add edge between nodes"""
        edge = WorkflowEdge(
            source=source,
            target=target,
            edge_type=edge_type,
            condition=condition,
        )
        self.edges.append(edge)
        logger.debug(f"Added edge: {source} -> {target}")

    def add_conditional_edge(
        self,
        source: str,
        conditions: dict[str, str],
        default: str = None,
    ):
        """Add conditional routing edge"""
        edge = ConditionalEdge(
            source=source,
            target=default or list(conditions.keys())[0],
            conditions=conditions,
            default_target=default,
        )
        self.edges.append(edge)

    def set_entry_point(self, node_name: str):
        """Set workflow entry point"""
        if node_name not in self.nodes:
            raise ValueError(f"Unknown node: {node_name}")
        self.entry_point = node_name

    def set_finish_point(self, node_name: str):
        """Add finish point"""
        if node_name not in self.nodes:
            raise ValueError(f"Unknown node: {node_name}")
        if node_name not in self.finish_points:
            self.finish_points.append(node_name)

    def get_next_nodes(self, current: str) -> list[str]:
        """Get nodes that follow current node"""
        next_nodes = []
        for edge in self.edges:
            if edge.source == current:
                next_nodes.append(edge.target)
        return next_nodes

    def validate(self) -> tuple[bool, list[str]]:
        """Validate graph structure"""
        errors = []

        if not self.entry_point:
            errors.append("No entry point defined")

        if not self.finish_points:
            errors.append("No finish points defined")

        # Check all edge references
        for edge in self.edges:
            if edge.source not in self.nodes:
                errors.append(f"Edge source not found: {edge.source}")
            if edge.target not in self.nodes:
                errors.append(f"Edge target not found: {edge.target}")

        # Check for orphan nodes
        connected = {self.entry_point}
        for edge in self.edges:
            connected.add(edge.source)
            connected.add(edge.target)

        orphans = set(self.nodes.keys()) - connected
        for orphan in orphans:
            errors.append(f"Orphan node: {orphan}")

        return len(errors) == 0, errors

    def to_dict(self) -> dict[str, Any]:
        """Export graph structure"""
        return {
            "name": self.name,
            "nodes": list(self.nodes.keys()),
            "edges": [e.dict() for e in self.edges],
            "entry_point": self.entry_point,
            "finish_points": self.finish_points,
        }


# =============================================================================
# Workflow Manager
# =============================================================================


class WorkflowManager:
    """
    Main workflow execution manager.

    Usage:
        manager = WorkflowManager()

        # Create workflow
        workflow = manager.create_workflow("product_launch")

        # Add nodes
        workflow.add_node(ContentGenerationNode())
        workflow.add_node(ImageGenerationNode())
        workflow.add_node(UploadNode())

        # Connect nodes
        workflow.add_edge("content", "images")
        workflow.add_edge("images", "upload")

        workflow.set_entry_point("content")
        workflow.set_finish_point("upload")

        # Execute
        state = SkyyRoseWorkflowState(
            product_name="Heart aRose Bomber",
            collection="BLACK_ROSE"
        )
        result = await manager.execute(workflow, state)
    """

    def __init__(self, checkpoint_dir: str = None):
        self.workflows: dict[str, WorkflowGraph] = {}
        self.checkpoint_dir = checkpoint_dir
        self._running: dict[str, asyncio.Task] = {}

    def create_workflow(self, name: str) -> WorkflowGraph:
        """Create new workflow"""
        workflow = WorkflowGraph(name)
        self.workflows[name] = workflow
        return workflow

    def get_workflow(self, name: str) -> WorkflowGraph | None:
        """Get workflow by name"""
        return self.workflows.get(name)

    async def execute(
        self,
        workflow: WorkflowGraph,
        initial_state: WorkflowState,
        resume_from: str = None,
    ) -> WorkflowState:
        """
        Execute workflow.

        Args:
            workflow: Workflow graph to execute
            initial_state: Initial state
            resume_from: Optional node to resume from

        Returns:
            Final state after execution
        """
        # Validate workflow
        is_valid, errors = workflow.validate()
        if not is_valid:
            raise ValueError(f"Invalid workflow: {errors}")

        state = initial_state
        state.status = WorkflowStatus.RUNNING
        state.started_at = datetime.now(UTC).isoformat()

        # Determine starting point
        current_node = resume_from or workflow.entry_point

        try:
            while current_node:
                logger.info(f"Executing node: {current_node}")

                node = workflow.nodes.get(current_node)
                if not node:
                    raise ValueError(f"Node not found: {current_node}")

                # Execute node
                state = await node.run(state)

                # Check if finished
                if current_node in workflow.finish_points:
                    logger.info(f"Reached finish point: {current_node}")
                    break

                # Get next node
                next_nodes = workflow.get_next_nodes(current_node)

                if not next_nodes:
                    logger.warning(f"No next nodes from: {current_node}")
                    break

                # Handle routing
                if "_next_node" in state.context:
                    current_node = state.context.pop("_next_node")
                elif len(next_nodes) == 1:
                    current_node = next_nodes[0]
                else:
                    # Default to first for now
                    current_node = next_nodes[0]

                # Save checkpoint if configured
                if self.checkpoint_dir:
                    await self._save_checkpoint(state)

            state.status = WorkflowStatus.COMPLETED
            state.completed_at = datetime.now(UTC).isoformat()

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            state.status = WorkflowStatus.FAILED
            state.record_error("workflow", str(e))
            raise

        return state

    async def execute_parallel(
        self,
        workflow: WorkflowGraph,
        states: list[WorkflowState],
        max_concurrency: int = 5,
    ) -> list[WorkflowState]:
        """Execute workflow with multiple states in parallel"""
        semaphore = asyncio.Semaphore(max_concurrency)

        async def run_with_limit(state: WorkflowState) -> WorkflowState:
            async with semaphore:
                return await self.execute(workflow, state)

        tasks = [run_with_limit(s) for s in states]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def _save_checkpoint(self, state: WorkflowState):
        """Save state checkpoint"""
        if not self.checkpoint_dir:
            return

        from pathlib import Path

        import aiofiles

        checkpoint_path = Path(self.checkpoint_dir) / f"{state.workflow_id}.json"
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(checkpoint_path, "w") as f:
            await f.write(json.dumps(state.to_checkpoint(), indent=2))

    async def resume(
        self,
        workflow_name: str,
        workflow_id: str,
    ) -> WorkflowState:
        """Resume workflow from checkpoint"""
        from pathlib import Path

        import aiofiles

        if not self.checkpoint_dir:
            raise ValueError("Checkpoint directory not configured")

        checkpoint_path = Path(self.checkpoint_dir) / f"{workflow_id}.json"

        async with aiofiles.open(checkpoint_path) as f:
            data = json.loads(await f.read())

        state = WorkflowState.from_checkpoint(data)
        workflow = self.get_workflow(workflow_name)

        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_name}")

        # Resume from last node
        resume_from = state.current_node
        return await self.execute(workflow, state, resume_from=resume_from)

    def cancel(self, workflow_id: str):
        """Cancel running workflow"""
        if workflow_id in self._running:
            self._running[workflow_id].cancel()


# =============================================================================
# Pre-built SkyyRose Workflows
# =============================================================================


def create_product_launch_workflow() -> WorkflowGraph:
    """
    Create product launch workflow.

    Nodes:
    1. generate_content - Create product description
    2. generate_images - Create product images
    3. generate_3d - Create 3D model
    4. review - Human review checkpoint
    5. upload - Upload to WordPress
    6. publish - Publish product
    """
    workflow = WorkflowGraph("product_launch")

    # Content generation node
    class ContentNode(AgentNode):
        async def execute(self, state: WorkflowState) -> WorkflowState:
            # Generate description based on product info
            product_name = state.context.get("product_name", "Product")
            collection = state.context.get("collection", "SIGNATURE")

            # Simulated content generation
            description = f"Introducing {product_name} from the {collection} collection. Where Love Meets Luxury."

            state.outputs[self.name] = {"description": description}
            state.add_message("assistant", f"Generated content for {product_name}")

            return state

    # Image generation node
    class ImageNode(AgentNode):
        async def execute(self, state: WorkflowState) -> WorkflowState:
            product_name = state.context.get("product_name", "Product")

            # Simulated image generation
            state.outputs[self.name] = {
                "images": [f"/images/{product_name.lower().replace(' ', '_')}_1.jpg"],
            }
            state.add_message("assistant", "Generated product images")

            return state

    # Upload node
    class UploadNode(AgentNode):
        async def execute(self, state: WorkflowState) -> WorkflowState:
            content = state.outputs.get("generate_content", {})
            images = state.outputs.get("generate_images", {})

            state.outputs[self.name] = {
                "uploaded": True,
                "content": content,
                "images": images,
            }
            state.add_message("assistant", "Uploaded assets to WordPress")

            return state

    # Add nodes
    workflow.add_node(ContentNode("generate_content", "Generate product content"))
    workflow.add_node(ImageNode("generate_images", "Generate product images"))
    workflow.add_node(UploadNode("upload", "Upload to WordPress"))

    # Add edges
    workflow.add_edge("generate_content", "generate_images")
    workflow.add_edge("generate_images", "upload")

    # Set entry/exit
    workflow.set_entry_point("generate_content")
    workflow.set_finish_point("upload")

    return workflow


def create_customer_support_workflow() -> WorkflowGraph:
    """
    Create customer support workflow.

    Routes based on inquiry type:
    - Order inquiry -> check_order -> respond
    - Product inquiry -> search_products -> respond
    - Complaint -> escalate -> respond
    """
    workflow = WorkflowGraph("customer_support")

    class ClassifyNode(AgentNode):
        async def execute(self, state: WorkflowState) -> WorkflowState:
            message = state.context.get("message", "")

            # Simple classification
            if "order" in message.lower():
                intent = "order"
            elif "product" in message.lower() or "item" in message.lower():
                intent = "product"
            elif "complaint" in message.lower() or "issue" in message.lower():
                intent = "complaint"
            else:
                intent = "general"

            state.outputs[self.name] = {"intent": intent}
            state.context["intent"] = intent

            return state

    class RouterNodeImpl(AgentNode):
        async def execute(self, state: WorkflowState) -> WorkflowState:
            intent = state.context.get("intent", "general")

            route_map = {
                "order": "check_order",
                "product": "search_products",
                "complaint": "escalate",
                "general": "respond",
            }

            state.context["_next_node"] = route_map.get(intent, "respond")
            return state

    class CheckOrderNode(AgentNode):
        async def execute(self, state: WorkflowState) -> WorkflowState:
            state.outputs[self.name] = {"order_status": "Processing"}
            return state

    class SearchProductsNode(AgentNode):
        async def execute(self, state: WorkflowState) -> WorkflowState:
            state.outputs[self.name] = {"products": ["Heart aRose Bomber"]}
            return state

    class EscalateNode(AgentNode):
        async def execute(self, state: WorkflowState) -> WorkflowState:
            state.outputs[self.name] = {"escalated": True, "ticket_id": "TKT-001"}
            return state

    class RespondNode(AgentNode):
        async def execute(self, state: WorkflowState) -> WorkflowState:
            intent = state.context.get("intent", "general")

            responses = {
                "order": "Your order is currently processing.",
                "product": "Here are some products that might interest you.",
                "complaint": "We've escalated your issue to our team.",
                "general": "How can I help you today?",
            }

            state.outputs[self.name] = {
                "response": responses.get(intent, "Thank you for contacting SkyyRose.")
            }
            return state

    # Add nodes
    workflow.add_node(ClassifyNode("classify", "Classify inquiry"))
    workflow.add_node(RouterNodeImpl("router", "Route to handler"))
    workflow.add_node(CheckOrderNode("check_order", "Check order status"))
    workflow.add_node(SearchProductsNode("search_products", "Search products"))
    workflow.add_node(EscalateNode("escalate", "Escalate complaint"))
    workflow.add_node(RespondNode("respond", "Generate response"))

    # Add edges
    workflow.add_edge("classify", "router")
    workflow.add_edge("router", "check_order")
    workflow.add_edge("router", "search_products")
    workflow.add_edge("router", "escalate")
    workflow.add_edge("router", "respond")
    workflow.add_edge("check_order", "respond")
    workflow.add_edge("search_products", "respond")
    workflow.add_edge("escalate", "respond")

    # Set entry/exit
    workflow.set_entry_point("classify")
    workflow.set_finish_point("respond")

    return workflow
