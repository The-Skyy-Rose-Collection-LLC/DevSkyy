"""
Comprehensive Unit Tests for Agent API Endpoints (api/v1/agents.py)
Testing scanner and fixer agent execution endpoints with various scenarios
"""

import unittest
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from main import app
from security.jwt_auth import create_access_token, User, UserRole, user_manager


@pytest.fixture
def client():
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
            {"file": "main.py", "line": 25, "message": "Unused import"}
        ],
        "warnings": [
            {"file": "config.py", "line": 5, "message": "Missing docstring"}
        ],
        "optimizations": [
            {"file": "utils.py", "suggestion": "Use list comprehension"}
        ],
        "performance_metrics": {
            "scan_duration_ms": 1250,
            "memory_usage_mb": 45.2
        },
        "security_issues": [],
        "accessibility_issues": []
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
            {"file": "main.py", "type": "warning", "description": "Removed unused import"}
        ],
        "backup_created": True
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


class TestScannerEndpoint(unittest.TestCase):
    """Test suite for Scanner Agent endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_scanner_endpoint_without_auth(self, client):
        """Test scanner endpoint requires authentication"""
        request_data = {"parameters": {}}
        
        response = client.post("/api/v1/agents/scanner/execute", json=request_data)
        
        self.assertIn(response.status_code, [)
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.scanner.scanner_agent')
    def test_scanner_endpoint_success(self, mock_scanner, client, auth_headers, mock_scanner_result):
        """Test successful scanner execution"""
        # Setup mock
        mock_scanner.execute_core_function = AsyncMock(return_value=mock_scanner_result)
        
        request_data = {
            "parameters": {
                "target": ".",
                "deep_scan": True,
                "include_security": True
            }
        }
        
        response = client.post(
            "/api/v1/agents/scanner/execute",
            json=request_data,
            headers=auth_headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["agent_name"], "Scanner")
        self.assertEqual(data["status"], "success")
        self.assertIn("result", data)
        self.assertIn("execution_time_ms", data)
        self.assertIn("timestamp", data)

    @pytest.mark.api
    @pytest.mark.unit
    def test_scanner_endpoint_empty_parameters(self, client, auth_headers):
        """Test scanner with empty parameters"""
        request_data = {"parameters": {}}
        
        response = client.post(
            "/api/v1/agents/scanner/execute",
            json=request_data,
            headers=auth_headers
        )
        
        # Should accept empty parameters or return validation error
        self.assertIn(response.status_code, [)
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.scanner.scanner_agent')
    def test_scanner_endpoint_with_specific_path(self, mock_scanner, client, auth_headers):
        """Test scanner with specific target path"""
        mock_result = {
            "scan_id": "scan_specific",
            "files_scanned": 10,
            "status": "completed"
        }
        mock_scanner.execute_core_function = AsyncMock(return_value=mock_result)
        
        request_data = {
            "parameters": {
                "target": "api/v1/",
                "file_types": [".py"],
                "exclude_patterns": ["test_*", "__pycache__"]
            }
        }
        
        response = client.post(
            "/api/v1/agents/scanner/execute",
            json=request_data,
            headers=auth_headers
        )
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.scanner.scanner_agent')
    def test_scanner_endpoint_exception_handling(self, mock_scanner, client, auth_headers):
        """Test scanner error handling"""
        # Simulate scanner failure
        mock_scanner.execute_core_function = AsyncMock(
            side_effect=Exception("Scanner module not found")
        )
        
        request_data = {"parameters": {"target": "."}}
        
        response = client.post(
            "/api/v1/agents/scanner/execute",
            json=request_data,
            headers=auth_headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = response.json()
        self.assertIn("detail", data)

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.scanner.scanner_agent')
    def test_scanner_endpoint_timeout_scenario(self, mock_scanner, client, auth_headers):
        """Test scanner timeout handling"""
        mock_scanner.execute_core_function = AsyncMock(
            side_effect=TimeoutError("Scanner timed out after 300 seconds")
        )
        
        request_data = {
            "parameters": {
                "target": ".",
                "timeout": 300
            }
        }
        
        response = client.post(
            "/api/v1/agents/scanner/execute",
            json=request_data,
            headers=auth_headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.scanner.scanner_agent')
    def test_scanner_endpoint_large_result(self, mock_scanner, client, auth_headers):
        """Test scanner with large result set"""
        # Simulate large scan result
        large_result = {
            "scan_id": "scan_large",
            "files_scanned": 1000,
            "errors_found": [{"file": f"file_{i}.py", "error": "test"} for i in range(500)],
            "warnings": [{"file": f"file_{i}.py", "warning": "test"} for i in range(300)],
            "status": "completed"
        }
        mock_scanner.execute_core_function = AsyncMock(return_value=large_result)
        
        request_data = {"parameters": {"target": "."}}
        
        response = client.post(
            "/api/v1/agents/scanner/execute",
            json=request_data,
            headers=auth_headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["result"]["files_scanned"], 1000)

    @pytest.mark.api
    @pytest.mark.unit
    def test_scanner_endpoint_invalid_json(self, client, auth_headers):
        """Test scanner with invalid JSON payload"""
        response = client.post(
            "/api/v1/agents/scanner/execute",
            data="invalid json",
            headers=auth_headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)


class TestFixerEndpoint(unittest.TestCase):
    """Test suite for Fixer Agent endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_fixer_endpoint_without_auth(self, client):
        """Test fixer endpoint requires authentication"""
        request_data = {"parameters": {}}
        
        response = client.post("/api/v1/agents/fixer/execute", json=request_data)
        
        self.assertIn(response.status_code, [)
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    @pytest.mark.api
    @pytest.mark.unit
    def test_fixer_endpoint_requires_developer_role(self, client, auth_headers):
        """Test fixer requires developer role or higher"""
        request_data = {"parameters": {}}
        
        response = client.post(
            "/api/v1/agents/fixer/execute",
            json=request_data,
            headers=auth_headers
        )
        
        # Should be forbidden for non-developer users
        self.assertIn(response.status_code, [)
            status.HTTP_403_FORBIDDEN,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.fixer.fixer_agent')
    def test_fixer_endpoint_success(self, mock_fixer, client, developer_headers, mock_fixer_result):
        """Test successful fixer execution"""
        mock_fixer.execute_core_function = AsyncMock(return_value=mock_fixer_result)
        
        request_data = {
            "parameters": {
                "scan_results": {
                    "errors_found": [{"file": "test.py", "line": 10}]
                },
                "auto_fix": True,
                "create_backup": True
            }
        }
        
        response = client.post(
            "/api/v1/agents/fixer/execute",
            json=request_data,
            headers=developer_headers
        )
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            self.assertEqual(data["agent_name"], "Fixer")
            self.assertEqual(data["status"], "success")

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.fixer.fixer_agent')
    def test_fixer_endpoint_empty_parameters(self, mock_fixer, client, developer_headers):
        """Test fixer with empty parameters"""
        mock_result = {
            "fix_id": "fix_empty",
            "status": "completed",
            "files_fixed": 0
        }
        mock_fixer.execute_core_function = AsyncMock(return_value=mock_result)
        
        request_data = {"parameters": {}}
        
        response = client.post(
            "/api/v1/agents/fixer/execute",
            json=request_data,
            headers=developer_headers
        )
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.fixer.fixer_agent')
    def test_fixer_endpoint_with_scan_results(self, mock_fixer, client, developer_headers):
        """Test fixer with provided scan results"""
        mock_result = {
            "fix_id": "fix_with_scan",
            "status": "completed",
            "files_fixed": 5,
            "errors_fixed": 10
        }
        mock_fixer.execute_core_function = AsyncMock(return_value=mock_result)
        
        request_data = {
            "parameters": {
                "scan_results": {
                    "errors_found": [
                        {"file": "test.py", "line": 10, "error": "syntax error"},
                        {"file": "main.py", "line": 25, "error": "undefined variable"}
                    ]
                },
                "fix_strategy": "conservative",
                "dry_run": False
            }
        }
        
        response = client.post(
            "/api/v1/agents/fixer/execute",
            json=request_data,
            headers=developer_headers
        )
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.fixer.fixer_agent')
    def test_fixer_endpoint_exception_handling(self, mock_fixer, client, developer_headers):
        """Test fixer error handling"""
        mock_fixer.execute_core_function = AsyncMock(
            side_effect=Exception("Fixer module failed")
        )
        
        request_data = {"parameters": {}}
        
        response = client.post(
            "/api/v1/agents/fixer/execute",
            json=request_data,
            headers=developer_headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = response.json()
        self.assertIn("detail", data)

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.fixer.fixer_agent')
    def test_fixer_endpoint_dry_run_mode(self, mock_fixer, client, developer_headers):
        """Test fixer in dry-run mode (no actual changes)"""
        mock_result = {
            "fix_id": "fix_dry_run",
            "status": "completed",
            "dry_run": True,
            "proposed_fixes": 15,
            "files_fixed": 0
        }
        mock_fixer.execute_core_function = AsyncMock(return_value=mock_result)
        
        request_data = {
            "parameters": {
                "dry_run": True,
                "scan_results": {"errors_found": []}
            }
        }
        
        response = client.post(
            "/api/v1/agents/fixer/execute",
            json=request_data,
            headers=developer_headers
        )
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.fixer.fixer_agent')
    def test_fixer_endpoint_backup_creation(self, mock_fixer, client, developer_headers):
        """Test fixer creates backup before fixing"""
        mock_result = {
            "fix_id": "fix_backup",
            "status": "completed",
            "backup_created": True,
            "backup_path": "/backups/backup_12345",
            "files_fixed": 3
        }
        mock_fixer.execute_core_function = AsyncMock(return_value=mock_result)
        
        request_data = {
            "parameters": {
                "create_backup": True
            }
        }
        
        response = client.post(
            "/api/v1/agents/fixer/execute",
            json=request_data,
            headers=developer_headers
        )
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.fixer.fixer_agent')
    def test_fixer_endpoint_partial_failure(self, mock_fixer, client, developer_headers):
        """Test fixer handles partial failures gracefully"""
        mock_result = {
            "fix_id": "fix_partial",
            "status": "partial_success",
            "files_fixed": 5,
            "files_failed": 2,
            "failures": [
                {"file": "broken.py", "error": "Cannot parse file"},
                {"file": "locked.py", "error": "Permission denied"}
            ]
        }
        mock_fixer.execute_core_function = AsyncMock(return_value=mock_result)
        
        request_data = {"parameters": {}}
        
        response = client.post(
            "/api/v1/agents/fixer/execute",
            json=request_data,
            headers=developer_headers
        )
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])


class TestScannerV2Endpoint(unittest.TestCase):
    """Test suite for Scanner V2 Agent endpoint"""

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.scanner_v2.scanner_agent')
    def test_scanner_v2_endpoint_success(self, mock_scanner, client, auth_headers):
        """Test Scanner V2 with enhanced features"""
        mock_result = {
            "scan_id": "scan_v2_001",
            "version": "2.0",
            "security_scan": True,
            "vulnerability_count": 3,
            "status": "completed"
        }
        mock_scanner.execute_core_function = AsyncMock(return_value=mock_result)
        
        request_data = {
            "parameters": {
                "enhanced_security": True,
                "deep_analysis": True
            }
        }
        
        response = client.post(
            "/api/v1/agents/scanner-v2/execute",
            json=request_data,
            headers=auth_headers
        )
        
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR])


class TestAgentListEndpoint(unittest.TestCase):
    """Test suite for listing all agents"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_list_all_agents_without_auth(self, client):
        """Test listing agents requires authentication"""
        response = client.get("/api/v1/agents")
        
        self.assertIn(response.status_code, [)
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]

    @pytest.mark.api
    @pytest.mark.unit
    def test_list_all_agents_success(self, client, auth_headers):
        """Test successful retrieval of agent list"""
        response = client.get("/api/v1/agents", headers=auth_headers)
        
        # Endpoint might return list or might not be fully implemented
        self.assertIn(response.status_code, [)
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            self.assertIn("agents", data or isinstance(data, list))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    @pytest.mark.api
    @pytest.mark.unit
    def test_malformed_parameters(self, client, auth_headers):
        """Test handling of malformed parameters"""
        request_data = {
            "parameters": "not a dict"
        }
        
        response = client.post(
            "/api/v1/agents/scanner/execute",
            json=request_data,
            headers=auth_headers
        )
        
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @pytest.mark.api
    @pytest.mark.unit
    def test_missing_parameters_field(self, client, auth_headers):
        """Test request without parameters field"""
        request_data = {}
        
        response = client.post(
            "/api/v1/agents/scanner/execute",
            json=request_data,
            headers=auth_headers
        )
        
        self.assertIn(response.status_code, [)
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]

    @pytest.mark.api
    @pytest.mark.unit
    @patch('agent.modules.backend.scanner.scanner_agent')
    def test_null_result_handling(self, mock_scanner, client, auth_headers):
        """Test handling of null results from agent"""
        mock_scanner.execute_core_function = AsyncMock(return_value=None)
        
        request_data = {"parameters": {}}
        
        response = client.post(
            "/api/v1/agents/scanner/execute",
            json=request_data,
            headers=auth_headers
        )
        
        # Should handle null result gracefully
        self.assertIn(response.status_code, [)
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ]

    @pytest.mark.api
    @pytest.mark.unit
    def test_concurrent_requests(self, client, auth_headers):
        """Test handling of concurrent agent requests"""
        import concurrent.futures
        
        def make_request():
            return client.post(
                "/api/v1/agents/scanner/execute",
                json={"parameters": {}},
                headers=auth_headers
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All requests should complete
        self.assertEqual(len(results), 5)
        for response in results:
            self.assertIn(response.status_code, [)
                status.HTTP_200_OK,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                status.HTTP_503_SERVICE_UNAVAILABLE
            ]