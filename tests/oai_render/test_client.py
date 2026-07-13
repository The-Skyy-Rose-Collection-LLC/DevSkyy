"""
tests.oai_render.test_client — gpt-image-2 edit client contract.

CORRECTED 2026-06-30 (bug-172): the prior version of this test locked in
input_fidelity="high" being sent unconditionally, based on a 2026-06-24
Context7 read that turned out to be wrong for gpt-image-2 specifically -- the
live API rejects the parameter for that model with a 400
invalid_input_fidelity_model error (reproduced). Context7 (openai/openai-openapi,
images/edits schema) confirms support is listed for gpt-image-1 /
gpt-image-1-mini / gpt-image-1.5 only. client.edit() now sends input_fidelity
only when config.MODEL is in config.INPUT_FIDELITY_SUPPORTED_MODELS -- this
file locks BOTH the omit-for-gpt-image-2 case (today's production model) and
the send-when-supported case, so neither direction can silently regress.
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


def test_edit_omits_input_fidelity_for_unsupported_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """gpt-image-2 (today's production model) rejects input_fidelity outright (bug-172)."""
    client, fake_sdk = _build_client_with_mock(monkeypatch)
    img = tmp_path / "ref.png"
    img.write_bytes(_FAKE_PNG)

    out = client.edit(prompt="SKYYROSE varsity, studio", image_paths=[img])

    assert out == b"image-bytes"
    fake_sdk.images.edit.assert_called_once()
    kwargs = fake_sdk.images.edit.call_args.kwargs
    assert kwargs["model"] == "gpt-image-2"
    assert "input_fidelity" not in kwargs  # gpt-image-2 400s on this param
    assert config.MODEL not in config.INPUT_FIDELITY_SUPPORTED_MODELS


def test_edit_sends_input_fidelity_for_supported_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the configured model DOES support it, input_fidelity="high" is still sent."""
    monkeypatch.setattr(config, "MODEL", "gpt-image-1.5")
    client, fake_sdk = _build_client_with_mock(monkeypatch)
    img = tmp_path / "ref.png"
    img.write_bytes(_FAKE_PNG)

    out = client.edit(prompt="SKYYROSE varsity, studio", image_paths=[img])

    assert out == b"image-bytes"
    kwargs = fake_sdk.images.edit.call_args.kwargs
    assert kwargs["model"] == "gpt-image-1.5"
    assert kwargs["input_fidelity"] == "high"  # not omitted, not "low"
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
