"""Unit tests for TRELLIS configuration."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.three_d.trellis.config import (
    TrellisBackend,
    TrellisConfig,
    TrellisQualityPreset,
    TrellisSamplingParams,
)


class TestSamplingParams:
    def test_each_preset_has_params(self) -> None:
        for preset in TrellisQualityPreset:
            params = TrellisSamplingParams.for_preset(preset)
            assert params.ss_sampling_steps > 0
            assert params.slat_sampling_steps > 0
            assert 0 < params.mesh_simplify <= 1

    def test_quality_monotonic(self) -> None:
        draft = TrellisSamplingParams.for_preset(TrellisQualityPreset.DRAFT)
        standard = TrellisSamplingParams.for_preset(TrellisQualityPreset.STANDARD)
        production = TrellisSamplingParams.for_preset(TrellisQualityPreset.PRODUCTION)

        # Steps grow with quality
        assert draft.ss_sampling_steps < standard.ss_sampling_steps < production.ss_sampling_steps
        assert draft.target_polycount < standard.target_polycount < production.target_polycount


class TestTrellisConfig:
    def test_defaults(self) -> None:
        cfg = TrellisConfig()
        assert cfg.backend == TrellisBackend.HF_SPACE
        assert cfg.quality == TrellisQualityPreset.STANDARD
        assert cfg.hf_space_id == "JeffreyXiang/TRELLIS"
        assert cfg.timeout_seconds > 0
        assert cfg.retry_attempts >= 0

    def test_sampling_property(self) -> None:
        cfg = TrellisConfig(quality=TrellisQualityPreset.PRODUCTION)
        assert cfg.sampling.ss_sampling_steps == 20

    def test_from_env_with_overrides(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setenv("TRELLIS_BACKEND", "local")
        monkeypatch.setenv("TRELLIS_QUALITY", "production")
        monkeypatch.setenv("TRELLIS_OUTPUT_DIR", str(tmp_path / "out"))
        monkeypatch.setenv("TRELLIS_CACHE_DIR", str(tmp_path / "cache"))
        monkeypatch.setenv("TRELLIS_SEED", "1234")
        monkeypatch.setenv("TRELLIS_TIMEOUT", "999")
        monkeypatch.setenv("TRELLIS_RETRIES", "5")

        cfg = TrellisConfig.from_env()
        assert cfg.backend == TrellisBackend.LOCAL
        assert cfg.quality == TrellisQualityPreset.PRODUCTION
        assert cfg.output_dir == str(tmp_path / "out")
        assert cfg.cache_dir == str(tmp_path / "cache")
        assert cfg.seed == 1234
        assert cfg.timeout_seconds == 999
        assert cfg.retry_attempts == 5

    def test_ensure_dirs(self, tmp_path: Path) -> None:
        cfg = TrellisConfig(
            output_dir=str(tmp_path / "out"),
            cache_dir=str(tmp_path / "cache"),
        )
        cfg.ensure_dirs()
        assert (tmp_path / "out").is_dir()
        assert (tmp_path / "cache").is_dir()
