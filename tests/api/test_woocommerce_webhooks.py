# tests/api/test_woocommerce_webhooks.py
"""Tests for WooCommerce webhook endpoints.

Implements US-003: WooCommerce auto-ingestion webhook.

Author: DevSkyy Platform Team
"""

import base64
import hashlib
import hmac
import json
import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.woocommerce_webhooks import (
    router,
    WooCommerceSignatureVerifier,
    WooCommerceProduct,
    WooCommerceImage,
    WooCommerceWebhookConfig,
)
from services.image_ingestion import IngestionResult, IngestionStatus


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def webhook_secret() -> str:
    """Test webhook secret."""
    return "test_webhook_secret_12345"


@pytest.fixture
def app() -> FastAPI:
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_product_payload() -> dict:
    """Sample WooCommerce product webhook payload."""
    return {
        "id": 123,
        "name": "SkyyRose Black Rose Hoodie",
        "slug": "skyyrose-black-rose-hoodie",
        "type": "simple",
        "status": "publish",
        "sku": "SR-BR-HOODIE-001",
        "description": "Luxury hoodie from the Black Rose collection",
        "short_description": "Premium quality hoodie",
        "images": [
            {
                "id": 1,
                "src": "https://example.com/images/product-front.jpg",
                "name": "Front View",
                "alt": "Black Rose Hoodie Front",
            },
            {
                "id": 2,
                "src": "https://example.com/images/product-back.jpg",
                "name": "Back View",
                "alt": "Black Rose Hoodie Back",
            },
        ],
        "categories": [{"id": 1, "name": "Hoodies"}],
        "tags": [{"id": 1, "name": "luxury"}],
        "attributes": [],
    }


def sign_payload(payload: bytes, secret: str) -> str:
    """Sign payload using WooCommerce format (HMAC-SHA256 + base64)."""
    return base64.b64encode(
        hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")


# =============================================================================
# Signature Verification Tests
# =============================================================================


class TestSignatureVerification:
    """Tests for WooCommerce signature verification."""

    def test_verify_valid_signature(self, webhook_secret: str) -> None:
        """Should verify valid HMAC-SHA256 signature."""
        verifier = WooCommerceSignatureVerifier(webhook_secret)
        payload = b'{"id": 123, "name": "Test Product"}'
        signature = sign_payload(payload, webhook_secret)

        assert verifier.verify(payload, signature) is True

    def test_reject_invalid_signature(self, webhook_secret: str) -> None:
        """Should reject invalid signature."""
        verifier = WooCommerceSignatureVerifier(webhook_secret)
        payload = b'{"id": 123, "name": "Test Product"}'

        assert verifier.verify(payload, "invalid_signature") is False

    def test_reject_tampered_payload(self, webhook_secret: str) -> None:
        """Should reject tampered payload."""
        verifier = WooCommerceSignatureVerifier(webhook_secret)
        original = b'{"id": 123, "name": "Test Product"}'
        tampered = b'{"id": 456, "name": "Test Product"}'
        signature = sign_payload(original, webhook_secret)

        assert verifier.verify(tampered, signature) is False

    def test_empty_secret_returns_false(self) -> None:
        """Should return False when secret is empty."""
        verifier = WooCommerceSignatureVerifier("")
        payload = b'{"id": 123}'
        signature = "any_signature"

        assert verifier.verify(payload, signature) is False


# =============================================================================
# Product Model Tests
# =============================================================================


class TestWooCommerceModels:
    """Tests for WooCommerce data models."""

    def test_parse_product(self, sample_product_payload: dict) -> None:
        """Should parse product payload correctly."""
        product = WooCommerceProduct(**sample_product_payload)

        assert product.id == 123
        assert product.name == "SkyyRose Black Rose Hoodie"
        assert product.sku == "SR-BR-HOODIE-001"
        assert len(product.images) == 2

    def test_parse_product_minimal(self) -> None:
        """Should parse product with minimal fields."""
        product = WooCommerceProduct(id=1, name="Test")

        assert product.id == 1
        assert product.name == "Test"
        assert product.images == []

    def test_parse_image(self) -> None:
        """Should parse image data correctly."""
        image = WooCommerceImage(
            id=1,
            src="https://example.com/image.jpg",
            name="Product Image",
            alt="Alt text",
        )

        assert image.id == 1
        assert image.src == "https://example.com/image.jpg"


# =============================================================================
# Webhook Endpoint Tests
# =============================================================================


class TestWebhookEndpoint:
    """Tests for webhook receive endpoint."""

    @patch("api.v1.woocommerce_webhooks.WooCommerceWebhookConfig.from_env")
    @patch("api.v1.woocommerce_webhooks.process_product_images")
    def test_receive_webhook_success(
        self,
        mock_process: MagicMock,
        mock_config: MagicMock,
        client: TestClient,
        sample_product_payload: dict,
        webhook_secret: str,
    ) -> None:
        """Should process valid webhook successfully."""
        # Setup mocks
        config = WooCommerceWebhookConfig()
        config.secret = webhook_secret
        mock_config.return_value = config

        mock_process.return_value = [
            IngestionResult(
                status=IngestionStatus.COMPLETED,
                job_id="job_123",
                asset_id="asset_123",
            ),
            IngestionResult(
                status=IngestionStatus.COMPLETED,
                job_id="job_456",
                asset_id="asset_456",
            ),
        ]

        # Prepare request
        payload = json.dumps(sample_product_payload).encode()
        signature = sign_payload(payload, webhook_secret)

        response = client.post(
            "/woocommerce/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-WC-Webhook-Signature": signature,
                "X-WC-Webhook-Topic": "product.created",
                "X-WC-Webhook-Source": "https://store.example.com",
                "X-WC-Webhook-Delivery-ID": "delivery_123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["images_queued"] == 2
        assert len(data["job_ids"]) == 2

    @patch("api.v1.woocommerce_webhooks.WooCommerceWebhookConfig.from_env")
    def test_reject_missing_signature(
        self,
        mock_config: MagicMock,
        client: TestClient,
        sample_product_payload: dict,
        webhook_secret: str,
    ) -> None:
        """Should reject webhook without signature."""
        config = WooCommerceWebhookConfig()
        config.secret = webhook_secret
        mock_config.return_value = config

        payload = json.dumps(sample_product_payload).encode()

        response = client.post(
            "/woocommerce/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-WC-Webhook-Topic": "product.created",
            },
        )

        assert response.status_code == 401
        assert "Missing webhook signature" in response.json()["detail"]

    @patch("api.v1.woocommerce_webhooks.WooCommerceWebhookConfig.from_env")
    def test_reject_invalid_signature(
        self,
        mock_config: MagicMock,
        client: TestClient,
        sample_product_payload: dict,
        webhook_secret: str,
    ) -> None:
        """Should reject webhook with invalid signature."""
        config = WooCommerceWebhookConfig()
        config.secret = webhook_secret
        mock_config.return_value = config

        payload = json.dumps(sample_product_payload).encode()

        response = client.post(
            "/woocommerce/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-WC-Webhook-Signature": "invalid_signature",
                "X-WC-Webhook-Topic": "product.created",
            },
        )

        assert response.status_code == 401
        assert "Invalid webhook signature" in response.json()["detail"]

    @patch("api.v1.woocommerce_webhooks.WooCommerceWebhookConfig.from_env")
    def test_ignore_unhandled_topic(
        self,
        mock_config: MagicMock,
        client: TestClient,
        webhook_secret: str,
    ) -> None:
        """Should acknowledge but not process unhandled topics."""
        config = WooCommerceWebhookConfig()
        config.secret = webhook_secret
        mock_config.return_value = config

        payload = b'{"id": 123}'
        signature = sign_payload(payload, webhook_secret)

        response = client.post(
            "/woocommerce/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-WC-Webhook-Signature": signature,
                "X-WC-Webhook-Topic": "order.created",
            },
        )

        assert response.status_code == 200
        assert "not handled" in response.json()["message"]

    @patch("api.v1.woocommerce_webhooks.WooCommerceWebhookConfig.from_env")
    def test_handle_product_without_images(
        self,
        mock_config: MagicMock,
        client: TestClient,
        webhook_secret: str,
    ) -> None:
        """Should handle products with no images."""
        config = WooCommerceWebhookConfig()
        config.secret = webhook_secret
        mock_config.return_value = config

        payload = json.dumps({"id": 123, "name": "No Images", "images": []}).encode()
        signature = sign_payload(payload, webhook_secret)

        response = client.post(
            "/woocommerce/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-WC-Webhook-Signature": signature,
                "X-WC-Webhook-Topic": "product.created",
            },
        )

        assert response.status_code == 200
        assert "no images" in response.json()["message"].lower()

    @patch("api.v1.woocommerce_webhooks.WooCommerceWebhookConfig.from_env")
    def test_handle_invalid_json(
        self,
        mock_config: MagicMock,
        client: TestClient,
        webhook_secret: str,
    ) -> None:
        """Should reject invalid JSON payload."""
        config = WooCommerceWebhookConfig()
        config.secret = webhook_secret
        mock_config.return_value = config

        payload = b"not valid json"
        signature = sign_payload(payload, webhook_secret)

        response = client.post(
            "/woocommerce/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-WC-Webhook-Signature": signature,
                "X-WC-Webhook-Topic": "product.created",
            },
        )

        assert response.status_code == 400
        assert "Invalid webhook payload" in response.json()["detail"]


class TestWebhookStatus:
    """Tests for webhook status endpoint."""

    @patch("api.v1.woocommerce_webhooks.WooCommerceWebhookConfig.from_env")
    def test_get_status(
        self,
        mock_config: MagicMock,
        client: TestClient,
        webhook_secret: str,
    ) -> None:
        """Should return webhook integration status."""
        config = WooCommerceWebhookConfig()
        config.secret = webhook_secret
        mock_config.return_value = config

        response = client.get("/woocommerce/status")

        assert response.status_code == 200
        data = response.json()
        assert data["secret_configured"] is True
        assert "product.created" in data["supported_topics"]
        assert data["deduplication_enabled"] is True


class TestWebhookTest:
    """Tests for webhook test endpoint."""

    @patch("api.v1.woocommerce_webhooks.WooCommerceWebhookConfig.from_env")
    def test_test_endpoint_valid_signature(
        self,
        mock_config: MagicMock,
        client: TestClient,
        webhook_secret: str,
    ) -> None:
        """Should verify signature in test endpoint."""
        config = WooCommerceWebhookConfig()
        config.secret = webhook_secret
        mock_config.return_value = config

        payload = b'{"test": true}'
        signature = sign_payload(payload, webhook_secret)

        response = client.post(
            "/woocommerce/webhook/test",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-WC-Webhook-Signature": signature,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["signature_valid"] is True
        assert data["secret_configured"] is True
