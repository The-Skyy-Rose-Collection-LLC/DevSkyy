import asyncio
import importlib
import inspect
import logging
from pathlib import Path
from typing import Any

from agent.modules.base_agent import BaseAgent
from agent.orchestrator import ExecutionPriority, orchestrator
from agent.security_manager import SecurityRole, security_manager


"""
Enterprise Agent Registry
Automatic agent discovery, registration, and management

Features:
- Auto-discovery of agents in modules/backend and modules/frontend
- Automatic capability detection
- Dependency resolution
- Health monitoring
- Version management
- Hot reloading support
"""

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Centralized registry for managing all agents in the system.

    Provides:
    - Automatic agent discovery
    - Registration with orchestrator
    - Capability detection
    - Health monitoring
    - Version management
    """

    def __init__(self):
        self.registered_agents: dict[str, dict[str, Any]] = {}
        self.agent_capabilities: dict[str, list[str]] = {}
        self.agent_metadata: dict[str, dict[str, Any]] = {}

        # Agent capability mappings
        self.capability_map = {
            # Infrastructure agents
            "scanner": ["scan", "analyze", "detect_issues", "security_scan"],
            "fixer": ["fix", "repair", "format", "optimize"],
            "security": ["authenticate", "authorize", "encrypt", "audit"],
            "performance": ["optimize", "profile", "benchmark"],
            # AI agents
            "claude_sonnet": ["reason", "analyze", "generate_text", "explain"],
            "openai": ["generate", "complete", "embed", "moderate"],
            "multi_model": ["orchestrate", "route", "fallback"],
            # E-commerce agents
            "ecommerce": ["products", "orders", "cart", "pricing"],
            "inventory": ["stock", "warehouse", "forecast", "replenish"],
            "financial": ["payments", "invoices", "analytics", "reporting"],
            # Content agents
            "seo": ["keywords", "optimize_content", "meta_tags", "sitemap"],
            "social_media": ["post", "schedule", "engage", "analytics"],
            "email": ["send", "template", "campaign", "automation"],
            # Technical agents
            "computer_vision": ["detect", "classify", "segment", "recognize"],
            "voice": ["transcribe", "synthesize", "translate"],
            "blockchain": ["mint", "transfer", "verify", "wallet"],
        }

        # Agent dependency mappings
        self.dependency_map = {
            "fixer": ["scanner"],  # Fixer depends on scanner
            "seo": ["ecommerce", "claude_sonnet"],  # SEO needs product data and AI
            "social_media": [
                "ecommerce",
                "claude_sonnet",
            ],  # Social needs products and content generation
            "email": [
                "ecommerce",
                "claude_sonnet",
            ],  # Email needs customer data and templates
            "performance": ["scanner"],  # Performance depends on scan results
        }

        # Agent priority mappings
        self.priority_map = {
            "security": ExecutionPriority.CRITICAL,
            "scanner": ExecutionPriority.HIGH,
            "fixer": ExecutionPriority.HIGH,
            "ecommerce": ExecutionPriority.HIGH,
            "financial": ExecutionPriority.HIGH,
            "inventory": ExecutionPriority.MEDIUM,
            "claude_sonnet": ExecutionPriority.MEDIUM,
            "openai": ExecutionPriority.MEDIUM,
        }

    async def discover_and_register_all_agents(self) -> dict[str, Any]:
        """
        Discover and register all agents automatically.

        Returns:
            Summary of discovered and registered agents
        """
        logger.info("🔍 Starting automatic agent discovery...")

        summary = {
            "discovered": 0,
            "registered": 0,
            "failed": 0,
            "agents": [],
            "errors": [],
        }

        # Discover backend agents
        backend_path = Path(__file__).parent / "modules" / "backend"
        if backend_path.exists():
            backend_agents = await self._discover_agents_in_directory(backend_path, "agent.modules.backend")
            summary["discovered"] += len(backend_agents)

            for agent_info in backend_agents:
                success = await self._register_discovered_agent(agent_info)
                if success:
                    summary["registered"] += 1
                    summary["agents"].append(agent_info["name"])
                else:
                    summary["failed"] += 1
                    summary["errors"].append(f"Failed to register: {agent_info['name']}")

        # Discover frontend agents
        frontend_path = Path(__file__).parent / "modules" / "frontend"
        if frontend_path.exists():
            frontend_agents = await self._discover_agents_in_directory(frontend_path, "agent.modules.frontend")
            summary["discovered"] += len(frontend_agents)

            for agent_info in frontend_agents:
                success = await self._register_discovered_agent(agent_info)
                if success:
                    summary["registered"] += 1
                    summary["agents"].append(agent_info["name"])
                else:
                    summary["failed"] += 1
                    summary["errors"].append(f"Failed to register: {agent_info['name']}")

        logger.info(f"✅ Discovery complete: {summary['registered']}/{summary['discovered']} agents registered")
        return summary

    async def _discover_agents_in_directory(self, directory: Path, module_prefix: str) -> list[dict[str, Any]]:
        """Discover all agent files in a directory"""
        agents = []

        for file_path in directory.glob("*_v2.py"):  # Prioritize V2 agents
            agent_info = await self._analyze_agent_file(file_path, module_prefix)
            if agent_info:
                agents.append(agent_info)

        # If no V2 agents found, check for regular agents
        if not agents:
            for file_path in directory.glob("*_agent.py"):
                agent_info = await self._analyze_agent_file(file_path, module_prefix)
                if agent_info:
                    agents.append(agent_info)

        return agents

    async def _analyze_agent_file(self, file_path: Path, module_prefix: str) -> dict[str, Any] | None:
        """Analyze an agent file to extract information"""
        try:
            # Get module name
            module_name = file_path.stem
            full_module_path = f"{module_prefix}.{module_name}"

            # Import module
            module = importlib.import_module(full_module_path)

            # Find BaseAgent subclasses
            for _name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseAgent) and obj != BaseAgent:
                    # Extract agent info
                    agent_key = module_name.replace("_v2", "").replace("_agent", "")

                    return {
                        "name": agent_key,
                        "class": obj,
                        "module": full_module_path,
                        "file": str(file_path),
                        "version": "2.0" if "_v2" in module_name else "1.0",
                    }

        except Exception as e:
            logger.warning(f"Failed to analyze agent file {file_path}: {e}")

        return None

    async def _register_discovered_agent(self, agent_info: dict[str, Any]) -> bool:
        """Register a discovered agent with the orchestrator"""
        try:
            agent_name = agent_info["name"]
            agent_class = agent_info["class"]

            # Create agent instance
            agent_instance = agent_class()

            # Get capabilities for this agent
            capabilities = self.capability_map.get(agent_name, [agent_name])

            # Get dependencies
            dependencies = self.dependency_map.get(agent_name, [])

            # Get priority
            priority = self.priority_map.get(agent_name, ExecutionPriority.MEDIUM)

            # Register with orchestrator
            success = await orchestrator.register_agent(
                agent=agent_instance,
                capabilities=capabilities,
                dependencies=dependencies,
                priority=priority,
            )

            if success:
                # Generate API key for agent
                api_key = security_manager.generate_api_key(agent_name, SecurityRole.SERVICE)

                # Store metadata
                self.registered_agents[agent_name] = {
                    "instance": agent_instance,
                    "capabilities": capabilities,
                    "dependencies": dependencies,
                    "priority": priority,
                    "version": agent_info["version"],
                    "module": agent_info["module"],
                }

                self.agent_capabilities[agent_name] = capabilities
                self.agent_metadata[agent_name] = {
                    "registered_at": asyncio.get_event_loop().time(),
                    "api_key_id": api_key.split(".")[0],
                    "status": "active",
                }

                logger.info(f"✅ Registered agent: {agent_name} v{agent_info['version']}")
                return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_info['name']}: {e}")

        return False

    def get_agent(self, agent_name: str) -> BaseAgent | None:
        """Get a registered agent by name"""
        agent_info = self.registered_agents.get(agent_name)
        return agent_info["instance"] if agent_info else None

    def list_agents(self, capability: str | None = None) -> list[str]:
        """
        List all registered agents.

        Args:
            capability: Filter by specific capability

        Returns:
            List of agent names
        """
        if capability:
            return [name for name, caps in self.agent_capabilities.items() if capability in caps]

        return list(self.registered_agents.keys())

    def get_agent_info(self, agent_name: str) -> dict[str, Any] | None:
        """Get detailed information about an agent"""
        if agent_name not in self.registered_agents:
            return None

        agent_data = self.registered_agents[agent_name]
        metadata = self.agent_metadata[agent_name]

        return {
            "name": agent_name,
            "version": agent_data["version"],
            "capabilities": agent_data["capabilities"],
            "dependencies": agent_data["dependencies"],
            "priority": agent_data["priority"].value,
            "status": metadata["status"],
            "module": agent_data["module"],
        }

    async def health_check_all(self) -> dict[str, Any]:
        """Perform health check on all registered agents"""
        results = {}

        for agent_name, agent_info in self.registered_agents.items():
            agent = agent_info["instance"]
            try:
                health = await agent.health_check()
                results[agent_name] = health
            except Exception as e:
                results[agent_name] = {"status": "error", "error": str(e)}

        healthy_count = sum(1 for r in results.values() if r.get("status") == "healthy")
        total_count = len(results)

        return {
            "timestamp": asyncio.get_event_loop().time(),
            "total_agents": total_count,
            "healthy_agents": healthy_count,
            "unhealthy_agents": total_count - healthy_count,
            "agents": results,
        }

    async def reload_agent(self, agent_name: str) -> bool:
        """Hot reload an agent"""
        try:
            if agent_name not in self.registered_agents:
                return False

            agent_info = self.registered_agents[agent_name]

            # Unregister from orchestrator
            await orchestrator.unregister_agent(agent_name)

            # Reload module
            module = importlib.import_module(agent_info["module"])
            importlib.reload(module)

            # Re-register (discovery will handle it)
            file_path = Path(agent_info["module"].replace(".", "/") + ".py")
            new_agent_info = await self._analyze_agent_file(file_path, agent_info["module"].rsplit(".", 1)[0])

            if new_agent_info:
                success = await self._register_discovered_agent(new_agent_info)
                logger.info(f"♻️  Reloaded agent: {agent_name}")
                return success

        except Exception as e:
            logger.error(f"Failed to reload agent {agent_name}: {e}")

        return False

    async def execute_workflow(self, workflow_name: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a predefined multi-agent workflow.

        Workflows:
        - scan_and_fix: Run scanner then fixer
        - content_pipeline: Generate, optimize, and publish content
        - ecommerce_order: Process order through multiple agents
        """
        if workflow_name == "scan_and_fix":
            return await self._workflow_scan_and_fix(parameters)
        elif workflow_name == "content_pipeline":
            return await self._workflow_content_pipeline(parameters)
        elif workflow_name == "ecommerce_order":
            return await self._workflow_ecommerce_order(parameters)
        else:
            return {"error": f"Unknown workflow: {workflow_name}"}

    async def _workflow_scan_and_fix(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Workflow: Scan codebase then apply fixes"""
        # Execute scan
        scan_result = await orchestrator.execute_task(
            task_type="scan",
            parameters=parameters,
            required_capabilities=["scan"],
            priority=ExecutionPriority.HIGH,
        )

        if "error" in scan_result:
            return scan_result

        # Execute fix with scan results
        fix_result = await orchestrator.execute_task(
            task_type="fix",
            parameters={"scan_results": scan_result.get("results", {}).get("scanner", {})},
            required_capabilities=["fix"],
            priority=ExecutionPriority.HIGH,
        )

        return {
            "workflow": "scan_and_fix",
            "scan": scan_result,
            "fix": fix_result,
            "status": "completed" if "error" not in fix_result else "partial",
        }

    async def _workflow_content_pipeline(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Workflow: Content generation → SEO optimization → Publishing"""
        results = {}

        # Generate content with AI
        content_result = await orchestrator.execute_task(
            task_type="generate_content",
            parameters=parameters,
            required_capabilities=["generate_text"],
            priority=ExecutionPriority.MEDIUM,
        )
        results["generation"] = content_result

        # Optimize for SEO
        if "error" not in content_result:
            seo_result = await orchestrator.execute_task(
                task_type="optimize_seo",
                parameters={"content": content_result},
                required_capabilities=["optimize_content"],
                priority=ExecutionPriority.MEDIUM,
            )
            results["seo"] = seo_result

        return {"workflow": "content_pipeline", "results": results}

    async def _workflow_ecommerce_order(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Workflow: Order processing through multiple agents"""
        results = {}

        # Validate order
        validation = await orchestrator.execute_task(
            task_type="validate_order",
            parameters=parameters,
            required_capabilities=["orders"],
            priority=ExecutionPriority.HIGH,
        )
        results["validation"] = validation

        # Check inventory
        if "error" not in validation:
            inventory = await orchestrator.execute_task(
                task_type="check_stock",
                parameters=parameters,
                required_capabilities=["stock"],
                priority=ExecutionPriority.HIGH,
            )
            results["inventory"] = inventory

        # Process payment
        if "error" not in validation and results.get("inventory", {}).get("available"):
            payment = await orchestrator.execute_task(
                task_type="process_payment",
                parameters=parameters,
                required_capabilities=["payments"],
                priority=ExecutionPriority.CRITICAL,
            )
            results["payment"] = payment

        return {"workflow": "ecommerce_order", "results": results}


# Global registry instance
registry = AgentRegistry()
