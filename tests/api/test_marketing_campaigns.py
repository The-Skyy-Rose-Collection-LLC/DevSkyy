"""Tests for the marketing campaigns endpoint (``api/v1/marketing.py``).

Verifies the endpoint is wired to :class:`MarketingAgent` and returns the real
generated campaign content. The prior implementation returned hardcoded mock
metrics (``estimated_revenue=5625.0`` etc.); these tests lock in the real wiring
and that no fabricated metrics remain in the response.
"""

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from adk.base import ADKProvider, AgentResult, AgentStatus
from api.v1 import marketing as marketing_module
from api.v1.marketing import router


@pytest.fixture
def mock_user():
    """An authenticated user payload for the dependency override."""
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub="user_123",
        jti="jti_123",
        type=TokenType.ACCESS,
        roles=["user"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


def _make_client(mock_user, agent_cls, monkeypatch) -> TestClient:
    from security.jwt_oauth2_auth import get_current_user

    # Replace the real agent so the endpoint never constructs the heavy agent
    # or makes a live LLM call during the test.
    monkeypatch.setattr(marketing_module, "MarketingAgent", agent_cls)

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    return TestClient(app)


def test_create_campaign_returns_real_agent_content(mock_user, monkeypatch):
    captured: dict = {}

    class _StubAgent:
        name = "marketing_agent"

        async def create_campaign(self, brief, channels):
            captured["brief"] = brief
            captured["channels"] = channels
            return AgentResult(
                agent_name="marketing_agent",
                agent_provider=ADKProvider.PYDANTIC,
                content="CONCEPT: bold drop. CALENDAR: 2 weeks. HASHTAGS: #SkyyRose",
                status=AgentStatus.COMPLETED,
                metadata={"task_type": "campaign"},
            )

    client = _make_client(mock_user, _StubAgent, monkeypatch)
    resp = client.post(
        "/marketing/campaigns",
        json={
            "campaign_type": "social",
            "target_audience": {"segment": "high_value"},
            "budget": 5000,
        },
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["campaign_content"] == "CONCEPT: bold drop. CALENDAR: 2 weeks. HASHTAGS: #SkyyRose"
    assert body["campaign_type"] == "social"
    assert body["channels"] == ["instagram", "facebook", "tiktok"]
    assert body["metadata"] == {"task_type": "campaign"}
    # Fabricated metrics are gone from the response contract.
    assert "metrics" not in body
    # The brief handed to the agent reflects the request inputs.
    assert "social" in captured["brief"]
    assert "5000.00" in captured["brief"]
    assert captured["channels"] == ["instagram", "facebook", "tiktok"]


def test_create_campaign_agent_failure_returns_502(mock_user, monkeypatch):
    class _FailingAgent:
        name = "marketing_agent"

        async def create_campaign(self, brief, channels):
            return AgentResult(
                agent_name="marketing_agent",
                agent_provider=ADKProvider.PYDANTIC,
                content="",
                status=AgentStatus.FAILED,
                error="llm unavailable",
            )

    client = _make_client(mock_user, _FailingAgent, monkeypatch)
    resp = client.post(
        "/marketing/campaigns",
        json={"campaign_type": "email", "target_audience": {"segment": "all"}},
    )
    assert resp.status_code == 502, resp.text
