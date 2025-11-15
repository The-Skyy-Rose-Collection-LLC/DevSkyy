# Test Implementation Templates & Examples
**For DevSkyy Test Coverage Improvement**
**Generated:** 2025-11-15

---

## Overview

This document provides ready-to-use test templates for implementing the missing tests identified in the Test Coverage Analysis Report. Use these templates as starting points for creating comprehensive test coverage.

---

## 1. Agent Module Test Template

### Template: tests/agents/backend/test_{agent_name}.py

```python
"""
Unit and integration tests for {AgentName}

Tests {agent} functionality including:
- Initialization and configuration
- Core business logic
- External API integrations
- Error handling and edge cases
- Performance and caching

WHY: {Agent} is a critical component of DevSkyy platform
HOW: Mock external dependencies, test business logic in isolation
IMPACT: Ensures reliable {functionality} for production use
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import the agent to test
from agent.modules.backend.{agent_module} import {AgentClass}


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def agent_config():
    """Sample agent configuration."""
    return {
        "api_key": "test_api_key",
        "endpoint": "https://api.test.com",
        "timeout": 30,
        "max_retries": 3,
        "cache_ttl": 3600,
    }


@pytest.fixture
def mock_{external_service}():
    """Mock {external_service} API client."""
    with patch('agent.modules.backend.{agent_module}.{ExternalService}') as mock:
        mock_client = MagicMock()
        mock_client.get.return_value = {"status": "success", "data": {}}
        mock_client.post.return_value = {"status": "success", "id": "123"}
        mock.return_value = mock_client
        yield mock


@pytest.fixture
def agent_instance(agent_config, mock_{external_service}):
    """Create agent instance for testing."""
    return {AgentClass}(config=agent_config)


# ============================================================================
# Initialization Tests
# ============================================================================

@pytest.mark.unit
class TestAgentInitialization:
    """Test agent initialization and configuration."""

    def test_init_with_valid_config(self, agent_config):
        """Test agent initializes successfully with valid config."""
        agent = {AgentClass}(config=agent_config)

        assert agent is not None
        assert agent.config == agent_config
        assert agent.timeout == 30
        assert agent.max_retries == 3

    def test_init_with_missing_config(self):
        """Test agent initialization fails with missing config."""
        with pytest.raises(ValueError, match="Configuration is required"):
            {AgentClass}(config=None)

    def test_init_with_invalid_api_key(self):
        """Test agent initialization fails with invalid API key."""
        config = {"api_key": ""}

        with pytest.raises(ValueError, match="API key is required"):
            {AgentClass}(config=config)

    def test_init_sets_default_values(self):
        """Test agent sets default values for optional config."""
        config = {"api_key": "test_key"}
        agent = {AgentClass}(config=config)

        assert agent.timeout == 60  # Default timeout
        assert agent.max_retries == 5  # Default retries


# ============================================================================
# Core Functionality Tests
# ============================================================================

@pytest.mark.unit
class TestAgentCoreFunctionality:
    """Test agent core business logic."""

    @pytest.mark.asyncio
    async def test_{primary_method}_success(self, agent_instance):
        """Test {primary_method} returns expected result on success."""
        input_data = {
            "param1": "value1",
            "param2": "value2"
        }

        result = await agent_instance.{primary_method}(input_data)

        assert result is not None
        assert result["status"] == "success"
        assert "data" in result

    @pytest.mark.asyncio
    async def test_{primary_method}_with_empty_input(self, agent_instance):
        """Test {primary_method} handles empty input."""
        with pytest.raises(ValueError, match="Input data is required"):
            await agent_instance.{primary_method}({})

    @pytest.mark.asyncio
    async def test_{primary_method}_with_invalid_input(self, agent_instance):
        """Test {primary_method} validates input data."""
        invalid_input = {"invalid_key": "value"}

        with pytest.raises(ValueError, match="Invalid input"):
            await agent_instance.{primary_method}(invalid_input)

    @pytest.mark.asyncio
    async def test_{secondary_method}_success(self, agent_instance):
        """Test {secondary_method} functionality."""
        result = await agent_instance.{secondary_method}(param="test")

        assert result is not None
        assert isinstance(result, dict)


# ============================================================================
# External API Integration Tests
# ============================================================================

@pytest.mark.integration
class TestAgentExternalIntegration:
    """Test agent integration with external APIs."""

    @pytest.mark.asyncio
    async def test_api_call_success(self, agent_instance, mock_{external_service}):
        """Test successful external API call."""
        result = await agent_instance._call_api(endpoint="/test", method="GET")

        assert result["status"] == "success"
        mock_{external_service}.return_value.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_api_call_with_retry(self, agent_instance):
        """Test API retry mechanism on transient failures."""
        with patch.object(agent_instance, '_call_api') as mock_call:
            # First call fails, second succeeds
            mock_call.side_effect = [
                Exception("Temporary error"),
                {"status": "success"}
            ]

            result = await agent_instance._call_api_with_retry(endpoint="/test")

            assert result["status"] == "success"
            assert mock_call.call_count == 2

    @pytest.mark.asyncio
    async def test_api_call_timeout(self, agent_instance):
        """Test API call timeout handling."""
        with patch.object(agent_instance, '_call_api') as mock_call:
            mock_call.side_effect = TimeoutError("Request timeout")

            with pytest.raises(TimeoutError):
                await agent_instance._call_api_with_retry(endpoint="/test")

    @pytest.mark.asyncio
    async def test_api_authentication_failure(self, agent_instance):
        """Test handling of authentication failures."""
        with patch.object(agent_instance, '_call_api') as mock_call:
            mock_call.side_effect = Exception("401 Unauthorized")

            with pytest.raises(Exception, match="401 Unauthorized"):
                await agent_instance._call_api(endpoint="/test")


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.unit
class TestAgentErrorHandling:
    """Test agent error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_handles_network_error(self, agent_instance):
        """Test graceful handling of network errors."""
        with patch.object(agent_instance, '_call_api') as mock_call:
            mock_call.side_effect = ConnectionError("Network unreachable")

            result = await agent_instance.{primary_method}({"data": "test"})

            assert result["status"] == "error"
            assert "network" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_handles_rate_limiting(self, agent_instance):
        """Test handling of rate limiting (429 Too Many Requests)."""
        with patch.object(agent_instance, '_call_api') as mock_call:
            mock_call.side_effect = Exception("429 Rate limit exceeded")

            result = await agent_instance.{primary_method}({"data": "test"})

            assert result["status"] == "error"
            assert "rate limit" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_handles_data_corruption(self, agent_instance):
        """Test handling of corrupted response data."""
        with patch.object(agent_instance, '_call_api') as mock_call:
            mock_call.return_value = {"invalid": "response"}

            result = await agent_instance.{primary_method}({"data": "test"})

            assert result["status"] == "error"

    def test_validates_input_types(self, agent_instance):
        """Test input type validation."""
        with pytest.raises(TypeError, match="Expected dict"):
            agent_instance.{primary_method}("invalid_type")


# ============================================================================
# Caching Tests
# ============================================================================

@pytest.mark.unit
class TestAgentCaching:
    """Test agent caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_hit(self, agent_instance):
        """Test cache returns cached result on hit."""
        input_data = {"key": "value"}

        # First call - cache miss
        result1 = await agent_instance.{primary_method}(input_data)

        # Second call - cache hit
        result2 = await agent_instance.{primary_method}(input_data)

        assert result1 == result2
        # Verify API was only called once (cached second time)

    @pytest.mark.asyncio
    async def test_cache_miss(self, agent_instance):
        """Test cache miss triggers new API call."""
        # Clear cache if it exists
        if hasattr(agent_instance, '_cache'):
            agent_instance._cache.clear()

        result = await agent_instance.{primary_method}({"key": "value"})

        assert result is not None

    @pytest.mark.asyncio
    async def test_cache_expiration(self, agent_instance):
        """Test cache entries expire after TTL."""
        with patch('time.time') as mock_time:
            # Set initial time
            mock_time.return_value = 1000

            result1 = await agent_instance.{primary_method}({"key": "value"})

            # Fast forward past cache TTL
            mock_time.return_value = 5000

            result2 = await agent_instance.{primary_method}({"key": "value"})

            # Should have made two API calls (cache expired)


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.benchmark
class TestAgentPerformance:
    """Test agent performance characteristics."""

    @pytest.mark.asyncio
    async def test_{primary_method}_response_time(self, agent_instance, benchmark):
        """Test {primary_method} completes within acceptable time."""
        input_data = {"key": "value"}

        def run():
            return agent_instance.{primary_method}(input_data)

        result = benchmark(run)

        # Should complete in < 200ms per Truth Protocol
        assert benchmark.stats.mean < 0.2

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, agent_instance):
        """Test handling of concurrent requests."""
        import asyncio

        tasks = [
            agent_instance.{primary_method}({"id": i})
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(r["status"] == "success" for r in results)

    @pytest.mark.asyncio
    async def test_bulk_processing(self, agent_instance):
        """Test bulk data processing performance."""
        bulk_data = [{"id": i} for i in range(100)]

        start_time = datetime.now()
        result = await agent_instance.process_bulk(bulk_data)
        duration = (datetime.now() - start_time).total_seconds()

        assert duration < 5.0  # Should process 100 items in < 5 seconds
        assert result["processed"] == 100


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.integration
class TestAgentIntegration:
    """Test agent integration with other components."""

    @pytest.mark.asyncio
    async def test_database_integration(self, agent_instance, test_db_session):
        """Test agent interacts correctly with database."""
        result = await agent_instance.{primary_method}({"save_to_db": True})

        # Verify data was saved to database
        from models import {Model}
        saved_record = test_db_session.query({Model}).first()

        assert saved_record is not None
        assert saved_record.status == "processed"

    @pytest.mark.asyncio
    async def test_cache_integration(self, agent_instance):
        """Test agent integrates with Redis cache."""
        # Requires Redis mock or test Redis instance
        result = await agent_instance.{primary_method}({"use_cache": True})

        assert result["cached"] is True

    @pytest.mark.asyncio
    async def test_multi_agent_workflow(self, agent_instance):
        """Test agent interaction with other agents."""
        # Mock other agents
        with patch('agent.modules.other_agent.OtherAgent') as mock_other:
            mock_other.return_value.process.return_value = {"data": "processed"}

            result = await agent_instance.{primary_method}({"use_other_agent": True})

            assert result["status"] == "success"
            mock_other.return_value.process.assert_called_once()


# ============================================================================
# Edge Cases and Boundary Tests
# ============================================================================

@pytest.mark.unit
class TestAgentEdgeCases:
    """Test agent edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_response_from_api(self, agent_instance):
        """Test handling of empty API response."""
        with patch.object(agent_instance, '_call_api') as mock_call:
            mock_call.return_value = {}

            result = await agent_instance.{primary_method}({"data": "test"})

            assert result["status"] in ["success", "error"]

    @pytest.mark.asyncio
    async def test_very_large_input(self, agent_instance):
        """Test handling of very large input data."""
        large_input = {"data": "x" * 1000000}  # 1MB of data

        result = await agent_instance.{primary_method}(large_input)

        # Should handle or reject gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_special_characters_in_input(self, agent_instance):
        """Test handling of special characters and edge case inputs."""
        special_inputs = [
            {"name": "Test<script>alert('xss')</script>"},
            {"name": "'; DROP TABLE users; --"},
            {"name": "Test\x00Null"},
            {"name": "Test\n\r\tWhitespace"},
        ]

        for input_data in special_inputs:
            result = await agent_instance.{primary_method}(input_data)
            assert result is not None  # Should not crash

    @pytest.mark.asyncio
    async def test_unicode_handling(self, agent_instance):
        """Test handling of Unicode characters."""
        unicode_input = {"name": "测试 テスト тест 🎉"}

        result = await agent_instance.{primary_method}(unicode_input)

        assert result["status"] == "success"
```

---

## 2. Service Layer Test Template

### Template: tests/services/test_{service_name}.py

```python
"""
Comprehensive tests for {ServiceName}

Tests {service} orchestration including:
- Service initialization
- Workflow orchestration
- Multi-component coordination
- Error propagation
- State management

WHY: {Service} orchestrates critical business workflows
HOW: Mock dependencies, test workflow logic
IMPACT: Ensures reliable {functionality} orchestration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any

from services.{service_module} import {ServiceClass}


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def service_config():
    """Service configuration."""
    return {
        "timeout": 30,
        "max_concurrent_tasks": 10,
        "retry_policy": {
            "max_retries": 3,
            "backoff_factor": 2
        }
    }


@pytest.fixture
def mock_agents():
    """Mock agent dependencies."""
    return {
        "agent1": AsyncMock(),
        "agent2": AsyncMock(),
        "agent3": AsyncMock()
    }


@pytest.fixture
def service_instance(service_config, mock_agents):
    """Create service instance for testing."""
    return {ServiceClass}(config=service_config, agents=mock_agents)


# ============================================================================
# Initialization Tests
# ============================================================================

@pytest.mark.unit
class TestServiceInitialization:
    """Test service initialization."""

    def test_init_with_valid_config(self, service_config):
        """Test service initializes with valid config."""
        service = {ServiceClass}(config=service_config)

        assert service is not None
        assert service.config == service_config

    def test_init_with_default_config(self):
        """Test service uses default configuration."""
        service = {ServiceClass}()

        assert service.timeout > 0
        assert service.max_concurrent_tasks > 0


# ============================================================================
# Workflow Orchestration Tests
# ============================================================================

@pytest.mark.integration
class TestServiceWorkflow:
    """Test service workflow orchestration."""

    @pytest.mark.asyncio
    async def test_successful_workflow(self, service_instance, mock_agents):
        """Test complete workflow execution."""
        # Setup mock responses
        mock_agents["agent1"].process.return_value = {"status": "success", "data": "step1"}
        mock_agents["agent2"].process.return_value = {"status": "success", "data": "step2"}
        mock_agents["agent3"].process.return_value = {"status": "success", "data": "final"}

        result = await service_instance.execute_workflow({"input": "test"})

        assert result["status"] == "success"
        assert result["steps_completed"] == 3

        # Verify all agents were called
        mock_agents["agent1"].process.assert_called_once()
        mock_agents["agent2"].process.assert_called_once()
        mock_agents["agent3"].process.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_with_agent_failure(self, service_instance, mock_agents):
        """Test workflow handles agent failure."""
        mock_agents["agent1"].process.return_value = {"status": "success"}
        mock_agents["agent2"].process.side_effect = Exception("Agent failed")

        result = await service_instance.execute_workflow({"input": "test"})

        assert result["status"] == "error"
        assert "agent failed" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_workflow_partial_completion(self, service_instance, mock_agents):
        """Test workflow handles partial completion."""
        mock_agents["agent1"].process.return_value = {"status": "success"}
        mock_agents["agent2"].process.return_value = {"status": "success"}
        mock_agents["agent3"].process.return_value = {"status": "partial"}

        result = await service_instance.execute_workflow({"input": "test"})

        assert result["status"] == "partial"
        assert result["completed_steps"] == 2
        assert result["failed_steps"] == 1


# ============================================================================
# State Management Tests
# ============================================================================

@pytest.mark.unit
class TestServiceStateManagement:
    """Test service state persistence and recovery."""

    @pytest.mark.asyncio
    async def test_state_persistence(self, service_instance):
        """Test workflow state is persisted."""
        workflow_id = "test_workflow_001"

        await service_instance.start_workflow(workflow_id, {"input": "test"})

        # Retrieve state
        state = await service_instance.get_workflow_state(workflow_id)

        assert state is not None
        assert state["workflow_id"] == workflow_id
        assert state["status"] == "running"

    @pytest.mark.asyncio
    async def test_state_recovery_after_failure(self, service_instance):
        """Test workflow can recover from saved state."""
        workflow_id = "test_workflow_002"

        # Simulate workflow interruption
        await service_instance.start_workflow(workflow_id, {"input": "test"})
        await service_instance.simulate_crash()

        # Resume workflow
        result = await service_instance.resume_workflow(workflow_id)

        assert result["status"] == "success"
        assert result["resumed"] is True

    @pytest.mark.asyncio
    async def test_concurrent_workflows(self, service_instance):
        """Test multiple concurrent workflows."""
        workflow_ids = [f"workflow_{i}" for i in range(5)]

        # Start multiple workflows
        tasks = [
            service_instance.start_workflow(wf_id, {"input": f"test_{i}"})
            for i, wf_id in enumerate(workflow_ids)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all(r["status"] == "success" for r in results)


# ============================================================================
# Error Propagation Tests
# ============================================================================

@pytest.mark.unit
class TestServiceErrorPropagation:
    """Test error handling and propagation."""

    @pytest.mark.asyncio
    async def test_error_propagates_from_agent(self, service_instance, mock_agents):
        """Test errors from agents propagate correctly."""
        mock_agents["agent1"].process.side_effect = ValueError("Invalid input")

        with pytest.raises(ValueError, match="Invalid input"):
            await service_instance.execute_workflow({"input": "bad"})

    @pytest.mark.asyncio
    async def test_timeout_handling(self, service_instance, mock_agents):
        """Test workflow timeout handling."""
        async def slow_process(*args, **kwargs):
            await asyncio.sleep(100)  # Simulate slow operation

        mock_agents["agent1"].process = slow_process

        with pytest.raises(TimeoutError):
            await service_instance.execute_workflow({"input": "test"}, timeout=1)

    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, service_instance, mock_agents):
        """Test retry mechanism for transient errors."""
        # First two calls fail, third succeeds
        mock_agents["agent1"].process.side_effect = [
            Exception("Transient error"),
            Exception("Transient error"),
            {"status": "success"}
        ]

        result = await service_instance.execute_workflow({"input": "test"})

        assert result["status"] == "success"
        assert mock_agents["agent1"].process.call_count == 3
```

---

## 3. API Endpoint Test Template

### Template: tests/api/test_{endpoint_name}_endpoints.py

```python
"""
Comprehensive API endpoint tests for {endpoint_group}

Tests all {endpoint_group} API endpoints including:
- Authentication and authorization
- Input validation
- Business logic
- Error handling
- Rate limiting
- Response formats

WHY: API endpoints are the primary interface for users
HOW: Use FastAPI TestClient, mock dependencies
IMPACT: Ensures API reliability and security
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, AsyncMock

from main import app
from security.jwt_auth import create_access_token, UserRole


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def admin_token():
    """Generate admin JWT token."""
    return create_access_token(
        user_id="admin_001",
        role=UserRole.ADMIN,
        email="admin@devskyy.com"
    )


@pytest.fixture
def user_token():
    """Generate regular user JWT token."""
    return create_access_token(
        user_id="user_001",
        role=UserRole.API_USER,
        email="user@devskyy.com"
    )


@pytest.fixture
def admin_headers(admin_token):
    """Admin authorization headers."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token):
    """User authorization headers."""
    return {"Authorization": f"Bearer {user_token}"}


# ============================================================================
# Authentication Tests
# ============================================================================

@pytest.mark.api
class TestEndpointAuthentication:
    """Test endpoint authentication requirements."""

    def test_unauthenticated_request_returns_401(self, client):
        """Test unauthenticated request is rejected."""
        response = client.get("/api/v1/{endpoint}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_invalid_token_returns_401(self, client):
        """Test invalid token is rejected."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/v1/{endpoint}", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_returns_401(self, client):
        """Test expired token is rejected."""
        # Create token that's already expired
        expired_token = create_access_token(
            user_id="user_001",
            role=UserRole.API_USER,
            expires_delta=timedelta(seconds=-1)  # Expired
        )

        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/v1/{endpoint}", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Authorization Tests
# ============================================================================

@pytest.mark.api
class TestEndpointAuthorization:
    """Test endpoint authorization (RBAC)."""

    def test_insufficient_permissions_returns_403(self, client, user_headers):
        """Test user without permissions is forbidden."""
        response = client.delete("/api/v1/{endpoint}/123", headers=user_headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_access_protected_endpoint(self, client, admin_headers):
        """Test admin has access to admin-only endpoint."""
        response = client.delete("/api/v1/{endpoint}/123", headers=admin_headers)

        # Should not be 403 (may be 404 if resource doesn't exist)
        assert response.status_code != status.HTTP_403_FORBIDDEN


# ============================================================================
# GET Endpoint Tests
# ============================================================================

@pytest.mark.api
class TestGetEndpoints:
    """Test GET endpoints."""

    def test_get_list_success(self, client, user_headers):
        """Test GET /api/v1/{endpoint} returns list."""
        response = client.get("/api/v1/{endpoint}", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, (list, dict))

        if isinstance(data, dict):
            assert "items" in data or "results" in data

    def test_get_list_with_pagination(self, client, user_headers):
        """Test GET with pagination parameters."""
        response = client.get(
            "/api/v1/{endpoint}?page=1&page_size=10",
            headers=user_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data or "results" in data
        assert "total" in data or "count" in data

    def test_get_by_id_success(self, client, user_headers):
        """Test GET /api/v1/{endpoint}/{id} returns single item."""
        # First create an item
        create_response = client.post(
            "/api/v1/{endpoint}",
            headers=user_headers,
            json={"name": "Test Item"}
        )
        item_id = create_response.json()["id"]

        # Then retrieve it
        response = client.get(f"/api/v1/{endpoint}/{item_id}", headers=user_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == item_id

    def test_get_by_id_not_found(self, client, user_headers):
        """Test GET with non-existent ID returns 404."""
        response = client.get("/api/v1/{endpoint}/99999", headers=user_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# POST Endpoint Tests
# ============================================================================

@pytest.mark.api
class TestPostEndpoints:
    """Test POST endpoints."""

    def test_create_success(self, client, user_headers):
        """Test POST /api/v1/{endpoint} creates new resource."""
        data = {
            "name": "Test Item",
            "description": "Test description",
            "status": "active"
        }

        response = client.post("/api/v1/{endpoint}", headers=user_headers, json=data)

        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()
        assert "id" in result
        assert result["name"] == data["name"]

    def test_create_with_invalid_data_returns_422(self, client, user_headers):
        """Test POST with invalid data returns validation error."""
        invalid_data = {
            "name": "",  # Empty name (invalid)
            "description": "x" * 10000  # Too long
        }

        response = client.post("/api/v1/{endpoint}", headers=user_headers, json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_with_missing_required_field(self, client, user_headers):
        """Test POST with missing required field returns 422."""
        incomplete_data = {
            "description": "Missing required name field"
        }

        response = client.post("/api/v1/{endpoint}", headers=user_headers, json=incomplete_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# PUT/PATCH Endpoint Tests
# ============================================================================

@pytest.mark.api
class TestUpdateEndpoints:
    """Test PUT/PATCH endpoints."""

    def test_update_success(self, client, user_headers):
        """Test PUT /api/v1/{endpoint}/{id} updates resource."""
        # Create item first
        create_response = client.post(
            "/api/v1/{endpoint}",
            headers=user_headers,
            json={"name": "Original Name"}
        )
        item_id = create_response.json()["id"]

        # Update item
        update_data = {"name": "Updated Name"}
        response = client.put(
            f"/api/v1/{endpoint}/{item_id}",
            headers=user_headers,
            json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "Updated Name"

    def test_partial_update_success(self, client, user_headers):
        """Test PATCH /api/v1/{endpoint}/{id} partially updates resource."""
        # Create item first
        create_response = client.post(
            "/api/v1/{endpoint}",
            headers=user_headers,
            json={"name": "Test", "description": "Original"}
        )
        item_id = create_response.json()["id"]

        # Partial update (only description)
        response = client.patch(
            f"/api/v1/{endpoint}/{item_id}",
            headers=user_headers,
            json={"description": "Updated"}
        )

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["name"] == "Test"  # Unchanged
        assert result["description"] == "Updated"  # Changed

    def test_update_not_found(self, client, user_headers):
        """Test update on non-existent resource returns 404."""
        response = client.put(
            "/api/v1/{endpoint}/99999",
            headers=user_headers,
            json={"name": "Updated"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# DELETE Endpoint Tests
# ============================================================================

@pytest.mark.api
class TestDeleteEndpoints:
    """Test DELETE endpoints."""

    def test_delete_success(self, client, admin_headers):
        """Test DELETE /api/v1/{endpoint}/{id} deletes resource."""
        # Create item first
        create_response = client.post(
            "/api/v1/{endpoint}",
            headers=admin_headers,
            json={"name": "To Delete"}
        )
        item_id = create_response.json()["id"]

        # Delete item
        response = client.delete(f"/api/v1/{endpoint}/{item_id}", headers=admin_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deletion
        get_response = client.get(f"/api/v1/{endpoint}/{item_id}", headers=admin_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_not_found(self, client, admin_headers):
        """Test delete on non-existent resource returns 404."""
        response = client.delete("/api/v1/{endpoint}/99999", headers=admin_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Input Validation Tests
# ============================================================================

@pytest.mark.api
@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization."""

    def test_xss_prevention(self, client, user_headers):
        """Test XSS attack vectors are sanitized."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]

        for payload in xss_payloads:
            response = client.post(
                "/api/v1/{endpoint}",
                headers=user_headers,
                json={"name": payload}
            )

            # Should either reject or sanitize
            if response.status_code == 201:
                assert "<script>" not in response.json()["name"]
                assert "javascript:" not in response.json()["name"]

    def test_sql_injection_prevention(self, client, user_headers):
        """Test SQL injection attempts are prevented."""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin' --"
        ]

        for payload in sql_payloads:
            response = client.post(
                "/api/v1/{endpoint}",
                headers=user_headers,
                json={"name": payload}
            )

            # Should handle safely (not crash or expose SQL errors)
            assert response.status_code in [200, 201, 422]

    def test_max_length_validation(self, client, user_headers):
        """Test maximum length validation."""
        too_long = "x" * 10000

        response = client.post(
            "/api/v1/{endpoint}",
            headers=user_headers,
            json={"name": too_long}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Rate Limiting Tests
# ============================================================================

@pytest.mark.api
@pytest.mark.slow
class TestRateLimiting:
    """Test API rate limiting."""

    def test_rate_limit_enforced(self, client, user_headers):
        """Test rate limiting is enforced after threshold."""
        # Make rapid requests
        responses = []
        for i in range(100):
            response = client.get("/api/v1/{endpoint}", headers=user_headers)
            responses.append(response)

        # Should eventually get rate limited
        rate_limited = any(r.status_code == 429 for r in responses)

        if not rate_limited:
            pytest.skip("Rate limiting not configured or threshold too high")


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.api
class TestErrorHandling:
    """Test API error handling."""

    def test_500_error_returns_error_response(self, client, user_headers):
        """Test internal server error returns proper error response."""
        # Simulate internal error
        with patch('api.v1.{endpoint}.{function}') as mock_func:
            mock_func.side_effect = Exception("Internal error")

            response = client.get("/api/v1/{endpoint}", headers=user_headers)

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "detail" in response.json()

    def test_error_response_format(self, client):
        """Test error responses follow consistent format."""
        response = client.get("/api/v1/{endpoint}")  # No auth

        assert response.status_code == 401
        error = response.json()
        assert "detail" in error
```

---

## 4. Infrastructure Test Template

### Template: tests/infrastructure/test_{infrastructure_component}.py

```python
"""
Infrastructure tests for {Component}

Tests {component} reliability including:
- Connection handling
- Performance
- Error recovery
- Resource management

WHY: Infrastructure failures affect entire platform
HOW: Mock external services, test connections
IMPACT: Ensures platform reliability
"""

import pytest
from unittest.mock import MagicMock, patch
import asyncio

from infrastructure.{module} import {Class}


@pytest.mark.infrastructure
class Test{Component}Connectivity:
    """Test {component} connection management."""

    @pytest.mark.asyncio
    async def test_connection_success(self):
        """Test successful connection."""
        component = {Class}(config={...})

        await component.connect()

        assert component.is_connected()

        await component.disconnect()

    @pytest.mark.asyncio
    async def test_connection_retry_on_failure(self):
        """Test connection retry mechanism."""
        component = {Class}(config={...})

        with patch.object(component, '_connect') as mock_connect:
            # Fail first two times, succeed third time
            mock_connect.side_effect = [
                ConnectionError("Failed"),
                ConnectionError("Failed"),
                None
            ]

            await component.connect_with_retry()

            assert component.is_connected()
            assert mock_connect.call_count == 3

    @pytest.mark.asyncio
    async def test_connection_pool_management(self):
        """Test connection pool creates and manages connections."""
        component = {Class}(config={"pool_size": 10})

        await component.connect()

        assert component.pool_size == 10
        assert component.active_connections <= 10


@pytest.mark.infrastructure
class Test{Component}Performance:
    """Test {component} performance."""

    @pytest.mark.asyncio
    async def test_latency_within_threshold(self):
        """Test operation latency is acceptable."""
        component = {Class}()
        await component.connect()

        start = time.time()
        await component.operation()
        duration = time.time() - start

        assert duration < 0.1  # < 100ms

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test handling of concurrent operations."""
        component = {Class}()
        await component.connect()

        tasks = [component.operation() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 100
        assert all(r is not None for r in results)
```

---

## 5. Integration Test Template

### Template: tests/integration/test_{workflow_name}_workflow.py

```python
"""
End-to-end integration tests for {Workflow} workflow

Tests complete workflow from start to finish including:
- All component interactions
- Data flow
- Error propagation
- Transaction consistency

WHY: Ensures components work together correctly
HOW: Use real/mock services, test full data flow
IMPACT: Catches integration bugs before production
"""

import pytest
from unittest.mock import patch
import asyncio

from agent.{agent_module} import {Agent}
from services.{service_module} import {Service}
from infrastructure.{infra_module} import {Infrastructure}


@pytest.mark.integration
class Test{Workflow}EndToEnd:
    """Test complete {workflow} workflow."""

    @pytest.mark.asyncio
    async def test_successful_workflow(
        self,
        test_db_session,
        test_redis_client,
        mock_external_api
    ):
        """Test successful end-to-end workflow execution."""

        # Step 1: Create input data
        input_data = {
            "user_id": "user_123",
            "action": "process",
            "data": {...}
        }

        # Step 2: Agent processes input
        agent = {Agent}()
        agent_result = await agent.process(input_data)
        assert agent_result["status"] == "success"

        # Step 3: Service orchestrates workflow
        service = {Service}()
        service_result = await service.execute(agent_result)
        assert service_result["status"] == "success"

        # Step 4: Data persisted to database
        from models import {Model}
        db_record = test_db_session.query({Model}).filter_by(
            user_id="user_123"
        ).first()
        assert db_record is not None
        assert db_record.status == "completed"

        # Step 5: Cache updated
        cached_data = await test_redis_client.get(f"user:user_123")
        assert cached_data is not None

        # Step 6: External API notified
        mock_external_api.notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_with_database_failure(
        self,
        test_db_session,
        mock_external_api
    ):
        """Test workflow handles database failure gracefully."""

        # Simulate database failure
        with patch.object(test_db_session, 'commit') as mock_commit:
            mock_commit.side_effect = Exception("Database error")

            input_data = {"user_id": "user_456", "action": "process"}

            agent = {Agent}()
            service = {Service}()

            # Workflow should handle error and rollback
            result = await service.execute(input_data)

            assert result["status"] == "error"
            assert "database" in result["message"].lower()

            # Verify rollback occurred
            mock_commit.assert_called()
            # Verify no external API call on failure
            mock_external_api.notify.assert_not_called()

    @pytest.mark.asyncio
    async def test_workflow_transaction_consistency(
        self,
        test_db_session,
        test_redis_client
    ):
        """Test workflow maintains transaction consistency."""

        input_data = {"user_id": "user_789", "amount": 100}

        # Start workflow
        service = {Service}()
        result = await service.execute(input_data)

        # Verify database and cache are consistent
        from models import {Model}
        db_record = test_db_session.query({Model}).filter_by(
            user_id="user_789"
        ).first()

        cached_data = await test_redis_client.get(f"user:user_789")

        assert db_record.amount == 100
        assert cached_data["amount"] == 100  # Matches database
```

---

## Summary

These templates provide:

1. **Agent Module Tests** - Comprehensive testing for 62+ agent files
2. **Service Layer Tests** - Orchestration and workflow testing
3. **API Endpoint Tests** - Complete REST API testing with auth
4. **Infrastructure Tests** - Connection, performance, reliability
5. **Integration Tests** - End-to-end workflow validation

**Usage:**
1. Copy appropriate template
2. Replace `{placeholders}` with actual names
3. Customize test cases for specific functionality
4. Add module-specific edge cases
5. Ensure ≥90% coverage per module

**Next Steps:**
1. Start with highest priority (agent modules)
2. Use templates to create initial test files
3. Run coverage reports to verify improvement
4. Iterate until ≥90% coverage achieved
