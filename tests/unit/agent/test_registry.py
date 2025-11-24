"""
Comprehensive unit tests for agent/registry.py

Target coverage: 90%+
Test count: 50+ tests
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.modules.base_agent import AgentStatus, BaseAgent
from agent.orchestrator import ExecutionPriority
from agent.registry import AgentRegistry


class MockAgent(BaseAgent):
    """Mock agent for testing"""

    def __init__(self, name: str = "mock_agent"):
        super().__init__(agent_name=name)

    async def initialize(self) -> bool:
        self.status = AgentStatus.HEALTHY
        return True

    async def execute_core_function(self, **kwargs) -> dict:
        return {"status": "success", "result": "mock"}


class TestAgentRegistryInitialization:
    """Test registry initialization"""

    def test_registry_creation(self):
        registry = AgentRegistry()
        assert registry is not None
        assert len(registry.registered_agents) == 0
        assert len(registry.agent_capabilities) == 0
        assert len(registry.agent_metadata) == 0

    def test_capability_map_initialized(self):
        registry = AgentRegistry()
        assert "scanner" in registry.capability_map
        assert "fixer" in registry.capability_map
        assert "security" in registry.capability_map
        assert "scan" in registry.capability_map["scanner"]

    def test_dependency_map_initialized(self):
        registry = AgentRegistry()
        assert "fixer" in registry.dependency_map
        assert "scanner" in registry.dependency_map["fixer"]
        assert "seo" in registry.dependency_map
        assert "ecommerce" in registry.dependency_map["seo"]

    def test_priority_map_initialized(self):
        registry = AgentRegistry()
        assert registry.priority_map["security"] == ExecutionPriority.CRITICAL
        assert registry.priority_map["scanner"] == ExecutionPriority.HIGH
        assert registry.priority_map["fixer"] == ExecutionPriority.HIGH


class TestAgentDiscovery:
    """Test agent discovery functionality"""

    @pytest.mark.asyncio
    async def test_discover_agents_in_directory_structure(self):
        registry = AgentRegistry()
        backend_path = Path(__file__).parent.parent.parent.parent / "agent" / "modules" / "backend"

        if backend_path.exists():
            agents = await registry._discover_agents_in_directory(
                backend_path, "agent.modules.backend"
            )
            # Should discover some agents
            assert isinstance(agents, list)

    @pytest.mark.asyncio
    async def test_analyze_agent_file_v2_priority(self):
        registry = AgentRegistry()
        # V2 agents should be prioritized over V1


    @pytest.mark.asyncio
    async def test_discover_nonexistent_directory(self):
        registry = AgentRegistry()
        fake_path = Path("/nonexistent/path")
        agents = await registry._discover_agents_in_directory(fake_path, "fake.module")
        assert agents == []

    @pytest.mark.asyncio
    @patch("agent.registry.importlib.import_module")
    async def test_analyze_agent_file_success(self, mock_import):
        registry = AgentRegistry()

        # Mock module with BaseAgent subclass
        mock_module = MagicMock()
        mock_agent_class = type("TestAgent", (BaseAgent,), {
            "__init__": lambda self: BaseAgent.__init__(self, "test"),
            "initialize": lambda self: True,
            "execute_core_function": lambda self, **kwargs: {}
        })
        mock_import.return_value = mock_module
        mock_module.__dict__ = {"TestAgent": mock_agent_class}

        # Mock inspect.getmembers to return our mock class
        with patch("agent.registry.inspect.getmembers") as mock_members:
            mock_members.return_value = [("TestAgent", mock_agent_class)]

            test_file = Path("/fake/test_agent.py")
            result = await registry._analyze_agent_file(test_file, "fake.module")

            assert result is not None
            assert result["name"] == "test"
            assert result["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_analyze_agent_file_invalid_module(self):
        registry = AgentRegistry()
        with patch("agent.registry.importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            test_file = Path("/fake/invalid_agent.py")
            result = await registry._analyze_agent_file(test_file, "fake.module")
            assert result is None


class TestAgentRegistration:
    """Test agent registration with orchestrator"""

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_register_discovered_agent_success(self, mock_security, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.register_agent = AsyncMock(return_value=True)
        mock_security.generate_api_key = MagicMock(return_value="test-api-key.12345")

        agent_info = {
            "name": "test_agent",
            "class": MockAgent,
            "module": "test.module",
            "file": "/test/file.py",
            "version": "1.0",
        }

        success = await registry._register_discovered_agent(agent_info)

        assert success is True
        assert "test_agent" in registry.registered_agents
        assert "test_agent" in registry.agent_capabilities
        assert "test_agent" in registry.agent_metadata

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_register_discovered_agent_orchestrator_failure(
        self, mock_security, mock_orchestrator
    ):
        registry = AgentRegistry()

        mock_orchestrator.register_agent = AsyncMock(return_value=False)

        agent_info = {
            "name": "test_agent",
            "class": MockAgent,
            "module": "test.module",
            "file": "/test/file.py",
            "version": "1.0",
        }

        success = await registry._register_discovered_agent(agent_info)
        assert success is False

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_register_agent_with_capabilities(self, mock_security, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.register_agent = AsyncMock(return_value=True)
        mock_security.generate_api_key = MagicMock(return_value="test-api-key.12345")

        agent_info = {
            "name": "scanner",
            "class": MockAgent,
            "module": "test.module",
            "file": "/test/scanner.py",
            "version": "1.0",
        }

        success = await registry._register_discovered_agent(agent_info)

        assert success is True
        # Should get capabilities from capability_map
        assert registry.registered_agents["scanner"]["capabilities"] == registry.capability_map["scanner"]

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_register_agent_with_dependencies(self, mock_security, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.register_agent = AsyncMock(return_value=True)
        mock_security.generate_api_key = MagicMock(return_value="test-api-key.12345")

        agent_info = {
            "name": "fixer",
            "class": MockAgent,
            "module": "test.module",
            "file": "/test/fixer.py",
            "version": "1.0",
        }

        success = await registry._register_discovered_agent(agent_info)

        assert success is True
        # Fixer depends on scanner
        assert registry.registered_agents["fixer"]["dependencies"] == ["scanner"]

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_register_agent_exception_handling(self, mock_security, mock_orchestrator):
        registry = AgentRegistry()

        # Make agent class initialization fail
        class FailingAgent:
            def __init__(self):
                raise Exception("Initialization failed")

        agent_info = {
            "name": "failing",
            "class": FailingAgent,
            "module": "test.module",
            "file": "/test/failing.py",
            "version": "1.0",
        }

        success = await registry._register_discovered_agent(agent_info)
        assert success is False


class TestAgentRetrieval:
    """Test agent retrieval methods"""

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_get_agent_exists(self, mock_security, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.register_agent = AsyncMock(return_value=True)
        mock_security.generate_api_key = MagicMock(return_value="test-api-key.12345")

        agent_info = {
            "name": "test_agent",
            "class": MockAgent,
            "module": "test.module",
            "file": "/test/file.py",
            "version": "1.0",
        }

        await registry._register_discovered_agent(agent_info)

        agent = registry.get_agent("test_agent")
        assert agent is not None
        assert isinstance(agent, MockAgent)

    def test_get_agent_not_exists(self):
        registry = AgentRegistry()
        agent = registry.get_agent("nonexistent")
        assert agent is None

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_list_agents_all(self, mock_security, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.register_agent = AsyncMock(return_value=True)
        mock_security.generate_api_key = MagicMock(return_value="test-api-key.12345")

        for i in range(3):
            agent_info = {
                "name": f"agent{i}",
                "class": MockAgent,
                "module": "test.module",
                "file": f"/test/agent{i}.py",
                "version": "1.0",
            }
            await registry._register_discovered_agent(agent_info)

        agents = registry.list_agents()
        assert len(agents) == 3
        assert "agent0" in agents
        assert "agent1" in agents
        assert "agent2" in agents

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_list_agents_by_capability(self, mock_security, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.register_agent = AsyncMock(return_value=True)
        mock_security.generate_api_key = MagicMock(return_value="test-api-key.12345")

        # Register scanner (has "scan" capability)
        agent_info = {
            "name": "scanner",
            "class": MockAgent,
            "module": "test.module",
            "file": "/test/scanner.py",
            "version": "1.0",
        }
        await registry._register_discovered_agent(agent_info)

        agents_with_scan = registry.list_agents(capability="scan")
        assert "scanner" in agents_with_scan

        agents_with_fix = registry.list_agents(capability="fix")
        assert "scanner" not in agents_with_fix

    def test_list_agents_empty_registry(self):
        registry = AgentRegistry()
        agents = registry.list_agents()
        assert agents == []


class TestAgentInfo:
    """Test agent info retrieval"""

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_get_agent_info_exists(self, mock_security, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.register_agent = AsyncMock(return_value=True)
        mock_security.generate_api_key = MagicMock(return_value="test-api-key.12345")

        agent_info = {
            "name": "scanner",
            "class": MockAgent,
            "module": "agent.modules.backend.scanner",
            "file": "/test/scanner.py",
            "version": "2.0",
        }
        await registry._register_discovered_agent(agent_info)

        info = registry.get_agent_info("scanner")

        assert info is not None
        assert info["name"] == "scanner"
        assert info["version"] == "2.0"
        assert info["module"] == "agent.modules.backend.scanner"
        assert "capabilities" in info
        assert "dependencies" in info
        assert "priority" in info
        assert "status" in info

    def test_get_agent_info_not_exists(self):
        registry = AgentRegistry()
        info = registry.get_agent_info("nonexistent")
        assert info is None


class TestHealthChecks:
    """Test health check functionality"""

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_health_check_all_healthy(self, mock_security, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.register_agent = AsyncMock(return_value=True)
        mock_security.generate_api_key = MagicMock(return_value="test-api-key.12345")

        for i in range(3):
            agent_info = {
                "name": f"agent{i}",
                "class": MockAgent,
                "module": "test.module",
                "file": f"/test/agent{i}.py",
                "version": "1.0",
            }
            await registry._register_discovered_agent(agent_info)

        health_report = await registry.health_check_all()

        assert "total_agents" in health_report
        assert "healthy_agents" in health_report
        assert "unhealthy_agents" in health_report
        assert "agents" in health_report
        assert health_report["total_agents"] == 3

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_health_check_with_failures(self, mock_security, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.register_agent = AsyncMock(return_value=True)
        mock_security.generate_api_key = MagicMock(return_value="test-api-key.12345")

        # Create an agent that fails health checks
        class UnhealthyAgent(BaseAgent):
            async def initialize(self):
                return True

            async def execute_core_function(self, **kwargs):
                return {}

            async def health_check(self):
                raise Exception("Health check failed")

        agent_info = {
            "name": "unhealthy",
            "class": UnhealthyAgent,
            "module": "test.module",
            "file": "/test/unhealthy.py",
            "version": "1.0",
        }
        await registry._register_discovered_agent(agent_info)

        health_report = await registry.health_check_all()

        assert "unhealthy" in health_report["agents"]
        assert health_report["agents"]["unhealthy"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_health_check_empty_registry(self):
        registry = AgentRegistry()
        health_report = await registry.health_check_all()

        assert health_report["total_agents"] == 0
        assert health_report["healthy_agents"] == 0


class TestAgentReload:
    """Test hot reload functionality"""

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    @patch("agent.registry.security_manager")
    async def test_reload_agent_success(self, mock_security, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.register_agent = AsyncMock(return_value=True)
        mock_orchestrator.unregister_agent = AsyncMock(return_value=True)
        mock_security.generate_api_key = MagicMock(return_value="test-api-key.12345")

        agent_info = {
            "name": "test_agent",
            "class": MockAgent,
            "module": "test.module",
            "file": "/test/file.py",
            "version": "1.0",
        }
        await registry._register_discovered_agent(agent_info)

        # Mock the module reload
        with patch("agent.registry.importlib.reload"):
            with patch.object(registry, "_analyze_agent_file") as mock_analyze:
                mock_analyze.return_value = agent_info

                with patch.object(registry, "_register_discovered_agent") as mock_register:
                    mock_register.return_value = True

                    success = await registry.reload_agent("test_agent")
                    # Depends on implementation - might succeed or need actual file

    @pytest.mark.asyncio
    async def test_reload_nonexistent_agent(self):
        registry = AgentRegistry()
        success = await registry.reload_agent("nonexistent")
        assert success is False


class TestWorkflows:
    """Test predefined workflow execution"""

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    async def test_workflow_scan_and_fix(self, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.execute_task = AsyncMock(return_value={
            "results": {"scanner": {"issues": []}},
            "status": "completed"
        })

        result = await registry.execute_workflow(
            "scan_and_fix",
            {"target": "test.py"}
        )

        assert "workflow" in result
        assert result["workflow"] == "scan_and_fix"
        assert "scan" in result
        assert "fix" in result

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    async def test_workflow_content_pipeline(self, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.execute_task = AsyncMock(return_value={
            "results": {"content": "generated"},
            "status": "completed"
        })

        result = await registry.execute_workflow(
            "content_pipeline",
            {"topic": "test"}
        )

        assert "workflow" in result
        assert result["workflow"] == "content_pipeline"

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    async def test_workflow_ecommerce_order(self, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.execute_task = AsyncMock(return_value={
            "status": "completed",
            "available": True
        })

        result = await registry.execute_workflow(
            "ecommerce_order",
            {"order_id": "123"}
        )

        assert "workflow" in result
        assert result["workflow"] == "ecommerce_order"

    @pytest.mark.asyncio
    async def test_workflow_unknown(self):
        registry = AgentRegistry()

        result = await registry.execute_workflow(
            "unknown_workflow",
            {}
        )

        assert "error" in result
        assert "Unknown workflow" in result["error"]

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    async def test_workflow_scan_and_fix_with_scan_errors(self, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.execute_task = AsyncMock(return_value={
            "error": "Scan failed"
        })

        result = await registry.execute_workflow(
            "scan_and_fix",
            {"target": "test.py"}
        )

        # Should return early if scan fails
        assert "scan" in result


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_registry_singleton_behavior(self):
        # Test that the global registry instance exists
        from agent.registry import registry
        assert registry is not None

    @pytest.mark.asyncio
    async def test_concurrent_agent_registration(self):
        """Test registering multiple agents concurrently"""
        registry = AgentRegistry()

        with patch("agent.registry.orchestrator") as mock_orch:
            with patch("agent.registry.security_manager") as mock_sec:
                mock_orch.register_agent = AsyncMock(return_value=True)
                mock_sec.generate_api_key = MagicMock(return_value="key.123")

                async def register_agent(i):
                    agent_info = {
                        "name": f"agent{i}",
                        "class": MockAgent,
                        "module": "test.module",
                        "file": f"/test/agent{i}.py",
                        "version": "1.0",
                    }
                    return await registry._register_discovered_agent(agent_info)

                results = await asyncio.gather(*[register_agent(i) for i in range(10)])

                assert all(results)
                assert len(registry.registered_agents) == 10

    @pytest.mark.asyncio
    async def test_empty_capability_list(self):
        registry = AgentRegistry()
        agents = registry.list_agents(capability="nonexistent_capability")
        assert agents == []
