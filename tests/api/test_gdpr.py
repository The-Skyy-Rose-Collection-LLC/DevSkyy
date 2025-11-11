import unittest
from security.jwt_auth import create_access_token, UserRole

from fastapi.testclient import TestClient

from security.jwt_auth import User, user_manager
from main import app
import pytest

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

class TestGDPRExportEndpoint(unittest.TestCase):
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

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify response structure
        self.assertIn("request_id", data)
        self.assertIn("user_id", data)
        self.assertIn("email", data)
        self.assertIn("export_timestamp", data)
        self.assertIn("data", data)
        self.assertIn("metadata", data)

        # Verify user data structure
        user_data = data["data"]
        self.assertIn("personal_information", user_data)
        self.assertIn("account_data", user_data)

        # Verify personal information
        personal_info = user_data["personal_information"]
        self.assertIn("user_id", personal_info)
        self.assertIn("email", personal_info)
        self.assertIn("username", personal_info)
        self.assertIn("role", personal_info)

        # Verify metadata
        metadata = data["metadata"]
        self.assertEqual(metadata["export_format"], "json")
        self.assertIn("legal_basis", metadata)
        self.assertIn("GDPR Article 15", metadata["legal_basis"])

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

        self.assertEqual(response.status_code, 200)
        data = response.json()
        user_data = data["data"]

        # Audit logs should not be included
        self.assertIn("audit_logs" not, user_data or user_data.get("audit_logs") is None)

    def test_export_requires_authentication(self, client):
        """Test that export endpoint requires authentication"""
        response = client.get("/api/v1/gdpr/export")

        self.assertEqual(response.status_code, 401  # Unauthorized)

    def test_export_different_formats(self, client, auth_headers):
        """Test export with different format options"""
        for format_type in ["json", "csv", "xml"]:
            response = client.get(
                "/api/v1/gdpr/export",
                headers=auth_headers,
                params={"format": format_type},
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["metadata"]["export_format"], format_type)

class TestGDPRDeleteEndpoint(unittest.TestCase):
    """Test GDPR data deletion endpoint (Article 17)"""

    def test_delete_user_data_success(self, client, auth_headers):
        """Test successful user data deletion"""
        delete_request = {
            "confirmation_code": "CONFIRM_DELETE_12345678",
            "delete_activity_logs": True,
            "anonymize_instead_of_delete": False,
        }

        response = client.request(
            "DELETE", "/api/v1/gdpr/delete", headers=auth_headers, json=delete_request
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify response structure
        self.assertIn("request_id", data)
        self.assertIn("user_id", data)
        self.assertIn("email", data)
        self.assertIn("deletion_timestamp", data)
        self.assertIn("status", data)
        self.assertIn("deleted_records", data)

        # Verify deletion status
        self.assertIn(data["status"], ["deleted", "anonymized"])
        self.assertIsInstance(data["deleted_records"], dict)

    def test_delete_with_anonymization(self, client, auth_headers):
        """Test user data anonymization instead of deletion"""
        delete_request = {
            "confirmation_code": "CONFIRM_ANONYMIZE_12345678",
            "delete_activity_logs": False,
            "anonymize_instead_of_delete": True,
        }

        response = client.request(
            "DELETE", "/api/v1/gdpr/delete", headers=auth_headers, json=delete_request
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify anonymization status
        self.assertEqual(data["status"], "anonymized")
        self.assertIn("retained_records", data)
        self.assertIsNotNone(data["retained_records"])

    def test_delete_requires_confirmation_code(self, client, auth_headers):
        """Test that deletion requires valid confirmation code"""
        delete_request = {
            "confirmation_code": "short",  # Too short
            "delete_activity_logs": True,
            "anonymize_instead_of_delete": False,
        }

        response = client.request(
            "DELETE", "/api/v1/gdpr/delete", headers=auth_headers, json=delete_request
        )

        self.assertEqual(response.status_code, 400  # Bad request)

    def test_delete_requires_authentication(self, client):
        """Test that delete endpoint requires authentication"""
        delete_request = {
            "confirmation_code": "CONFIRM_DELETE_12345678",
            "delete_activity_logs": True,
            "anonymize_instead_of_delete": False,
        }

        response = client.request("DELETE", "/api/v1/gdpr/delete", json=delete_request)

        self.assertEqual(response.status_code, 401  # Unauthorized)

class TestDataRetentionPolicy(unittest.TestCase):
    """Test data retention policy endpoint"""

    def test_get_retention_policy(self, client):
        """Test retrieving data retention policy (public endpoint)"""
        response = client.get("/api/v1/gdpr/retention-policy")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify response structure
        self.assertIn("policy_version", data)
        self.assertIn("last_updated", data)
        self.assertIn("retention_periods", data)
        self.assertIn("legal_basis", data)

        # Verify retention periods
        retention_periods = data["retention_periods"]
        self.assertIsInstance(retention_periods, dict)
        self.assertIn("user_accounts", retention_periods)
        self.assertIn("activity_logs", retention_periods)
        self.assertIn("audit_logs", retention_periods)

        # Verify legal basis
        legal_basis = data["legal_basis"]
        self.assertIsInstance(legal_basis, list)
        self.assertGreater(len(legal_basis), 0)

    def test_retention_policy_no_auth_required(self, client):
        """Test that retention policy endpoint is public (no auth required)"""
        # Should work without authentication
        response = client.get("/api/v1/gdpr/retention-policy")
        self.assertEqual(response.status_code, 200)

class TestDataSubjectRequests(unittest.TestCase):
    """Test admin endpoint for listing GDPR requests"""

    def test_list_requests_requires_admin(self, client, auth_headers):
        """Test that listing requests requires admin role"""
        # Regular user should not be able to access
        response = client.get("/api/v1/gdpr/requests", headers=auth_headers)

        # This might be 403 (Forbidden) depending on RBAC implementation
        self.assertIn(response.status_code, [401, 403])

    def test_list_requests_success(self, client, admin_headers):
        """Test successful listing of GDPR requests (admin only)"""
        response = client.get("/api/v1/gdpr/requests", headers=admin_headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify response structure
        self.assertIn("export_requests", data)
        self.assertIn("deletion_requests", data)
        self.assertIn("total_requests", data)

class TestGDPRCompliance(unittest.TestCase):
    """Test overall GDPR compliance requirements"""

    def test_gdpr_endpoints_exist(self, client):
        """Test that all required GDPR endpoints exist"""
        # Test OpenAPI schema includes GDPR endpoints
        response = client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)

        openapi_schema = response.json()
        paths = openapi_schema.get("paths", {})

        # Verify GDPR endpoints are documented
        self.assertIn("/api/v1/gdpr/export", paths)
        self.assertIn("/api/v1/gdpr/delete", paths)
        self.assertIn("/api/v1/gdpr/retention-policy", paths)
        self.assertIn("/api/v1/gdpr/requests", paths)

    def test_export_response_includes_legal_basis(self, client, auth_headers):
        """Test that export includes legal basis per GDPR Article 13"""
        response = client.get("/api/v1/gdpr/export", headers=auth_headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify legal basis is documented
        self.assertIn("metadata", data)
        self.assertIn("legal_basis", data["metadata"])
        self.assertGreater(len(data["metadata"]["legal_basis"]), 0)

    def test_deletion_preserves_audit_trail(self, client, auth_headers):
        """Test that deletion preserves necessary audit trail"""
        delete_request = {
            "confirmation_code": "CONFIRM_DELETE_12345678",
            "delete_activity_logs": True,
            "anonymize_instead_of_delete": False,
        }

        response = client.request(
            "DELETE", "/api/v1/gdpr/delete", headers=auth_headers, json=delete_request
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify audit trail is preserved
        if "retained_records" in data and data["retained_records"]:
            # Some records should be retained for legal compliance
            self.assertIn("deletion_audit_log", data["retained_records"])

@pytest.mark.integration
class TestGDPRIntegration(unittest.TestCase):
    """Integration tests for GDPR workflows"""

    def test_full_export_delete_workflow(self, client, auth_headers):
        """Test complete workflow: export data, then delete"""
        # Step 1: Export user data
        export_response = client.get("/api/v1/gdpr/export", headers=auth_headers)
        self.assertEqual(export_response.status_code, 200)
        export_data = export_response.json()

        # Verify user has data
        self.assertGreater(len(export_data["data"]), 0)

        # Step 2: Delete user data
        delete_request = {
            "confirmation_code": "CONFIRM_DELETE_WORKFLOW_TEST",
            "delete_activity_logs": True,
            "anonymize_instead_of_delete": False,
        }

        delete_response = client.request(
            "DELETE", "/api/v1/gdpr/delete", headers=auth_headers, json=delete_request
        )
        self.assertEqual(delete_response.status_code, 200)
        delete_data = delete_response.json()

        # Verify deletion occurred
        self.assertEqual(delete_data["status"], "deleted")
        self.assertGreater(len(delete_data["deleted_records"]), 0)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
