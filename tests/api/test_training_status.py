"""Tests for the Training Status API (api/v1/training_status.py).

Every endpoint previously returned HTTP 500: the async file helpers
(_find_training_versions / _load_progress_file / _load_status_file /
_load_round_table_results) were called without ``await``. A coroutine object is
truthy, so the ``if not ...`` guards passed and the subsequent iteration /
attribute access raised ``TypeError`` -> caught -> HTTP 500. These tests lock
the awaited behavior (real values round-trip through the response model) and the
export endpoint's real HuggingFace wiring with an honest no-token fallback.
``HfApi`` is stubbed so no real dataset is ever created or uploaded.
"""

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1 import training_status as tmod
from api.v1.training_status import training_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(training_router)
    return TestClient(app)


def _write_progress(base: Path, name: str, **fields: object) -> None:
    vdir = base / name
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "progress.json").write_text(json.dumps(fields))


# ---------------------------------------------------------------------------
# status / jobs / job-by-id  — these prove the missing-await fix (were all 500)
# ---------------------------------------------------------------------------


def test_status_idle_when_no_runs(monkeypatch, tmp_path):
    monkeypatch.setattr(tmod, "TRAINING_OUTPUT_DIR", tmp_path)
    resp = _client().get("/training/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "idle"
    assert body["message"] == "No training jobs found"


def test_status_returns_active_training_values(monkeypatch, tmp_path):
    monkeypatch.setattr(tmod, "TRAINING_OUTPUT_DIR", tmp_path)
    _write_progress(
        tmp_path,
        "v3",
        status="training",
        version="v3",
        current_epoch=2,
        total_epochs=5,
        progress_percentage=40.0,
        loss=0.1234,
    )
    body = _client().get("/training/status").json()
    # Round-tripped values prove the helper was awaited, not left a coroutine.
    assert body["status"] == "training"
    assert body["version"] == "v3"
    assert body["current_epoch"] == 2
    assert body["progress_percentage"] == 40.0
    assert body["loss"] == pytest.approx(0.1234)


def test_status_prefers_active_over_latest(monkeypatch, tmp_path):
    monkeypatch.setattr(tmod, "TRAINING_OUTPUT_DIR", tmp_path)
    _write_progress(tmp_path, "v1", status="training", version="v1", progress_percentage=10.0)
    _write_progress(tmp_path, "v2", status="completed", version="v2", progress_percentage=100.0)
    body = _client().get("/training/status").json()
    assert body["version"] == "v1"  # active beats the sorted-first completed v2


def test_list_jobs_counts_by_status(monkeypatch, tmp_path):
    monkeypatch.setattr(tmod, "TRAINING_OUTPUT_DIR", tmp_path)
    _write_progress(tmp_path, "a", status="training")
    _write_progress(tmp_path, "b", status="completed")
    _write_progress(tmp_path, "c", status="failed")
    body = _client().get("/training/jobs").json()
    assert body["total_jobs"] == 3
    assert body["running"] == 1
    assert body["completed"] == 1
    assert body["failed"] == 1
    assert len(body["jobs"]) == 3


def test_get_job_by_id(monkeypatch, tmp_path):
    monkeypatch.setattr(tmod, "TRAINING_OUTPUT_DIR", tmp_path)
    _write_progress(
        tmp_path, "run-7", status="completed", version="run-7", progress_percentage=100.0
    )
    resp = _client().get("/training/jobs/run-7")
    assert resp.status_code == 200
    assert resp.json()["version"] == "run-7"


def test_get_job_missing_is_404(monkeypatch, tmp_path):
    monkeypatch.setattr(tmod, "TRAINING_OUTPUT_DIR", tmp_path)
    assert _client().get("/training/jobs/does-not-exist").status_code == 404


def test_get_job_invalid_id_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(tmod, "TRAINING_OUTPUT_DIR", tmp_path)
    # '$' fails the route-level pattern (422); a char that slipped past it would
    # still be caught by _validate_job_id (400).
    assert _client().get("/training/jobs/bad$id").status_code in (400, 422)


def test_health_ok(monkeypatch, tmp_path):
    monkeypatch.setattr(tmod, "TRAINING_OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(tmod, "ROUND_TABLE_RESULTS_PATH", tmp_path / "rt.json")
    body = _client().get("/training/health").json()
    assert body["status"] == "healthy"
    assert body["checks"]["training_versions_found"] == 0


# ---------------------------------------------------------------------------
# export  — Round Table -> HuggingFace dataset, honest fallback when no token
# ---------------------------------------------------------------------------


def _seed_round_table(tmp_path: Path, monkeypatch) -> None:
    rt = tmp_path / "rt.json"
    rt.write_text(
        json.dumps(
            {
                "generated_at": "2026-06-25T00:00:00",
                "collections": {
                    "signature": {
                        "winner": {
                            "provider": "p",
                            "total_score": 9.0,
                            "verdict": "SHIP",
                            "scene_spec": {"x": 1},
                            "summary": "s",
                        }
                    },
                },
            }
        )
    )
    monkeypatch.setattr(tmod, "ROUND_TABLE_RESULTS_PATH", rt)
    monkeypatch.setattr(tmod, "EXPORT_DIR", tmp_path / "exports")


def test_export_dry_run_uploads_nothing(monkeypatch, tmp_path):
    _seed_round_table(tmp_path, monkeypatch)
    body = _client().post("/training/export", json={"dataset_name": "ds", "dry_run": True}).json()
    assert body["dry_run"] is True
    assert body["exported_count"] == 1
    assert body["dataset_url"] is None


def test_export_local_only_when_no_token(monkeypatch, tmp_path):
    _seed_round_table(tmp_path, monkeypatch)
    monkeypatch.setattr(tmod, "HF_TOKEN", None)
    resp = _client().post("/training/export", json={"dataset_name": "ds"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert body["dataset_url"] is None  # honest: never fabricate a remote URL
    assert "skipped" in body["message"].lower()
    assert (tmp_path / "exports" / "ds.json").exists()


def test_export_uploads_when_token_present(monkeypatch, tmp_path):
    _seed_round_table(tmp_path, monkeypatch)
    monkeypatch.setattr(tmod, "HF_TOKEN", "fake-token")
    monkeypatch.setattr(tmod, "HF_USERNAME", "tester")
    calls: dict[str, object] = {}

    class _StubHfApi:
        def create_repo(self, repo_id, repo_type=None, exist_ok=False, token=None):
            calls["create"] = (repo_id, repo_type, exist_ok, token)
            return f"https://huggingface.co/datasets/{repo_id}"

        def upload_file(
            self,
            *,
            path_or_fileobj,
            path_in_repo,
            repo_id,
            repo_type=None,
            token=None,
            commit_message=None,
        ):
            calls["upload"] = (path_in_repo, repo_id, repo_type, token)
            return object()

    monkeypatch.setattr(tmod, "HfApi", _StubHfApi)
    body = _client().post("/training/export", json={"dataset_name": "ds"}).json()
    assert body["dataset_url"] == "https://huggingface.co/datasets/tester/ds"
    assert calls["create"][0] == "tester/ds"
    assert calls["create"][1] == "dataset"
    assert calls["create"][2] is True
    assert calls["upload"][1] == "tester/ds"
    assert calls["upload"][3] == "fake-token"


def test_export_upload_failure_is_502(monkeypatch, tmp_path):
    _seed_round_table(tmp_path, monkeypatch)
    monkeypatch.setattr(tmod, "HF_TOKEN", "fake-token")

    class _BoomHfApi:
        def create_repo(self, *a, **k):
            raise RuntimeError("hub down")

    monkeypatch.setattr(tmod, "HfApi", _BoomHfApi)
    resp = _client().post("/training/export", json={"dataset_name": "ds"})
    assert resp.status_code == 502
    # Raw exception strings must NOT be echoed to clients (security + info-leak).
    detail = resp.json()["detail"]
    assert "hub down" not in detail
    assert "HuggingFace upload failed" in detail


def test_export_404_when_no_round_table(monkeypatch, tmp_path):
    monkeypatch.setattr(tmod, "ROUND_TABLE_RESULTS_PATH", tmp_path / "missing.json")
    assert _client().post("/training/export", json={"dataset_name": "ds"}).status_code == 404


# ---------------------------------------------------------------------------
# best_loss field validator — non-finite float coercion (regression guard)
# A progress.json with inf/nan used to crash JSON serialisation with a 500;
# the field_validator must silently coerce those values to None.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw_value",
    [
        float("inf"),
        float("-inf"),
        float("nan"),
        "inf",
        "-inf",
        "nan",
        "Infinity",
        "-Infinity",
        "NaN",
    ],
)
def test_best_loss_non_finite_coerced_to_none(monkeypatch, tmp_path, raw_value):
    """Non-finite best_loss values must be serialised as JSON null (not crash)."""
    monkeypatch.setattr(tmod, "TRAINING_OUTPUT_DIR", tmp_path)
    _write_progress(tmp_path, "v1", status="training", version="v1", best_loss=raw_value)
    resp = _client().get("/training/status")
    assert resp.status_code == 200, resp.text
    assert resp.json()["best_loss"] is None


def test_best_loss_finite_value_preserved(monkeypatch, tmp_path):
    monkeypatch.setattr(tmod, "TRAINING_OUTPUT_DIR", tmp_path)
    _write_progress(tmp_path, "v1", status="training", version="v1", best_loss=0.3456)
    assert _client().get("/training/status").json()["best_loss"] == pytest.approx(0.3456)


def test_best_loss_null_preserved(monkeypatch, tmp_path):
    monkeypatch.setattr(tmod, "TRAINING_OUTPUT_DIR", tmp_path)
    _write_progress(tmp_path, "v1", status="training", version="v1", best_loss=None)
    assert _client().get("/training/status").json()["best_loss"] is None
