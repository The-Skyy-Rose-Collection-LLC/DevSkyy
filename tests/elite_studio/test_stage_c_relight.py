"""Phase 1 / P-failclosed-C: stage C relight must fail closed.

Model-free — both IC-Light providers are monkeypatched, no network/GPU. When
both providers fail, relight must raise instead of returning the unrelit alpha
path (which would silently poison downstream QC). The LIVE path is the inline
``CompositorAgent._relight_subject``; the module ``relight_subject`` is a
(currently unused) parallel copy — both are covered.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from skyyrose.elite_studio.agents.compositor import orchestrator as _orch
from skyyrose.elite_studio.agents.compositor import stage_c_relight

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _isolate_relight_cache(tmp_path, monkeypatch):
    """``_cache_dir('relight')`` is a process-global cache shared across tests;
    redirect it to a per-test tmp dir so a cache hit can't mask the raise."""
    cache = tmp_path / "relight-cache"
    cache.mkdir()
    monkeypatch.setattr(stage_c_relight, "_cache_dir", lambda name: cache)
    monkeypatch.setattr(_orch, "_cache_dir", lambda name: cache)


def _png(p: Path) -> str:
    Image.new("RGBA", (4, 4), (255, 255, 255, 255)).save(p)
    return str(p)


def test_module_relight_raises_when_all_providers_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(stage_c_relight, "_run_iclight_replicate", lambda **k: None)
    monkeypatch.setattr(stage_c_relight, "_run_iclight", lambda **k: None)
    alpha = _png(tmp_path / "alpha.png")
    scene = _png(tmp_path / "scene.png")
    with pytest.raises(RuntimeError, match="provider"):
        stage_c_relight.relight_subject(alpha, scene, "x", "br-001", str(tmp_path / "out"))


def test_module_relight_returns_new_path_on_success(tmp_path, monkeypatch):
    """Happy path unaffected: a successful provider returns a new relit path."""
    monkeypatch.setattr(
        stage_c_relight, "_run_iclight_replicate", lambda **k: b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
    )
    alpha = _png(tmp_path / "alpha.png")
    scene = _png(tmp_path / "scene.png")
    out = stage_c_relight.relight_subject(alpha, scene, "x", "br-001", str(tmp_path / "out"))
    assert out.endswith("br-001-relit.png") and out != alpha


def test_inline_orchestrator_relight_raises_when_all_providers_fail(tmp_path, monkeypatch):
    """The LIVE path is CompositorAgent._relight_subject (inline copy) — fail closed too."""
    monkeypatch.setattr(_orch.CompositorAgent, "_run_iclight_replicate", lambda self, **k: None)
    monkeypatch.setattr(_orch.CompositorAgent, "_run_iclight", lambda self, **k: None)
    agent = _orch.CompositorAgent.__new__(_orch.CompositorAgent)
    alpha = _png(tmp_path / "alpha.png")
    scene = _png(tmp_path / "scene.png")
    with pytest.raises(RuntimeError, match="provider"):
        agent._relight_subject(alpha, scene, "x", "br-001", str(tmp_path / "out"))
