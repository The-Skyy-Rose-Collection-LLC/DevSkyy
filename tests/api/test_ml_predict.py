"""Tests for POST /ml/predict (api/v1/ml.py) wired to MLCapabilitiesModule.

The endpoint previously returned hardcoded mock predictions. These tests lock the
real wiring: MLModelType -> (SuperAgentType, model_name) routing, the single->list
reshape, honest status="failed" for degraded/unfitted models, and 503 for an
unavailable model or a failed module init. The ML module is stubbed so no model
loads and no HuggingFace download happens.
"""

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.base_super_agent.types import MLPrediction as AgentMLPrediction
from agents.base_super_agent.types import SuperAgentType
from api.v1 import ml as ml_module
from api.v1.ml import router


@pytest.fixture
def mock_user():
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub="u1",
        jti="j1",
        type=TokenType.ACCESS,
        roles=["user"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


def _client(mock_user, module_cls, monkeypatch) -> TestClient:
    from security.jwt_oauth2_auth import get_current_user

    monkeypatch.setattr(ml_module, "MLCapabilitiesModule", module_cls)
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    return TestClient(app)


def _ok_module(captured=None, available=None):
    avail = (
        available
        if available is not None
        else [
            "trend_predictor",
            "sentiment_analyzer",
            "price_optimizer",
            "demand_forecaster",
            "clusterer",
        ]
    )

    class _Mod:
        def __init__(self, agent_type):
            if captured is not None:
                captured["agent_type"] = agent_type

        async def initialize(self):
            return None

        def list_available_models(self):
            return avail

        async def predict(self, model_name, input_data, **kwargs):
            if captured is not None:
                captured["model_name"] = model_name
            return AgentMLPrediction(
                task=model_name,
                prediction={"score": 0.9},
                confidence=0.85,
                model_used=model_name,
                latency_ms=12.3,
                metadata={},
            )

    return _Mod


def test_sync_predict_success_and_routing(mock_user, monkeypatch):
    captured = {}
    client = _client(mock_user, _ok_module(captured), monkeypatch)
    resp = client.post("/ml/predict", json={"model_type": "trend_prediction", "data": {"x": 1}})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert body["model_version"] == "agent-ml-1"
    assert len(body["predictions"]) == 1
    assert body["predictions"][0]["label"] == "trend_predictor"
    assert body["predictions"][0]["value"] == {"score": 0.9}
    assert body["predictions"][0]["confidence"] == 0.85
    # routing: trend_prediction -> (MARKETING, trend_predictor)
    assert captured["agent_type"] == SuperAgentType.MARKETING
    assert captured["model_name"] == "trend_predictor"


def test_sync_predict_degraded_returns_failed(mock_user, monkeypatch):
    class _Mod:
        def __init__(self, agent_type):
            pass

        async def initialize(self):
            return None

        def list_available_models(self):
            return ["price_optimizer"]

        async def predict(self, model_name, input_data, **kwargs):
            return AgentMLPrediction(
                task=model_name,
                prediction=None,
                confidence=0.0,
                model_used=model_name,
                latency_ms=1.0,
                metadata={"error": "model not fitted"},
            )

    client = _client(mock_user, _Mod, monkeypatch)
    resp = client.post("/ml/predict", json={"model_type": "dynamic_pricing", "data": {}})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "failed"
    assert body["predictions"] == []
    assert "error" in body["metrics"]


def test_model_unavailable_returns_503(mock_user, monkeypatch):
    client = _client(mock_user, _ok_module(available=[]), monkeypatch)
    resp = client.post("/ml/predict", json={"model_type": "sentiment_analysis", "data": {}})
    assert resp.status_code == 503, resp.text


def test_init_failure_returns_503(mock_user, monkeypatch):
    class _Mod:
        def __init__(self, agent_type):
            pass

        async def initialize(self):
            raise RuntimeError("no sklearn")

        def list_available_models(self):
            return []

        async def predict(self, *args, **kwargs):
            raise AssertionError("predict should not be reached after init failure")

    client = _client(mock_user, _Mod, monkeypatch)
    resp = client.post("/ml/predict", json={"model_type": "sentiment_analysis", "data": {}})
    assert resp.status_code == 503, resp.text


def test_invalid_model_type_returns_422(mock_user, monkeypatch):
    client = _client(mock_user, _ok_module(), monkeypatch)
    resp = client.post("/ml/predict", json={"model_type": "not_a_real_type", "data": {}})
    assert resp.status_code == 422, resp.text
