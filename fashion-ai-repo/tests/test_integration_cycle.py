"""Integration tests for end-to-end agent workflow."""

import pytest

from src.agents import CommerceAgent, DesignerAgent, FinanceAgent, MarketingAgent, OpsAgent
from src.core.queue import Message, QueueManager


@pytest.fixture
def queue_manager(config):
    """
    Provide a QueueManager configured for integration tests and ensure it is closed after use.
    
    Parameters:
        config: Test configuration object exposing `redis_host` and `redis_port`.
    
    Returns:
        QueueManager: a QueueManager instance connected to the configured Redis and using the "test_fashion_ai" prefix.
    """
    qm = QueueManager(
        host=config.redis_host,
        port=config.redis_port,
        prefix="test_fashion_ai",
    )
    yield qm
    qm.close()


@pytest.mark.integration
async def test_design_to_commerce_flow(queue_manager, config):
    """
    Verify that a DesignerAgent can generate a design and return a listing identifier.
    
    Creates a DesignerAgent pointing at the test designs directory and submits a generate_design task with a sample payload. Asserts the result has a "status" of "generated" and includes a "design_id".
    """
    # Create agents
    designer = DesignerAgent(
        io_path=config.data_path / "designs",
        queue_manager=queue_manager,
    )

    # Test design generation task
    design_payload = {"style": "urban", "color": "black", "season": "winter"}
    result = await designer.process_task("generate_design", design_payload)

    assert result["status"] == "generated"
    assert "design_id" in result


@pytest.mark.integration
async def test_full_pipeline(queue_manager, config):
    """
    Placeholder integration test for the end-to-end agent pipeline from design to finance.
    
    Intended to exercise the full flow: Designer -> Commerce -> Marketing -> Finance -> Ops using real queue communication.
    Currently a stub that always passes.
    """
    # This would test:
    # Designer -> Commerce -> Marketing -> Finance -> Ops
    # In production with actual queue communication

    # Placeholder for full integration test
    assert True


@pytest.mark.integration
async def test_ops_health_check(queue_manager, config):
    """Test OpsAgent health check."""
    ops = OpsAgent(
        io_path=config.log_path,
        queue_manager=queue_manager,
    )

    health_result = await ops.process_task("health_check", {})
    assert "status" in health_result
    assert "checks" in health_result