"""Tests for POST /hf-spaces/{space_id}/refresh (api/v1/hf_spaces.py).

The endpoint previously returned a fake success without touching HuggingFace.
These tests lock the real wiring to HfApi.restart_space: the repo_id derived from
the Space URL, 404 for unknown space, 500 when HF_TOKEN is unset, and 502 when the
HuggingFace API call fails. HfApi is stubbed so no real Space is restarted.
"""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1 import hf_spaces as hf_module
from api.v1.hf_spaces import hf_spaces_router

# A real Space id from DEVSKYY_SPACES (url: .../spaces/damBruh/skyyrose-3d-converter).
SPACE_ID = "skyyrose-3d-converter"
EXPECTED_REPO_ID = "damBruh/skyyrose-3d-converter"


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(hf_spaces_router)
    return TestClient(app)


def test_refresh_success_calls_restart_space(monkeypatch):
    captured = {}

    class _StubHfApi:
        def restart_space(self, repo_id, token=None, factory_reboot=False):
            captured["repo_id"] = repo_id
            captured["token"] = token
            return SimpleNamespace(stage="BUILDING")

    monkeypatch.setattr(hf_module, "HF_TOKEN", "fake-token")
    monkeypatch.setattr(hf_module, "HfApi", _StubHfApi)

    resp = _client().post(f"/hf-spaces/{SPACE_ID}/refresh")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["space_id"] == SPACE_ID
    assert body["repo_id"] == EXPECTED_REPO_ID
    assert body["stage"] == "BUILDING"
    # repo_id derived from the Space URL is what HF was actually asked to restart.
    assert captured["repo_id"] == EXPECTED_REPO_ID
    assert captured["token"] == "fake-token"


def test_refresh_unknown_space_returns_404(monkeypatch):
    monkeypatch.setattr(hf_module, "HF_TOKEN", "fake-token")
    resp = _client().post("/hf-spaces/not-a-real-space/refresh")
    assert resp.status_code == 404, resp.text


def test_refresh_without_token_returns_500(monkeypatch):
    monkeypatch.setattr(hf_module, "HF_TOKEN", None)
    resp = _client().post(f"/hf-spaces/{SPACE_ID}/refresh")
    assert resp.status_code == 500, resp.text


def test_refresh_hf_failure_returns_502(monkeypatch):
    class _FailingHfApi:
        def restart_space(self, repo_id, token=None, factory_reboot=False):
            raise RuntimeError("hub 500")

    monkeypatch.setattr(hf_module, "HF_TOKEN", "fake-token")
    monkeypatch.setattr(hf_module, "HfApi", _FailingHfApi)

    resp = _client().post(f"/hf-spaces/{SPACE_ID}/refresh")
    assert resp.status_code == 502, resp.text
