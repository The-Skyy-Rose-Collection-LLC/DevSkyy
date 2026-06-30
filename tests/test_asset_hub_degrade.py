"""asset_hub graceful-degradation test — runs REGARDLESS of manifest presence.

The hub manifest lives under the gitignored ``assets/hub/`` tree, so on a fresh
checkout / CI it is absent. asset_hub must degrade to "no verified assets" rather
than crash — this is what keeps hard importers (e.g. ``build-collection-sot.py``,
which imports ``served_theme_path``) safe on a manifest-less environment.

Unlike ``test_asset_hub.py`` (which asserts the contract against the LIVE manifest
and is skipped when absent), this test fabricates the absent-manifest condition with
monkeypatch, so it needs no real manifest and always runs.
"""

from __future__ import annotations

import json

import pytest

import skyyrose.core.asset_hub as hub


def test_missing_manifest_degrades(monkeypatch, tmp_path):
    """A non-existent manifest path → empty manifest + None resolutions, no exception."""
    monkeypatch.setattr(hub, "_MANIFEST_PATH", tmp_path / "does-not-exist.json")
    hub.refresh()  # drop any cached real manifest
    try:
        assert hub.manifest() == {}
        assert hub.resolve("br-001", "front") is None
        assert hub.served_theme_path("br-001", "front") is None
        assert hub.by_usage("product-card") == []
        assert hub.pending() == []
        assert hub.verify_integrity() == []
    finally:
        hub.refresh()  # restore cache state for other tests


def test_corrupt_manifest_raises(monkeypatch, tmp_path):
    """A malformed manifest (JSONDecodeError) MUST propagate loudly, not degrade to {}.

    Absent → {} is truthful ("nothing promoted yet"); corrupt → {} would silently mask a
    data-integrity failure. The guard catches only FileNotFoundError on purpose — this test
    pins that intent so a future broadening of the except clause is caught.
    """
    bad = tmp_path / "bad.json"
    bad.write_text("not valid json")
    monkeypatch.setattr(hub, "_MANIFEST_PATH", bad)
    hub.refresh()
    try:
        with pytest.raises(json.JSONDecodeError):
            hub.manifest()
    finally:
        hub.refresh()
