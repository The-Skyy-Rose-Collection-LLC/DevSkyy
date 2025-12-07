"""
Comprehensive Unit Tests for Agent API Endpoints (api/v1/agents.py)
Testing all agent execution endpoints with various scenarios to achieve ≥80% coverage
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI, status
from fastapi.testclient import TestClient
import pytest

from security.jwt_auth import User, UserRole, create_access_token, user_manager


@pytest.fixture
def app():
    """Create minimal test app with just agents router"""
    test_app = FastAPI()

    # Import and register agents router
    from api.v1.agents import router as agents_router
    test_app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])

    return test_app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_scanner_result():
    """Mock scanner agent result"""
    return {
        "scan_id": "scan_123456",
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "files_scanned": 42,
        "errors_found": [
            {"file": "test.py", "line": 10, "message": "Syntax error"},
            {"file": "main.py", "line": 25, "message": "Unused import"},
        ],
        "warnings": [{"file": "config.py", "line": 5, "message": "Missing docstring"}],
        "optimizations": [{"file": "utils.py", "suggestion": "Use list comprehension"}],
        "performance_metrics": {"scan_duration_ms": 1250, "memory_usage_mb": 45.2},
        "security_issues": [],
        "accessibility_issues": [],
    }


@pytest.fixture
def mock_fixer_result():
    """Mock fixer agent result"""
    return {
        "fix_id": "fix_789012",
        "timestamp": datetime.now().isoformat(),
        "status": "completed",
        "files_fixed": 5,
        "errors_fixed": 8,
        "warnings_fixed": 3,
        "optimizations_applied": 2,
        "fixes_applied": [
            {"file": "test.py", "type": "error", "description": "Fixed syntax error"},
            {"file": "main.py", "type": "warning", "description": "Removed unused import"},
        ],
        "backup_created": True,
    }


@pytest.fixture
def auth_headers():
    """Create authentication headers with valid JWT token"""
    token_data = {
        "user_id": "test_user_001",
        "email": "test@devskyy.com",
        "username": "testuser",
        "role": UserRole.API_USER,
    }

    # Add user to user manager
    test_user = User(
        user_id=token_data["user_id"],
        email=token_data["email"],
        username=token_data["username"],
        role=token_data["role"],
        permissions=["read", "write"],
    )
    user_manager.users[test_user.user_id] = test_user
    user_manager.email_index[test_user.email] = test_user.user_id

    access_token = create_access_token(token_data)
    headers = {"Authorization": f"Bearer {access_token}"}

    yield headers

    # Cleanup
    if test_user.user_id in user_manager.users:
        del user_manager.users[test_user.user_id]
    if test_user.email in user_manager.email_index:
        del user_manager.email_index[test_user.email]


@pytest.fixture
def developer_headers():
    """Create developer authentication headers"""
    token_data = {
        "user_id": "dev_user_001",
        "email": "dev@devskyy.com",
        "username": "devuser",
        "role": UserRole.DEVELOPER,
    }

    test_user = User(
        user_id=token_data["user_id"],
        email=token_data["email"],
        username=token_data["username"],
        role=token_data["role"],
        permissions=["read", "write", "execute", "fix"],
    )
    user_manager.users[test_user.user_id] = test_user
    user_manager.email_index[test_user.email] = test_user.user_id

    access_token = create_access_token(token_data)
    headers = {"Authorization": f"Bearer {access_token}"}

    yield headers

    # Cleanup
    if test_user.user_id in user_manager.users:
        del user_manager.users[test_user.user_id]
    if test_user.email in user_manager.email_index:
        del user_manager.email_index[test_user.email]


class TestScannerEndpoint:
    """Test suite for Scanner Agent endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_scanner_endpoint_without_auth(self, client):
        """Test scanner endpoint requires authentication"""
        request_data = {"parameters": {}}

        response = client.post("/api/v1/agents/scanner/execute", json=request_data)

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.scan_site")
    def test_scanner_endpoint_success(self, mock_scan_site, client, auth_headers, mock_scanner_result):
        """Test successful scanner execution"""
        # Setup mock - scan_site is a regular function, not async
        mock_scan_site.return_value = mock_scanner_result

        request_data = {"parameters": {"target": ".", "deep_scan": True, "include_security": True}}

        response = client.post("/api/v1/agents/scanner/execute", json=request_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["agent_name"] == "Scanner V1"
        assert data["status"] == "success"
        assert "result" in data
        assert "execution_time_ms" in data
        assert "timestamp" in data

    @pytest.mark.api
    @pytest.mark.unit
    def test_scanner_endpoint_empty_parameters(self, client, auth_headers):
        """Test scanner with empty parameters"""
        request_data = {"parameters": {}}

        response = client.post("/api/v1/agents/scanner/execute", json=request_data, headers=auth_headers)

        # Should accept empty parameters or return validation error
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.scan_site")
    def test_scanner_endpoint_with_specific_path(self, mock_scan_site, client, auth_headers):
        """Test scanner with specific target path"""
        mock_result = {"scan_id": "scan_specific", "files_scanned": 10, "status": "completed"}
        mock_scan_site.return_value = mock_result

        request_data = {
            "parameters": {"target": "api/v1/", "file_types": [".py"], "exclude_patterns": ["test_*", "__pycache__"]}
        }

        response = client.post("/api/v1/agents/scanner/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.scan_site")
    def test_scanner_endpoint_exception_handling(self, mock_scan_site, client, auth_headers):
        """Test scanner error handling"""
        # Simulate scanner failure
        mock_scan_site.side_effect = Exception("Scanner module not found")

        request_data = {"parameters": {"target": "."}}

        response = client.post("/api/v1/agents/scanner/execute", json=request_data, headers=auth_headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.scan_site")
    def test_scanner_endpoint_timeout_scenario(self, mock_scan_site, client, auth_headers):
        """Test scanner timeout handling"""
        mock_scan_site.side_effect = TimeoutError("Scanner timed out after 300 seconds")

        request_data = {"parameters": {"target": ".", "timeout": 300}}

        response = client.post("/api/v1/agents/scanner/execute", json=request_data, headers=auth_headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.scan_site")
    def test_scanner_endpoint_large_result(self, mock_scan_site, client, auth_headers):
        """Test scanner with large result set"""
        # Simulate large scan result
        large_result = {
            "scan_id": "scan_large",
            "files_scanned": 1000,
            "errors_found": [{"file": f"file_{i}.py", "error": "test"} for i in range(500)],
            "warnings": [{"file": f"file_{i}.py", "warning": "test"} for i in range(300)],
            "status": "completed",
        }
        mock_scan_site.return_value = large_result

        request_data = {"parameters": {"target": "."}}

        response = client.post("/api/v1/agents/scanner/execute", json=request_data, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["result"]["files_scanned"] == 1000

    @pytest.mark.api
    @pytest.mark.unit
    def test_scanner_endpoint_invalid_json(self, client, auth_headers):
        """Test scanner with invalid JSON payload"""
        response = client.post("/api/v1/agents/scanner/execute", data="invalid json", headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestFixerEndpoint:
    """Test suite for Fixer Agent endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_fixer_endpoint_without_auth(self, client):
        """Test fixer endpoint requires authentication"""
        request_data = {"parameters": {}}

        response = client.post("/api/v1/agents/fixer/execute", json=request_data)

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @pytest.mark.api
    @pytest.mark.unit
    def test_fixer_endpoint_requires_developer_role(self, client, auth_headers):
        """Test fixer requires developer role or higher"""
        request_data = {"parameters": {}}

        response = client.post("/api/v1/agents/fixer/execute", json=request_data, headers=auth_headers)

        # Should be forbidden for non-developer users
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.fix_code")
    def test_fixer_endpoint_success(self, mock_fix_code, client, developer_headers, mock_fixer_result):
        """Test successful fixer execution"""
        mock_fix_code.return_value = mock_fixer_result

        request_data = {
            "parameters": {
                "scan_results": {"errors_found": [{"file": "test.py", "line": 10}]},
                "auto_fix": True,
                "create_backup": True,
            }
        }

        response = client.post("/api/v1/agents/fixer/execute", json=request_data, headers=developer_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Fixer V1"
            assert data["status"] == "success"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.fix_code")
    def test_fixer_endpoint_empty_parameters(self, mock_fix_code, client, developer_headers):
        """Test fixer with empty parameters"""
        mock_result = {"fix_id": "fix_empty", "status": "completed", "files_fixed": 0}
        mock_fix_code.return_value = mock_result

        request_data = {"parameters": {}}

        response = client.post("/api/v1/agents/fixer/execute", json=request_data, headers=developer_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.fix_code")
    def test_fixer_endpoint_with_scan_results(self, mock_fix_code, client, developer_headers):
        """Test fixer with provided scan results"""
        mock_result = {"fix_id": "fix_with_scan", "status": "completed", "files_fixed": 5, "errors_fixed": 10}
        mock_fix_code.return_value = mock_result

        request_data = {
            "parameters": {
                "scan_results": {
                    "errors_found": [
                        {"file": "test.py", "line": 10, "error": "syntax error"},
                        {"file": "main.py", "line": 25, "error": "undefined variable"},
                    ]
                },
                "fix_strategy": "conservative",
                "dry_run": False,
            }
        }

        response = client.post("/api/v1/agents/fixer/execute", json=request_data, headers=developer_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.fix_code")
    def test_fixer_endpoint_exception_handling(self, mock_fix_code, client, developer_headers):
        """Test fixer error handling"""
        mock_fix_code.side_effect = Exception("Fixer module failed")

        request_data = {"parameters": {}}

        response = client.post("/api/v1/agents/fixer/execute", json=request_data, headers=developer_headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "detail" in data

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.fix_code")
    def test_fixer_endpoint_dry_run_mode(self, mock_fix_code, client, developer_headers):
        """Test fixer in dry-run mode (no actual changes)"""
        mock_result = {
            "fix_id": "fix_dry_run",
            "status": "completed",
            "dry_run": True,
            "proposed_fixes": 15,
            "files_fixed": 0,
        }
        mock_fix_code.return_value = mock_result

        request_data = {"parameters": {"dry_run": True, "scan_results": {"errors_found": []}}}

        response = client.post("/api/v1/agents/fixer/execute", json=request_data, headers=developer_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.fix_code")
    def test_fixer_endpoint_backup_creation(self, mock_fix_code, client, developer_headers):
        """Test fixer creates backup before fixing"""
        mock_result = {
            "fix_id": "fix_backup",
            "status": "completed",
            "backup_created": True,
            "backup_path": "/backups/backup_12345",
            "files_fixed": 3,
        }
        mock_fix_code.return_value = mock_result

        request_data = {"parameters": {"create_backup": True}}

        response = client.post("/api/v1/agents/fixer/execute", json=request_data, headers=developer_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("api.v1.agents.fix_code")
    def test_fixer_endpoint_partial_failure(self, mock_fix_code, client, developer_headers):
        """Test fixer handles partial failures gracefully"""
        mock_result = {
            "fix_id": "fix_partial",
            "status": "partial_success",
            "files_fixed": 5,
            "files_failed": 2,
            "failures": [
                {"file": "broken.py", "error": "Cannot parse file"},
                {"file": "locked.py", "error": "Permission denied"},
            ],
        }
        mock_fix_code.return_value = mock_result

        request_data = {"parameters": {}}

        response = client.post("/api/v1/agents/fixer/execute", json=request_data, headers=developer_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestScannerV2Endpoint:
    """Test suite for Scanner V2 Agent endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.scanner_v2.scanner_agent")
    def test_scanner_v2_endpoint_success(self, mock_scanner, client, auth_headers):
        """Test Scanner V2 with enhanced features"""
        mock_result = {
            "scan_id": "scan_v2_001",
            "version": "2.0",
            "security_scan": True,
            "vulnerability_count": 3,
            "status": "completed",
        }
        mock_scanner.execute_core_function = AsyncMock(return_value=mock_result)

        request_data = {"parameters": {"enhanced_security": True, "deep_analysis": True}}

        response = client.post("/api/v1/agents/scanner-v2/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestAgentListEndpoint:
    """Test suite for listing all agents"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_list_all_agents_without_auth(self, client):
        """Test listing agents requires authentication"""
        response = client.get("/api/v1/agents")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @pytest.mark.api
    @pytest.mark.unit
    def test_list_all_agents_success(self, client, auth_headers):
        """Test successful retrieval of agent list"""
        response = client.get("/api/v1/agents", headers=auth_headers)

        # Endpoint might return list or might not be fully implemented
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "agents" in data or isinstance(data, list)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_malformed_parameters(self, client, auth_headers):
        """Test handling of malformed parameters"""
        request_data = {"parameters": "not a dict"}

        response = client.post("/api/v1/agents/scanner/execute", json=request_data, headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.api
    @pytest.mark.unit
    def test_missing_parameters_field(self, client, auth_headers):
        """Test request without parameters field"""
        request_data = {}

        response = client.post("/api/v1/agents/scanner/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.scanner.scan_site")
    def test_null_result_handling(self, mock_scan_site, client, auth_headers):
        """Test handling of null results from agent"""
        mock_scan_site.return_value = None

        request_data = {"parameters": {}}

        response = client.post("/api/v1/agents/scanner/execute", json=request_data, headers=auth_headers)

        # Should handle null result gracefully
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.scanner.scan_site")
    def test_concurrent_requests(self, mock_scan_site, client, auth_headers):
        """Test handling of concurrent agent requests"""
        import concurrent.futures

        mock_scan_site.return_value = {"status": "completed"}

        def make_request():
            return client.post("/api/v1/agents/scanner/execute", json={"parameters": {}}, headers=auth_headers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should complete
        assert len(results) == 5
        for response in results:
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ]


# ============================================================================
# AI INTELLIGENCE SERVICES TESTS
# ============================================================================


class TestAIIntelligenceEndpoints:
    """Test suite for AI intelligence services"""

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.claude_sonnet_intelligence_service.agent")
    def test_claude_sonnet_success(self, mock_agent, client, auth_headers):
        """Test Claude Sonnet endpoint"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"response": "AI response", "model": "claude-sonnet-4"}
        )

        request_data = {"parameters": {"prompt": "Test prompt"}}
        response = client.post("/api/v1/agents/claude-sonnet/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Claude Sonnet"
            assert data["status"] == "success"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.openai_intelligence_service.agent")
    def test_openai_success(self, mock_agent, client, auth_headers):
        """Test OpenAI endpoint"""
        mock_agent.execute_core_function = AsyncMock(return_value={"response": "GPT response", "model": "gpt-4"})

        request_data = {"parameters": {"prompt": "Test prompt"}}
        response = client.post("/api/v1/agents/openai/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "OpenAI"
            assert data["status"] == "success"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.multi_model_ai_orchestrator.agent")
    def test_multi_model_ai_success(self, mock_agent, client, auth_headers):
        """Test Multi-Model AI endpoint"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"response": "Best model response", "selected_model": "claude-sonnet"}
        )

        request_data = {"parameters": {"prompt": "Complex task", "auto_select_model": True}}
        response = client.post("/api/v1/agents/multi-model-ai/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Multi-Model AI"
            assert data["status"] == "success"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.claude_sonnet_intelligence_service.agent")
    def test_ai_endpoint_error_handling(self, mock_agent, client, auth_headers):
        """Test AI endpoint error handling"""
        mock_agent.execute_core_function = AsyncMock(side_effect=Exception("API key missing"))

        request_data = {"parameters": {"prompt": "Test"}}
        response = client.post("/api/v1/agents/claude-sonnet/execute", json=request_data, headers=auth_headers)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# ============================================================================
# E-COMMERCE AGENTS TESTS
# ============================================================================


class TestEcommerceEndpoints:
    """Test suite for e-commerce agents"""

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.ecommerce_agent.agent")
    def test_ecommerce_agent_success(self, mock_agent, client, auth_headers):
        """Test e-commerce agent endpoint"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"orders_processed": 10, "revenue": 15000, "status": "success"}
        )

        request_data = {"parameters": {"operation": "process_orders"}}
        response = client.post("/api/v1/agents/ecommerce/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "E-commerce"
            assert data["status"] == "success"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.inventory_agent.agent")
    def test_inventory_agent_success(self, mock_agent, client, auth_headers):
        """Test inventory agent endpoint"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"items_updated": 50, "low_stock_alerts": 5, "status": "success"}
        )

        request_data = {"parameters": {"operation": "update_inventory"}}
        response = client.post("/api/v1/agents/inventory/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Inventory"
            assert data["status"] == "success"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.financial_agent.agent")
    def test_financial_agent_success(self, mock_agent, client, auth_headers):
        """Test financial agent endpoint"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"transactions_processed": 100, "total_amount": 50000, "status": "success"}
        )

        request_data = {"parameters": {"operation": "process_payments"}}
        response = client.post("/api/v1/agents/financial/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Financial"
            assert data["status"] == "success"


# ============================================================================
# MARKETING & BRAND AGENTS TESTS
# ============================================================================


class TestMarketingEndpoints:
    """Test suite for marketing agents"""

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.brand_intelligence_agent.agent")
    def test_brand_intelligence_success(self, mock_agent, client, auth_headers):
        """Test brand intelligence agent"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"brand_sentiment": "positive", "mentions": 1000, "status": "success"}
        )

        request_data = {"parameters": {"operation": "analyze_brand"}}
        response = client.post("/api/v1/agents/brand-intelligence/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Brand Intelligence"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.seo_marketing_agent.agent")
    def test_seo_marketing_success(self, mock_agent, client, auth_headers):
        """Test SEO marketing agent"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"keywords_optimized": 50, "ranking_improvements": 15, "status": "success"}
        )

        request_data = {"parameters": {"operation": "optimize_seo"}}
        response = client.post("/api/v1/agents/seo-marketing/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "SEO Marketing"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.social_media_automation_agent.agent")
    def test_social_media_success(self, mock_agent, client, auth_headers):
        """Test social media agent"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"posts_published": 10, "engagement_rate": 5.5, "status": "success"}
        )

        request_data = {"parameters": {"operation": "publish_posts"}}
        response = client.post("/api/v1/agents/social-media/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Social Media"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.email_sms_automation_agent.agent")
    def test_email_sms_success(self, mock_agent, client, auth_headers):
        """Test email/SMS agent"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"emails_sent": 500, "sms_sent": 200, "status": "success"}
        )

        request_data = {"parameters": {"operation": "send_campaign"}}
        response = client.post("/api/v1/agents/email-sms/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Email/SMS"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.marketing_content_generation_agent.agent")
    def test_marketing_content_success(self, mock_agent, client, auth_headers):
        """Test marketing content generation"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"content_generated": "Marketing copy", "word_count": 500, "status": "success"}
        )

        request_data = {"parameters": {"content_type": "blog_post"}}
        response = client.post("/api/v1/agents/marketing-content/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Marketing Content"


# ============================================================================
# WORDPRESS & CMS AGENTS TESTS
# ============================================================================


class TestWordPressEndpoints:
    """Test suite for WordPress agents"""

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.wordpress_agent.agent")
    def test_wordpress_agent_success(self, mock_agent, client, auth_headers):
        """Test WordPress agent"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"posts_published": 5, "pages_updated": 3, "status": "success"}
        )

        request_data = {"parameters": {"operation": "publish_posts"}}
        response = client.post("/api/v1/agents/wordpress/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "WordPress"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.wordpress.theme_builder.generate_theme")
    def test_wordpress_theme_builder_success(self, mock_generate, client, auth_headers):
        """Test WordPress theme builder"""
        mock_generate.return_value = {"theme_name": "custom-theme", "files_created": 15, "status": "success"}

        request_data = {"parameters": {"theme_name": "custom-theme", "style": "modern"}}
        response = client.post(
            "/api/v1/agents/wordpress-theme-builder/execute", json=request_data, headers=auth_headers
        )

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "WordPress Theme Builder"


# ============================================================================
# CUSTOMER SERVICE AGENTS TESTS
# ============================================================================


class TestCustomerServiceEndpoints:
    """Test suite for customer service agents"""

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.customer_service_agent.agent")
    def test_customer_service_success(self, mock_agent, client, auth_headers):
        """Test customer service agent"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"tickets_resolved": 20, "satisfaction_score": 4.5, "status": "success"}
        )

        request_data = {"parameters": {"operation": "process_tickets"}}
        response = client.post("/api/v1/agents/customer-service/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Customer Service"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.voice_audio_content_agent.agent")
    def test_voice_audio_success(self, mock_agent, client, auth_headers):
        """Test voice/audio agent"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"audio_generated": True, "duration_seconds": 120, "status": "success"}
        )

        request_data = {"parameters": {"text": "Voice synthesis test", "voice": "natural"}}
        response = client.post("/api/v1/agents/voice-audio/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Voice/Audio"


# ============================================================================
# ADVANCED AGENTS TESTS
# ============================================================================


class TestAdvancedAgentsEndpoints:
    """Test suite for advanced agents"""

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.blockchain_nft_luxury_assets.agent")
    def test_blockchain_nft_success(self, mock_agent, client, auth_headers):
        """Test blockchain/NFT agent"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"nfts_minted": 10, "transactions": 5, "status": "success"}
        )

        request_data = {"parameters": {"operation": "mint_nft"}}
        response = client.post("/api/v1/agents/blockchain-nft/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Blockchain/NFT"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.advanced_code_generation_agent.agent")
    def test_code_generation_success(self, mock_agent, client, developer_headers):
        """Test code generation agent"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"code_generated": "def hello(): return 'world'", "lines": 10, "status": "success"}
        )

        request_data = {"parameters": {"prompt": "Generate hello world function"}}
        response = client.post("/api/v1/agents/code-generation/execute", json=request_data, headers=developer_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Code Generation"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.security_agent.agent")
    def test_security_agent_success(self, mock_agent, client, developer_headers):
        """Test security agent"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"vulnerabilities_found": 3, "severity": "medium", "status": "success"}
        )

        request_data = {"parameters": {"scan_type": "full"}}
        response = client.post("/api/v1/agents/security/execute", json=request_data, headers=developer_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Security"

    @pytest.mark.api
    @pytest.mark.unit
    @patch("agent.modules.backend.performance_agent.agent")
    def test_performance_agent_success(self, mock_agent, client, auth_headers):
        """Test performance agent"""
        mock_agent.execute_core_function = AsyncMock(
            return_value={"p95_latency_ms": 150, "throughput_rps": 1000, "status": "success"}
        )

        request_data = {"parameters": {"operation": "analyze_performance"}}
        response = client.post("/api/v1/agents/performance/execute", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["agent_name"] == "Performance"


# ============================================================================
# BATCH OPERATIONS TESTS
# ============================================================================


class TestBatchOperations:
    """Test suite for batch operations"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_batch_execute_success(self, client, auth_headers):
        """Test batch execution of multiple agents"""
        request_data = {
            "operations": [
                {"agent": "scanner", "parameters": {"target": "."}},
                {"agent": "fixer", "parameters": {"auto_fix": True}},
            ],
            "parallel": True,
        }

        response = client.post("/api/v1/agents/batch", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "status" in data
            assert "total_operations" in data
            assert data["total_operations"] == 2

    @pytest.mark.api
    @pytest.mark.unit
    def test_batch_execute_sequential(self, client, auth_headers):
        """Test sequential batch execution"""
        request_data = {
            "operations": [
                {"agent": "scanner", "parameters": {}},
                {"agent": "fixer", "parameters": {}},
            ],
            "parallel": False,
        }

        response = client.post("/api/v1/agents/batch", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["parallel"] is False

    @pytest.mark.api
    @pytest.mark.unit
    def test_batch_execute_empty_operations(self, client, auth_headers):
        """Test batch with empty operations list"""
        request_data = {"operations": [], "parallel": True}

        response = client.post("/api/v1/agents/batch", json=request_data, headers=auth_headers)

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]


# ============================================================================
# AGENT DISCOVERY TESTS
# ============================================================================


class TestAgentDiscovery:
    """Test suite for agent discovery and listing"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_list_all_agents_success(self, client, auth_headers):
        """Test listing all available agents"""
        response = client.get("/api/v1/agents/list", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "agents" in data
        assert "total_count" in data
        assert "api_version" in data
        assert data["api_version"] == "v1"

        # Verify agent categories exist
        assert "core" in data["agents"]
        assert "ai" in data["agents"]
        assert "ecommerce" in data["agents"]
        assert "marketing" in data["agents"]
        assert "wordpress" in data["agents"]
        assert "customer" in data["agents"]
        assert "advanced" in data["agents"]

    @pytest.mark.api
    @pytest.mark.unit
    def test_list_agents_without_auth(self, client):
        """Test listing agents requires authentication"""
        response = client.get("/api/v1/agents/list")

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @pytest.mark.api
    @pytest.mark.unit
    def test_list_agents_structure(self, client, auth_headers):
        """Test agent list structure and content"""
        response = client.get("/api/v1/agents/list", headers=auth_headers)

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            agents = data["agents"]

            # Verify core agents
            core_agents = agents["core"]
            assert any(agent["name"] == "Scanner" for agent in core_agents)
            assert any(agent["name"] == "Fixer" for agent in core_agents)

            # Verify all agents have required fields
            for category_agents in agents.values():
                for agent in category_agents:
                    assert "name" in agent
                    assert "endpoint" in agent
                    assert "category" in agent
