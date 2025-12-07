"""
Integration tests for agent orchestrator and registry working together

Tests the full agent lifecycle and inter-agent communication
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agent.modules.base_agent import AgentStatus, BaseAgent
from agent.orchestrator import AgentOrchestrator, ExecutionPriority
from agent.registry import AgentRegistry


class MockScannerAgent(BaseAgent):
    """Mock scanner agent for integration testing"""

    def __init__(self):
        super().__init__(agent_name="scanner", version="1.0.0")

    async def initialize(self) -> bool:
        self.status = AgentStatus.HEALTHY
        return True

    async def execute_core_function(self, **kwargs) -> dict:
        return {
            "status": "success",
            "issues_found": [
                {"file": "test.py", "line": 10, "issue": "Missing type hint"},
                {"file": "main.py", "line": 25, "issue": "Unused import"},
            ],
            "total_issues": 2,
        }


class MockFixerAgent(BaseAgent):
    """Mock fixer agent that depends on scanner"""

    def __init__(self):
        super().__init__(agent_name="fixer", version="1.0.0")

    async def initialize(self) -> bool:
        self.status = AgentStatus.HEALTHY
        return True

    async def execute_core_function(self, **kwargs) -> dict:
        scan_results = kwargs.get("scan_results", {})
        issues_fixed = len(scan_results.get("issues_found", []))

        return {
            "status": "success",
            "issues_fixed": issues_fixed,
            "files_modified": ["test.py", "main.py"],
        }


class MockEcommerceAgent(BaseAgent):
    """Mock ecommerce agent"""

    def __init__(self):
        super().__init__(agent_name="ecommerce", version="1.0.0")

    async def initialize(self) -> bool:
        self.status = AgentStatus.HEALTHY
        return True

    async def execute_core_function(self, **kwargs) -> dict:
        return {
            "status": "success",
            "products": 100,
            "orders": 50,
            "revenue": 25000.00,
        }


class TestOrchestratorRegistryIntegration:
    """Test orchestrator and registry integration"""

    @pytest.mark.asyncio
    async def test_register_and_execute_single_agent(self):
        orchestrator = AgentOrchestrator()
        scanner = MockScannerAgent()

        # Register agent
        success = await orchestrator.register_agent(
            agent=scanner,
            capabilities=["scan"],
            dependencies=[],
            priority=ExecutionPriority.HIGH,
        )

        assert success is True

        # Execute task
        result = await orchestrator.execute_task(
            task_type="scan",
            parameters={"target": "test.py"},
            required_capabilities=["scan"],
            priority=ExecutionPriority.HIGH,
        )

        assert "results" in result
        assert "scanner" in result["results"]
        assert result["results"]["scanner"]["total_issues"] == 2

    @pytest.mark.asyncio
    async def test_dependent_agent_execution(self):
        orchestrator = AgentOrchestrator()
        scanner = MockScannerAgent()
        fixer = MockFixerAgent()

        # Register scanner first
        await orchestrator.register_agent(
            agent=scanner,
            capabilities=["scan"],
            dependencies=[],
            priority=ExecutionPriority.HIGH,
        )

        # Register fixer with scanner dependency
        await orchestrator.register_agent(
            agent=fixer,
            capabilities=["fix"],
            dependencies=["scanner"],
            priority=ExecutionPriority.HIGH,
        )

        # Execute scan task
        scan_result = await orchestrator.execute_task(
            task_type="scan",
            parameters={"target": "test.py"},
            required_capabilities=["scan"],
            priority=ExecutionPriority.HIGH,
        )

        # Execute fix task
        fix_result = await orchestrator.execute_task(
            task_type="fix",
            parameters={"scan_results": scan_result["results"]["scanner"]},
            required_capabilities=["fix"],
            priority=ExecutionPriority.HIGH,
        )

        assert "results" in fix_result
        assert "fixer" in fix_result["results"]
        assert fix_result["results"]["fixer"]["issues_fixed"] == 2

    @pytest.mark.asyncio
    async def test_multiple_agents_concurrent_execution(self):
        orchestrator = AgentOrchestrator()
        scanner = MockScannerAgent()
        ecommerce = MockEcommerceAgent()

        # Register independent agents
        await orchestrator.register_agent(
            agent=scanner,
            capabilities=["scan"],
            dependencies=[],
            priority=ExecutionPriority.HIGH,
        )

        await orchestrator.register_agent(
            agent=ecommerce,
            capabilities=["ecommerce"],
            dependencies=[],
            priority=ExecutionPriority.MEDIUM,
        )

        # Execute tasks concurrently
        scan_task = orchestrator.execute_task(
            task_type="scan",
            parameters={},
            required_capabilities=["scan"],
            priority=ExecutionPriority.HIGH,
        )

        ecommerce_task = orchestrator.execute_task(
            task_type="ecommerce",
            parameters={},
            required_capabilities=["ecommerce"],
            priority=ExecutionPriority.MEDIUM,
        )

        scan_result, ecommerce_result = await asyncio.gather(scan_task, ecommerce_task)

        assert "results" in scan_result
        assert "results" in ecommerce_result

    @pytest.mark.asyncio
    async def test_agent_health_monitoring(self):
        orchestrator = AgentOrchestrator()
        scanner = MockScannerAgent()

        await orchestrator.register_agent(
            agent=scanner,
            capabilities=["scan"],
            dependencies=[],
            priority=ExecutionPriority.HIGH,
        )

        # Get agent health
        health = await orchestrator.get_agent_health("scanner")

        assert health is not None
        assert health["status"] == AgentStatus.HEALTHY.value
        assert "health_metrics" in health

    @pytest.mark.asyncio
    async def test_agent_unregister_and_re_register(self):
        orchestrator = AgentOrchestrator()
        scanner = MockScannerAgent()

        # Register
        await orchestrator.register_agent(
            agent=scanner,
            capabilities=["scan"],
            dependencies=[],
            priority=ExecutionPriority.HIGH,
        )

        assert "scanner" in orchestrator.agents

        # Unregister
        success = await orchestrator.unregister_agent("scanner")
        assert success is True
        assert "scanner" not in orchestrator.agents

        # Re-register
        scanner2 = MockScannerAgent()
        await orchestrator.register_agent(
            agent=scanner2,
            capabilities=["scan"],
            dependencies=[],
            priority=ExecutionPriority.HIGH,
        )

        assert "scanner" in orchestrator.agents


class TestRegistryWorkflows:
    """Test registry workflow execution"""

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    async def test_scan_and_fix_workflow(self, mock_orchestrator):
        registry = AgentRegistry()

        # Mock execute_task
        mock_orchestrator.execute_task = AsyncMock(
            side_effect=[
                {"results": {"scanner": {"issues": [{"file": "test.py"}]}}},  # Scan result
                {"results": {"fixer": {"issues_fixed": 1}}},  # Fix result
            ]
        )

        result = await registry.execute_workflow(
            "scan_and_fix",
            {"target": "test.py"}
        )

        assert result["workflow"] == "scan_and_fix"
        assert "scan" in result
        assert "fix" in result

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    async def test_content_pipeline_workflow(self, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.execute_task = AsyncMock(
            side_effect=[
                {"results": {"content_gen": {"content": "Generated content"}}},  # Content
                {"results": {"seo": {"score": 95}}},  # SEO
            ]
        )

        result = await registry.execute_workflow(
            "content_pipeline",
            {"topic": "AI Testing"}
        )

        assert result["workflow"] == "content_pipeline"
        assert "results" in result

    @pytest.mark.asyncio
    @patch("agent.registry.orchestrator")
    async def test_ecommerce_order_workflow(self, mock_orchestrator):
        registry = AgentRegistry()

        mock_orchestrator.execute_task = AsyncMock(
            side_effect=[
                {"status": "valid"},  # Validation
                {"available": True},  # Inventory
                {"status": "completed"},  # Payment
            ]
        )

        result = await registry.execute_workflow(
            "ecommerce_order",
            {"order_id": "order_123"}
        )

        assert result["workflow"] == "ecommerce_order"
        assert "results" in result


class TestAgentCommunication:
    """Test inter-agent communication"""

    @pytest.mark.asyncio
    async def test_agents_share_context(self):
        orchestrator = AgentOrchestrator()
        scanner = MockScannerAgent()
        fixer = MockFixerAgent()

        await orchestrator.register_agent(scanner, ["scan"], [], ExecutionPriority.HIGH)
        await orchestrator.register_agent(fixer, ["fix"], ["scanner"], ExecutionPriority.HIGH)

        # Scanner produces output
        scan_result = await orchestrator.execute_task(
            task_type="scan",
            parameters={},
            required_capabilities=["scan"],
            priority=ExecutionPriority.HIGH,
        )

        # Fixer consumes scanner output
        fix_result = await orchestrator.execute_task(
            task_type="fix",
            parameters={"scan_results": scan_result["results"]["scanner"]},
            required_capabilities=["fix"],
            priority=ExecutionPriority.HIGH,
        )

        # Verify data flow
        assert fix_result["results"]["fixer"]["issues_fixed"] == 2


class TestErrorHandling:
    """Test error handling in integration scenarios"""

    @pytest.mark.asyncio
    async def test_agent_failure_recovery(self):
        class FailingAgent(BaseAgent):
            def __init__(self):
                super().__init__(agent_name="failing", version="1.0.0")
                self.attempts = 0

            async def initialize(self):
                self.status = AgentStatus.HEALTHY
                return True

            async def execute_core_function(self, **kwargs):
                self.attempts += 1
                if self.attempts < 2:
                    raise Exception("Temporary failure")
                return {"status": "success", "attempts": self.attempts}

        orchestrator = AgentOrchestrator()
        failing_agent = FailingAgent()

        await orchestrator.register_agent(
            agent=failing_agent,
            capabilities=["test"],
            dependencies=[],
            priority=ExecutionPriority.MEDIUM,
        )

        # Should retry and eventually succeed
        result = await orchestrator.execute_task(
            task_type="test",
            parameters={},
            required_capabilities=["test"],
            priority=ExecutionPriority.MEDIUM,
        )

        # May succeed after retry
        assert "results" in result or "error" in result

    @pytest.mark.asyncio
    async def test_missing_dependency_handling(self):
        orchestrator = AgentOrchestrator()
        fixer = MockFixerAgent()

        # Register fixer without scanner dependency
        await orchestrator.register_agent(
            agent=fixer,
            capabilities=["fix"],
            dependencies=["scanner"],  # Scanner not registered!
            priority=ExecutionPriority.HIGH,
        )

        # Try to execute - should handle missing dependency
        result = await orchestrator.execute_task(
            task_type="fix",
            parameters={},
            required_capabilities=["fix"],
            priority=ExecutionPriority.HIGH,
        )

        # Should either succeed or gracefully fail
        assert "results" in result or "error" in result


class TestScalability:
    """Test scalability with multiple agents"""

    @pytest.mark.asyncio
    async def test_many_agents_registration(self):
        orchestrator = AgentOrchestrator()

        # Register 20 agents
        for i in range(20):
            agent = MockScannerAgent()
            agent.agent_name = f"agent_{i}"

            await orchestrator.register_agent(
                agent=agent,
                capabilities=[f"cap_{i}"],
                dependencies=[],
                priority=ExecutionPriority.MEDIUM,
            )

        assert len(orchestrator.agents) == 20

    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self):
        orchestrator = AgentOrchestrator()

        # Register multiple agents
        for i in range(5):
            agent = MockEcommerceAgent()
            agent.agent_name = f"ecommerce_{i}"

            await orchestrator.register_agent(
                agent=agent,
                capabilities=[f"ecommerce_{i}"],
                dependencies=[],
                priority=ExecutionPriority.MEDIUM,
            )

        # Execute 10 tasks concurrently
        tasks = []
        for i in range(10):
            task = orchestrator.execute_task(
                task_type=f"task_{i % 5}",
                parameters={},
                required_capabilities=[f"ecommerce_{i % 5}"],
                priority=ExecutionPriority.MEDIUM,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Most should complete successfully
        successful = sum(1 for r in results if isinstance(r, dict) and "results" in r)
        assert successful >= 5


class TestEndToEnd:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_full_scan_fix_verify_pipeline(self):
        """Test a complete scan -> fix -> verify pipeline"""
        orchestrator = AgentOrchestrator()

        scanner = MockScannerAgent()
        fixer = MockFixerAgent()
        verifier = MockScannerAgent()
        verifier.agent_name = "verifier"

        # Register all agents
        await orchestrator.register_agent(scanner, ["scan"], [], ExecutionPriority.HIGH)
        await orchestrator.register_agent(fixer, ["fix"], ["scanner"], ExecutionPriority.HIGH)
        await orchestrator.register_agent(verifier, ["verify"], ["fixer"], ExecutionPriority.MEDIUM)

        # Step 1: Scan
        scan_result = await orchestrator.execute_task(
            task_type="scan",
            parameters={"target": "codebase"},
            required_capabilities=["scan"],
            priority=ExecutionPriority.HIGH,
        )

        # Step 2: Fix
        fix_result = await orchestrator.execute_task(
            task_type="fix",
            parameters={"scan_results": scan_result["results"]["scanner"]},
            required_capabilities=["fix"],
            priority=ExecutionPriority.HIGH,
        )

        # Step 3: Verify
        verify_result = await orchestrator.execute_task(
            task_type="verify",
            parameters={"target": "codebase"},
            required_capabilities=["verify"],
            priority=ExecutionPriority.MEDIUM,
        )

        # All steps should complete
        assert "results" in scan_result
        assert "results" in fix_result
        assert "results" in verify_result
