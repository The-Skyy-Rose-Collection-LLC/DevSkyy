"""
tests.flux_lora.test_upload — Unit tests for upload.upload_zip().

Security contract verified:
- confirmed=False raises RequiresConfirmationError BEFORE any network call.
- confirmed=True with mocked hub calls returns well-formed https URL.
- Missing token raises RuntimeError (not masked by RequiresConfirmationError).

Token isolation:
- conftest._clear_env_token removes REPLICATE_API_TOKEN (autouse).
- Each test that exercises token logic also clears HF_TOKEN and
  HUGGINGFACE_API_TOKEN and patches upload.load_dotenv to a no-op so
  the real .env.hf on disk cannot inject a live token.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.flux_lora import RequiresConfirmationError
from scripts.flux_lora.upload import show_upload_stopandshow, upload_zip

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HF_TOKEN_VARS = ("HF_TOKEN", "HUGGINGFACE_API_TOKEN")


def _noop_load_dotenv(*_args, **_kwargs) -> bool:
    """Drop-in replacement for load_dotenv that does nothing."""
    return False


def _make_zip(tmp_path: Path, name: str = "dataset.zip") -> Path:
    """Create a minimal fake zip file for testing."""
    p = tmp_path / name
    p.write_bytes(b"PK\x05\x06" + b"\x00" * 18)  # minimal ZIP end-of-central-dir
    return p


# ---------------------------------------------------------------------------
# Security gate: confirmed=False raises BEFORE any network call
# ---------------------------------------------------------------------------


def test_unconfirmed_raises_requires_confirmation(tmp_path: Path) -> None:
    """upload_zip(confirmed=False) must raise RequiresConfirmationError immediately."""
    zip_path = _make_zip(tmp_path)

    with (
        patch("scripts.flux_lora.upload.HfApi") as mock_api_cls,
        patch("scripts.flux_lora.upload.hf_hub_url") as mock_url,
    ):
        with pytest.raises(RequiresConfirmationError):
            upload_zip(zip_path, "skyyrose/test-dataset", confirmed=False)

        # No network call whatsoever
        mock_api_cls.assert_not_called()
        mock_url.assert_not_called()


def test_unconfirmed_raises_before_token_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """confirmed=False must raise BEFORE token is loaded (gate is truly first)."""
    zip_path = _make_zip(tmp_path)

    # Even if token env vars are absent the confirmed=False gate fires first
    for var in _HF_TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr("scripts.flux_lora.upload.load_dotenv", _noop_load_dotenv)

    with pytest.raises(RequiresConfirmationError):
        upload_zip(zip_path, "skyyrose/test-dataset", confirmed=False)


# ---------------------------------------------------------------------------
# confirmed=True — happy path with mocked hub calls
# ---------------------------------------------------------------------------


def test_confirmed_returns_https_url(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """confirmed=True with mocked hub → well-formed https resolve URL returned."""
    zip_path = _make_zip(tmp_path, "my-dataset.zip")

    # Isolate HF tokens
    for var in _HF_TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("HF_TOKEN", "hf_fake_token_for_test")
    monkeypatch.setattr("scripts.flux_lora.upload.load_dotenv", _noop_load_dotenv)

    expected_url = (
        "https://huggingface.co/datasets/skyyrose/test-dataset/resolve/main/my-dataset.zip"
    )

    mock_api_instance = MagicMock()
    mock_api_instance.create_repo.return_value = None
    mock_api_instance.upload_file.return_value = None

    with (
        patch("scripts.flux_lora.upload.HfApi", return_value=mock_api_instance),
        patch("scripts.flux_lora.upload.hf_hub_url", return_value=expected_url) as mock_url,
    ):
        result = upload_zip(
            zip_path,
            "skyyrose/test-dataset",
            confirmed=True,
        )

    assert result == expected_url
    assert result.startswith("https://")

    # Hub calls wired correctly
    mock_api_instance.create_repo.assert_called_once_with(
        repo_id="skyyrose/test-dataset",
        repo_type="dataset",
        exist_ok=True,
        private=False,
        token="hf_fake_token_for_test",
    )
    mock_api_instance.upload_file.assert_called_once()
    upload_call_kwargs = mock_api_instance.upload_file.call_args
    assert upload_call_kwargs.kwargs.get("repo_id") == "skyyrose/test-dataset"
    assert upload_call_kwargs.kwargs.get("repo_type") == "dataset"

    mock_url.assert_called_once_with(
        repo_id="skyyrose/test-dataset",
        filename="my-dataset.zip",
        repo_type="dataset",
    )


def test_confirmed_private_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """private=True passed through to create_repo."""
    zip_path = _make_zip(tmp_path, "private.zip")

    for var in _HF_TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("HF_TOKEN", "hf_fake_token_for_test")
    monkeypatch.setattr("scripts.flux_lora.upload.load_dotenv", _noop_load_dotenv)

    expected_url = "https://huggingface.co/datasets/skyyrose/private-repo/resolve/main/private.zip"

    mock_api_instance = MagicMock()
    with (
        patch("scripts.flux_lora.upload.HfApi", return_value=mock_api_instance),
        patch("scripts.flux_lora.upload.hf_hub_url", return_value=expected_url),
    ):
        upload_zip(zip_path, "skyyrose/private-repo", private=True, confirmed=True)

    mock_api_instance.create_repo.assert_called_once_with(
        repo_id="skyyrose/private-repo",
        repo_type="dataset",
        exist_ok=True,
        private=True,
        token="hf_fake_token_for_test",
    )


def test_custom_path_in_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """path_in_repo overrides default filename in hub calls."""
    zip_path = _make_zip(tmp_path, "source.zip")

    for var in _HF_TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("HF_TOKEN", "hf_fake_token_for_test")
    monkeypatch.setattr("scripts.flux_lora.upload.load_dotenv", _noop_load_dotenv)

    expected_url = "https://huggingface.co/datasets/skyyrose/test-ds/resolve/main/custom-name.zip"

    mock_api_instance = MagicMock()
    with (
        patch("scripts.flux_lora.upload.HfApi", return_value=mock_api_instance),
        patch("scripts.flux_lora.upload.hf_hub_url", return_value=expected_url) as mock_url,
    ):
        result = upload_zip(
            zip_path,
            "skyyrose/test-ds",
            path_in_repo="custom-name.zip",
            confirmed=True,
        )

    assert "custom-name.zip" in result
    # hf_hub_url called with custom filename
    mock_url.assert_called_once_with(
        repo_id="skyyrose/test-ds",
        filename="custom-name.zip",
        repo_type="dataset",
    )


# ---------------------------------------------------------------------------
# Missing token raises RuntimeError
# ---------------------------------------------------------------------------


def test_missing_token_raises_runtime_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    confirmed=True but no HF token in env → RuntimeError.

    Must pass confirmed=True so the RequiresConfirmationError gate doesn't fire
    first (which would mask the token error and give a misleading test result).
    """
    zip_path = _make_zip(tmp_path)

    # Remove all token sources
    for var in _HF_TOKEN_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr("scripts.flux_lora.upload.load_dotenv", _noop_load_dotenv)

    with patch("scripts.flux_lora.upload.HfApi") as mock_api_cls:
        with pytest.raises(RuntimeError, match="token"):
            upload_zip(zip_path, "skyyrose/test-dataset", confirmed=True)

        # No API calls before the token error
        mock_api_cls.assert_not_called()


def test_fallback_token_var_used(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """HUGGINGFACE_API_TOKEN fallback accepted when HF_TOKEN absent."""
    zip_path = _make_zip(tmp_path, "fallback.zip")

    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("HUGGINGFACE_API_TOKEN", "hf_fallback_token")
    monkeypatch.setattr("scripts.flux_lora.upload.load_dotenv", _noop_load_dotenv)

    expected_url = (
        "https://huggingface.co/datasets/skyyrose/fallback-repo/resolve/main/fallback.zip"
    )

    mock_api_instance = MagicMock()
    with (
        patch("scripts.flux_lora.upload.HfApi", return_value=mock_api_instance),
        patch("scripts.flux_lora.upload.hf_hub_url", return_value=expected_url),
    ):
        result = upload_zip(zip_path, "skyyrose/fallback-repo", confirmed=True)

    assert result.startswith("https://")
    mock_api_instance.create_repo.assert_called_once()
    # token passed to create_repo is the fallback token
    assert mock_api_instance.create_repo.call_args.kwargs["token"] == "hf_fallback_token"


# ---------------------------------------------------------------------------
# show_upload_stopandshow
# ---------------------------------------------------------------------------


def test_show_upload_stopandshow_prints_key_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """STOP-AND-SHOW output contains file path, repo, and proceed prompt."""
    zip_path = _make_zip(tmp_path, "test.zip")
    show_upload_stopandshow(zip_path, "skyyrose/my-dataset")

    out = capsys.readouterr().out
    assert str(zip_path.resolve()) in out or "test.zip" in out
    assert "skyyrose/my-dataset" in out
    assert "Proceed?" in out
    assert "STOP" in out
