"""Tests for skyyrose.elite_studio.telemetry (Phase 1 compositor instrumentation)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from skyyrose.elite_studio import telemetry


@pytest.fixture(autouse=True)
def _isolated_log_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("COMPOSITOR_TELEMETRY_DIR", str(tmp_path))
    return tmp_path


def _read_events(log_dir: Path) -> list[dict]:
    files = sorted(log_dir.glob("compositor-telemetry-*.jsonl"))
    events: list[dict] = []
    for f in files:
        for line in f.read_text().splitlines():
            if line.strip():
                events.append(json.loads(line))
    return events


def test_new_run_id_is_stable_format() -> None:
    rid = telemetry.new_run_id()
    assert isinstance(rid, str)
    assert len(rid) == 12
    assert rid.isalnum()


def test_hash_inputs_is_deterministic_and_skips_none() -> None:
    a = telemetry.hash_inputs("scene", "subject", "prompt")
    b = telemetry.hash_inputs("scene", "subject", "prompt")
    c = telemetry.hash_inputs("scene", None, "subject", "prompt")
    d = telemetry.hash_inputs("scene", "different", "prompt")
    assert a == b == c
    assert a != d
    assert len(a) == 16


def test_stage_success_emits_ok_event(_isolated_log_dir: Path) -> None:
    run_id = telemetry.new_run_id()
    with telemetry.stage(
        run_id=run_id,
        stage_name="alpha",
        sku="br-001",
        scene_name="bay-bridge",
        collection="black-rose",
    ) as st:
        st.set(provider="bria-rmbg-2.0", bytes_out=123456)

    events = _read_events(_isolated_log_dir)
    assert len(events) == 1
    ev = events[0]
    assert ev["status"] == "ok"
    assert ev["error_type"] is None
    assert ev["stage"] == "alpha"
    assert ev["sku"] == "br-001"
    assert ev["scene_name"] == "bay-bridge"
    assert ev["collection"] == "black-rose"
    assert ev["run_id"] == run_id
    assert ev["provider"] == "bria-rmbg-2.0"
    assert ev["bytes_out"] == 123456
    assert ev["duration_ms"] >= 0
    # ISO8601 parseable
    datetime.fromisoformat(ev["started_at"])


def test_stage_error_emits_error_event_and_reraises(_isolated_log_dir: Path) -> None:
    run_id = telemetry.new_run_id()
    with pytest.raises(RuntimeError, match="simulated"):
        with telemetry.stage(run_id=run_id, stage_name="flux", sku="sg-001") as st:
            st.set(provider="fal")
            raise RuntimeError("simulated")

    events = _read_events(_isolated_log_dir)
    assert len(events) == 1
    ev = events[0]
    assert ev["status"] == "error"
    assert ev["error_type"] == "RuntimeError"
    assert ev["provider"] == "fal"


def test_stage_meta_freeform_fields_land_under_meta(_isolated_log_dir: Path) -> None:
    with telemetry.stage(run_id="r", stage_name="qa", sku="x") as st:
        st.set(model="gemini-3-pro-image-preview", verdict="pass", iterations=2)

    ev = _read_events(_isolated_log_dir)[0]
    assert ev["model"] == "gemini-3-pro-image-preview"
    assert ev["meta"] == {"verdict": "pass", "iterations": 2}


def test_emit_never_raises_on_bad_input(monkeypatch: pytest.MonkeyPatch) -> None:
    # Unserializable object should be tolerated via default=str, but even if
    # something pathological slipped through, emit must never raise.
    class Bad:
        def __repr__(self) -> str:
            raise ValueError("cannot stringify")

    telemetry.emit({"payload": Bad()})  # must not raise


def test_log_file_is_dated_utc(_isolated_log_dir: Path) -> None:
    with telemetry.stage(run_id="r", stage_name="alpha", sku="x"):
        pass
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    expected = _isolated_log_dir / f"compositor-telemetry-{today}.jsonl"
    assert expected.exists()


def test_multiple_stages_share_run_id(_isolated_log_dir: Path) -> None:
    run_id = telemetry.new_run_id()
    for stage_name in ("alpha", "prompt", "relight", "flux", "shadows", "qa"):
        with telemetry.stage(run_id=run_id, stage_name=stage_name, sku="br-001"):
            pass

    events = _read_events(_isolated_log_dir)
    assert len(events) == 6
    assert {e["run_id"] for e in events} == {run_id}
    assert [e["stage"] for e in events] == list(telemetry.STAGE_NAMES)
