"""Offline unit tests for cli-anything-comfyui core and utils.

All tests run without a live ComfyUI server.  Network calls are
patched via unittest.mock.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Secrets
# ---------------------------------------------------------------------------


class TestComfyUISecrets:
    def test_default_host(self) -> None:
        from cli_anything.comfyui.core.secrets import resolve_secrets

        s = resolve_secrets()
        assert s.host == "http://127.0.0.1:8188"

    def test_host_override(self) -> None:
        from cli_anything.comfyui.core.secrets import resolve_secrets

        s = resolve_secrets(host_override="http://localhost:9000")
        assert s.base_url == "http://localhost:9000"

    def test_host_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli_anything.comfyui.core.secrets import resolve_secrets

        monkeypatch.setenv("COMFYUI_HOST", "http://remote:8188")
        s = resolve_secrets()
        assert "remote" in s.host

    def test_token_override(self) -> None:
        from cli_anything.comfyui.core.secrets import resolve_secrets

        s = resolve_secrets(token_override="tok123")
        assert s.token == "tok123"

    def test_token_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli_anything.comfyui.core.secrets import resolve_secrets

        monkeypatch.setenv("COMFYUI_AUTH_TOKEN", "envtok")
        s = resolve_secrets()
        assert s.token == "envtok"

    def test_no_token_gives_empty_headers(self) -> None:
        from cli_anything.comfyui.core.secrets import resolve_secrets

        s = resolve_secrets()
        assert s.auth_headers() == {}

    def test_token_gives_bearer_header(self) -> None:
        from cli_anything.comfyui.core.secrets import resolve_secrets

        s = resolve_secrets(token_override="mytoken")
        assert s.auth_headers() == {"Authorization": "Bearer mytoken"}

    def test_trailing_slash_stripped(self) -> None:
        from cli_anything.comfyui.core.secrets import resolve_secrets

        s = resolve_secrets(host_override="http://localhost:8188/")
        assert not s.base_url.endswith("/")

    def test_host_override_wins_over_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli_anything.comfyui.core.secrets import resolve_secrets

        monkeypatch.setenv("COMFYUI_HOST", "http://env-host:8188")
        s = resolve_secrets(host_override="http://override:9999")
        assert "override" in s.host

    def test_frozen_dataclass(self) -> None:
        from cli_anything.comfyui.core.secrets import ComfyUISecrets

        s = ComfyUISecrets(host="http://a", token=None)
        with pytest.raises((AttributeError, TypeError)):
            s.host = "http://b"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


class TestNodeInfo:
    def test_from_dict_ok(self) -> None:
        from cli_anything.comfyui.core.workflow import NodeInfo

        n = NodeInfo.from_dict("1", {"class_type": "KSampler", "inputs": {"seed": 42}})
        assert n.class_type == "KSampler"
        assert n.inputs["seed"] == 42

    def test_from_dict_missing_class_type_raises(self) -> None:
        from cli_anything.comfyui.core.workflow import NodeInfo

        with pytest.raises(ValueError, match="class_type"):
            NodeInfo.from_dict("1", {"inputs": {}})

    def test_to_dict_roundtrip(self) -> None:
        from cli_anything.comfyui.core.workflow import NodeInfo

        n = NodeInfo.from_dict("1", {"class_type": "KSampler", "inputs": {"steps": 20}})
        d = n.to_dict()
        assert d["class_type"] == "KSampler"

    def test_upstream_ids_extracts_list_refs(self) -> None:
        from cli_anything.comfyui.core.workflow import NodeInfo

        n = NodeInfo(
            node_id="2", class_type="VAEDecode", inputs={"samples": ["1", 0], "vae": ["3", 0]}
        )
        assert set(n.upstream_ids()) == {"1", "3"}

    def test_upstream_ids_ignores_scalars(self) -> None:
        from cli_anything.comfyui.core.workflow import NodeInfo

        n = NodeInfo(node_id="2", class_type="KSampler", inputs={"steps": 20, "cfg": 7.0})
        assert n.upstream_ids() == []


class TestWorkflow:
    def _simple(self) -> dict:
        return {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "v1.safetensors"},
            },
            "2": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "steps": 20}},
        }

    def test_from_dict_ok(self) -> None:
        from cli_anything.comfyui.core.workflow import Workflow

        wf = Workflow.from_dict(self._simple())
        assert len(wf.nodes) == 2

    def test_from_json_string_ok(self) -> None:
        from cli_anything.comfyui.core.workflow import Workflow

        wf = Workflow.from_json_string(json.dumps(self._simple()))
        assert "1" in wf.nodes

    def test_from_json_string_bad_json_raises(self) -> None:
        from cli_anything.comfyui.core.workflow import Workflow

        with pytest.raises(ValueError, match="Invalid JSON"):
            Workflow.from_json_string("{bad}")

    def test_from_json_string_non_dict_raises(self) -> None:
        from cli_anything.comfyui.core.workflow import Workflow

        with pytest.raises(ValueError, match="JSON object"):
            Workflow.from_json_string("[1, 2]")

    def test_validate_ok(self) -> None:
        from cli_anything.comfyui.core.workflow import Workflow

        wf = Workflow.from_dict(self._simple())
        assert wf.validate() == []

    def test_validate_missing_ref(self) -> None:
        from cli_anything.comfyui.core.workflow import Workflow

        data = {"2": {"class_type": "KSampler", "inputs": {"model": ["99", 0]}}}
        wf = Workflow.from_dict(data)
        errors = wf.validate()
        assert any("99" in e for e in errors)

    def test_class_types(self) -> None:
        from cli_anything.comfyui.core.workflow import Workflow

        wf = Workflow.from_dict(self._simple())
        ct = wf.class_types()
        assert "KSampler" in ct

    def test_find_by_class(self) -> None:
        from cli_anything.comfyui.core.workflow import Workflow

        wf = Workflow.from_dict(self._simple())
        results = wf.find_by_class("KSampler")
        assert len(results) == 1

    def test_to_dict_roundtrip(self) -> None:
        from cli_anything.comfyui.core.workflow import Workflow

        wf = Workflow.from_dict(self._simple())
        d = wf.to_dict()
        wf2 = Workflow.from_dict(d)
        assert wf2.node_ids() == wf.node_ids()

    def test_summary_keys(self) -> None:
        from cli_anything.comfyui.core.workflow import Workflow

        wf = Workflow.from_dict(self._simple())
        s = wf.summary()
        assert "node_count" in s
        assert "class_types" in s

    def test_load_workflow_file(self, tmp_path: Path) -> None:
        from cli_anything.comfyui.core.workflow import load_workflow

        p = tmp_path / "wf.json"
        p.write_text(json.dumps(self._simple()))
        wf = load_workflow(p)
        assert len(wf.nodes) == 2

    def test_load_workflow_missing_raises(self, tmp_path: Path) -> None:
        from cli_anything.comfyui.core.workflow import load_workflow

        with pytest.raises(FileNotFoundError):
            load_workflow(tmp_path / "ghost.json")

    def test_dump_workflow(self, tmp_path: Path) -> None:
        from cli_anything.comfyui.core.workflow import Workflow, dump_workflow, load_workflow

        wf = Workflow.from_dict(self._simple())
        out = tmp_path / "out.json"
        dump_workflow(wf, out)
        wf2 = load_workflow(out)
        assert set(wf2.node_ids()) == set(wf.node_ids())


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------


class TestQueueItem:
    def test_from_running_tuple(self) -> None:
        from cli_anything.comfyui.core.queue import QueueItem, QueueStatus

        item = QueueItem.from_running_tuple([0, "abc-123", {}, {}, {}])
        assert item.prompt_id == "abc-123"
        assert item.status == QueueStatus.RUNNING

    def test_from_pending_tuple(self) -> None:
        from cli_anything.comfyui.core.queue import QueueItem, QueueStatus

        item = QueueItem.from_pending_tuple([1, "def-456", {}, {}])
        assert item.number == 1
        assert item.status == QueueStatus.PENDING

    def test_to_dict_has_fields(self) -> None:
        from cli_anything.comfyui.core.queue import QueueItem, QueueStatus

        item = QueueItem(prompt_id="x", number=0, status=QueueStatus.RUNNING)
        d = item.to_dict()
        assert d["prompt_id"] == "x"

    def test_from_running_too_short_raises(self) -> None:
        from cli_anything.comfyui.core.queue import QueueItem

        with pytest.raises(ValueError):
            QueueItem.from_running_tuple([0])

    def test_from_pending_too_short_raises(self) -> None:
        from cli_anything.comfyui.core.queue import QueueItem

        with pytest.raises(ValueError):
            QueueItem.from_pending_tuple([0])


class TestBuildPromptPayload:
    def test_returns_prompt_key(self) -> None:
        from cli_anything.comfyui.core.queue import build_prompt_payload

        p = build_prompt_payload({"1": {}})
        assert "prompt" in p
        assert "client_id" in p

    def test_custom_client_id(self) -> None:
        from cli_anything.comfyui.core.queue import build_prompt_payload

        p = build_prompt_payload({}, client_id="my-id")
        assert p["client_id"] == "my-id"

    def test_generates_uuid_when_no_client_id(self) -> None:
        from cli_anything.comfyui.core.queue import build_prompt_payload

        p = build_prompt_payload({})
        assert len(p["client_id"]) == 36  # UUID4 string

    def test_extra_data_included(self) -> None:
        from cli_anything.comfyui.core.queue import build_prompt_payload

        p = build_prompt_payload({}, extra_data={"foo": "bar"})
        assert p["extra_data"]["foo"] == "bar"


class TestParseQueueResponse:
    def test_parses_running_and_pending(self) -> None:
        from cli_anything.comfyui.core.queue import parse_queue_response

        raw = {
            "queue_running": [[0, "run-1", {}, {}, {}]],
            "queue_pending": [[1, "pend-1", {}, {}]],
        }
        result = parse_queue_response(raw)
        assert len(result["running"]) == 1
        assert len(result["pending"]) == 1

    def test_empty_response(self) -> None:
        from cli_anything.comfyui.core.queue import parse_queue_response

        result = parse_queue_response({})
        assert result["running"] == []
        assert result["pending"] == []

    def test_bad_entry_skipped(self) -> None:
        from cli_anything.comfyui.core.queue import parse_queue_response

        raw = {"queue_running": ["not-a-list"]}
        result = parse_queue_response(raw)
        assert result["running"] == []


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


class TestOutputFile:
    def test_view_path_includes_filename(self) -> None:
        from cli_anything.comfyui.core.history import OutputFile

        f = OutputFile(filename="img.png", subfolder="", file_type="output")
        assert "img.png" in f.view_path()

    def test_view_path_with_subfolder(self) -> None:
        from cli_anything.comfyui.core.history import OutputFile

        f = OutputFile(filename="img.png", subfolder="batch1", file_type="output")
        assert "subfolder=batch1" in f.view_path()

    def test_to_dict(self) -> None:
        from cli_anything.comfyui.core.history import OutputFile

        f = OutputFile(filename="img.png", subfolder="", file_type="output")
        d = f.to_dict()
        assert d["filename"] == "img.png"


class TestHistoryItem:
    def _entry(self) -> dict:
        return {
            "outputs": {
                "9": {"images": [{"filename": "out.png", "subfolder": "", "type": "output"}]}
            },
            "status": {"status_str": "success"},
            "node_errors": {},
        }

    def test_from_dict_ok(self) -> None:
        from cli_anything.comfyui.core.history import HistoryItem

        item = HistoryItem.from_dict("pid-1", self._entry())
        assert item.status == "success"
        assert len(item.all_output_files()) == 1

    def test_all_output_files_flattens(self) -> None:
        from cli_anything.comfyui.core.history import HistoryItem

        item = HistoryItem.from_dict("pid-1", self._entry())
        files = item.all_output_files()
        assert files[0].filename == "out.png"

    def test_to_dict_has_prompt_id(self) -> None:
        from cli_anything.comfyui.core.history import HistoryItem

        item = HistoryItem.from_dict("pid-1", self._entry())
        assert item.to_dict()["prompt_id"] == "pid-1"

    def test_parse_history_response(self) -> None:
        from cli_anything.comfyui.core.history import parse_history_response

        data = {"pid-1": self._entry()}
        items = parse_history_response(data)
        assert len(items) == 1

    def test_parse_skips_non_dict(self) -> None:
        from cli_anything.comfyui.core.history import parse_history_response

        data = {"pid-1": "not-a-dict"}
        items = parse_history_response(data)
        assert items == []

    def test_video_outputs_parsed(self) -> None:
        from cli_anything.comfyui.core.history import HistoryItem

        entry = {
            "outputs": {
                "9": {"videos": [{"filename": "v.mp4", "subfolder": "", "type": "output"}]}
            },
            "status": {"status_str": "success"},
            "node_errors": {},
        }
        item = HistoryItem.from_dict("pid-2", entry)
        assert item.all_output_files()[0].filename == "v.mp4"


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


class TestChangeItem:
    def test_destructive_kind(self) -> None:
        from cli_anything.comfyui.core.manifest import ChangeItem, ChangeKind

        c = ChangeItem(kind=ChangeKind.QUEUE_CLEAR, description="clear")
        assert c.is_destructive()

    def test_non_destructive_kind(self) -> None:
        from cli_anything.comfyui.core.manifest import ChangeItem, ChangeKind

        c = ChangeItem(kind=ChangeKind.QUEUE_SUBMIT, description="submit")
        assert not c.is_destructive()

    def test_summary_includes_tag(self) -> None:
        from cli_anything.comfyui.core.manifest import ChangeItem, ChangeKind

        c = ChangeItem(kind=ChangeKind.QUEUE_INTERRUPT, description="stop it")
        assert "DESTRUCTIVE" in c.summary()

    def test_to_dict_roundtrip(self) -> None:
        from cli_anything.comfyui.core.manifest import ChangeItem, ChangeKind

        c = ChangeItem(kind=ChangeKind.QUEUE_SUBMIT, description="sub", params={"p": 1})
        d = c.to_dict()
        c2 = ChangeItem.from_dict(d)
        assert c2.kind == c.kind
        assert c2.params == c.params


class TestActionManifest:
    def test_build_plan(self) -> None:
        from cli_anything.comfyui.core.manifest import ChangeItem, ChangeKind, build_plan

        changes = [ChangeItem(kind=ChangeKind.QUEUE_SUBMIT, description="sub")]
        m = build_plan(changes)
        assert len(m.changes) == 1

    def test_has_destructive(self) -> None:
        from cli_anything.comfyui.core.manifest import ActionManifest, ChangeItem, ChangeKind

        m = ActionManifest()
        m.add(ChangeItem(kind=ChangeKind.QUEUE_CLEAR, description="clear"))
        assert m.has_destructive()

    def test_no_destructive(self) -> None:
        from cli_anything.comfyui.core.manifest import ActionManifest, ChangeItem, ChangeKind

        m = ActionManifest()
        m.add(ChangeItem(kind=ChangeKind.QUEUE_SUBMIT, description="sub"))
        assert not m.has_destructive()

    def test_to_dict_from_dict_roundtrip(self) -> None:
        from cli_anything.comfyui.core.manifest import ActionManifest, ChangeItem, ChangeKind

        m = ActionManifest()
        m.add(ChangeItem(kind=ChangeKind.HISTORY_CLEAR, description="clr"))
        d = m.to_dict()
        m2 = ActionManifest.from_dict(d)
        assert m2.changes[0].kind == ChangeKind.HISTORY_CLEAR

    def test_save_load_manifest(self, tmp_path: Path) -> None:
        from cli_anything.comfyui.core.manifest import (
            ActionManifest,
            ChangeItem,
            ChangeKind,
            load_manifest,
            save_manifest,
        )

        m = ActionManifest()
        m.add(ChangeItem(kind=ChangeKind.QUEUE_SUBMIT, description="s"))
        path = tmp_path / "manifest.json"
        save_manifest(m, path)
        m2 = load_manifest(path)
        assert len(m2.changes) == 1

    def test_load_missing_manifest_returns_empty(self, tmp_path: Path) -> None:
        from cli_anything.comfyui.core.manifest import load_manifest

        m = load_manifest(tmp_path / "nope.json")
        assert m.changes == []

    def test_plan_helpers(self) -> None:
        from cli_anything.comfyui.core.manifest import (
            ChangeKind,
            plan_history_clear,
            plan_queue_clear,
            plan_queue_interrupt,
            plan_queue_submit,
        )

        assert plan_queue_submit("wf.json").kind == ChangeKind.QUEUE_SUBMIT
        assert plan_queue_clear().kind == ChangeKind.QUEUE_CLEAR
        assert plan_queue_interrupt().kind == ChangeKind.QUEUE_INTERRUPT
        assert plan_history_clear().kind == ChangeKind.HISTORY_CLEAR
        assert plan_history_clear("pid").params["prompt_id"] == "pid"


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class TestSession:
    def test_new_session_has_uuid(self) -> None:
        from cli_anything.comfyui.core.session import Session

        s = Session()
        assert len(s.session_id) == 36

    def test_push_history_appends(self) -> None:
        from cli_anything.comfyui.core.session import Session

        s = Session()
        s.push_history({"prompt_id": "x"})
        assert len(s.history) == 1

    def test_push_history_caps_at_max(self) -> None:
        from cli_anything.comfyui.core.session import MAX_HISTORY, Session

        s = Session()
        for i in range(MAX_HISTORY + 10):
            s.push_history({"i": i})
        assert len(s.history) == MAX_HISTORY

    def test_push_history_keeps_latest(self) -> None:
        from cli_anything.comfyui.core.session import MAX_HISTORY, Session

        s = Session()
        for i in range(MAX_HISTORY + 5):
            s.push_history({"i": i})
        # Last entry should be the most recently appended
        assert s.history[-1]["i"] == MAX_HISTORY + 4

    def test_to_dict_from_dict_roundtrip(self) -> None:
        from cli_anything.comfyui.core.session import Session

        s = Session(host="http://test:9999")
        s.push_history({"a": 1})
        d = s.to_dict()
        s2 = Session.from_dict(d)
        assert s2.host == s.host
        assert s2.history == s.history

    def test_save_and_load(self, tmp_path: Path) -> None:
        from cli_anything.comfyui.core.session import Session, load_session, save_session

        s = Session()
        s.push_history({"prompt_id": "abc"})
        save_session(s, tmp_path)
        s2 = load_session(s.session_id, tmp_path)
        assert s2.session_id == s.session_id
        assert s2.history[0]["prompt_id"] == "abc"

    def test_load_missing_raises(self, tmp_path: Path) -> None:
        from cli_anything.comfyui.core.session import load_session

        with pytest.raises(FileNotFoundError):
            load_session("ghost-id", tmp_path)

    def test_delete_session(self, tmp_path: Path) -> None:
        from cli_anything.comfyui.core.session import Session, delete_session, save_session

        s = Session()
        save_session(s, tmp_path)
        assert delete_session(s.session_id, tmp_path) is True
        assert delete_session(s.session_id, tmp_path) is False

    def test_list_sessions(self, tmp_path: Path) -> None:
        from cli_anything.comfyui.core.session import Session, list_sessions, save_session

        s1 = Session()
        s2 = Session()
        save_session(s1, tmp_path)
        save_session(s2, tmp_path)
        result = list_sessions(tmp_path)
        ids = [r["session_id"] for r in result]
        assert s1.session_id in ids
        assert s2.session_id in ids

    def test_list_sessions_empty_dir(self, tmp_path: Path) -> None:
        from cli_anything.comfyui.core.session import list_sessions

        empty = tmp_path / "empty"
        result = list_sessions(empty)
        assert result == []


# ---------------------------------------------------------------------------
# Backend exceptions
# ---------------------------------------------------------------------------


class TestBackendExceptions:
    def test_hierarchy(self) -> None:
        from cli_anything.comfyui.utils.comfyui_backend import (
            ComfyUIAuthError,
            ComfyUIBackendError,
            ComfyUINotFoundError,
            ComfyUIRateLimitError,
            ComfyUIServerError,
            ComfyUIValidationError,
        )

        assert issubclass(ComfyUIAuthError, ComfyUIBackendError)
        assert issubclass(ComfyUINotFoundError, ComfyUIBackendError)
        assert issubclass(ComfyUIValidationError, ComfyUIBackendError)
        assert issubclass(ComfyUIRateLimitError, ComfyUIBackendError)
        assert issubclass(ComfyUIServerError, ComfyUIBackendError)

    def test_status_code_stored(self) -> None:
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUIAuthError

        exc = ComfyUIAuthError("denied", status_code=401)
        assert exc.status_code == 401

    def test_message_stored(self) -> None:
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUINotFoundError

        exc = ComfyUINotFoundError("not here", status_code=404)
        assert "not here" in str(exc)


# ---------------------------------------------------------------------------
# Backend — translate_status
# ---------------------------------------------------------------------------


class TestBackendTranslateStatus:
    def _backend(self):
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackend

        return ComfyUIBackend()

    def _mock_response(self, status_code: int, text: str = "err") -> MagicMock:
        r = MagicMock()
        r.status_code = status_code
        r.text = text
        return r

    def test_2xx_no_raise(self) -> None:
        b = self._backend()
        b._translate_status(self._mock_response(200))  # no exception

    def test_401_raises_auth(self) -> None:
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUIAuthError

        b = self._backend()
        with pytest.raises(ComfyUIAuthError):
            b._translate_status(self._mock_response(401))

    def test_403_raises_auth(self) -> None:
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUIAuthError

        b = self._backend()
        with pytest.raises(ComfyUIAuthError):
            b._translate_status(self._mock_response(403))

    def test_404_raises_not_found(self) -> None:
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUINotFoundError

        b = self._backend()
        with pytest.raises(ComfyUINotFoundError):
            b._translate_status(self._mock_response(404))

    def test_422_raises_validation(self) -> None:
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUIValidationError

        b = self._backend()
        with pytest.raises(ComfyUIValidationError):
            b._translate_status(self._mock_response(422))

    def test_429_raises_rate_limit(self) -> None:
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUIRateLimitError

        b = self._backend()
        with pytest.raises(ComfyUIRateLimitError):
            b._translate_status(self._mock_response(429))

    def test_500_raises_server_error(self) -> None:
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUIServerError

        b = self._backend()
        with pytest.raises(ComfyUIServerError):
            b._translate_status(self._mock_response(500))

    def test_unknown_4xx_raises_backend_error(self) -> None:
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackendError

        b = self._backend()
        with pytest.raises(ComfyUIBackendError):
            b._translate_status(self._mock_response(418))


# ---------------------------------------------------------------------------
# Backend — mocked HTTP
# ---------------------------------------------------------------------------


class TestComfyUIBackendMocked:
    def _make_response(self, status: int, body: object) -> MagicMock:
        r = MagicMock()
        r.status_code = status
        r.text = json.dumps(body)
        r.json.return_value = body
        r.content = b"bytes"
        return r

    def _backend(self):
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackend

        return ComfyUIBackend(base_url="http://mock:8188")

    @patch("httpx.request")
    def test_system_stats(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {"system": {"cpu": 10}})
        b = self._backend()
        result = b.system_stats()
        assert result == {"system": {"cpu": 10}}

    @patch("httpx.request")
    def test_embeddings(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, ["emb1", "emb2"])
        b = self._backend()
        result = b.embeddings()
        assert "emb1" in result

    @patch("httpx.request")
    def test_object_info(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {"KSampler": {}})
        b = self._backend()
        result = b.object_info()
        assert "KSampler" in result

    @patch("httpx.request")
    def test_object_info_node(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {"KSampler": {"input": {}}})
        b = self._backend()
        result = b.object_info_node("KSampler")
        assert "KSampler" in result

    @patch("httpx.request")
    def test_history(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {"pid-1": {"outputs": {}, "status": {}}})
        b = self._backend()
        result = b.history()
        assert "pid-1" in result

    @patch("httpx.request")
    def test_history_prompt(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {"pid-1": {}})
        b = self._backend()
        result = b.history_prompt("pid-1")
        assert isinstance(result, dict)

    @patch("httpx.request")
    def test_clear_history_all(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {})
        b = self._backend()
        b.clear_history()
        call_kwargs = mock_req.call_args
        assert call_kwargs[1]["json"] == {"clear": True}

    @patch("httpx.request")
    def test_clear_history_single(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {})
        b = self._backend()
        b.clear_history(prompt_id="pid-1")
        call_kwargs = mock_req.call_args
        assert call_kwargs[1]["json"] == {"delete": ["pid-1"]}

    @patch("httpx.request")
    def test_queue_get(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {"queue_running": [], "queue_pending": []})
        b = self._backend()
        result = b.queue()
        assert "queue_running" in result

    @patch("httpx.request")
    def test_queue_clear(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {})
        b = self._backend()
        b.queue_clear()
        call_kwargs = mock_req.call_args
        assert call_kwargs[1]["json"] == {"clear": True}

    @patch("httpx.request")
    def test_submit_prompt(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(
            200, {"prompt_id": "new-id", "number": 1, "node_errors": {}}
        )
        b = self._backend()
        result = b.submit_prompt({"prompt": {}, "client_id": "c1"})
        assert result["prompt_id"] == "new-id"

    @patch("httpx.request")
    def test_interrupt(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {})
        b = self._backend()
        result = b.interrupt()
        assert isinstance(result, dict)

    @patch("httpx.request")
    def test_view(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {})
        b = self._backend()
        result = b.view("img.png")
        assert result == b"bytes"

    @patch("httpx.request")
    def test_models(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, ["model_a.safetensors"])
        b = self._backend()
        result = b.models("checkpoints")
        assert "model_a.safetensors" in result

    @patch("httpx.request")
    def test_prompt_status(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {"exec_info": {"queue_remaining": 0}})
        b = self._backend()
        result = b.prompt_status()
        assert "exec_info" in result

    @patch("httpx.request")
    def test_connection_error_raises_backend_error(self, mock_req: MagicMock) -> None:
        import httpx as _httpx
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackendError

        mock_req.side_effect = _httpx.ConnectError("refused")
        b = self._backend()
        with pytest.raises(ComfyUIBackendError, match="Connection error"):
            b.system_stats()

    @patch("httpx.request")
    def test_auth_header_sent(self, mock_req: MagicMock) -> None:
        mock_req.return_value = self._make_response(200, {})
        from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackend

        b = ComfyUIBackend(
            base_url="http://mock:8188", auth_headers={"Authorization": "Bearer tok"}
        )
        b.system_stats()
        headers_sent = mock_req.call_args[1]["headers"]
        assert headers_sent.get("Authorization") == "Bearer tok"

    @patch("time.sleep")
    @patch("httpx.request")
    def test_429_retry_then_success(self, mock_req: MagicMock, mock_sleep: MagicMock) -> None:
        rate_resp = MagicMock()
        rate_resp.status_code = 429
        rate_resp.text = "rate limited"
        rate_resp.headers = {"Retry-After": "0"}

        ok_resp = self._make_response(200, {"ok": True})

        mock_req.side_effect = [rate_resp, ok_resp]
        b = self._backend()
        result = b.system_stats()
        assert result == {"ok": True}
        mock_sleep.assert_called_once()


# ---------------------------------------------------------------------------
# ReplSkin (offline rendering smoke tests)
# ---------------------------------------------------------------------------


class TestReplSkin:
    def test_init_json_mode(self) -> None:
        from cli_anything.comfyui.utils.repl_skin import ReplSkin

        skin = ReplSkin(json_mode=True)
        assert skin._json is True

    def test_success_prints(self, capsys: pytest.CaptureFixture) -> None:
        from cli_anything.comfyui.utils.repl_skin import ReplSkin

        skin = ReplSkin(json_mode=False)
        skin.success("done")
        captured = capsys.readouterr()
        assert "done" in captured.out

    def test_error_prints(self, capsys: pytest.CaptureFixture) -> None:
        from cli_anything.comfyui.utils.repl_skin import ReplSkin

        skin = ReplSkin(json_mode=False)
        skin.error("boom")
        captured = capsys.readouterr()
        assert "boom" in captured.out

    def test_json_mode_suppresses_success(self, capsys: pytest.CaptureFixture) -> None:
        from cli_anything.comfyui.utils.repl_skin import ReplSkin

        skin = ReplSkin(json_mode=True)
        skin.success("silent")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_table_no_rows_shows_hint(self, capsys: pytest.CaptureFixture) -> None:
        from cli_anything.comfyui.utils.repl_skin import ReplSkin

        skin = ReplSkin(json_mode=False)
        skin.table(["A", "B"], [])
        captured = capsys.readouterr()
        assert "no rows" in captured.out

    def test_table_renders_rows(self, capsys: pytest.CaptureFixture) -> None:
        from cli_anything.comfyui.utils.repl_skin import ReplSkin

        skin = ReplSkin(json_mode=False)
        skin.table(["Name", "Value"], [["foo", "bar"]])
        captured = capsys.readouterr()
        assert "foo" in captured.out
        assert "bar" in captured.out

    def test_section_suppressed_in_json_mode(self, capsys: pytest.CaptureFixture) -> None:
        from cli_anything.comfyui.utils.repl_skin import ReplSkin

        skin = ReplSkin(json_mode=True)
        skin.section("Test")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_warning_prints(self, capsys: pytest.CaptureFixture) -> None:
        from cli_anything.comfyui.utils.repl_skin import ReplSkin

        skin = ReplSkin()
        skin.warning("watch out")
        captured = capsys.readouterr()
        assert "watch out" in captured.out

    def test_info_prints(self, capsys: pytest.CaptureFixture) -> None:
        from cli_anything.comfyui.utils.repl_skin import ReplSkin

        skin = ReplSkin()
        skin.info("fyi")
        captured = capsys.readouterr()
        assert "fyi" in captured.out

    def test_hint_prints(self, capsys: pytest.CaptureFixture) -> None:
        from cli_anything.comfyui.utils.repl_skin import ReplSkin

        skin = ReplSkin()
        skin.hint("tip")
        captured = capsys.readouterr()
        assert "tip" in captured.out

    def test_create_prompt_session_no_error(self) -> None:
        from cli_anything.comfyui.utils.repl_skin import ReplSkin

        skin = ReplSkin()
        # Returns None if prompt_toolkit absent, or a session object
        result = skin.create_prompt_session()
        # Just checking no exception raised
        assert result is None or hasattr(result, "prompt")
