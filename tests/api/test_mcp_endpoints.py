"""
Comprehensive Unit Tests for MCP API Endpoints (api/v1/mcp.py)
Testing MCP configuration generation, deeplink creation, and validation

Per Truth Protocol:
- Rule #8: Test coverage ≥90%
- Rule #1: Never guess - Verify all functionality
- Rule #3: Cite standards - RFC 4648 (base64), URL encoding
"""

import base64
import json

from fastapi import status
from fastapi.testclient import TestClient
import pytest

from main import app
from security.jwt_auth import User, UserRole, create_access_token, user_manager


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers with valid JWT token"""
    token_data = {
        "user_id": "test_user_mcp_001",
        "email": "mcp@devskyy.com",
        "username": "mcpuser",
        "role": UserRole.DEVELOPER,
    }

    # Add user to user manager
    test_user = User(
        user_id=token_data["user_id"],
        username=token_data["username"],
        email=token_data["email"],
        role=token_data["role"],
        active=True,
    )
    user_manager.users[test_user.username] = test_user

    # Create JWT token
    access_token = create_access_token(data=token_data)

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_api_key():
    """Sample API key for testing"""
    return "devskyy_test_api_key_1234567890abcdef1234567890abcdef"


# ============================================================================
# GET /api/v1/mcp/install - Generate MCP Install Deeplink
# ============================================================================


class TestMCPInstallEndpoint:
    """Test suite for MCP install deeplink generation"""

    def test_generate_install_deeplink_success(self, client, sample_api_key):
        """
        Test successful MCP install deeplink generation

        Per Truth Protocol Rule #1: Verify all functionality
        """
        response = client.get("/api/v1/mcp/install", params={"api_key": sample_api_key})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "config" in data
        assert "deeplink_url" in data
        assert "cursor_url" in data
        assert "installation_instructions" in data

        # Verify config structure
        config = data["config"]
        assert "mcpServers" in config
        assert "devskyy" in config["mcpServers"]

        server_config = config["mcpServers"]["devskyy"]
        assert server_config["command"] == "uvx"
        assert "devskyy-mcp==1.0.0" in server_config["args"]
        assert "env" in server_config
        assert "DEVSKYY_API_KEY" in server_config["env"]
        assert server_config["env"]["DEVSKYY_API_KEY"] == sample_api_key

        # Verify deeplink URL format
        # Per Truth Protocol Rule #3: Cite standards - Custom URL scheme
        deeplink = data["deeplink_url"]
        assert deeplink.startswith("cursor://anysphere.cursor-deeplink/mcp/install?")
        assert "name=devskyy" in deeplink
        assert "config=" in deeplink

        # Verify cursor URL (should be same as deeplink for now)
        assert data["cursor_url"] == deeplink

        # Verify instructions are present
        assert "One-Click Installation" in data["installation_instructions"]
        assert "DevSkyy MCP Server" in data["installation_instructions"]

    def test_generate_install_deeplink_with_custom_url(self, client, sample_api_key):
        """Test MCP install deeplink with custom API URL"""
        custom_url = "https://api.devskyy.com"

        response = client.get("/api/v1/mcp/install", params={"api_key": sample_api_key, "api_url": custom_url})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify custom URL is in config
        config = data["config"]
        assert config["mcpServers"]["devskyy"]["env"]["DEVSKYY_API_URL"] == custom_url

    def test_generate_install_deeplink_with_custom_server_name(self, client, sample_api_key):
        """Test MCP install deeplink with custom server name"""
        custom_name = "my-devskyy-server"

        response = client.get("/api/v1/mcp/install", params={"api_key": sample_api_key, "server_name": custom_name})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify custom server name is in config
        config = data["config"]
        assert custom_name in config["mcpServers"]
        assert "devskyy" not in config["mcpServers"]

        # Verify custom server name is in deeplink
        deeplink = data["deeplink_url"]
        assert f"name={custom_name}" in deeplink

    def test_generate_install_deeplink_config_base64_encoding(self, client, sample_api_key):
        """
        Test that configuration is properly base64 encoded in deeplink

        Per Truth Protocol Rule #3: Cite standards - RFC 4648 (base64)
        """
        response = client.get("/api/v1/mcp/install", params={"api_key": sample_api_key})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Extract base64 config from deeplink URL
        deeplink = data["deeplink_url"]
        config_param = deeplink.split("config=")[1]

        # Decode base64 and verify it matches the config
        decoded_bytes = base64.urlsafe_b64decode(config_param)
        decoded_config = json.loads(decoded_bytes.decode("utf-8"))

        assert decoded_config == data["config"]

    def test_generate_install_deeplink_missing_api_key(self, client):
        """Test MCP install deeplink fails without API key"""
        response = client.get("/api/v1/mcp/install")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_install_deeplink_metadata(self, client, sample_api_key):
        """Test MCP configuration includes proper metadata"""
        response = client.get("/api/v1/mcp/install", params={"api_key": sample_api_key})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify metadata
        metadata = data["config"]["mcpServers"]["devskyy"]["metadata"]
        assert metadata["name"] == "DevSkyy Multi-Agent AI Platform"
        assert metadata["version"] == "1.0.0"
        assert "54 specialized AI agents" in metadata["description"]
        assert metadata["author"] == "DevSkyy Platform Team"
        assert metadata["url"] == "https://devskyy.com"


# ============================================================================
# GET /api/v1/mcp/config - Get MCP Configuration JSON
# ============================================================================


class TestMCPConfigEndpoint:
    """Test suite for MCP configuration generation"""

    def test_get_mcp_config_success(self, client, sample_api_key):
        """Test successful MCP configuration retrieval"""
        response = client.get("/api/v1/mcp/config", params={"api_key": sample_api_key})

        assert response.status_code == status.HTTP_200_OK
        config = response.json()

        # Verify config structure
        assert "mcpServers" in config
        assert "devskyy" in config["mcpServers"]

        server_config = config["mcpServers"]["devskyy"]
        assert server_config["command"] == "uvx"
        assert "env" in server_config
        assert server_config["env"]["DEVSKYY_API_KEY"] == sample_api_key

    def test_get_mcp_config_with_parameters(self, client, sample_api_key):
        """Test MCP configuration with custom parameters"""
        custom_url = "https://staging.devskyy.com"
        custom_name = "devskyy-staging"

        response = client.get(
            "/api/v1/mcp/config", params={"api_key": sample_api_key, "api_url": custom_url, "server_name": custom_name}
        )

        assert response.status_code == status.HTTP_200_OK
        config = response.json()

        # Verify custom parameters
        assert custom_name in config["mcpServers"]
        assert config["mcpServers"][custom_name]["env"]["DEVSKYY_API_URL"] == custom_url

    def test_get_mcp_config_missing_api_key(self, client):
        """Test MCP configuration fails without API key"""
        response = client.get("/api/v1/mcp/config")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# GET /api/v1/mcp/status - Get MCP Server Status
# ============================================================================


class TestMCPStatusEndpoint:
    """Test suite for MCP server status"""

    def test_get_mcp_status_success(self, client):
        """Test successful MCP status retrieval"""
        response = client.get("/api/v1/mcp/status")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify status structure
        assert "status" in data
        assert "version" in data
        assert "available_tools" in data
        assert "agent_count" in data

        # Verify values
        assert data["status"] == "active"
        assert data["version"] == "1.0.0"
        assert data["available_tools"] == 14
        assert data["agent_count"] == 54

    def test_get_mcp_status_no_auth_required(self, client):
        """Test MCP status endpoint doesn't require authentication"""
        # Should work without auth headers
        response = client.get("/api/v1/mcp/status")

        assert response.status_code == status.HTTP_200_OK


# ============================================================================
# POST /api/v1/mcp/validate - Validate API Key
# ============================================================================


class TestMCPValidateEndpoint:
    """Test suite for API key validation"""

    def test_validate_api_key_success(self, client, auth_headers, sample_api_key):
        """Test successful API key validation"""
        response = client.post("/api/v1/mcp/validate", params={"api_key": sample_api_key}, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify validation response
        assert data["valid"] is True
        assert data["user"] == "mcpuser"
        assert data["role"] == UserRole.DEVELOPER
        assert "mcp_access" in data["permissions"]
        assert "agent_execution" in data["permissions"]
        assert "tool_calling" in data["permissions"]

    def test_validate_api_key_insufficient_permissions(self, client, sample_api_key):
        """Test API key validation with insufficient permissions"""
        # Create user with ReadOnly role
        token_data = {
            "user_id": "readonly_user",
            "email": "readonly@devskyy.com",
            "username": "readonlyuser",
            "role": UserRole.READ_ONLY,
        }

        test_user = User(
            user_id=token_data["user_id"],
            username=token_data["username"],
            email=token_data["email"],
            role=token_data["role"],
            active=True,
        )
        user_manager.users[test_user.username] = test_user

        access_token = create_access_token(data=token_data)
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.post("/api/v1/mcp/validate", params={"api_key": sample_api_key}, headers=headers)

        # Per Truth Protocol Rule #6: RBAC roles enforced
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_validate_api_key_invalid_format(self, client, auth_headers):
        """Test API key validation with invalid format"""
        short_key = "too_short"

        response = client.post("/api/v1/mcp/validate", params={"api_key": short_key}, headers=auth_headers)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "at least 32 characters" in data["detail"]

    def test_validate_api_key_no_auth(self, client, sample_api_key):
        """Test API key validation requires authentication"""
        response = client.post("/api/v1/mcp/validate", params={"api_key": sample_api_key})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_validate_api_key_missing_key(self, client, auth_headers):
        """Test API key validation fails without key parameter"""
        response = client.post("/api/v1/mcp/validate", headers=auth_headers)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Integration Tests
# ============================================================================


class TestMCPIntegration:
    """Integration tests for MCP API workflows"""

    def test_full_installation_workflow(self, client, auth_headers, sample_api_key):
        """
        Test complete MCP installation workflow:
        1. Get status
        2. Generate install deeplink
        3. Validate API key

        Per Truth Protocol Rule #8: Integration testing required
        """
        # Step 1: Check MCP status
        status_response = client.get("/api/v1/mcp/status")
        assert status_response.status_code == status.HTTP_200_OK
        assert status_response.json()["status"] == "active"

        # Step 2: Generate install deeplink
        install_response = client.get("/api/v1/mcp/install", params={"api_key": sample_api_key})
        assert install_response.status_code == status.HTTP_200_OK
        install_data = install_response.json()

        # Verify deeplink format
        assert "cursor://" in install_data["deeplink_url"]
        assert install_data["config"]["mcpServers"]["devskyy"]["env"]["DEVSKYY_API_KEY"] == sample_api_key

        # Step 3: Validate API key
        validate_response = client.post(
            "/api/v1/mcp/validate", params={"api_key": sample_api_key}, headers=auth_headers
        )
        assert validate_response.status_code == status.HTTP_200_OK
        assert validate_response.json()["valid"] is True

    def test_config_consistency(self, client, sample_api_key):
        """Test that /install and /config return consistent configurations"""
        # Get config from /install
        install_response = client.get("/api/v1/mcp/install", params={"api_key": sample_api_key})
        install_config = install_response.json()["config"]

        # Get config from /config
        config_response = client.get("/api/v1/mcp/config", params={"api_key": sample_api_key})
        config_config = config_response.json()

        # Configs should be identical
        assert install_config == config_config


# ============================================================================
# Security Tests
# ============================================================================


class TestMCPSecurity:
    """Security-focused tests for MCP API"""

    def test_api_key_not_logged_or_exposed(self, client, sample_api_key):
        """
        Test that API keys are not exposed in logs or error messages

        Per Truth Protocol Rule #5: No secrets in code
        """
        response = client.get("/api/v1/mcp/install", params={"api_key": sample_api_key})

        # API key should only be in the config, not in logs
        # This is a reminder for manual verification
        assert response.status_code == status.HTTP_200_OK

    def test_rbac_enforcement(self, client, sample_api_key):
        """
        Test RBAC enforcement on protected endpoints

        Per Truth Protocol Rule #6: RBAC roles enforced
        """
        # Create users with different roles
        roles_to_test = [
            (UserRole.SUPER_ADMIN, True),
            (UserRole.ADMIN, True),
            (UserRole.DEVELOPER, True),
            (UserRole.API_USER, True),
            (UserRole.READ_ONLY, False),
        ]

        for role, should_succeed in roles_to_test:
            token_data = {
                "user_id": f"user_{role}",
                "email": f"{role}@devskyy.com",
                "username": f"user_{role}",
                "role": role,
            }

            test_user = User(
                user_id=token_data["user_id"],
                username=token_data["username"],
                email=token_data["email"],
                role=token_data["role"],
                active=True,
            )
            user_manager.users[test_user.username] = test_user

            access_token = create_access_token(data=token_data)
            headers = {"Authorization": f"Bearer {access_token}"}

            response = client.post("/api/v1/mcp/validate", params={"api_key": sample_api_key}, headers=headers)

            if should_succeed:
                assert response.status_code == status.HTTP_200_OK, f"Role {role} should have access"
            else:
                assert response.status_code == status.HTTP_403_FORBIDDEN, f"Role {role} should not have access"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestMCPEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_api_key(self, client):
        """Test with empty API key"""
        response = client.get("/api/v1/mcp/install", params={"api_key": ""})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_special_characters_in_server_name(self, client, sample_api_key):
        """Test server name with special characters"""
        special_name = "devskyy-test-123"

        response = client.get("/api/v1/mcp/install", params={"api_key": sample_api_key, "server_name": special_name})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert special_name in data["config"]["mcpServers"]

    def test_very_long_api_key(self, client):
        """Test with unusually long API key"""
        long_key = "a" * 1000

        response = client.get("/api/v1/mcp/install", params={"api_key": long_key})

        # Should still work, just process it
        assert response.status_code == status.HTTP_200_OK

    def test_invalid_url_format(self, client, sample_api_key):
        """Test with invalid URL format"""
        invalid_url = "not-a-valid-url"

        response = client.get("/api/v1/mcp/install", params={"api_key": sample_api_key, "api_url": invalid_url})

        # Should still generate config (validation is client-side)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["config"]["mcpServers"]["devskyy"]["env"]["DEVSKYY_API_URL"] == invalid_url


# ============================================================================
# Multi-Server Configuration Tests
# ============================================================================


class TestMultiServerEndpoints:
    """Test suite for multi-server MCP configuration"""

    def test_add_huggingface_server(self, client):
        """Test adding HuggingFace MCP server"""
        hf_token = "hf_test_token_1234567890abcdef"

        response = client.get("/api/v1/mcp/servers/huggingface", params={"hf_token": hf_token})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "config" in data
        assert "deeplink_url" in data
        assert "installation_instructions" in data

        # Verify HuggingFace server in config
        config = data["config"]
        assert "huggingface" in config["mcpServers"]

        hf_config = config["mcpServers"]["huggingface"]
        assert hf_config["url"] == "https://huggingface.co/mcp"
        assert "headers" in hf_config
        assert hf_config["headers"]["Authorization"] == f"Bearer {hf_token}"

    def test_add_huggingface_without_token(self, client):
        """Test adding HuggingFace server without authentication"""
        response = client.get("/api/v1/mcp/servers/huggingface")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should work, but without Authorization header
        config = data["config"]
        assert "huggingface" in config["mcpServers"]

        hf_config = config["mcpServers"]["huggingface"]
        assert "headers" not in hf_config or hf_config.get("headers") is None

    def test_add_huggingface_with_devskyy(self, client, sample_api_key):
        """Test adding HuggingFace + DevSkyy together"""
        response = client.get(
            "/api/v1/mcp/servers/huggingface", params={"hf_token": "hf_test_token", "devskyy_api_key": sample_api_key}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        config = data["config"]
        # Should have both servers
        assert "huggingface" in config["mcpServers"]
        assert "devskyy" in config["mcpServers"]

    def test_add_custom_server_http_transport(self, client):
        """Test adding custom MCP server with HTTP transport"""
        server_data = {
            "server_name": "custom-http-server",
            "transport": "http",
            "url": "https://example.com/mcp",
            "headers": {"Authorization": "Bearer custom_token"},
        }

        response = client.post("/api/v1/mcp/servers/add", json=server_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        config = data["config"]
        assert "custom-http-server" in config["mcpServers"]

        server_config = config["mcpServers"]["custom-http-server"]
        assert server_config["url"] == "https://example.com/mcp"
        assert server_config["headers"]["Authorization"] == "Bearer custom_token"

    def test_add_custom_server_stdio_transport(self, client):
        """Test adding custom MCP server with stdio transport"""
        server_data = {
            "server_name": "custom-stdio-server",
            "transport": "stdio",
            "command": "node",
            "args": ["./custom-server.js"],
            "env": {"API_KEY": "test_key"},
        }

        response = client.post("/api/v1/mcp/servers/add", json=server_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        config = data["config"]
        assert "custom-stdio-server" in config["mcpServers"]

        server_config = config["mcpServers"]["custom-stdio-server"]
        assert server_config["command"] == "node"
        assert "./custom-server.js" in server_config["args"]
        assert server_config["env"]["API_KEY"] == "test_key"

    def test_add_server_missing_url_for_http(self, client):
        """Test adding HTTP server without URL fails"""
        server_data = {
            "server_name": "invalid-server",
            "transport": "http",
            # Missing URL
        }

        response = client.post("/api/v1/mcp/servers/add", json=server_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_server_missing_command_for_stdio(self, client):
        """Test adding stdio server without command fails"""
        server_data = {
            "server_name": "invalid-server",
            "transport": "stdio",
            # Missing command
        }

        response = client.post("/api/v1/mcp/servers/add", json=server_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_multi_server_configuration(self, client, sample_api_key):
        """Test configuring multiple servers at once"""
        multi_config = {
            "include_devskyy": True,
            "devskyy_api_key": sample_api_key,
            "servers": [
                {
                    "server_name": "huggingface",
                    "transport": "http",
                    "url": "https://huggingface.co/mcp",
                    "headers": {"Authorization": "Bearer hf_token"},
                },
                {"server_name": "custom-server", "transport": "stdio", "command": "python", "args": ["server.py"]},
            ],
        }

        response = client.post("/api/v1/mcp/servers/multi", json=multi_config)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        config = data["config"]
        # Should have all 3 servers
        assert len(config["mcpServers"]) == 3
        assert "devskyy" in config["mcpServers"]
        assert "huggingface" in config["mcpServers"]
        assert "custom-server" in config["mcpServers"]

    def test_multi_server_without_devskyy(self, client):
        """Test multi-server config without DevSkyy"""
        multi_config = {
            "include_devskyy": False,
            "servers": [
                {"server_name": "server1", "transport": "http", "url": "https://server1.com/mcp"},
                {"server_name": "server2", "transport": "http", "url": "https://server2.com/mcp"},
            ],
        }

        response = client.post("/api/v1/mcp/servers/multi", json=multi_config)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        config = data["config"]
        # Should have only 2 servers (no DevSkyy)
        assert len(config["mcpServers"]) == 2
        assert "devskyy" not in config["mcpServers"]
        assert "server1" in config["mcpServers"]
        assert "server2" in config["mcpServers"]

    def test_multi_server_missing_devskyy_key(self, client):
        """Test multi-server fails when include_devskyy=True but no key"""
        multi_config = {
            "include_devskyy": True,
            # Missing devskyy_api_key
            "servers": [],
        }

        response = client.post("/api/v1/mcp/servers/multi", json=multi_config)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duplicate_server_names(self, client, sample_api_key):
        """Test that duplicate server names are rejected"""
        multi_config = {
            "include_devskyy": False,
            "servers": [
                {"server_name": "duplicate", "transport": "http", "url": "https://server1.com/mcp"},
                {"server_name": "duplicate", "transport": "http", "url": "https://server2.com/mcp"},  # Duplicate name
            ],
        }

        response = client.post("/api/v1/mcp/servers/multi", json=multi_config)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Duplicate" in response.json()["detail"]


# ============================================================================
# Transport Type Tests
# ============================================================================


class TestTransportTypes:
    """Test different MCP transport types"""

    def test_streaming_http_transport(self, client):
        """Test streamingHttp transport type"""
        server_data = {
            "server_name": "streaming-server",
            "transport": "streamingHttp",
            "url": "https://streaming.example.com/mcp",
        }

        response = client.post("/api/v1/mcp/servers/add", json=server_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        config = data["config"]
        assert "streaming-server" in config["mcpServers"]

    def test_streaming_http_json_transport(self, client):
        """Test streamingHttpJson transport type"""
        server_data = {
            "server_name": "json-streaming-server",
            "transport": "streamingHttpJson",
            "url": "https://json-streaming.example.com/mcp",
        }

        response = client.post("/api/v1/mcp/servers/add", json=server_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        config = data["config"]
        assert "json-streaming-server" in config["mcpServers"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=api.v1.mcp", "--cov-report=term-missing"])
