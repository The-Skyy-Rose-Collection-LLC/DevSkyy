"""
GDPR Compliance Tests
=====================

Tests for GDPR compliance endpoints:
- Article 15: Right of Access (data export)
- Article 17: Right to Erasure (deletion)
- Article 13: Right to Information (retention policies)
- Article 30: Records of Processing (audit trail)
"""

import pytest
from datetime import datetime, timezone

pytestmark = [pytest.mark.integration]


class TestGDPRExport:
    """Article 15 - Right of Access tests"""
    
    @pytest.mark.asyncio
    async def test_export_user_data_json(self, client, auth_headers):
        """Test data export in JSON format"""
        response = await client.post(
            "/api/v1/gdpr/export",
            headers=auth_headers,
            json={
                "format": "json",
                "categories": ["identity", "financial", "behavioral"],
                "include_metadata": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "request_id" in data
        assert data["request_id"].startswith("gdpr_exp_")
        assert "user_id" in data
        assert data["format"] == "json"
        assert "created_at" in data
        assert "expires_at" in data
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_export_includes_all_categories(self, client, auth_headers):
        """Test export includes all requested categories"""
        response = await client.post(
            "/api/v1/gdpr/export",
            headers=auth_headers,
            json={
                "format": "json",
                "categories": ["identity", "financial", "behavioral", "technical", "communications"],
                "include_metadata": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        assert "identity" in data
        assert "financial" in data
        assert "behavioral" in data
        assert "technical" in data
        assert "communications" in data
    
    @pytest.mark.asyncio
    async def test_export_metadata_includes_rights(self, client, auth_headers):
        """Test export metadata includes user rights"""
        response = await client.post(
            "/api/v1/gdpr/export",
            headers=auth_headers,
            json={
                "format": "json",
                "categories": ["identity"],
                "include_metadata": True
            }
        )
        
        assert response.status_code == 200
        metadata = response.json()["data"]["_metadata"]
        
        assert "your_rights" in metadata
        assert "rectification" in metadata["your_rights"]
        assert "erasure" in metadata["your_rights"]
        assert "restriction" in metadata["your_rights"]
        assert "portability" in metadata["your_rights"]
        assert "object" in metadata["your_rights"]
    
    @pytest.mark.asyncio
    async def test_export_requires_authentication(self, client):
        """Test export requires authentication"""
        response = await client.post(
            "/api/v1/gdpr/export",
            json={"format": "json", "categories": ["identity"]}
        )
        
        assert response.status_code == 401


class TestGDPRDelete:
    """Article 17 - Right to Erasure tests"""
    
    @pytest.mark.asyncio
    async def test_delete_with_valid_confirmation(self, client, auth_headers):
        """Test deletion with valid confirmation code"""
        response = await client.delete(
            "/api/v1/gdpr/delete",
            headers=auth_headers,
            json={
                "confirmation_code": "CONFIRM_DELETE",
                "anonymize_instead": False,
                "reason": "No longer using service"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["request_id"].startswith("gdpr_del_")
        assert data["status"] == "completed"
        assert data["action_taken"] == "deleted"
        assert len(data["deleted_categories"]) > 0
    
    @pytest.mark.asyncio
    async def test_delete_with_invalid_confirmation(self, client, auth_headers):
        """Test deletion with invalid confirmation code"""
        response = await client.delete(
            "/api/v1/gdpr/delete",
            headers=auth_headers,
            json={
                "confirmation_code": "WRONG_CODE",
                "anonymize_instead": False
            }
        )
        
        assert response.status_code == 400
        assert "Invalid confirmation" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_anonymize_instead_of_delete(self, client, auth_headers):
        """Test anonymization option"""
        response = await client.delete(
            "/api/v1/gdpr/delete",
            headers=auth_headers,
            json={
                "confirmation_code": "CONFIRM_DELETE",
                "anonymize_instead": True,
                "reason": "Want to preserve some data"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["action_taken"] == "anonymized"
    
    @pytest.mark.asyncio
    async def test_delete_retains_financial_data(self, client, auth_headers):
        """Test that financial data is retained for legal compliance"""
        response = await client.delete(
            "/api/v1/gdpr/delete",
            headers=auth_headers,
            json={
                "confirmation_code": "CONFIRM_DELETE",
                "anonymize_instead": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Financial data should be retained
        assert data["retained_data"] is not None
        assert "financial" in data["retained_data"]
        assert "tax" in data["retained_data"]["financial"].lower()


class TestRetentionPolicies:
    """Article 13 - Right to Information tests"""
    
    @pytest.mark.asyncio
    async def test_get_retention_policies_public(self, client):
        """Test retention policies are publicly accessible"""
        response = await client.get("/api/v1/gdpr/retention-policy")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "policies" in data
        assert "data_controller" in data
        assert "privacy_officer_contact" in data
    
    @pytest.mark.asyncio
    async def test_retention_policies_structure(self, client):
        """Test retention policies have correct structure"""
        response = await client.get("/api/v1/gdpr/retention-policy")
        
        assert response.status_code == 200
        policies = response.json()["policies"]
        
        for policy in policies:
            assert "data_category" in policy
            assert "retention_days" in policy
            assert "legal_basis" in policy
            assert "description" in policy
    
    @pytest.mark.asyncio
    async def test_data_controller_info(self, client):
        """Test data controller information is present"""
        response = await client.get("/api/v1/gdpr/retention-policy")
        
        assert response.status_code == 200
        controller = response.json()["data_controller"]
        
        assert "name" in controller
        assert "email" in controller
        assert "address" in controller


class TestGDPRAudit:
    """Article 30 - Records of Processing tests"""
    
    @pytest.mark.asyncio
    async def test_admin_can_view_requests(self, client, admin_headers):
        """Test admin can view GDPR requests"""
        response = await client.get(
            "/api/v1/gdpr/requests",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_non_admin_cannot_view_requests(self, client, auth_headers):
        """Test non-admin cannot view all requests"""
        response = await client.get(
            "/api/v1/gdpr/requests",
            headers=auth_headers
        )
        
        # Should be forbidden for non-admin
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_filter_requests_by_type(self, client, admin_headers):
        """Test filtering requests by type"""
        response = await client.get(
            "/api/v1/gdpr/requests",
            headers=admin_headers,
            params={"request_type": "export"}
        )
        
        assert response.status_code == 200


class TestConsent:
    """Consent management tests"""
    
    @pytest.mark.asyncio
    async def test_record_consent(self, client, auth_headers):
        """Test recording consent"""
        response = await client.post(
            "/api/v1/gdpr/consent",
            headers=auth_headers,
            params={
                "purpose": "marketing_emails",
                "granted": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["recorded"] is True
        assert "consent_id" in data
    
    @pytest.mark.asyncio
    async def test_get_user_consents(self, client, auth_headers):
        """Test retrieving user consents"""
        # First record a consent
        await client.post(
            "/api/v1/gdpr/consent",
            headers=auth_headers,
            params={"purpose": "analytics", "granted": True}
        )
        
        # Then retrieve
        response = await client.get(
            "/api/v1/gdpr/consent",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    async def test_consent_requires_auth(self, client):
        """Test consent endpoints require authentication"""
        response = await client.post(
            "/api/v1/gdpr/consent",
            params={"purpose": "test", "granted": True}
        )
        
        assert response.status_code == 401


class TestGDPRIntegration:
    """GDPR workflow integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_data_lifecycle(self, client, auth_headers):
        """Test complete data lifecycle: consent → export → delete"""
        # 1. Record consent
        consent_response = await client.post(
            "/api/v1/gdpr/consent",
            headers=auth_headers,
            params={"purpose": "data_processing", "granted": True}
        )
        assert consent_response.status_code == 200
        
        # 2. Export data
        export_response = await client.post(
            "/api/v1/gdpr/export",
            headers=auth_headers,
            json={
                "format": "json",
                "categories": ["identity", "behavioral"],
                "include_metadata": True
            }
        )
        assert export_response.status_code == 200
        assert "data" in export_response.json()
        
        # 3. Request deletion
        delete_response = await client.delete(
            "/api/v1/gdpr/delete",
            headers=auth_headers,
            json={
                "confirmation_code": "CONFIRM_DELETE",
                "anonymize_instead": False,
                "reason": "Testing lifecycle"
            }
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_export_before_and_after_delete(self, client, auth_headers):
        """Test data export before and after deletion request"""
        # Export before delete
        export1 = await client.post(
            "/api/v1/gdpr/export",
            headers=auth_headers,
            json={"format": "json", "categories": ["identity"]}
        )
        assert export1.status_code == 200
        
        # Delete
        delete = await client.delete(
            "/api/v1/gdpr/delete",
            headers=auth_headers,
            json={"confirmation_code": "CONFIRM_DELETE", "anonymize_instead": False}
        )
        assert delete.status_code == 200
        
        # Export after delete (should still work but with less data)
        export2 = await client.post(
            "/api/v1/gdpr/export",
            headers=auth_headers,
            json={"format": "json", "categories": ["identity"]}
        )
        # This depends on implementation - may still work or return minimal data
        assert export2.status_code in [200, 404]


class TestGDPRCompliance:
    """GDPR regulation compliance tests"""
    
    @pytest.mark.asyncio
    async def test_response_within_30_days(self, client, auth_headers):
        """Test export response includes 30-day validity"""
        response = await client.post(
            "/api/v1/gdpr/export",
            headers=auth_headers,
            json={"format": "json", "categories": ["identity"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        created = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        expires = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
        
        diff = expires - created
        assert diff.days == 30  # GDPR requires response within 30 days
    
    @pytest.mark.asyncio
    async def test_portable_data_format(self, client, auth_headers):
        """Test data is provided in portable format (Article 20)"""
        response = await client.post(
            "/api/v1/gdpr/export",
            headers=auth_headers,
            json={"format": "json", "categories": ["identity", "financial"]}
        )
        
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")
    
    @pytest.mark.asyncio
    async def test_legal_basis_documented(self, client):
        """Test legal basis is documented for all data categories"""
        response = await client.get("/api/v1/gdpr/retention-policy")
        
        assert response.status_code == 200
        policies = response.json()["policies"]
        
        valid_legal_bases = [
            "consent", "contract", "legal_obligation",
            "vital_interests", "public_task", "legitimate_interests"
        ]
        
        for policy in policies:
            assert policy["legal_basis"] in valid_legal_bases
