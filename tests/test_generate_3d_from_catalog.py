"""Tests for scripts/generate_3d_from_catalog.py — the SKU-to-3D batch orchestrator.

Zero real network calls: a fake `tripo3d` module is injected into
`sys.modules` for every test in this file (mirrors
tests/test_tripo_credentials.py's fake-SDK-injection pattern), and paid
`TripoAssetAgent` tool calls are mocked directly for dispatch-path tests. No
real `TripoClient`, no real API key, is ever touched.
"""

from __future__ import annotations

import sys
import types
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from scripts import generate_3d_from_catalog as orchestrator

# =============================================================================
# Fake tripo3d SDK (defense-in-depth, mirrors test_tripo_credentials.py)
# =============================================================================


class _FakeBalance:
    """Mimics the tripo3d SDK's Balance response object."""

    def __init__(self, balance: float) -> None:
        self.balance = balance
        self.frozen = 0.0


def _make_fake_tripo_module(balance: float = 100.0) -> types.ModuleType:
    class _FakeTripoClient:
        def __init__(self, api_key: str, IS_GLOBAL: bool) -> None:
            self.api_key = api_key
            self.is_global = IS_GLOBAL

        async def __aenter__(self) -> _FakeTripoClient:
            return self

        async def __aexit__(self, *exc_info: Any) -> bool:
            return False

        async def get_balance(self) -> _FakeBalance:
            return _FakeBalance(balance)

    module = types.ModuleType("tripo3d")
    module.TripoClient = _FakeTripoClient  # type: ignore[attr-defined]
    return module


class _FakeStdin:
    """Test seam for `_confirm()` — avoids mutating pytest's captured stdin."""

    def __init__(self, is_tty: bool) -> None:
        self._is_tty = is_tty

    def isatty(self) -> bool:
        return self._is_tty


@pytest.fixture(autouse=True)
def _fake_tripo_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject a fake tripo3d module for every test in this file — zero real
    network calls, zero real API keys, regardless of what a test does."""
    monkeypatch.setitem(sys.modules, "tripo3d", _make_fake_tripo_module())
    for var in ("TRIPO_API_KEYS", "TRIPO_API_KEY", "TRIPO3D_API_KEY", "TRIPO_API_BASE_URL"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("TRIPO_API_KEYS", "tsk_faketestkey0001")


# =============================================================================
# _resolve_sku_source_image
# =============================================================================


class TestResolveSkuSourceImage:
    def test_no_resolved_path_is_blocked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(orchestrator.sot_images, "resolve_image", lambda sku, role: None)

        path, reason = orchestrator._resolve_sku_source_image("br-001")

        assert path is None
        assert "no packshot" in reason.lower()

    def test_resolved_path_missing_on_disk_is_blocked(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            orchestrator.sot_images,
            "resolve_image",
            lambda sku, role: "assets/images/products/br-001-crewneck.png",
        )
        monkeypatch.setattr(Path, "exists", lambda self: False)

        path, reason = orchestrator._resolve_sku_source_image("br-001")

        assert path is None
        assert "missing on disk" in reason.lower()

    def test_resolved_and_present_joins_theme_root(self, monkeypatch: pytest.MonkeyPatch) -> None:
        relative = "assets/images/products/br-001-crewneck.png"
        monkeypatch.setattr(orchestrator.sot_images, "resolve_image", lambda sku, role: relative)
        monkeypatch.setattr(Path, "exists", lambda self: True)

        path, reason = orchestrator._resolve_sku_source_image("br-001")

        assert path is not None
        assert reason == ""
        assert path == orchestrator.THEME_ROOT / relative
        assert path.is_absolute()

    def test_always_called_with_role_packshot(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[tuple[str, str]] = []

        def _fake_resolve(sku: str, role: str) -> None:
            calls.append((sku, role))
            return None

        monkeypatch.setattr(orchestrator.sot_images, "resolve_image", _fake_resolve)

        orchestrator._resolve_sku_source_image("br-001")

        assert calls == [("br-001", "packshot")]


# =============================================================================
# build_manifest / exceeds_budget — manifest math
# =============================================================================


class TestBuildManifest:
    def test_total_is_n_skus_times_cost(self) -> None:
        manifest = orchestrator.build_manifest(
            ["br-001", "br-002", "br-003"], cost_per_generation=20.0, balance=1000.0
        )

        assert manifest.total_cost == 60.0

    def test_balance_after_is_balance_minus_total(self) -> None:
        manifest = orchestrator.build_manifest(["br-001"], cost_per_generation=20.0, balance=100.0)

        assert manifest.balance_after == 80.0
        assert manifest.insufficient_balance is False

    def test_insufficient_balance_flagged_before_dispatch(self) -> None:
        manifest = orchestrator.build_manifest(["br-001"], cost_per_generation=20.0, balance=5.0)

        assert manifest.balance_after == -15.0
        assert manifest.insufficient_balance is True

    def test_balance_none_produces_no_balance_after(self) -> None:
        manifest = orchestrator.build_manifest(["br-001"], cost_per_generation=20.0, balance=None)

        assert manifest.balance_after is None
        assert manifest.insufficient_balance is False


class TestExceedsBudget:
    def test_no_ceiling_never_exceeds(self) -> None:
        manifest = orchestrator.build_manifest(["br-001"], cost_per_generation=20.0, balance=None)

        assert orchestrator.exceeds_budget(manifest, None) is False

    def test_total_over_ceiling_exceeds(self) -> None:
        manifest = orchestrator.build_manifest(["br-001"], cost_per_generation=20.0, balance=None)

        assert orchestrator.exceeds_budget(manifest, 10.0) is True

    def test_total_under_ceiling_does_not_exceed(self) -> None:
        manifest = orchestrator.build_manifest(["br-001"], cost_per_generation=20.0, balance=None)

        assert orchestrator.exceeds_budget(manifest, 100.0) is False


# =============================================================================
# _confirm — STOP-AND-SHOW gate
# =============================================================================


class TestConfirmGate:
    def test_non_interactive_no_auto_confirm_aborts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
        monkeypatch.setattr(orchestrator.sys, "stdin", _FakeStdin(False))

        assert orchestrator._confirm() is False

    def test_auto_confirm_env_proceeds_even_without_tty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SKYYROSE_AUTO_CONFIRM", "1")
        monkeypatch.setattr(orchestrator.sys, "stdin", _FakeStdin(False))

        assert orchestrator._confirm() is True

    def test_interactive_y_proceeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
        monkeypatch.setattr(orchestrator.sys, "stdin", _FakeStdin(True))
        monkeypatch.setattr("builtins.input", lambda: "y")

        assert orchestrator._confirm() is True

    def test_interactive_yes_proceeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
        monkeypatch.setattr(orchestrator.sys, "stdin", _FakeStdin(True))
        monkeypatch.setattr("builtins.input", lambda: "yes")

        assert orchestrator._confirm() is True

    def test_interactive_anything_else_aborts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
        monkeypatch.setattr(orchestrator.sys, "stdin", _FakeStdin(True))
        monkeypatch.setattr("builtins.input", lambda: "n")

        assert orchestrator._confirm() is False

    def test_interactive_eof_aborts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SKYYROSE_AUTO_CONFIRM", raising=False)
        monkeypatch.setattr(orchestrator.sys, "stdin", _FakeStdin(True))

        def _raise_eof() -> str:
            raise EOFError

        monkeypatch.setattr("builtins.input", _raise_eof)

        assert orchestrator._confirm() is False


# =============================================================================
# dispatch_sku — full single-SKU dispatch path
# =============================================================================


class _FakeSession:
    """Collects added rows; mirrors the AsyncSession context-manager shape."""

    def __init__(self, sink: list[Any]) -> None:
        self._sink = sink
        self.committed = False

    async def __aenter__(self) -> _FakeSession:
        return self

    async def __aexit__(self, *exc_info: Any) -> bool:
        return False

    def add(self, row: Any) -> None:
        self._sink.append(row)

    async def commit(self) -> None:
        self.committed = True


class _FakeDbManager:
    """Mirrors `database.db_manager`'s public surface used by dispatch_sku."""

    def __init__(self) -> None:
        self.added_rows: list[Any] = []
        self.initialize = AsyncMock()

    def session(self) -> _FakeSession:
        return _FakeSession(self.added_rows)


class _FakeR2UploadResult:
    """Mirrors `R2UploadResult`'s public surface used by dispatch_sku (just `.key`)."""

    def __init__(self, key: str) -> None:
        self.key = key


class _FakeR2Client:
    """Records `upload_file` calls; can be configured to raise for one category.

    Mirrors `R2Client`'s public surface used by dispatch_sku (`upload_file` only) --
    zero real boto3/network calls, regardless of what a test does.
    """

    def __init__(self, *, fail_category: Any | None = None) -> None:
        self.fail_category = fail_category
        self.uploads: list[tuple[str, Any, str | None]] = []

    def upload_file(
        self, file_path: Any, category: Any, *, product_id: str | None = None, **_: Any
    ) -> _FakeR2UploadResult:
        self.uploads.append((str(file_path), category, product_id))
        if category == self.fail_category:
            raise orchestrator.R2Error(f"simulated R2 failure for category={category}")
        return _FakeR2UploadResult(key=f"{category.value}/{product_id}/fake-key")


@pytest.mark.asyncio
class TestDispatchSku:
    async def test_full_dispatch_writes_db_row_and_moves_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        generated_file = tmp_path / "generated_assets" / "3d" / "images" / "task-abc123.glb"
        generated_file.parent.mkdir(parents=True)
        generated_file.write_bytes(b"glTF" + b"\x00" * 20)

        fake_agent = Mock(spec=orchestrator.TripoAssetAgent)
        fake_agent._tool_generate_from_image = AsyncMock(
            return_value={
                "task_id": "task-abc123",
                "model_path": str(generated_file),
                "model_url": str(generated_file),
                "format": "glb",
                "metadata": {},
            }
        )
        fake_agent._tool_validate_asset = AsyncMock(
            return_value={
                "is_valid": True,
                "polycount": 4200,
                "texture_size": None,
                "warnings": [],
                "errors": [],
            }
        )

        fake_db_manager = _FakeDbManager()
        monkeypatch.setattr(orchestrator, "db_manager", fake_db_manager)
        monkeypatch.setattr(
            orchestrator, "OUTPUT_ROOT", tmp_path / "assets" / "3d-models-generated"
        )
        fake_r2 = _FakeR2Client()
        monkeypatch.setattr(orchestrator, "R2Client", lambda: fake_r2)

        source_image = tmp_path / "source.png"
        source_image.write_bytes(b"\x89PNG\r\n")

        result = await orchestrator.dispatch_sku(
            fake_agent, sku="br-001", name="BLACK Rose Crewneck", source_image=source_image
        )

        # Result dict.
        assert result["sku"] == "br-001"
        assert result["task_id"] == "task-abc123"
        assert result["validation_status"] == "valid"

        # File moved (not copied) to the SKU-organized final location.
        final_path = tmp_path / "assets" / "3d-models-generated" / "br-001" / "br-001.glb"
        assert final_path.exists()
        assert not generated_file.exists()
        assert result["model_path"] == str(final_path)

        # R2: model GLB uploaded (from the final, moved location); no preview
        # file was in the agent's result, so no preview upload was attempted.
        assert fake_r2.uploads == [
            (str(final_path), orchestrator.AssetCategory.MODEL_3D, "br-001"),
        ]
        assert result["model_r2_key"] == "3d-models/br-001/fake-key"
        assert result["rendered_preview_r2_key"] is None

        # db_manager.initialize() awaited before session() is used.
        fake_db_manager.initialize.assert_awaited_once()

        # DB row written with the correct fields.
        assert len(fake_db_manager.added_rows) == 1
        row = fake_db_manager.added_rows[0]
        assert isinstance(row.id, uuid.UUID)
        assert row.sku == "br-001"
        assert row.task_id == "task-abc123"
        assert row.provider == "tripo3d"
        assert row.format == "glb"
        assert row.model_path == str(final_path)
        assert row.source_image_path == str(source_image)
        assert row.validation_status == "valid"
        assert row.validation_details == {
            "is_valid": True,
            "polycount": 4200,
            "texture_size": None,
            "warnings": [],
            "errors": [],
        }
        assert row.model_r2_key == "3d-models/br-001/fake-key"
        assert row.rendered_preview_r2_key is None

        fake_agent._tool_generate_from_image.assert_awaited_once_with(
            image_path=str(source_image),
            product_name="BLACK Rose Crewneck",
            output_format="glb",
        )
        fake_agent._tool_validate_asset.assert_awaited_once_with(model_path=str(generated_file))

    async def test_dispatch_with_warnings_sets_warnings_status(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        generated_file = tmp_path / "gen" / "br-002.glb"
        generated_file.parent.mkdir(parents=True)
        generated_file.write_bytes(b"glTF" + b"\x00" * 20)

        fake_agent = Mock(spec=orchestrator.TripoAssetAgent)
        fake_agent._tool_generate_from_image = AsyncMock(
            return_value={"task_id": "task-002", "model_path": str(generated_file)}
        )
        fake_agent._tool_validate_asset = AsyncMock(
            return_value={
                "is_valid": True,
                "warnings": ["high polycount"],
                "errors": [],
            }
        )

        fake_db_manager = _FakeDbManager()
        monkeypatch.setattr(orchestrator, "db_manager", fake_db_manager)
        monkeypatch.setattr(orchestrator, "OUTPUT_ROOT", tmp_path / "out")
        fake_r2 = _FakeR2Client()
        monkeypatch.setattr(orchestrator, "R2Client", lambda: fake_r2)

        source_image = tmp_path / "src.png"
        source_image.write_bytes(b"x")

        result = await orchestrator.dispatch_sku(
            fake_agent, sku="br-002", name="BLACK Rose Joggers", source_image=source_image
        )

        assert result["validation_status"] == "warnings"
        assert fake_db_manager.added_rows[0].validation_status == "warnings"
        assert fake_db_manager.added_rows[0].model_r2_key == "3d-models/br-002/fake-key"
        assert fake_db_manager.added_rows[0].rendered_preview_r2_key is None

    async def test_rendered_preview_uploaded_when_present_on_disk(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        generated_file = tmp_path / "gen" / "br-003.glb"
        generated_file.parent.mkdir(parents=True)
        generated_file.write_bytes(b"glTF" + b"\x00" * 20)

        preview_file = tmp_path / "gen" / "task-003_rendered.webp"
        preview_file.write_bytes(b"fake-webp-bytes")

        fake_agent = Mock(spec=orchestrator.TripoAssetAgent)
        fake_agent._tool_generate_from_image = AsyncMock(
            return_value={
                "task_id": "task-003",
                "model_path": str(generated_file),
                "thumbnail_path": str(preview_file),
            }
        )
        fake_agent._tool_validate_asset = AsyncMock(
            return_value={"is_valid": True, "warnings": [], "errors": []}
        )

        fake_db_manager = _FakeDbManager()
        monkeypatch.setattr(orchestrator, "db_manager", fake_db_manager)
        monkeypatch.setattr(orchestrator, "OUTPUT_ROOT", tmp_path / "out")
        fake_r2 = _FakeR2Client()
        monkeypatch.setattr(orchestrator, "R2Client", lambda: fake_r2)

        source_image = tmp_path / "src.png"
        source_image.write_bytes(b"x")

        result = await orchestrator.dispatch_sku(
            fake_agent, sku="br-003", name="BLACK Rose Tee", source_image=source_image
        )

        final_path = tmp_path / "out" / "br-003" / "br-003.glb"
        assert fake_r2.uploads == [
            (str(final_path), orchestrator.AssetCategory.MODEL_3D, "br-003"),
            (str(preview_file), orchestrator.AssetCategory.THUMBNAIL, "br-003"),
        ]
        assert result["rendered_preview_r2_key"] == "thumbnail/br-003/fake-key"
        assert fake_db_manager.added_rows[0].rendered_preview_r2_key == "thumbnail/br-003/fake-key"

    async def test_rendered_preview_skipped_when_path_missing_on_disk(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        generated_file = tmp_path / "gen" / "br-004.glb"
        generated_file.parent.mkdir(parents=True)
        generated_file.write_bytes(b"glTF" + b"\x00" * 20)

        fake_agent = Mock(spec=orchestrator.TripoAssetAgent)
        fake_agent._tool_generate_from_image = AsyncMock(
            return_value={
                "task_id": "task-004",
                "model_path": str(generated_file),
                # thumbnail_path present but the file was never written to disk
                # (e.g. the Tripo task produced no rendered_image this time).
                "thumbnail_path": str(tmp_path / "gen" / "task-004_rendered.webp"),
            }
        )
        fake_agent._tool_validate_asset = AsyncMock(
            return_value={"is_valid": True, "warnings": [], "errors": []}
        )

        fake_db_manager = _FakeDbManager()
        monkeypatch.setattr(orchestrator, "db_manager", fake_db_manager)
        monkeypatch.setattr(orchestrator, "OUTPUT_ROOT", tmp_path / "out")
        fake_r2 = _FakeR2Client()
        monkeypatch.setattr(orchestrator, "R2Client", lambda: fake_r2)

        source_image = tmp_path / "src.png"
        source_image.write_bytes(b"x")

        result = await orchestrator.dispatch_sku(
            fake_agent, sku="br-004", name="BLACK Rose Cap", source_image=source_image
        )

        # Only the model upload happened -- no preview upload attempted for a
        # path that doesn't exist on disk.
        assert len(fake_r2.uploads) == 1
        assert fake_r2.uploads[0][1] == orchestrator.AssetCategory.MODEL_3D
        assert result["rendered_preview_r2_key"] is None
        assert fake_db_manager.added_rows[0].rendered_preview_r2_key is None

    async def test_preview_upload_failure_is_reported_and_dispatch_continues(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        generated_file = tmp_path / "gen" / "br-005.glb"
        generated_file.parent.mkdir(parents=True)
        generated_file.write_bytes(b"glTF" + b"\x00" * 20)

        preview_file = tmp_path / "gen" / "task-005_rendered.webp"
        preview_file.write_bytes(b"fake-webp-bytes")

        fake_agent = Mock(spec=orchestrator.TripoAssetAgent)
        fake_agent._tool_generate_from_image = AsyncMock(
            return_value={
                "task_id": "task-005",
                "model_path": str(generated_file),
                "thumbnail_path": str(preview_file),
            }
        )
        fake_agent._tool_validate_asset = AsyncMock(
            return_value={"is_valid": True, "warnings": [], "errors": []}
        )

        fake_db_manager = _FakeDbManager()
        monkeypatch.setattr(orchestrator, "db_manager", fake_db_manager)
        monkeypatch.setattr(orchestrator, "OUTPUT_ROOT", tmp_path / "out")
        fake_r2 = _FakeR2Client(fail_category=orchestrator.AssetCategory.THUMBNAIL)
        monkeypatch.setattr(orchestrator, "R2Client", lambda: fake_r2)

        source_image = tmp_path / "src.png"
        source_image.write_bytes(b"x")

        result = await orchestrator.dispatch_sku(
            fake_agent, sku="br-005", name="BLACK Rose Beanie", source_image=source_image
        )

        # Model upload succeeded, preview upload failed -- dispatch still
        # completes and the DB row is still written, just without a preview key.
        assert result["model_r2_key"] == "3d-models/br-005/fake-key"
        assert result["rendered_preview_r2_key"] is None
        assert len(fake_db_manager.added_rows) == 1
        assert fake_db_manager.added_rows[0].model_r2_key == "3d-models/br-005/fake-key"
        assert fake_db_manager.added_rows[0].rendered_preview_r2_key is None

        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "br-005" in captured.out

    async def test_model_upload_failure_propagates_and_writes_no_db_row(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        generated_file = tmp_path / "gen" / "br-006.glb"
        generated_file.parent.mkdir(parents=True)
        generated_file.write_bytes(b"glTF" + b"\x00" * 20)

        fake_agent = Mock(spec=orchestrator.TripoAssetAgent)
        fake_agent._tool_generate_from_image = AsyncMock(
            return_value={"task_id": "task-006", "model_path": str(generated_file)}
        )
        fake_agent._tool_validate_asset = AsyncMock(
            return_value={"is_valid": True, "warnings": [], "errors": []}
        )

        fake_db_manager = _FakeDbManager()
        monkeypatch.setattr(orchestrator, "db_manager", fake_db_manager)
        monkeypatch.setattr(orchestrator, "OUTPUT_ROOT", tmp_path / "out")
        fake_r2 = _FakeR2Client(fail_category=orchestrator.AssetCategory.MODEL_3D)
        monkeypatch.setattr(orchestrator, "R2Client", lambda: fake_r2)

        source_image = tmp_path / "src.png"
        source_image.write_bytes(b"x")

        with pytest.raises(orchestrator.R2Error):
            await orchestrator.dispatch_sku(
                fake_agent, sku="br-006", name="BLACK Rose Hoodie", source_image=source_image
            )

        # No DB write was even attempted -- the GLB is the point of the
        # pipeline, so a failed model upload must not produce a "successful"
        # row with no servable asset behind it.
        fake_db_manager.initialize.assert_not_called()
        assert fake_db_manager.added_rows == []


# =============================================================================
# run() — CLI-level orchestration gates
# =============================================================================


class TestRunBudgetAndBlockedGates:
    @pytest.mark.asyncio
    async def test_budget_ceiling_exceeded_makes_zero_dispatch_calls(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        source_image = tmp_path / "src.png"
        source_image.write_bytes(b"x")

        monkeypatch.setattr(
            orchestrator,
            "read_catalog_rows",
            lambda: [{"sku": "br-001", "name": "BLACK Rose Crewneck"}],
        )
        monkeypatch.setattr(
            orchestrator,
            "resolve_sku_readiness",
            lambda rows: [
                orchestrator.SkuReadiness("br-001", "BLACK Rose Crewneck", True, "", source_image)
            ],
        )

        dispatch_mock = AsyncMock()
        monkeypatch.setattr(orchestrator, "dispatch_sku", dispatch_mock)
        monkeypatch.setattr(orchestrator, "_confirm", lambda: True)

        exit_code = await orchestrator.run(["--sku", "br-001", "--budget", "1"])

        dispatch_mock.assert_not_called()
        assert exit_code != 0

    @pytest.mark.asyncio
    async def test_blocked_sku_makes_zero_dispatch_calls(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            orchestrator,
            "read_catalog_rows",
            lambda: [{"sku": "br-099", "name": "Unresolved SKU"}],
        )
        monkeypatch.setattr(
            orchestrator,
            "resolve_sku_readiness",
            lambda rows: [
                orchestrator.SkuReadiness(
                    "br-099", "Unresolved SKU", False, "no packshot image declared in SOT", None
                )
            ],
        )

        dispatch_mock = AsyncMock()
        monkeypatch.setattr(orchestrator, "dispatch_sku", dispatch_mock)
        confirm_mock = Mock(return_value=True)
        monkeypatch.setattr(orchestrator, "_confirm", confirm_mock)

        exit_code = await orchestrator.run(["--sku", "br-099"])

        dispatch_mock.assert_not_called()
        confirm_mock.assert_not_called()
        assert exit_code != 0

    @pytest.mark.asyncio
    async def test_all_flag_raises_and_dispatches_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        dispatch_mock = AsyncMock()
        monkeypatch.setattr(orchestrator, "dispatch_sku", dispatch_mock)

        with pytest.raises(SystemExit):
            await orchestrator.run(["--all"])

        dispatch_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_agent_reuses_resolved_credentials_not_a_second_probe(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The account shown in the manifest must be the account dispatched with.

        Regression test for a code-review finding: `run()` used to build a bare
        `TripoAssetAgent()` after already resolving credentials for the manifest,
        letting the agent silently re-probe (and potentially pick a different
        account) instead of reusing what was already resolved and shown to the
        user in the STOP-AND-SHOW gate.
        """
        source_image = tmp_path / "src.png"
        source_image.write_bytes(b"x")

        monkeypatch.setattr(
            orchestrator,
            "read_catalog_rows",
            lambda: [{"sku": "br-001", "name": "BLACK Rose Crewneck"}],
        )
        monkeypatch.setattr(
            orchestrator,
            "resolve_sku_readiness",
            lambda rows: [
                orchestrator.SkuReadiness("br-001", "BLACK Rose Crewneck", True, "", source_image)
            ],
        )

        fake_creds = orchestrator.TripoCredentials(
            api_key="tsk_resolved_once",
            is_global=False,
            base_url="https://api.tripo3d.com/v2",
            balance=9999.0,
        )
        monkeypatch.setattr(
            orchestrator, "resolve_tripo_credentials", AsyncMock(return_value=fake_creds)
        )
        monkeypatch.setattr(orchestrator, "_confirm", lambda: True)
        monkeypatch.setattr(
            orchestrator,
            "dispatch_sku",
            AsyncMock(
                return_value={
                    "sku": "br-001",
                    "task_id": "t1",
                    "model_path": "/x.glb",
                    "validation_status": "valid",
                }
            ),
        )

        agent_cls_mock = Mock(wraps=orchestrator.TripoAssetAgent)
        monkeypatch.setattr(orchestrator, "TripoAssetAgent", agent_cls_mock)

        exit_code = await orchestrator.run(["--sku", "br-001", "--budget", "999999"])

        assert exit_code == 0
        agent_cls_mock.assert_called_once()
        _, kwargs = agent_cls_mock.call_args
        built_config = kwargs["config"]
        assert built_config.api_key == fake_creds.api_key
        assert built_config.base_url == fake_creds.base_url
        assert built_config.is_global == fake_creds.is_global


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
