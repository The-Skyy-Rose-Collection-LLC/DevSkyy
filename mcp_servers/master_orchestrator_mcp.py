"""
DevSkyy Master Orchestrator MCP Server

Coordinates all DevSkyy MCP servers and executes multi-step workflows.
Central command for Frontend, Backend, Development, and RAG MCPs.

Tools:
- execute_workflow: Multi-MCP workflows
- coordinate_mcps: Route to appropriate MCP
- get_mcp_status: Health of all servers
- load_mcp_tools: On-demand loading
- create_pipeline: Custom task pipelines
- schedule_task: Cron scheduling

Predefined Workflows:
- theme_build_deploy: Frontend → Backend → RAG
- product_launch: Backend → Frontend → RAG
- code_review: Development → RAG
- full_site_build: All MCPs orchestrated

Author: DevSkyy Enterprise
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
import sys
from typing import Any


# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.base_mcp_server import BaseMCPServer


class MCPType(Enum):
    """Available MCP server types."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DEVELOPMENT = "development"
    RAG = "rag"
    THEME = "theme"


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PredefinedWorkflow:
    """Predefined workflow definitions."""

    THEME_BUILD_DEPLOY = {
        "name": "theme_build_deploy",
        "description": "Build WordPress theme and deploy to site",
        "steps": [
            {"mcp": "frontend", "tool": "build_wordpress_theme", "args": {}},
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {"template_type": "homepage"}},
            {"mcp": "frontend", "tool": "apply_brand_styling", "args": {}},
            {"mcp": "backend", "tool": "woocommerce_sync", "args": {"sync_type": "products"}},
            {"mcp": "rag", "tool": "ingest_wordpress_guide", "args": {}},
        ],
    }

    PRODUCT_LAUNCH = {
        "name": "product_launch",
        "description": "Launch new product: sync to WooCommerce, update frontend, index in RAG",
        "steps": [
            {"mcp": "backend", "tool": "sync_catalog_to_woocommerce", "args": {}},
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {"template_type": "product"}},
            {"mcp": "rag", "tool": "ingest_catalog", "args": {}},
        ],
    }

    CODE_REVIEW = {
        "name": "code_review",
        "description": "Full code review: lint, type check, security scan, tests",
        "steps": [
            {"mcp": "development", "tool": "lint_and_format", "args": {"fix": True}},
            {"mcp": "development", "tool": "type_check", "args": {}},
            {"mcp": "development", "tool": "security_scan", "args": {}},
            {"mcp": "development", "tool": "run_tests", "args": {"coverage": True}},
        ],
    }

    FULL_SITE_BUILD = {
        "name": "full_site_build",
        "description": "Complete SkyyRose site build: all pages, products, integrations",
        "steps": [
            # Phase 1: Ingest all data
            {"mcp": "rag", "tool": "ingest_wordpress_guide", "args": {}},
            {"mcp": "rag", "tool": "ingest_catalog", "args": {}},
            # Phase 2: Backend setup
            {"mcp": "backend", "tool": "sync_catalog_to_woocommerce", "args": {}},
            # Phase 3: Frontend pages
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {"template_type": "homepage"}},
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {"template_type": "collection", "collection": "love-hurts"}},
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {"template_type": "collection", "collection": "black-rose"}},
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {"template_type": "collection", "collection": "signature"}},
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {"template_type": "product"}},
            # Phase 4: Brand styling
            {"mcp": "frontend", "tool": "apply_brand_styling", "args": {}},
            # Phase 5: Validation
            {"mcp": "frontend", "tool": "validate_accessibility", "args": {}},
            {"mcp": "development", "tool": "full_quality_check", "args": {}},
        ],
    }

    WORDPRESS_PAGES = {
        "name": "wordpress_pages",
        "description": "Build all WordPress/Elementor pages for SkyyRose",
        "steps": [
            # Homepage
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {
                "template_type": "homepage",
                "options": {"hero": True, "collections": True, "featured_products": True},
            }},
            # Collection pages
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {
                "template_type": "collection",
                "collection": "love-hurts",
            }},
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {
                "template_type": "collection",
                "collection": "black-rose",
            }},
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {
                "template_type": "collection",
                "collection": "signature",
            }},
            # Product template
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {
                "template_type": "product",
            }},
            # Shop archive
            {"mcp": "frontend", "tool": "generate_elementor_template", "args": {
                "template_type": "shop",
            }},
            # About page
            {"mcp": "frontend", "tool": "create_landing_page", "args": {
                "page_type": "about",
                "title": "About SkyyRose",
                "content": "Where Love Meets Luxury - Oakland's luxury streetwear brand",
            }},
            # Contact page
            {"mcp": "frontend", "tool": "create_landing_page", "args": {
                "page_type": "contact",
                "title": "Contact SkyyRose",
            }},
        ],
    }

    @classmethod
    def get_all(cls) -> dict[str, dict]:
        """Get all predefined workflows."""
        return {
            "theme_build_deploy": cls.THEME_BUILD_DEPLOY,
            "product_launch": cls.PRODUCT_LAUNCH,
            "code_review": cls.CODE_REVIEW,
            "full_site_build": cls.FULL_SITE_BUILD,
            "wordpress_pages": cls.WORDPRESS_PAGES,
        }


class MCPRegistry:
    """Registry of available MCP servers and their capabilities."""

    def __init__(self):
        self.mcps: dict[str, dict[str, Any]] = {}
        self.tools: dict[str, dict[str, Any]] = {}
        self._initialize_registry()

    def _initialize_registry(self):
        """Initialize the MCP registry with known servers."""
        self.mcps = {
            "frontend": {
                "name": "devskyy-frontend",
                "module": "mcp_servers.frontend_mcp",
                "description": "Theme building, Elementor, UI components",
                "tools": [
                    "build_wordpress_theme",
                    "generate_elementor_template",
                    "create_landing_page",
                    "apply_brand_styling",
                    "validate_accessibility",
                    "generate_css",
                    "deploy_to_wordpress",
                ],
                "status": "available",
            },
            "backend": {
                "name": "devskyy-backend",
                "module": "mcp_servers.backend_mcp",
                "description": "API operations, database, agents, e-commerce",
                "tools": [
                    "execute_agent_task",
                    "sync_catalog_to_woocommerce",
                    "manage_inventory",
                    "dynamic_pricing",
                    "process_order",
                    "woocommerce_sync",
                    "optimize_database",
                    "security_scan",
                ],
                "status": "available",
            },
            "development": {
                "name": "devskyy-development",
                "module": "mcp_servers.development_mcp",
                "description": "Code generation, testing, CI/CD, quality",
                "tools": [
                    "analyze_code",
                    "fix_code_issues",
                    "generate_code",
                    "run_tests",
                    "generate_tests",
                    "lint_and_format",
                    "security_scan",
                    "type_check",
                    "git_operations",
                    "full_quality_check",
                ],
                "status": "available",
            },
            "rag": {
                "name": "devskyy-rag",
                "module": "mcp_servers.rag_mcp",
                "description": "Vector store, embeddings, semantic search",
                "tools": [
                    "ingest_document",
                    "ingest_catalog",
                    "ingest_wordpress_guide",
                    "semantic_search",
                    "rag_query",
                    "iterative_rag_query",
                    "hybrid_search",
                    "manage_collection",
                    "learn_wordpress_updates",
                ],
                "status": "available",
            },
            "theme": {
                "name": "devskyy-theme",
                "module": "mcp_servers.theme_orchestrator",
                "description": "WordPress theme orchestration",
                "tools": [
                    "create_theme",
                    "generate_elementor_template",
                    "sync_woocommerce",
                ],
                "status": "available",
            },
        }

        # Build tool-to-MCP mapping
        for mcp_id, mcp_info in self.mcps.items():
            for tool in mcp_info.get("tools", []):
                self.tools[tool] = {"mcp": mcp_id, "info": mcp_info}

    def get_mcp_for_tool(self, tool_name: str) -> str | None:
        """Get the MCP server that provides a given tool."""
        if tool_name in self.tools:
            return self.tools[tool_name]["mcp"]
        return None

    def get_all_tools(self) -> list[str]:
        """Get all available tools across all MCPs."""
        return list(self.tools.keys())

    def get_mcp_status(self) -> dict[str, Any]:
        """Get status of all MCPs."""
        return {mcp_id: mcp["status"] for mcp_id, mcp in self.mcps.items()}


class WorkflowEngine:
    """Execute multi-step workflows across MCPs."""

    def __init__(self, registry: MCPRegistry):
        self.registry = registry
        self.workflows: dict[str, dict[str, Any]] = {}
        self.execution_history: list[dict[str, Any]] = []

    async def execute_workflow(
        self,
        workflow_name: str,
        args: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a predefined workflow."""
        workflows = PredefinedWorkflow.get_all()

        if workflow_name not in workflows:
            return {
                "success": False,
                "error": f"Unknown workflow: {workflow_name}",
                "available": list(workflows.keys()),
            }

        workflow = workflows[workflow_name]
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        execution = {
            "id": execution_id,
            "workflow": workflow_name,
            "status": WorkflowStatus.RUNNING.value,
            "started_at": datetime.now().isoformat(),
            "steps_completed": 0,
            "steps_total": len(workflow["steps"]),
            "results": [],
            "errors": [],
        }

        self.workflows[execution_id] = execution

        # Execute each step
        for i, step in enumerate(workflow["steps"]):
            try:
                step_result = await self._execute_step(step, args)
                execution["results"].append({
                    "step": i + 1,
                    "mcp": step["mcp"],
                    "tool": step["tool"],
                    "success": step_result.get("success", True),
                    "result": step_result,
                })
                execution["steps_completed"] = i + 1

                if not step_result.get("success", True):
                    execution["errors"].append({
                        "step": i + 1,
                        "error": step_result.get("error", "Step failed"),
                    })
                    # Continue execution despite errors (per Rule #10)

            except Exception as e:
                execution["errors"].append({
                    "step": i + 1,
                    "error": str(e),
                })
                execution["results"].append({
                    "step": i + 1,
                    "mcp": step["mcp"],
                    "tool": step["tool"],
                    "success": False,
                    "error": str(e),
                })

        execution["status"] = (
            WorkflowStatus.COMPLETED.value
            if not execution["errors"]
            else WorkflowStatus.FAILED.value
        )
        execution["completed_at"] = datetime.now().isoformat()

        self.execution_history.append(execution)

        return {
            "success": len(execution["errors"]) == 0,
            "execution_id": execution_id,
            "workflow": workflow_name,
            "steps_completed": execution["steps_completed"],
            "steps_total": execution["steps_total"],
            "results": execution["results"],
            "errors": execution["errors"],
            "status": execution["status"],
        }

    async def _execute_step(
        self,
        step: dict[str, Any],
        workflow_args: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a single workflow step."""
        mcp_id = step["mcp"]
        tool_name = step["tool"]
        step_args = step.get("args", {})

        # Merge workflow args with step args
        if workflow_args:
            step_args = {**step_args, **workflow_args}

        # Import and execute the appropriate MCP
        try:
            if mcp_id == "frontend":
                from mcp_servers.frontend_mcp import FrontendMCPServer
                server = FrontendMCPServer()
            elif mcp_id == "backend":
                from mcp_servers.backend_mcp import BackendMCPServer
                server = BackendMCPServer()
            elif mcp_id == "development":
                from mcp_servers.development_mcp import DevelopmentMCPServer
                server = DevelopmentMCPServer()
            elif mcp_id == "rag":
                from mcp_servers.rag_mcp import RAGMCPServer
                server = RAGMCPServer()
            else:
                return {"success": False, "error": f"Unknown MCP: {mcp_id}"}

            # Find and execute the tool handler
            handler = server._tool_handlers.get(tool_name)
            if handler:
                result = await handler(step_args)
                return result
            else:
                return {"success": False, "error": f"Tool not found: {tool_name}"}

        except ImportError as e:
            return {"success": False, "error": f"Failed to import MCP: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Execution failed: {e}"}

    def get_execution_status(self, execution_id: str) -> dict[str, Any] | None:
        """Get status of a workflow execution."""
        return self.workflows.get(execution_id)


class TaskScheduler:
    """Schedule tasks for future execution."""

    def __init__(self):
        self.scheduled_tasks: list[dict[str, Any]] = []

    def schedule_task(
        self,
        task: dict[str, Any],
        schedule: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Schedule a task for later execution."""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.scheduled_tasks)}"

        scheduled = {
            "id": task_id,
            "task": task,
            "schedule": schedule,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "scheduled",
        }

        self.scheduled_tasks.append(scheduled)

        return {
            "success": True,
            "task_id": task_id,
            "schedule": schedule,
            "message": f"Task scheduled: {description or task.get('tool', 'unknown')}",
        }

    def get_scheduled_tasks(self) -> list[dict[str, Any]]:
        """Get all scheduled tasks."""
        return self.scheduled_tasks

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        """Cancel a scheduled task."""
        for task in self.scheduled_tasks:
            if task["id"] == task_id:
                task["status"] = "cancelled"
                return {"success": True, "message": f"Task {task_id} cancelled"}

        return {"success": False, "error": f"Task not found: {task_id}"}


class MasterOrchestratorMCPServer(BaseMCPServer):
    """
    Master Orchestrator MCP Server for DevSkyy.

    Coordinates all MCP servers and executes multi-step workflows.
    """

    def __init__(self):
        super().__init__(
            name="devskyy-orchestrator",
            version="1.0.0",
        )
        self.registry = MCPRegistry()
        self.workflow_engine = WorkflowEngine(self.registry)
        self.scheduler = TaskScheduler()

    def _register_tools(self) -> None:
        """Register all orchestrator tools."""

        # Execute Workflow
        self._register_tool(
            name="execute_workflow",
            description="Execute a predefined multi-MCP workflow",
            handler=self._execute_workflow,
            input_schema={
                "type": "object",
                "properties": {
                    "workflow": {
                        "type": "string",
                        "enum": list(PredefinedWorkflow.get_all().keys()),
                        "description": "Workflow to execute",
                    },
                    "args": {
                        "type": "object",
                        "description": "Arguments to pass to workflow steps",
                    },
                },
                "required": ["workflow"],
            },
        )

        # List Workflows
        self._register_tool(
            name="list_workflows",
            description="List all available predefined workflows",
            handler=self._list_workflows,
            input_schema={
                "type": "object",
                "properties": {},
            },
        )

        # Coordinate MCPs
        self._register_tool(
            name="coordinate_mcps",
            description="Route a task to the appropriate MCP server",
            handler=self._coordinate_mcps,
            input_schema={
                "type": "object",
                "properties": {
                    "tool": {
                        "type": "string",
                        "description": "Tool to execute",
                    },
                    "args": {
                        "type": "object",
                        "description": "Tool arguments",
                    },
                },
                "required": ["tool"],
            },
        )

        # Get MCP Status
        self._register_tool(
            name="get_mcp_status",
            description="Get health and status of all MCP servers",
            handler=self._get_mcp_status,
            input_schema={
                "type": "object",
                "properties": {},
            },
        )

        # List MCP Tools
        self._register_tool(
            name="list_mcp_tools",
            description="List all available tools across all MCPs",
            handler=self._list_mcp_tools,
            input_schema={
                "type": "object",
                "properties": {
                    "mcp": {
                        "type": "string",
                        "description": "Filter by specific MCP",
                    },
                },
            },
        )

        # Create Pipeline
        self._register_tool(
            name="create_pipeline",
            description="Create a custom multi-step pipeline",
            handler=self._create_pipeline,
            input_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Pipeline name",
                    },
                    "description": {
                        "type": "string",
                        "description": "Pipeline description",
                    },
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "mcp": {"type": "string"},
                                "tool": {"type": "string"},
                                "args": {"type": "object"},
                            },
                            "required": ["mcp", "tool"],
                        },
                        "description": "Pipeline steps",
                    },
                },
                "required": ["name", "steps"],
            },
        )

        # Schedule Task
        self._register_tool(
            name="schedule_task",
            description="Schedule a task for later execution",
            handler=self._schedule_task,
            input_schema={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "object",
                        "properties": {
                            "mcp": {"type": "string"},
                            "tool": {"type": "string"},
                            "args": {"type": "object"},
                        },
                        "required": ["mcp", "tool"],
                        "description": "Task to schedule",
                    },
                    "schedule": {
                        "type": "string",
                        "description": "Cron expression or datetime",
                    },
                    "description": {
                        "type": "string",
                        "description": "Task description",
                    },
                },
                "required": ["task", "schedule"],
            },
        )

        # Get Execution History
        self._register_tool(
            name="get_execution_history",
            description="Get history of workflow executions",
            handler=self._get_execution_history,
            input_schema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of executions to return",
                        "default": 10,
                    },
                },
            },
        )

        # Build WordPress Site
        self._register_tool(
            name="build_wordpress_site",
            description="Build complete SkyyRose WordPress site with all pages",
            handler=self._build_wordpress_site,
            input_schema={
                "type": "object",
                "properties": {
                    "include_products": {
                        "type": "boolean",
                        "description": "Sync products to WooCommerce",
                        "default": True,
                    },
                    "include_rag": {
                        "type": "boolean",
                        "description": "Index content in RAG",
                        "default": True,
                    },
                },
            },
        )

        # Semantic Query (RAG integration)
        self._register_tool(
            name="semantic_query",
            description="Query knowledge base using semantic search",
            handler=self._semantic_query,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query",
                    },
                    "collections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Collections to search",
                    },
                },
                "required": ["query"],
            },
        )

    async def _execute_workflow(self, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a predefined workflow."""
        workflow_name = args["workflow"]
        workflow_args = args.get("args", {})

        return await self.workflow_engine.execute_workflow(workflow_name, workflow_args)

    async def _list_workflows(self, args: dict[str, Any]) -> dict[str, Any]:
        """List all available workflows."""
        workflows = PredefinedWorkflow.get_all()

        return {
            "success": True,
            "workflows": [
                {
                    "name": name,
                    "description": wf["description"],
                    "steps_count": len(wf["steps"]),
                }
                for name, wf in workflows.items()
            ],
        }

    async def _coordinate_mcps(self, args: dict[str, Any]) -> dict[str, Any]:
        """Route a task to the appropriate MCP."""
        tool_name = args["tool"]
        tool_args = args.get("args", {})

        # Find which MCP provides this tool
        mcp_id = self.registry.get_mcp_for_tool(tool_name)

        if not mcp_id:
            return {
                "success": False,
                "error": f"No MCP found for tool: {tool_name}",
                "available_tools": self.registry.get_all_tools(),
            }

        # Execute on the appropriate MCP
        step = {"mcp": mcp_id, "tool": tool_name, "args": tool_args}
        result = await self.workflow_engine._execute_step(step)

        return {
            "success": result.get("success", True),
            "mcp_used": mcp_id,
            "tool": tool_name,
            "result": result,
        }

    async def _get_mcp_status(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get status of all MCPs."""
        return {
            "success": True,
            "mcps": {
                mcp_id: {
                    "name": mcp["name"],
                    "description": mcp["description"],
                    "status": mcp["status"],
                    "tools_count": len(mcp["tools"]),
                }
                for mcp_id, mcp in self.registry.mcps.items()
            },
            "total_tools": len(self.registry.get_all_tools()),
        }

    async def _list_mcp_tools(self, args: dict[str, Any]) -> dict[str, Any]:
        """List all available tools."""
        mcp_filter = args.get("mcp")

        if mcp_filter:
            if mcp_filter in self.registry.mcps:
                tools = self.registry.mcps[mcp_filter]["tools"]
            else:
                return {"success": False, "error": f"Unknown MCP: {mcp_filter}"}
        else:
            tools = self.registry.get_all_tools()

        return {
            "success": True,
            "tools": tools,
            "count": len(tools),
            "mcp_filter": mcp_filter,
        }

    async def _create_pipeline(self, args: dict[str, Any]) -> dict[str, Any]:
        """Create a custom pipeline."""
        name = args["name"]
        description = args.get("description", "")
        steps = args["steps"]

        # Validate steps
        for step in steps:
            mcp_id = step["mcp"]
            tool_name = step["tool"]

            if mcp_id not in self.registry.mcps:
                return {"success": False, "error": f"Unknown MCP: {mcp_id}"}

            if tool_name not in self.registry.mcps[mcp_id]["tools"]:
                return {
                    "success": False,
                    "error": f"Tool {tool_name} not available in {mcp_id}",
                }

        # Store pipeline (in memory for now)
        pipeline = {
            "name": name,
            "description": description,
            "steps": steps,
            "created_at": datetime.now().isoformat(),
        }

        return {
            "success": True,
            "pipeline": pipeline,
            "message": f"Pipeline '{name}' created with {len(steps)} steps",
        }

    async def _schedule_task(self, args: dict[str, Any]) -> dict[str, Any]:
        """Schedule a task for later execution."""
        return self.scheduler.schedule_task(
            task=args["task"],
            schedule=args["schedule"],
            description=args.get("description"),
        )

    async def _get_execution_history(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get workflow execution history."""
        limit = args.get("limit", 10)
        history = self.workflow_engine.execution_history[-limit:]

        return {
            "success": True,
            "executions": history,
            "total": len(self.workflow_engine.execution_history),
            "showing": len(history),
        }

    async def _build_wordpress_site(self, args: dict[str, Any]) -> dict[str, Any]:
        """Build complete WordPress site."""
        include_products = args.get("include_products", True)
        include_rag = args.get("include_rag", True)

        workflow_name = "full_site_build" if include_products and include_rag else "wordpress_pages"

        return await self.workflow_engine.execute_workflow(workflow_name)

    async def _semantic_query(self, args: dict[str, Any]) -> dict[str, Any]:
        """Query knowledge base."""
        query = args["query"]
        collections = args.get("collections", ["wordpress_knowledge", "skyyrose_products"])

        # Route to RAG MCP
        step = {
            "mcp": "rag",
            "tool": "semantic_search",
            "args": {
                "query": query,
                "collection_name": collections[0] if collections else "wordpress_knowledge",
                "n_results": 5,
            },
        }

        return await self.workflow_engine._execute_step(step)


# Create the MCP server instance for module-level access
_server_instance: MasterOrchestratorMCPServer | None = None


def get_server() -> MasterOrchestratorMCPServer:
    """Get or create the server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = MasterOrchestratorMCPServer()
    return _server_instance


# Lazy proxy for mcp to avoid import-time initialization
class _MCPProxy:
    """Lazy proxy for the MCP server instance."""

    def __getattr__(self, name: str):
        return getattr(get_server().server, name)


# Export mcp instance for Claude Code compatibility
mcp = _MCPProxy()


# Module entry point
def main():
    """Run the Master Orchestrator MCP server."""

    server = get_server()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
