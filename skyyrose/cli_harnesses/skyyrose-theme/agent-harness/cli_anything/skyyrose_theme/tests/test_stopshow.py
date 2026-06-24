"""
STOP-AND-SHOW manifest emitter tests.

Covers:
 - Manifest shape for each destructive op
 - Required key presence
 - Values reflect the actual command being prepared
 - Non-destructive ops produce irreversible=False
 - Manifest serialises cleanly to JSON (no Path/datetime leakage)
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_script(tmp_path: Path) -> Path:
    script = tmp_path / "deploy-theme.sh"
    script.write_text("#!/bin/bash\n")
    return script


# ---------------------------------------------------------------------------
# A. STOP-AND-SHOW manifest emitter (~10 tests)
# ---------------------------------------------------------------------------


class TestStopShowManifestShape:
    """Manifest dict has required keys for every op type."""

    REQUIRED_KEYS = {"action", "irreversible", "dry_run"}

    def test_deploy_manifest_has_required_keys(self, tmp_path):
        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        script = _make_script(tmp_path)
        manifest = build_deploy_manifest(deploy_script=script, theme_root=tmp_path)
        d = manifest.to_dict()
        for key in self.REQUIRED_KEYS:
            assert key in d, f"Missing required key: {key}"

    def test_deploy_manifest_has_action_and_target(self, tmp_path):
        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        script = _make_script(tmp_path)
        manifest = build_deploy_manifest(deploy_script=script, theme_root=tmp_path)
        d = manifest.to_dict()
        assert d["action"] == "deploy"
        assert "theme_root" in d  # target info lives here

    def test_deploy_dry_run_manifest_dry_run_true(self, tmp_path):
        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        script = _make_script(tmp_path)
        manifest = build_deploy_manifest(dry_run=True, deploy_script=script, theme_root=tmp_path)
        d = manifest.to_dict()
        assert d["dry_run"] is True

    def test_deploy_with_maintenance_manifest_mode_is_maintenance(self, tmp_path):
        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        script = _make_script(tmp_path)
        manifest = build_deploy_manifest(
            with_maintenance=True, deploy_script=script, theme_root=tmp_path
        )
        d = manifest.to_dict()
        assert d["mode"] == "maintenance"
        assert manifest.with_maintenance is True

    def test_deploy_default_mode_is_hot_swap(self, tmp_path):
        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        script = _make_script(tmp_path)
        manifest = build_deploy_manifest(deploy_script=script, theme_root=tmp_path)
        d = manifest.to_dict()
        assert d["mode"] == "hot-swap"

    def test_deploy_manifest_irreversible_is_true_when_not_dry_run(self, tmp_path):
        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        script = _make_script(tmp_path)
        manifest = build_deploy_manifest(deploy_script=script, theme_root=tmp_path)
        d = manifest.to_dict()
        assert d["irreversible"] is True

    def test_deploy_manifest_irreversible_is_false_when_dry_run(self, tmp_path):
        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        script = _make_script(tmp_path)
        manifest = build_deploy_manifest(dry_run=True, deploy_script=script, theme_root=tmp_path)
        d = manifest.to_dict()
        assert d["irreversible"] is False

    def test_deploy_manifest_serialises_to_json_no_path_objects(self, tmp_path):
        """to_dict() must return JSON-serialisable values — no Path or datetime."""
        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        script = _make_script(tmp_path)
        manifest = build_deploy_manifest(deploy_script=script, theme_root=tmp_path)
        d = manifest.to_dict()
        # If this raises TypeError, a Path or datetime leaked into the dict
        serialised = json.dumps(d)
        roundtripped = json.loads(serialised)
        assert roundtripped["action"] == "deploy"

    def test_deploy_manifest_dry_run_serialises_to_json(self, tmp_path):
        from cli_anything.skyyrose_theme.core.deploy import \
            build_deploy_manifest

        script = _make_script(tmp_path)
        manifest = build_deploy_manifest(dry_run=True, deploy_script=script, theme_root=tmp_path)
        d = manifest.to_dict()
        serialised = json.dumps(d)
        roundtripped = json.loads(serialised)
        assert roundtripped["dry_run"] is True
        assert roundtripped["irreversible"] is False

    def test_non_destructive_doctor_does_not_produce_deploy_manifest(self, tmp_path):
        """doctor() returns a DoctorReport, not a DeployManifest — irreversible concept N/A."""
        from cli_anything.skyyrose_theme.utils.theme_backend import doctor

        report = doctor(theme_root=tmp_path / "nonexistent")
        # DoctorReport has no to_dict with irreversible — assert it's never a DeployManifest
        from cli_anything.skyyrose_theme.core.deploy import DeployManifest

        assert not isinstance(report, DeployManifest)

    def test_confirmed_false_never_calls_subprocess(self, tmp_path):
        """run_deploy(confirmed=False) raises before touching subprocess."""
        from cli_anything.skyyrose_theme.core.deploy import (
            DeployNotConfirmedError, build_deploy_manifest, run_deploy)

        script = _make_script(tmp_path)
        manifest = build_deploy_manifest(deploy_script=script, theme_root=tmp_path)
        with patch("subprocess.run") as mock_run:
            with pytest.raises(DeployNotConfirmedError):
                run_deploy(manifest, confirmed=False)
            mock_run.assert_not_called()
