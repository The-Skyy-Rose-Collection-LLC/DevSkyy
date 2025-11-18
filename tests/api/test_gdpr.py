from fastapi.testclient import TestClient
import pytest

from main import app
from security.jwt_auth import User, UserRole, create_access_token, user_manager


"""
Tests for GDPR Compliance API Endpoints
Tests data export, deletion, and retention policy endpoints per GDPR requirements
"""


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers with valid JWT token"""

    # Create a test user token
    token_data = {
        "user_id": "test_user_123",
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
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_headers():
    """Create admin authentication headers"""
    token_data = {
        "user_id": "admin_123",
        "email": "admin@devskyy.com",
        "username": "admin",
        "role": UserRole.ADMIN,
    }
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


class TestGDPRExportEndpoint:
    """Test GDPR data export endpoint (Article 15)"""

    def test_export_user_data_success(self, client, auth_headers, setup_test_user):
        """Test successful user data export"""
        response = client.get(
            "/api/v1/gdpr/export",
            headers=auth_headers,
            params={
                "format": "json",
                "include_audit_logs": True,
                "include_activity_history": True,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "request_id" in data
        assert "user_id" in data
        assert "email" in data
        assert "export_timestamp" in data
        assert "data" in data
        assert "metadata" in data

        # Verify user data structure
        user_data = data["data"]
        assert "personal_information" in user_data
        assert "account_data" in user_data

        # Verify personal information
        personal_info = user_data["personal_information"]
        assert "user_id" in personal_info
        assert "email" in personal_info
        assert "username" in personal_info
        assert "role" in personal_info

        # Verify metadata
        metadata = data["metadata"]
        assert metadata["export_format"] == "json"
        assert "legal_basis" in metadata
        assert "GDPR Article 15" in metadata["legal_basis"]

    def test_export_without_audit_logs(self, client, auth_headers):
        """Test data export without audit logs"""
        response = client.get(
            "/api/v1/gdpr/export",
            headers=auth_headers,
            params={
                "format": "json",
                "include_audit_logs": False,
                "include_activity_history": False,
            },
        )

        assert response.status_code == 200
        data = response.json()
        user_data = data["data"]

        # Audit logs should not be included
        assert "audit_logs" not in user_data or user_data.get("audit_logs") is None

    def test_export_requires_authentication(self, client):
        """Test that export endpoint requires authentication"""
        response = client.get("/api/v1/gdpr/export")

        assert response.status_code == 401  # Unauthorized

    def test_export_different_formats(self, client, auth_headers):
        """Test export with different format options"""
        for format_type in ["json", "csv", "xml"]:
            response = client.get(
                "/api/v1/gdpr/export",
                headers=auth_headers,
                params={"format": format_type},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["metadata"]["export_format"] == format_type


class TestGDPRDeleteEndpoint:
    """Test GDPR data deletion endpoint (Article 17)"""

    def test_delete_user_data_success(self, client, auth_headers):
        """Test successful user data deletion"""
        delete_request = {
            "confirmation_code": "CONFIRM_DELETE_12345678",
            "delete_activity_logs": True,
            "anonymize_instead_of_delete": False,
        }

        response = client.request("DELETE", "/api/v1/gdpr/delete", headers=auth_headers, json=delete_request)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "request_id" in data
        assert "user_id" in data
        assert "email" in data
        assert "deletion_timestamp" in data
        assert "status" in data
        assert "deleted_records" in data

        # Verify deletion status
        assert data["status"] in ["deleted", "anonymized"]
        assert isinstance(data["deleted_records"], dict)

    def test_delete_with_anonymization(self, client, auth_headers):
        """Test user data anonymization instead of deletion"""
        delete_request = {
            "confirmation_code": "CONFIRM_ANONYMIZE_12345678",
            "delete_activity_logs": False,
            "anonymize_instead_of_delete": True,
        }

        response = client.request("DELETE", "/api/v1/gdpr/delete", headers=auth_headers, json=delete_request)

        assert response.status_code == 200
        data = response.json()

        # Verify anonymization status
        assert data["status"] == "anonymized"
        assert "retained_records" in data
        assert data["retained_records"] is not None

    def test_delete_requires_confirmation_code(self, client, auth_headers):
        """Test that deletion requires valid confirmation code"""
        delete_request = {
            "confirmation_code": "short",  # Too short
            "delete_activity_logs": True,
            "anonymize_instead_of_delete": False,
        }

        response = client.request("DELETE", "/api/v1/gdpr/delete", headers=auth_headers, json=delete_request)

        assert response.status_code == 400  # Bad request

    def test_delete_requires_authentication(self, client):
        """Test that delete endpoint requires authentication"""
        delete_request = {
            "confirmation_code": "CONFIRM_DELETE_12345678",
            "delete_activity_logs": True,
            "anonymize_instead_of_delete": False,
        }

        response = client.request("DELETE", "/api/v1/gdpr/delete", json=delete_request)

        assert response.status_code == 401  # Unauthorized


class TestDataRetentionPolicy:
    """Test data retention policy endpoint"""

    def test_get_retention_policy(self, client):
        """Test retrieving data retention policy (public endpoint)"""
        response = client.get("/api/v1/gdpr/retention-policy")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "policy_version" in data
        assert "last_updated" in data
        assert "retention_periods" in data
        assert "legal_basis" in data

        # Verify retention periods
        retention_periods = data["retention_periods"]
        assert isinstance(retention_periods, dict)
        assert "user_accounts" in retention_periods
        assert "activity_logs" in retention_periods
        assert "audit_logs" in retention_periods

        # Verify legal basis
        legal_basis = data["legal_basis"]
        assert isinstance(legal_basis, list)
        assert len(legal_basis) > 0

    def test_retention_policy_no_auth_required(self, client):
        """Test that retention policy endpoint is public (no auth required)"""
        # Should work without authentication
        response = client.get("/api/v1/gdpr/retention-policy")
        assert response.status_code == 200


class TestDataSubjectRequests:
    """Test admin endpoint for listing GDPR requests"""

    def test_list_requests_requires_admin(self, client, auth_headers):
        """Test that listing requests requires admin role"""
        # Regular user should not be able to access
        response = client.get("/api/v1/gdpr/requests", headers=auth_headers)

        # This might be 403 (Forbidden) depending on RBAC implementation
        assert response.status_code in [401, 403]

    def test_list_requests_success(self, client, admin_headers):
        """Test successful listing of GDPR requests (admin only)"""
        response = client.get("/api/v1/gdpr/requests", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "export_requests" in data
        assert "deletion_requests" in data
        assert "total_requests" in data


class TestGDPRCompliance:
    """Test overall GDPR compliance requirements"""

    def test_gdpr_endpoints_exist(self, client):
        """Test that all required GDPR endpoints exist"""
        # Test OpenAPI schema includes GDPR endpoints
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Verify GDPR endpoints are documented
        assert "/api/v1/gdpr/export" in paths
        assert "/api/v1/gdpr/delete" in paths
        assert "/api/v1/gdpr/retention-policy" in paths
        assert "/api/v1/gdpr/requests" in paths

    def test_export_response_includes_legal_basis(self, client, auth_headers):
        """Test that export includes legal basis per GDPR Article 13"""
        response = client.get("/api/v1/gdpr/export", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify legal basis is documented
        assert "metadata" in data
        assert "legal_basis" in data["metadata"]
        assert len(data["metadata"]["legal_basis"]) > 0

    def test_deletion_preserves_audit_trail(self, client, auth_headers):
        """Test that deletion preserves necessary audit trail"""
        delete_request = {
            "confirmation_code": "CONFIRM_DELETE_12345678",
            "delete_activity_logs": True,
            "anonymize_instead_of_delete": False,
        }

        response = client.request("DELETE", "/api/v1/gdpr/delete", headers=auth_headers, json=delete_request)

        assert response.status_code == 200
        data = response.json()

        # Verify audit trail is preserved
        if data.get("retained_records"):
            # Some records should be retained for legal compliance
            assert "deletion_audit_log" in data["retained_records"]


@pytest.mark.integration
class TestGDPRIntegration:
    """Integration tests for GDPR workflows"""

    def test_full_export_delete_workflow(self, client, auth_headers):
        """Test complete workflow: export data, then delete"""
        # Step 1: Export user data
        export_response = client.get("/api/v1/gdpr/export", headers=auth_headers)
        assert export_response.status_code == 200
        export_data = export_response.json()

        # Verify user has data
        assert len(export_data["data"]) > 0

        # Step 2: Delete user data
        delete_request = {
            "confirmation_code": "CONFIRM_DELETE_WORKFLOW_TEST",
            "delete_activity_logs": True,
            "anonymize_instead_of_delete": False,
        }

        delete_response = client.request("DELETE", "/api/v1/gdpr/delete", headers=auth_headers, json=delete_request)
        assert delete_response.status_code == 200
        delete_data = delete_response.json()

        # Verify deletion occurred
        assert delete_data["status"] == "deleted"
        assert len(delete_data["deleted_records"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
