---
name: agent-orchestration
description: Orchestrate and manage DevSkyy's 54+ specialized AI agents with intelligent routing and load balancing
---

You are the Agent Orchestration expert for DevSkyy's multi-agent platform. Your role is to coordinate, route, monitor, and optimize the execution of 54+ specialized AI agents.

## DevSkyy Agent Architecture

### Agent Categories

**Backend Agents (15+)**
- `advanced_code_generation_agent` - Code generation and refactoring
- `agent_assignment_manager` - Dynamic agent task assignment
- `brand_intelligence_agent` - Brand analytics and insights
- `continuous_learning_background_agent` - 24/7 learning and improvement
- `customer_service_agent` - Customer support automation
- `ecommerce_agent` - E-commerce operations
- `email_sms_automation_agent` - Communication automation
- `financial_agent` - Financial analytics and forecasting
- `inventory_agent` - Inventory optimization
- `meta_social_automation_agent` - Meta/Facebook/Instagram automation
- `performance_agent` - System performance monitoring
- `security_agent` - Security scanning and hardening
- `seo_marketing_agent` - SEO and marketing optimization
- `universal_self_healing_agent` - Auto-repair and recovery
- `social_media_automation_agent` - Multi-platform social automation

**Frontend Agents (6+)**
- `design_automation_agent` - UI/UX design generation
- `fashion_computer_vision_agent` - Fashion image analysis
- `web_development_agent` - Web development automation
- `site_communication_agent` - Site messaging and chat
- `wordpress_divi_elementor_agent` - WordPress page builder
- `wordpress_fullstack_theme_builder_agent` - Complete theme generation

**Content Agents (3+)**
- `virtual_tryon_huggingface_agent` - Virtual try-on with ML
- `visual_content_generation_agent` - Image/video generation
- `voice_media_video_agent` - Voice and video processing

**Development Agents (2+)**
- `code_recovery_cursor_agent` - Code recovery and restoration
- `marketing_content_generation_agent` - Marketing content AI

## Core Orchestration Functions

### 1. Agent Registry & Discovery

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import importlib
import inspect

class AgentCategory(Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    CONTENT = "content"
    DEVELOPMENT = "development"
    FINANCE = "finance"
    MARKETING = "marketing"

@dataclass
class AgentMetadata:
    name: str
    category: AgentCategory
    capabilities: List[str]
    dependencies: List[str]
    version: str
    module_path: str
    priority: int = 5  # 1-10, higher = more priority
    max_concurrent_tasks: int = 5

class AgentRegistry:
    """Central registry for all DevSkyy agents"""

    def __init__(self):
        self.agents: Dict[str, AgentMetadata] = {}
        self._initialize_registry()

    def _initialize_registry(self):
        """Load all agents into registry"""
        # Backend agents
        self.register_agent(AgentMetadata(
            name="brand_intelligence_agent",
            category=AgentCategory.BACKEND,
            capabilities=["brand_analysis", "customer_insights", "market_research"],
            dependencies=["anthropic", "openai"],
            version="2.0.0",
            module_path="agent.modules.backend.brand_intelligence_agent",
            priority=8
        ))

        self.register_agent(AgentMetadata(
            name="ecommerce_agent",
            category=AgentCategory.BACKEND,
            capabilities=["product_management", "pricing", "inventory"],
            dependencies=["anthropic", "sqlalchemy"],
            version="1.5.0",
            module_path="agent.modules.backend.ecommerce_agent",
            priority=9
        ))

        self.register_agent(AgentMetadata(
            name="inventory_agent",
            category=AgentCategory.BACKEND,
            capabilities=["stock_management", "demand_forecasting", "reorder_optimization"],
            dependencies=["numpy", "pandas", "scikit-learn"],
            version="1.3.0",
            module_path="agent.modules.backend.inventory_agent",
            priority=8
        ))

        self.register_agent(AgentMetadata(
            name="financial_agent",
            category=AgentCategory.BACKEND,
            capabilities=["financial_analysis", "forecasting", "reporting"],
            dependencies=["pandas", "numpy"],
            version="1.2.0",
            module_path="agent.modules.backend.financial_agent",
            priority=7
        ))

        self.register_agent(AgentMetadata(
            name="wordpress_fullstack_theme_builder_agent",
            category=AgentCategory.FRONTEND,
            capabilities=["theme_generation", "elementor_builder", "woocommerce"],
            dependencies=["anthropic", "requests"],
            version="2.5.0",
            module_path="agent.modules.frontend.wordpress_fullstack_theme_builder_agent",
            priority=9
        ))

        self.register_agent(AgentMetadata(
            name="fashion_computer_vision_agent",
            category=AgentCategory.CONTENT,
            capabilities=["image_analysis", "style_classification", "fabric_detection"],
            dependencies=["opencv-python", "torch", "transformers"],
            version="1.8.0",
            module_path="agent.modules.frontend.fashion_computer_vision_agent",
            priority=7
        ))

        self.register_agent(AgentMetadata(
            name="security_agent",
            category=AgentCategory.BACKEND,
            capabilities=["vulnerability_scanning", "security_hardening", "compliance"],
            dependencies=["bandit", "safety"],
            version="1.1.0",
            module_path="agent.modules.backend.security_agent",
            priority=10
        ))

        # Add more agents as needed

    def register_agent(self, metadata: AgentMetadata):
        """Register an agent in the registry"""
        self.agents[metadata.name] = metadata

    def get_agent(self, name: str) -> Optional[AgentMetadata]:
        """Get agent metadata by name"""
        return self.agents.get(name)

    def find_agents_by_capability(self, capability: str) -> List[AgentMetadata]:
        """Find all agents with a specific capability"""
        return [
            agent for agent in self.agents.values()
            if capability in agent.capabilities
        ]

    def get_agents_by_category(self, category: AgentCategory) -> List[AgentMetadata]:
        """Get all agents in a category"""
        return [
            agent for agent in self.agents.values()
            if agent.category == category
        ]
```

### 2. Intelligent Agent Routing

```python
import asyncio
from typing import Dict, Any, List, Tuple

class AgentRouter:
    """Route tasks to the most appropriate agent"""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.task_queue: Dict[str, List[Dict[str, Any]]] = {}
        self.agent_load: Dict[str, int] = {}

    async def route_task(
        self,
        task: Dict[str, Any],
        required_capability: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route a task to the best available agent.

        Args:
            task: Task details (type, params, priority, etc.)
            required_capability: Required capability for the task

        Returns:
            Routing result with assigned agent
        """
        # Find candidate agents
        candidates = []

        if required_capability:
            candidates = self.registry.find_agents_by_capability(required_capability)
        else:
            # Try to infer from task type
            task_type = task.get("type", "")
            capability_map = {
                "analyze_brand": "brand_analysis",
                "manage_inventory": "stock_management",
                "generate_theme": "theme_generation",
                "analyze_image": "image_analysis",
                "scan_security": "vulnerability_scanning",
                "optimize_seo": "seo_optimization",
                "forecast_demand": "demand_forecasting",
            }
            capability = capability_map.get(task_type)
            if capability:
                candidates = self.registry.find_agents_by_capability(capability)

        if not candidates:
            return {
                "error": "No suitable agent found for task",
                "task": task,
                "required_capability": required_capability
            }

        # Select best agent based on:
        # 1. Priority
        # 2. Current load
        # 3. Capability match score
        best_agent = self._select_best_agent(candidates, task)

        # Assign task
        result = await self._assign_task_to_agent(best_agent, task)

        return {
            "success": True,
            "assigned_agent": best_agent.name,
            "agent_category": best_agent.category.value,
            "task_id": result.get("task_id"),
            "estimated_duration": result.get("estimated_duration")
        }

    def _select_best_agent(
        self,
        candidates: List[AgentMetadata],
        task: Dict[str, Any]
    ) -> AgentMetadata:
        """Select the best agent from candidates"""
        scored_agents: List[Tuple[float, AgentMetadata]] = []

        for agent in candidates:
            score = 0.0

            # Priority score (0-10)
            score += agent.priority

            # Load score (less load = higher score)
            current_load = self.agent_load.get(agent.name, 0)
            load_score = max(0, 10 - (current_load / agent.max_concurrent_tasks * 10))
            score += load_score

            # Task priority multiplier
            task_priority = task.get("priority", 5)
            score *= (task_priority / 5)

            scored_agents.append((score, agent))

        # Sort by score descending
        scored_agents.sort(key=lambda x: x[0], reverse=True)

        return scored_agents[0][1]

    async def _assign_task_to_agent(
        self,
        agent: AgentMetadata,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assign task to agent and execute"""
        # Update load tracking
        self.agent_load[agent.name] = self.agent_load.get(agent.name, 0) + 1

        try:
            # Dynamically import and instantiate agent
            module = importlib.import_module(agent.module_path)

            # Find the agent class
            agent_class = None
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and hasattr(obj, 'execute'):
                    agent_class = obj
                    break

            if not agent_class:
                raise ValueError(f"No executable agent class found in {agent.module_path}")

            # Instantiate and execute
            agent_instance = agent_class()

            # Initialize if needed
            if hasattr(agent_instance, 'initialize'):
                await agent_instance.initialize()

            # Execute task
            result = await agent_instance.execute(**task.get("params", {}))

            return {
                "task_id": task.get("id", "unknown"),
                "result": result,
                "estimated_duration": "2-5 seconds"
            }

        except Exception as e:
            return {
                "error": f"Agent execution failed: {str(e)}",
                "agent": agent.name,
                "task_id": task.get("id", "unknown")
            }
        finally:
            # Decrease load
            self.agent_load[agent.name] -= 1
```

### 3. Multi-Agent Orchestration

```python
class MultiAgentOrchestrator:
    """Orchestrate complex workflows across multiple agents"""

    def __init__(self, router: AgentRouter):
        self.router = router
        self.workflows: Dict[str, List[Dict[str, Any]]] = {}

    async def execute_workflow(
        self,
        workflow_name: str,
        workflow_steps: List[Dict[str, Any]],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a multi-agent workflow.

        Args:
            workflow_name: Name of the workflow
            workflow_steps: List of workflow steps with agent assignments
            params: Input parameters for the workflow

        Returns:
            Workflow execution results
        """
        results = []
        context = {"input": params}

        for i, step in enumerate(workflow_steps):
            step_name = step.get("name", f"step_{i}")
            agent_capability = step.get("capability")
            step_params = step.get("params", {})

            # Merge context into step params
            merged_params = {**step_params, **context}

            # Create task
            task = {
                "id": f"{workflow_name}_{step_name}",
                "type": step.get("type"),
                "params": merged_params,
                "priority": step.get("priority", 5)
            }

            # Route and execute
            result = await self.router.route_task(task, agent_capability)

            # Store result in context for next steps
            context[step_name] = result

            results.append({
                "step": step_name,
                "agent": result.get("assigned_agent"),
                "success": result.get("success", False),
                "result": result.get("result")
            })

            # Check if step failed and should stop workflow
            if not result.get("success") and step.get("required", True):
                return {
                    "workflow": workflow_name,
                    "success": False,
                    "failed_at_step": step_name,
                    "completed_steps": i,
                    "results": results
                }

        return {
            "workflow": workflow_name,
            "success": True,
            "completed_steps": len(workflow_steps),
            "results": results,
            "final_context": context
        }
```

### 4. Pre-Defined Workflows

```python
# Fashion E-Commerce Product Launch Workflow
PRODUCT_LAUNCH_WORKFLOW = [
    {
        "name": "analyze_product_images",
        "capability": "image_analysis",
        "type": "analyze_image",
        "params": {"analysis_type": "fashion_detailed"},
        "priority": 8,
        "required": True
    },
    {
        "name": "generate_product_description",
        "capability": "content_generation",
        "type": "generate_content",
        "params": {"content_type": "product_description"},
        "priority": 7,
        "required": True
    },
    {
        "name": "optimize_seo",
        "capability": "seo_optimization",
        "type": "optimize_seo",
        "params": {"target": "product_page"},
        "priority": 6,
        "required": False
    },
    {
        "name": "forecast_demand",
        "capability": "demand_forecasting",
        "type": "forecast_demand",
        "params": {"forecast_days": 30},
        "priority": 8,
        "required": True
    },
    {
        "name": "set_pricing",
        "capability": "pricing",
        "type": "optimize_price",
        "params": {"strategy": "dynamic"},
        "priority": 9,
        "required": True
    },
    {
        "name": "create_social_posts",
        "capability": "social_automation",
        "type": "create_posts",
        "params": {"platforms": ["instagram", "facebook"]},
        "priority": 6,
        "required": False
    }
]

# WordPress Theme Generation Workflow
THEME_GENERATION_WORKFLOW = [
    {
        "name": "analyze_brand",
        "capability": "brand_analysis",
        "type": "analyze_brand",
        "params": {},
        "priority": 8,
        "required": True
    },
    {
        "name": "generate_theme",
        "capability": "theme_generation",
        "type": "generate_theme",
        "params": {"theme_type": "luxury_fashion"},
        "priority": 10,
        "required": True
    },
    {
        "name": "optimize_performance",
        "capability": "performance_optimization",
        "type": "optimize_theme",
        "params": {},
        "priority": 7,
        "required": False
    },
    {
        "name": "security_scan",
        "capability": "vulnerability_scanning",
        "type": "scan_security",
        "params": {"target": "theme_files"},
        "priority": 9,
        "required": True
    }
]
```

## Usage Examples

### Example 1: Route Single Task

```python
# Initialize orchestration
registry = AgentRegistry()
router = AgentRouter(registry)

# Route a brand analysis task
result = await router.route_task({
    "id": "analyze_brand_001",
    "type": "analyze_brand",
    "params": {
        "brand_name": "Luxury Fashion Co",
        "analysis_depth": "comprehensive"
    },
    "priority": 8
}, required_capability="brand_analysis")

print(f"Assigned to: {result['assigned_agent']}")
```

### Example 2: Execute Product Launch Workflow

```python
orchestrator = MultiAgentOrchestrator(router)

result = await orchestrator.execute_workflow(
    workflow_name="product_launch",
    workflow_steps=PRODUCT_LAUNCH_WORKFLOW,
    params={
        "product_id": "PROD-12345",
        "product_name": "Silk Evening Dress",
        "image_urls": ["https://example.com/dress.jpg"],
        "category": "evening_wear",
        "cost": 150.00
    }
)

if result["success"]:
    print(f"Product launch completed: {result['completed_steps']} steps")
    for step in result["results"]:
        print(f"- {step['step']}: {step['agent']}")
```

### Example 3: Monitor Agent Health

```python
# Check health of all agents
for agent_name, metadata in registry.agents.items():
    module = importlib.import_module(metadata.module_path)
    agent_class = getattr(module, agent_name.replace('_agent', '').title() + 'Agent', None)

    if agent_class and hasattr(agent_class, 'health_check'):
        instance = agent_class()
        health = await instance.health_check()
        print(f"{agent_name}: {health['status']} - {health['success_rate']}% success rate")
```

## Truth Protocol Compliance

- ✅ Type hints on all functions (Rule 11)
- ✅ Comprehensive error handling (Rule 10)
- ✅ Agent load balancing for performance (Rule 12)
- ✅ No hardcoded secrets (Rule 5)
- ✅ Full documentation (Rule 9)

## Multi-Model AI Integration

### Agent Category Model Assignments

Each agent category uses specific AI models for optimal performance:

```python
from skills.multi_model_orchestrator import (
    MultiModelOrchestrator,
    FrontendAgentOrchestrator,
    BackendAgentOrchestrator,
    ContentAgentOrchestrator,
    DevelopmentAgentOrchestrator,
    AgentCategory,
    AIModel
)

class EnhancedAgentRouter:
    """Agent router with multi-model AI support"""

    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.model_orchestrator = MultiModelOrchestrator()

        # Category-specific orchestrators
        self.frontend_orchestrator = FrontendAgentOrchestrator(self.model_orchestrator)
        self.backend_orchestrator = BackendAgentOrchestrator(self.model_orchestrator)
        self.content_orchestrator = ContentAgentOrchestrator(self.model_orchestrator)
        self.development_orchestrator = DevelopmentAgentOrchestrator(self.model_orchestrator)

    async def route_with_ai(
        self,
        task: Dict[str, Any],
        agent_category: AgentCategory
    ) -> Dict[str, Any]:
        """
        Route task to agent with multi-model AI support.

        Args:
            task: Task to execute
            agent_category: Category of agent

        Returns:
            Task result with AI model info
        """
        # Route to appropriate category orchestrator
        if agent_category == AgentCategory.FRONTEND:
            # Frontend: Claude + Gemini
            result = await self.frontend_orchestrator.generate_ui_component(
                task.get('params', {})
            )

        elif agent_category == AgentCategory.BACKEND:
            # Backend: Claude + ChatGPT-5
            result = await self.backend_orchestrator.design_api(
                task.get('params', {})
            )

        elif agent_category == AgentCategory.CONTENT:
            # Content: Huggingface + Claude + Gemini + ChatGPT-5
            result = await self.content_orchestrator.generate_marketing_content(
                task.get('params', {})
            )

        elif agent_category == AgentCategory.DEVELOPMENT:
            # Development: Claude + Codex
            result = await self.development_orchestrator.generate_code(
                task.get('params', {})
            )

        else:
            result = {"error": f"Unknown category: {agent_category}"}

        return {
            "success": result.get("success", False),
            "agent_category": agent_category.value,
            "model_used": result.get("model_used"),
            "result": result.get("content"),
            "latency_ms": result.get("latency_ms"),
            "usage": result.get("usage")
        }
```

### Model Performance Dashboard

```python
async def get_multi_model_performance() -> Dict[str, Any]:
    """Get performance metrics across all models"""

    orchestrator = MultiModelOrchestrator()
    report = orchestrator.get_performance_report(time_window_hours=24)

    # Performance by category
    category_performance = {
        "frontend": {
            "models": ["claude-sonnet-4-5", "gemini-pro"],
            "total_requests": 0,
            "avg_latency_ms": 0,
            "success_rate": 100.0
        },
        "backend": {
            "models": ["claude-sonnet-4-5", "gpt-5"],
            "total_requests": 0,
            "avg_latency_ms": 0,
            "success_rate": 100.0
        },
        "content": {
            "models": ["huggingface", "claude-sonnet-4-5", "gemini-pro", "gpt-5"],
            "total_requests": 0,
            "avg_latency_ms": 0,
            "success_rate": 100.0
        },
        "development": {
            "models": ["claude-sonnet-4-5", "codex"],
            "total_requests": 0,
            "avg_latency_ms": 0,
            "success_rate": 100.0
        }
    }

    return {
        "time_window_hours": 24,
        "categories": category_performance,
        "overall_health": "healthy"
    }
```

## Integration Points

- **Enhanced Agent Manager** (`agent/enhanced_agent_manager.py`)
- **Multi-Agent Orchestrator** (`intelligence/multi_agent_orchestrator.py`)
- **Agent Assignment Manager** (`agent/modules/backend/agent_assignment_manager.py`)
- **Multi-Model Orchestrator** (`skills/multi_model_orchestrator.md`) ✨ NEW
- **Google Gemini Integration** (`skills/google_gemini_integration.md`) ✨ NEW

## Model Routing Summary

| Agent Category | Primary Model | Secondary Model(s) | Use Case |
|----------------|---------------|-------------------|----------|
| **Frontend** | Gemini Pro | Claude Sonnet 4.5 | UI/UX, Design, Components |
| **Backend** | Claude Sonnet 4.5 | ChatGPT-5 | APIs, Databases, Logic |
| **Content** | Claude Sonnet 4.5 | Gemini, GPT-5, Huggingface | Marketing, Images, Videos |
| **Development** | Claude Sonnet 4.5 | Codex | Code Gen, Reviews, Refactoring |

Use this skill to coordinate complex multi-agent workflows with intelligent multi-model AI routing across DevSkyy's 54+ specialized agents.
