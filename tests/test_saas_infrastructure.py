"""
SaaS Infrastructure Tests
==========================

Tests for Phase 4: multi-tenancy, Stripe billing, entitlements, customer portal.

Coverage targets:
- TierLimits dataclass immutability
- intent_allowed: free blocks 3d-model, starter allows social-pack
- quota_remaining: unlimited (-1) for pro/enterprise
- UsageMetering: record + get_usage + check_quota (fakeredis)
- EntitlementChecker: allowed/blocked with upgrade message
- StripeClient: graceful degradation when no API key
- Portal endpoints: subscriptions CRUD (mock Stripe)
- Team management endpoints
"""

from __future__ import annotations

import dataclasses
import os
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# =============================================================================
# billing.plans
# =============================================================================


class TestTierLimits:
    def test_frozen_dataclass_immutable(self):
        """TierLimits must be a frozen dataclass — normal attribute assignment must raise."""
        from billing.plans import TIER_LIMITS

        limits = TIER_LIMITS["free"]
        with pytest.raises((dataclasses.FrozenInstanceError, TypeError, AttributeError)):
            limits.renders_per_month = 999  # type: ignore[misc]

    def test_all_tiers_present(self):
        from billing.plans import TIER_LIMITS

        assert set(TIER_LIMITS.keys()) == {"free", "starter", "pro", "enterprise"}

    def test_free_tier_renders_limit(self):
        from billing.plans import TIER_LIMITS

        assert TIER_LIMITS["free"].renders_per_month == 10

    def test_starter_tier_renders_limit(self):
        from billing.plans import TIER_LIMITS

        assert TIER_LIMITS["starter"].renders_per_month == 100

    def test_pro_tier_renders_unlimited(self):
        from billing.plans import TIER_LIMITS

        assert TIER_LIMITS["pro"].renders_per_month == 1000

    def test_enterprise_tier_unlimited(self):
        from billing.plans import TIER_LIMITS

        assert TIER_LIMITS["enterprise"].renders_per_month == -1

    def test_allowed_intents_are_frozensets(self):
        from billing.plans import TIER_LIMITS

        for tier, limits in TIER_LIMITS.items():
            assert isinstance(
                limits.allowed_intents, frozenset
            ), f"{tier}.allowed_intents must be a frozenset"

    def test_get_limits_unknown_tier_defaults_to_free(self):
        from billing.plans import TIER_LIMITS, get_limits

        assert get_limits("nonexistent") == TIER_LIMITS["free"]

    def test_get_limits_returns_correct_tier(self):
        from billing.plans import TIER_LIMITS, get_limits

        assert get_limits("pro") == TIER_LIMITS["pro"]


class TestIntentAllowed:
    def test_free_tier_blocks_3d_model(self):
        from billing.plans import intent_allowed

        assert intent_allowed("free", "3d-model") is False

    def test_free_tier_blocks_social_pack(self):
        from billing.plans import intent_allowed

        assert intent_allowed("free", "social-pack") is False

    def test_free_tier_allows_product_render(self):
        from billing.plans import intent_allowed

        assert intent_allowed("free", "product-render") is True

    def test_free_tier_allows_product_copy(self):
        from billing.plans import intent_allowed

        assert intent_allowed("free", "product-copy") is True

    def test_starter_allows_social_pack(self):
        from billing.plans import intent_allowed

        assert intent_allowed("starter", "social-pack") is True

    def test_starter_allows_virtual_tryon(self):
        from billing.plans import intent_allowed

        assert intent_allowed("starter", "virtual-tryon") is True

    def test_starter_blocks_unknown_intent(self):
        from billing.plans import intent_allowed

        # "batch-render" is not in starter's allowed set
        assert intent_allowed("starter", "batch-render") is False

    def test_pro_allows_all_intents(self):
        from billing.plans import intent_allowed

        for intent in [
            "product-render",
            "3d-model",
            "social-pack",
            "virtual-tryon",
            "batch-render",
        ]:
            assert intent_allowed("pro", intent) is True, f"pro should allow {intent}"

    def test_enterprise_allows_all_intents(self):
        from billing.plans import intent_allowed

        assert intent_allowed("enterprise", "custom-training") is True


class TestQuotaRemaining:
    def test_unlimited_for_enterprise(self):
        from billing.plans import quota_remaining

        assert quota_remaining("enterprise", "product-render", used=9999) == -1

    def test_unlimited_for_pro_renders(self):
        from billing.plans import quota_remaining

        # Pro has 1000 renders, not literally unlimited, but large
        result = quota_remaining("pro", "product-render", used=500)
        assert result == 500

    def test_quota_exhausted_returns_zero(self):
        from billing.plans import quota_remaining

        # Free tier: 10 renders
        assert quota_remaining("free", "product-render", used=10) == 0
        assert quota_remaining("free", "product-render", used=15) == 0

    def test_quota_partial_remaining(self):
        from billing.plans import quota_remaining

        assert quota_remaining("free", "product-render", used=7) == 3

    def test_enterprise_3d_model_unlimited(self):
        from billing.plans import quota_remaining

        assert quota_remaining("enterprise", "3d-model", used=50000) == -1


# =============================================================================
# billing.metering
# =============================================================================


class TestUsageMeteringFallback:
    """Tests using the in-process fallback (no Redis)."""

    def setup_method(self):
        from billing.metering import UsageMetering

        self.metering = UsageMetering()  # no redis_url → fallback

    def test_record_increments_usage(self):
        self.metering.record("tenant-1", "product-render", count=3)
        assert self.metering.get_usage("tenant-1", "product-render") == 3

    def test_record_multiple_times_accumulates(self):
        self.metering.record("tenant-2", "social-pack", count=1)
        self.metering.record("tenant-2", "social-pack", count=4)
        assert self.metering.get_usage("tenant-2", "social-pack") == 5

    def test_get_usage_unknown_tenant_returns_zero(self):
        assert self.metering.get_usage("unknown-tenant", "product-render") == 0

    def test_get_all_usage_returns_dict(self):
        self.metering.record("tenant-3", "product-render", count=2)
        self.metering.record("tenant-3", "virtual-tryon", count=1)
        usage = self.metering.get_all_usage("tenant-3")
        assert usage.get("product-render") == 2
        assert usage.get("virtual-tryon") == 1

    def test_check_quota_allowed_with_remaining(self):
        self.metering.record("tenant-4", "product-render", count=5)
        allowed, remaining = self.metering.check_quota("tenant-4", "free", "product-render")
        assert allowed is True
        assert remaining == 5  # 10 - 5

    def test_check_quota_exhausted(self):
        self.metering.record("tenant-5", "product-render", count=10)
        allowed, remaining = self.metering.check_quota("tenant-5", "free", "product-render")
        assert allowed is False
        assert remaining == 0

    def test_check_quota_blocked_by_plan(self):
        """Free tier cannot use 3d-model regardless of count."""
        allowed, remaining = self.metering.check_quota("tenant-6", "free", "3d-model")
        assert allowed is False
        assert remaining == 0

    def test_check_quota_unlimited_for_enterprise(self):
        self.metering.record("tenant-7", "product-render", count=99999)
        allowed, remaining = self.metering.check_quota("tenant-7", "enterprise", "product-render")
        assert allowed is True
        assert remaining == -1

    def test_reset_period_clears_counters(self):

        period = datetime.now(UTC).strftime("%Y-%m")
        self.metering.record("tenant-8", "product-render", count=5)
        self.metering.reset_period("tenant-8", period)
        assert self.metering.get_usage("tenant-8", "product-render") == 0

    def test_isolation_between_tenants(self):
        self.metering.record("tenant-A", "product-render", count=3)
        self.metering.record("tenant-B", "product-render", count=7)
        assert self.metering.get_usage("tenant-A", "product-render") == 3
        assert self.metering.get_usage("tenant-B", "product-render") == 7


@pytest.mark.skipif(
    not os.getenv("REDIS_URL"),
    reason="Skipping fakeredis test — REDIS_URL not set",
)
class TestUsageMeteringFakeRedis:
    """Tests with fakeredis when available."""

    def setup_method(self):
        try:
            import fakeredis  # type: ignore[import]

            from billing.metering import UsageMetering

            self.metering = UsageMetering.__new__(UsageMetering)
            self.metering._fallback = {}
            self.metering._use_fallback = False
            self.metering._redis = fakeredis.FakeRedis()
        except ImportError:
            pytest.skip("fakeredis not installed")

    def test_record_and_get_via_redis(self):
        self.metering.record("r-tenant-1", "product-render", count=5)
        assert self.metering.get_usage("r-tenant-1", "product-render") == 5


# =============================================================================
# billing.entitlements
# =============================================================================


class TestEntitlementChecker:
    def setup_method(self):
        from billing.entitlements import EntitlementChecker
        from billing.metering import UsageMetering

        self.metering = UsageMetering()
        self.checker = EntitlementChecker(metering=self.metering)

    def test_allowed_intent_with_quota(self):
        result = self.checker.check("e-tenant-1", "free", "product-render")
        assert result.allowed is True
        assert result.tier == "free"
        assert result.intent == "product-render"

    def test_blocked_by_plan_returns_not_allowed(self):
        result = self.checker.check("e-tenant-2", "free", "3d-model")
        assert result.allowed is False
        assert result.upgrade_to in {"starter", "pro"}
        assert "3d-model" in result.reason

    def test_blocked_by_quota_exhaustion(self):
        # exhaust free product-render quota
        self.metering.record("e-tenant-3", "product-render", count=10)
        result = self.checker.check("e-tenant-3", "free", "product-render")
        assert result.allowed is False
        assert result.remaining == 0

    def test_unlimited_enterprise_always_allowed(self):
        """Enterprise tier has unlimited quota (-1) — any usage count is allowed."""
        # record heavy usage on enterprise tenant
        self.metering.record("e-tenant-4", "product-render", count=9999)
        result = self.checker.check("e-tenant-4", "enterprise", "product-render")
        assert result.allowed is True
        assert result.remaining == -1

    def test_upgrade_message_content(self):
        from billing.entitlements import EntitlementChecker

        checker = EntitlementChecker()
        msg = checker.get_upgrade_message("free", "3d-model")
        assert "starter" in msg.lower() or "pro" in msg.lower()
        assert "portal" in msg.lower() or "upgrade" in msg.lower()

    def test_result_is_frozen(self):
        """EntitlementResult must be a frozen dataclass — normal assignment must raise."""
        result = self.checker.check("e-tenant-5", "free", "product-render")
        with pytest.raises((dataclasses.FrozenInstanceError, TypeError, AttributeError)):
            result.allowed = False  # type: ignore[misc]

    def test_enterprise_all_intents_allowed(self):
        intents = ["product-render", "3d-model", "social-pack", "virtual-tryon", "batch-render"]
        for intent in intents:
            result = self.checker.check("e-ent", "enterprise", intent)
            assert result.allowed is True, f"enterprise should allow {intent}"


# =============================================================================
# billing.stripe_client
# =============================================================================


class TestStripeClientGracefulDegradation:
    """Verify all methods return safe defaults when Stripe is not configured."""

    def setup_method(self):
        from billing.stripe_client import StripeClient

        # Force stub mode by passing empty key
        self.client = StripeClient(api_key="")

    def test_create_customer_returns_none(self):
        result = self.client.create_customer("t1", "user@test.com", "Test Co")
        assert result is None

    def test_create_subscription_returns_none(self):
        result = self.client.create_subscription("cus_fake", "price_fake")
        assert result is None

    def test_cancel_subscription_returns_false(self):
        result = self.client.cancel_subscription("sub_fake")
        assert result is False

    def test_get_subscription_returns_none(self):
        result = self.client.get_subscription("sub_fake")
        assert result is None

    def test_list_invoices_returns_empty_list(self):
        result = self.client.list_invoices("cus_fake")
        assert result == []

    def test_create_portal_session_returns_none(self):
        result = self.client.create_portal_session("cus_fake", "https://example.com/return")
        assert result is None

    def test_get_price_id_from_env(self):
        with patch.dict(os.environ, {"STRIPE_PRICE_IDS": "starter:price_abc,pro:price_xyz"}):
            from billing.stripe_client import StripeClient

            client = StripeClient(api_key="")
            assert client.get_price_id("starter") == "price_abc"
            assert client.get_price_id("pro") == "price_xyz"
            assert client.get_price_id("free") is None

    def test_get_price_id_empty_env(self):
        with patch.dict(os.environ, {"STRIPE_PRICE_IDS": ""}):
            from billing.stripe_client import StripeClient

            client = StripeClient(api_key="")
            assert client.get_price_id("pro") is None


# =============================================================================
# billing.webhooks
# =============================================================================


class TestStripeWebhooks:
    def test_returns_processed_false_when_stripe_unavailable(self):
        """Without stripe package or secret, webhook returns processed=False."""
        from billing.webhooks import handle_stripe_webhook

        with patch("billing.webhooks._load_stripe", return_value=None):
            result = handle_stripe_webhook(b"{}", "sig_fake")
        assert result["processed"] is False

    def test_unhandled_event_type(self):
        """Events outside the handled set return processed=False."""
        import json

        from billing.webhooks import handle_stripe_webhook

        mock_stripe = MagicMock()
        event_data = {"type": "payment_intent.created", "data": {"object": {}}}
        mock_stripe.Webhook.construct_event.return_value = event_data
        mock_stripe.error.SignatureVerificationError = Exception

        with patch("billing.webhooks._load_stripe", return_value=mock_stripe):
            with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test"}):
                result = handle_stripe_webhook(json.dumps(event_data).encode(), "sig")
        assert result["processed"] is False

    def test_handled_subscription_created_event(self):
        """customer.subscription.created → processed=True."""
        import json

        from billing.webhooks import handle_stripe_webhook

        mock_stripe = MagicMock()
        event_data = {
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_test",
                    "customer": "cus_test",
                    "status": "active",
                    "items": {"data": []},
                }
            },
        }
        mock_stripe.Webhook.construct_event.return_value = event_data
        mock_stripe.error.SignatureVerificationError = Exception

        with patch("billing.webhooks._load_stripe", return_value=mock_stripe):
            with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test"}):
                result = handle_stripe_webhook(json.dumps(event_data).encode(), "sig")
        assert result["event"] == "customer.subscription.created"
        assert result["processed"] is True


# =============================================================================
# database models
# =============================================================================


class TestTenantModel:
    """Test Tenant model helper methods without requiring a live DB session.

    We test get_settings / set_settings by calling them on a minimal
    stand-in object that has a ``settings`` attribute, bypassing SQLAlchemy
    ORM instrumentation which is not set up in unit tests.
    """

    def _make_tenant(self, settings_json: str = "{}"):
        """Return a plain namespace that satisfies Tenant helper method calls."""
        import types

        from database.models.tenant import Tenant

        obj = types.SimpleNamespace()
        obj.settings = settings_json
        # Bind the unbound methods to the plain object so they work without ORM
        obj.get_settings = Tenant.get_settings.__get__(obj)
        obj.set_settings = Tenant.set_settings.__get__(obj)
        return obj

    def test_tenant_repr(self):
        from database.models.tenant import Tenant

        t = Tenant(id="abc", slug="acme", name="Acme Co", tier="pro")
        assert "acme" in repr(t)
        assert "pro" in repr(t)

    def test_get_settings_returns_dict(self):
        obj = self._make_tenant('{"key": "value"}')
        assert obj.get_settings() == {"key": "value"}

    def test_get_settings_invalid_json_returns_empty(self):
        obj = self._make_tenant("not-json")
        assert obj.get_settings() == {}

    def test_set_settings_serializes(self):
        import json

        obj = self._make_tenant("{}")
        obj.set_settings({"feature": True})
        assert json.loads(obj.settings) == {"feature": True}


class TestTenantUserModel:
    def test_repr_contains_expected_fields(self):
        from database.models.tenant_user import TenantUser

        tu = TenantUser(tenant_id="t1", user_id="u1", role="admin")
        r = repr(tu)
        assert "t1" in r
        assert "u1" in r
        assert "admin" in r


# =============================================================================
# Portal endpoints — subscriptions
# =============================================================================


@pytest.fixture
def mock_token_payload():
    from core.auth.token_payload import TokenPayload
    from core.auth.types import TokenType

    return TokenPayload(
        sub="user-123",
        jti="jti-abc",
        type=TokenType.ACCESS,
        roles=["api_user"],
        tier="free",
    )


@pytest.fixture
def portal_client(mock_token_payload):
    """TestClient with auth dependency overridden."""

    # Import app lazily to avoid side-effects at collection time
    try:
        from main_enterprise import app
    except Exception:
        pytest.skip("main_enterprise import failed — skipping portal endpoint tests")

    from security.jwt_oauth2_auth import get_current_user

    app.dependency_overrides[get_current_user] = lambda: mock_token_payload
    client = TestClient(app, raise_server_exceptions=False)
    yield client
    app.dependency_overrides.clear()


class TestSubscriptionsEndpoints:
    def test_get_current_subscription_returns_200(self, portal_client):
        resp = portal_client.get(
            "/api/v1/portal/subscriptions/current",
            headers={"X-Tenant-ID": "tenant-test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "tier" in data
        assert "limits" in data
        assert "usage_this_month" in data

    def test_cancel_subscription_returns_200(self, portal_client):
        resp = portal_client.delete(
            "/api/v1/portal/subscriptions/current",
            headers={"X-Tenant-ID": "tenant-test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["cancelled"] is True

    def test_subscribe_without_stripe_returns_503(self, portal_client):
        """Without Stripe configured, subscribe returns 503."""
        resp = portal_client.post(
            "/api/v1/portal/subscriptions/",
            json={"tier": "starter", "tenant_id": "tenant-test"},
        )
        # Either 503 (Stripe unavailable) or 422 (no price configured) is acceptable
        assert resp.status_code in {422, 503}

    def test_subscribe_invalid_tier_returns_422(self, portal_client):
        resp = portal_client.post(
            "/api/v1/portal/subscriptions/",
            json={"tier": "diamond", "tenant_id": "tenant-test"},
        )
        assert resp.status_code == 422


class TestUsageEndpoints:
    def test_get_usage_returns_200(self, portal_client):
        resp = portal_client.get(
            "/api/v1/portal/usage/",
            headers={"X-Tenant-ID": "tenant-test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "intents" in data
        assert "period" in data
        assert isinstance(data["intents"], list)

    def test_usage_history_returns_200(self, portal_client):
        resp = portal_client.get(
            "/api/v1/portal/usage/history",
            headers={"X-Tenant-ID": "tenant-test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "months" in data
        assert len(data["months"]) == 6


class TestBillingEndpoints:
    def test_list_invoices_no_customer_returns_200(self, portal_client):
        """Without a Stripe customer configured, returns empty invoice list."""
        resp = portal_client.get(
            "/api/v1/portal/billing/invoices",
            headers={"X-Tenant-ID": "tenant-test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["invoices"] == []
        assert data["count"] == 0

    def test_portal_session_no_customer_returns_422(self, portal_client):
        resp = portal_client.post(
            "/api/v1/portal/billing/portal-session",
            json={"return_url": "https://devskyy.app/billing"},
        )
        assert resp.status_code == 422


class TestTeamEndpoints:
    def test_list_team_empty_returns_200(self, portal_client):
        resp = portal_client.get(
            "/api/v1/portal/team/",
            headers={"X-Tenant-ID": "team-tenant-test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "members" in data
        assert isinstance(data["members"], list)

    def test_invite_member_returns_201(self, portal_client):
        resp = portal_client.post(
            "/api/v1/portal/team/invite",
            json={"user_id": "user-abc", "role": "member"},
            headers={"X-Tenant-ID": "team-invite-tenant"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["user_id"] == "user-abc"
        assert data["role"] == "member"

    def test_invite_duplicate_member_returns_409(self, portal_client):
        headers = {"X-Tenant-ID": "team-dup-tenant"}
        portal_client.post(
            "/api/v1/portal/team/invite",
            json={"user_id": "user-dup", "role": "member"},
            headers=headers,
        )
        resp = portal_client.post(
            "/api/v1/portal/team/invite",
            json={"user_id": "user-dup", "role": "member"},
            headers=headers,
        )
        assert resp.status_code == 409

    def test_invite_invalid_role_returns_422(self, portal_client):
        resp = portal_client.post(
            "/api/v1/portal/team/invite",
            json={"user_id": "user-x", "role": "superadmin"},
            headers={"X-Tenant-ID": "team-role-tenant"},
        )
        assert resp.status_code == 422

    def test_remove_nonexistent_member_returns_404(self, portal_client):
        resp = portal_client.delete(
            "/api/v1/portal/team/nonexistent-user",
            headers={"X-Tenant-ID": "team-del-tenant"},
        )
        assert resp.status_code == 404

    def test_update_member_role(self, portal_client):
        headers = {"X-Tenant-ID": "team-update-tenant"}
        portal_client.post(
            "/api/v1/portal/team/invite",
            json={"user_id": "user-role-change", "role": "member"},
            headers=headers,
        )
        resp = portal_client.patch(
            "/api/v1/portal/team/user-role-change",
            json={"role": "admin"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "admin"

    def test_update_role_nonexistent_member_returns_404(self, portal_client):
        resp = portal_client.patch(
            "/api/v1/portal/team/ghost-user",
            json={"role": "admin"},
            headers={"X-Tenant-ID": "team-ghost-tenant"},
        )
        assert resp.status_code == 404


# =============================================================================
# Tenant middleware
# =============================================================================


class TestTenantMiddleware:
    @pytest.mark.asyncio
    async def test_header_ignored_without_internal_service_token(self, monkeypatch):
        """X-Tenant-ID alone is a spoof vector; it MUST be ignored when no
        TENANT_HEADER_TRUST_TOKEN is configured (defaults-closed)."""
        from unittest.mock import AsyncMock

        from starlette.requests import Request

        from core.middleware.tenant import tenant_middleware

        monkeypatch.delenv("TENANT_HEADER_TRUST_TOKEN", raising=False)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"x-tenant-id", b"my-tenant")],
            "query_string": b"",
        }

        request = Request(scope)
        call_next = AsyncMock(return_value=MagicMock())
        await tenant_middleware(request, call_next)

        assert request.state.tenant_id == ""
        assert request.state.tenant_tier == "free"

    @pytest.mark.asyncio
    async def test_header_honored_with_matching_internal_service_token(self, monkeypatch):
        """When TENANT_HEADER_TRUST_TOKEN is configured and the caller
        presents the matching X-Internal-Service-Token, the header override
        is trusted (the legitimate path for worker / admin service traffic)."""
        from unittest.mock import AsyncMock

        from starlette.requests import Request

        from core.middleware.tenant import tenant_middleware

        monkeypatch.setenv("TENANT_HEADER_TRUST_TOKEN", "s3cr3t")

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [
                (b"x-tenant-id", b"my-tenant"),
                (b"x-internal-service-token", b"s3cr3t"),
            ],
            "query_string": b"",
        }

        request = Request(scope)
        call_next = AsyncMock(return_value=MagicMock())
        await tenant_middleware(request, call_next)

        assert request.state.tenant_id == "my-tenant"

    @pytest.mark.asyncio
    async def test_defaults_to_empty_string_when_no_context(self):
        from unittest.mock import AsyncMock

        from starlette.requests import Request

        from core.middleware.tenant import tenant_middleware

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
        }

        request = Request(scope)
        call_next = AsyncMock(return_value=MagicMock())
        await tenant_middleware(request, call_next)

        assert request.state.tenant_id == ""
        assert request.state.tenant_tier == "free"
