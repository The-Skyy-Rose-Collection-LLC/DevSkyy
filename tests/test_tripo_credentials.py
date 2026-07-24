"""
Tests for Tripo3D Multi-Account / Multi-Region Credential Resolution
======================================================================

Covers agents.tripo_credentials.resolve_tripo_credentials() and its helpers:
- Single valid key resolves on the first region it has balance on.
- A key that fails on .ai but has balance on .com falls through correctly.
- TRIPO_API_KEYS (csv) probes every candidate and resolves to the one with
  the HIGHEST balance, not the first non-zero one.
- Missing configuration and SDK-unavailable failure modes fail closed with
  ConfigurationError.

All tests run against a fake `tripo3d` module injected into `sys.modules` —
zero real network calls, zero real API keys.
"""

from __future__ import annotations

import sys
import types
from typing import Any

import pytest

from agents.errors import ConfigurationError
from agents.tripo_credentials import (
    _collect_candidate_keys,
    mask_api_key,
    resolve_tripo_credentials,
)

# =============================================================================
# Fake tripo3d SDK
# =============================================================================


class _FakeBalance:
    """Mimics the tripo3d SDK's Balance response object."""

    def __init__(self, balance: float, frozen: float = 0.0) -> None:
        self.balance = balance
        self.frozen = frozen


def _make_fake_tripo_module(
    balance_table: dict[tuple[str, bool], float | Exception],
) -> types.ModuleType:
    """Build a fake `tripo3d` module whose TripoClient is keyed by (api_key, IS_GLOBAL).

    A (key, region) combo absent from `balance_table` simulates an auth
    failure (401) on that combo, matching real Tripo3D behavior for a key
    bound to the other region.
    """

    class _FakeTripoClient:
        def __init__(self, api_key: str, IS_GLOBAL: bool) -> None:
            self.api_key = api_key
            self.is_global = IS_GLOBAL

        async def __aenter__(self) -> _FakeTripoClient:
            return self

        async def __aexit__(self, *exc_info: Any) -> bool:
            return False

        async def get_balance(self) -> _FakeBalance:
            outcome = balance_table.get((self.api_key, self.is_global))
            if isinstance(outcome, Exception):
                raise outcome
            if outcome is None:
                raise RuntimeError("401 Unauthorized: key not valid for this region")
            return _FakeBalance(balance=outcome)

    module = types.ModuleType("tripo3d")
    module.TripoClient = _FakeTripoClient  # type: ignore[attr-defined]
    return module


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def _clear_tripo_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no real Tripo env vars leak into resolver tests."""
    for var in ("TRIPO_API_KEYS", "TRIPO_API_KEY", "TRIPO3D_API_KEY", "TRIPO_API_BASE_URL"):
        monkeypatch.delenv(var, raising=False)


# =============================================================================
# resolve_tripo_credentials()
# =============================================================================


@pytest.mark.asyncio
class TestResolveTripoCredentials:
    """Multi-account / multi-region resolution — zero real network calls."""

    async def test_single_valid_key_on_global_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A single key with balance on .ai (global) resolves immediately."""
        fake_module = _make_fake_tripo_module({("tsk_onlyvalidkey1", True): 42.5})
        monkeypatch.setitem(sys.modules, "tripo3d", fake_module)

        creds = await resolve_tripo_credentials(candidate_keys=["tsk_onlyvalidkey1"])

        assert creds.api_key == "tsk_onlyvalidkey1"
        assert creds.is_global is True
        assert creds.balance == 42.5
        assert creds.base_url == "https://api.tripo3d.ai/v2"

    async def test_key_falls_through_to_china_region(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A key that's 401/0-balance on .ai but valid on .com falls through correctly."""
        # (key, True) is intentionally absent from the table -> simulated 401 on .ai.
        fake_module = _make_fake_tripo_module({("tsk_chinaonlykey1", False): 17.0})
        monkeypatch.setitem(sys.modules, "tripo3d", fake_module)

        creds = await resolve_tripo_credentials(candidate_keys=["tsk_chinaonlykey1"])

        assert creds.api_key == "tsk_chinaonlykey1"
        assert creds.is_global is False
        assert creds.balance == 17.0
        assert creds.base_url == "https://api.tripo3d.com/v2"

    async def test_csv_multiple_candidates_picks_highest_balance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """TRIPO_API_KEYS csv probes every candidate and resolves to the HIGHEST
        balance found — not the first non-zero one — so a low-balance account
        never wins over another configured account that holds more credit
        (matters for callers gating spend on `--max-cost`)."""
        fake_module = _make_fake_tripo_module(
            {
                ("tsk_firstkeyzero1", True): 0.0,
                ("tsk_firstkeyzero1", False): 0.0,
                ("tsk_secondkeygood1", True): 5.0,
                ("tsk_thirdbestkey1", True): 999.0,
            }
        )
        monkeypatch.setitem(sys.modules, "tripo3d", fake_module)
        monkeypatch.setenv(
            "TRIPO_API_KEYS",
            "tsk_firstkeyzero1,tsk_secondkeygood1,tsk_thirdbestkey1",
        )

        creds = await resolve_tripo_credentials()

        assert creds.api_key == "tsk_thirdbestkey1"
        assert creds.balance == 999.0

    async def test_no_key_configured_raises_configuration_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No TRIPO_API_KEYS / TRIPO_API_KEY / TRIPO3D_API_KEY set -> fail closed."""
        with pytest.raises(ConfigurationError, match="No Tripo API key configured"):
            await resolve_tripo_credentials()

    async def test_empty_candidate_list_fails_even_with_env_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicitly empty candidate_keys list is honored, ignoring env vars."""
        monkeypatch.setenv("TRIPO_API_KEY", "tsk_envkeythatexists")

        with pytest.raises(ConfigurationError, match="No Tripo API key configured"):
            await resolve_tripo_credentials(candidate_keys=[])

    async def test_sdk_not_installed_raises_configuration_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """tripo3d SDK unavailable -> fail closed, never a silent 0-balance result."""
        # `None` in sys.modules forces Python's import system to raise ImportError.
        monkeypatch.setitem(sys.modules, "tripo3d", None)

        with pytest.raises(ConfigurationError, match="tripo3d SDK not installed"):
            await resolve_tripo_credentials(candidate_keys=["tsk_somekey0001234"])

    async def test_no_candidate_has_balance_raises_configuration_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Every key+region combo auth-fails or has zero balance -> fail closed."""
        fake_module = _make_fake_tripo_module({})  # every combo simulates a 401
        monkeypatch.setitem(sys.modules, "tripo3d", fake_module)

        with pytest.raises(ConfigurationError, match="No Tripo account with credits"):
            await resolve_tripo_credentials(candidate_keys=["tsk_brokekey0001234"])

    async def test_never_returns_credentials_with_zero_balance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A key with auth_ok but balance == 0 must not be returned as usable."""
        fake_module = _make_fake_tripo_module(
            {("tsk_zerobalancekey1", True): 0.0, ("tsk_zerobalancekey1", False): 0.0}
        )
        monkeypatch.setitem(sys.modules, "tripo3d", fake_module)

        with pytest.raises(ConfigurationError, match="No Tripo account with credits"):
            await resolve_tripo_credentials(candidate_keys=["tsk_zerobalancekey1"])


# =============================================================================
# _collect_candidate_keys()
# =============================================================================


class TestCollectCandidateKeys:
    """Env-var candidate collection: de-duplication, tsk_ filtering, ordering."""

    def test_dedupes_and_preserves_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRIPO_API_KEYS", "tsk_aaaa1111,tsk_bbbb2222,tsk_aaaa1111")
        monkeypatch.setenv("TRIPO_API_KEY", "tsk_bbbb2222")

        assert _collect_candidate_keys() == ["tsk_aaaa1111", "tsk_bbbb2222"]

    def test_appends_single_key_env_var_if_not_already_present(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TRIPO_API_KEYS", "tsk_fromcsv0001")
        monkeypatch.setenv("TRIPO3D_API_KEY", "tsk_fromsingle01")

        assert _collect_candidate_keys() == ["tsk_fromcsv0001", "tsk_fromsingle01"]

    def test_filters_non_tsk_prefixed_keys(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TRIPO_API_KEYS", "not-a-tripo-key,tsk_validkey0001")

        assert _collect_candidate_keys() == ["tsk_validkey0001"]

    def test_no_env_vars_returns_empty_list(self) -> None:
        assert _collect_candidate_keys() == []


# =============================================================================
# mask_api_key()
# =============================================================================


class TestMaskApiKey:
    """Never log a full API key — first4...last4 only."""

    def test_masks_to_first4_and_last4(self) -> None:
        assert mask_api_key("tsk_abcdefgh1234") == "tsk_...1234"

    def test_short_key_fully_masked(self) -> None:
        assert mask_api_key("short") == "***"

    def test_masked_output_never_contains_the_middle_of_the_key(self) -> None:
        key = "tsk_supersecretmiddlepart9999"
        masked = mask_api_key(key)
        assert "supersecretmiddlepart" not in masked


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
