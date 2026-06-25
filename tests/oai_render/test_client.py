"""
tests.oai_render.test_client — gpt-image-2 edit client contract.

Locks the input_fidelity="high" parameter (verified against the openai-python
image_edit_params.py source via Context7, 2026-06-24: supported for gpt-image-2,
default "low") so the render pipeline never silently drops back to low fidelity.
No real OpenAI call is made — the SDK client is replaced with a mock.
"""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.oai_render import config
from scripts.oai_render.client import OAIImageClient

_FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16


def _build_client_with_mock(monkeypatch: pytest.MonkeyPatch) -> tuple[OAIImageClient, MagicMock]:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-abc")
    client = OAIImageClient()
    fake_sdk = MagicMock()
    fake_sdk.images.edit.return_value = MagicMock(
        data=[MagicMock(b64_json=base64.b64encode(b"image-bytes").decode())]
    )
    client._client = fake_sdk  # replace the real OpenAI SDK client
    return client, fake_sdk


def test_edit_sends_input_fidelity_high(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client, fake_sdk = _build_client_with_mock(monkeypatch)
    img = tmp_path / "ref.png"
    img.write_bytes(_FAKE_PNG)

    out = client.edit(prompt="SKYYROSE varsity, studio", image_paths=[img])

    assert out == b"image-bytes"
    fake_sdk.images.edit.assert_called_once()
    kwargs = fake_sdk.images.edit.call_args.kwargs
    assert kwargs["model"] == "gpt-image-2"
    assert kwargs["input_fidelity"] == "high"  # the fix: not omitted, not "low"
    assert config.INPUT_FIDELITY == "high"


def test_generate_text_to_image_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """generate() is text-to-image: no reference image, never sends response_format.

    gpt-image models reject ``response_format`` (Context7-verified) and always
    return base64 — this locks the call shape so the scene path can't regress.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-abc")
    client = OAIImageClient()
    fake_sdk = MagicMock()
    fake_sdk.images.generate.return_value = MagicMock(
        data=[MagicMock(b64_json=base64.b64encode(b"scene-bytes").decode())]
    )
    client._client = fake_sdk

    out = client.generate(prompt="gothic cathedral at night", size="1152x1536")

    assert out == b"scene-bytes"
    fake_sdk.images.generate.assert_called_once()
    kwargs = fake_sdk.images.generate.call_args.kwargs
    assert kwargs["model"] == "gpt-image-2"
    assert kwargs["size"] == "1152x1536"
    assert kwargs["background"] == "opaque"  # scenes are full backdrops
    assert "response_format" not in kwargs  # rejected by gpt-image models
    assert "image" not in kwargs  # text-to-image: no reference
