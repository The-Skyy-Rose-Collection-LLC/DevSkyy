"""SceneGeneratorAgent — OAI-primary / Gemini-fallback dispatch + size mapping.

No real image API call is made: both engine dispatchers (and the root client)
are mocked. Verifies the founder-locked engine order (gpt-image-2 primary,
Gemini fallback), the gpt-image-2 size mapping, and graceful failure.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from skyyrose.elite_studio.agents import scene_generator_agent as sga
from skyyrose.elite_studio.agents.scene_generator_agent import SceneGeneratorAgent

_SPEC = {
    "scene_description": "gothic cathedral at night",
    "render_aspect": "3:4 portrait",
    "expected_filename": "scene.png",
}
_SCENE = "black-rose-test-scene"


def _patch_canon(monkeypatch) -> None:
    """Make _SCENE canonical and return a fixed spec, so no scene.json is read."""
    monkeypatch.setattr(sga, "SCENE_LOOKBOOK", {_SCENE: {}})
    monkeypatch.setattr(sga, "load_lighting_spec", lambda collection, scene: dict(_SPEC))


def test_aspect_to_size_native_and_fallback() -> None:
    f = SceneGeneratorAgent._aspect_to_size
    assert f("3:4 portrait") == "1152x1536"  # native 3:4, both dims /16
    assert f("1:1") == "1536x1536"
    assert f("16:9") == "1536x864"
    assert f("garbage") == "1024x1536"  # unparseable → portrait default


async def test_oai_primary_success(tmp_path, monkeypatch) -> None:
    _patch_canon(monkeypatch)
    agent = SceneGeneratorAgent()
    oai = AsyncMock(return_value=(b"\x89PNG-oai", "gpt-image-2", 0.30))
    gem = AsyncMock()
    with (
        patch.object(agent, "_dispatch_oai", oai),
        patch.object(agent, "_dispatch_gemini", gem),
    ):
        result = await agent.generate_scene(_SCENE, output_dir=tmp_path)

    assert result.success
    assert result.provider == "openai/gpt-image-2"
    assert result.metadata["size"] == "1152x1536"
    gem.assert_not_called()  # primary succeeded → no fallback
    assert (tmp_path / "scene.png").read_bytes() == b"\x89PNG-oai"


async def test_falls_back_to_gemini_on_oai_failure(tmp_path, monkeypatch) -> None:
    _patch_canon(monkeypatch)
    agent = SceneGeneratorAgent()
    oai = AsyncMock(side_effect=RuntimeError("no OPENAI_API_KEY"))
    gem = AsyncMock(return_value=(b"GEM-bytes", "gemini-2.5-flash-image", 0.08))
    with (
        patch.object(agent, "_dispatch_oai", oai),
        patch.object(agent, "_dispatch_gemini", gem),
    ):
        result = await agent.generate_scene(_SCENE, output_dir=tmp_path)

    assert result.success
    assert result.provider == "google/gemini"
    oai.assert_awaited_once()
    gem.assert_awaited_once()
    assert (tmp_path / "scene.png").read_bytes() == b"GEM-bytes"


async def test_both_engines_fail(tmp_path, monkeypatch) -> None:
    _patch_canon(monkeypatch)
    agent = SceneGeneratorAgent()
    with (
        patch.object(agent, "_dispatch_oai", AsyncMock(side_effect=RuntimeError("oai down"))),
        patch.object(agent, "_dispatch_gemini", AsyncMock(side_effect=RuntimeError("gem down"))),
    ):
        result = await agent.generate_scene(_SCENE, output_dir=tmp_path)

    assert not result.success
    assert "oai down" in result.error
    assert "gem down" in result.error


async def test_dispatch_oai_calls_root_client(monkeypatch) -> None:
    """_dispatch_oai routes through scripts/oai_render/client.OAIImageClient.generate."""
    agent = SceneGeneratorAgent()
    fake_client = MagicMock()
    fake_client.generate.return_value = b"scene-png"
    with patch("scripts.oai_render.client.OAIImageClient", return_value=fake_client):
        out, model, cost = await agent._dispatch_oai("a gothic scene", "1152x1536", None)

    assert out == b"scene-png"
    assert model == "gpt-image-2"
    assert cost == 0.30
    fake_client.generate.assert_called_once()
    kwargs = fake_client.generate.call_args.kwargs
    assert kwargs["size"] == "1152x1536"
    assert kwargs["background"] == "opaque"
