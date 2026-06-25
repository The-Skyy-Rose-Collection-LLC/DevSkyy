"""Tests for the dynamic module loader."""

from __future__ import annotations

import sys
import types

import pytest

from aos.modules.loader import ModuleLoadError, load_from_path
from aos.modules.types import ModuleManifest


async def _noop_factory() -> object:
    return object()


def _make_fake_module(
    module_path: str,
    *,
    manifest: object = None,
    factories: object = None,
    set_manifest: bool = True,
    set_factories: bool = True,
) -> types.ModuleType:
    """Inject a fake module into sys.modules and return it."""
    mod = types.ModuleType(module_path)
    if set_manifest:
        mod.AOS_MODULE_MANIFEST = manifest  # type: ignore[attr-defined]
    if set_factories:
        mod.AOS_MODULE_FACTORIES = factories  # type: ignore[attr-defined]
    sys.modules[module_path] = mod
    return mod


@pytest.fixture(autouse=True)
def cleanup_fake_modules():
    """Remove any test-injected fake modules after each test."""
    keys_before = set(sys.modules)
    yield
    for key in list(sys.modules):
        if key not in keys_before:
            del sys.modules[key]


class TestLoadFromPath:
    def test_valid_module_returns_manifest_and_factories(self):
        manifest = ModuleManifest(name="commerce", version="1.0", agent_types=("buyer",))
        _make_fake_module("fake.commerce", manifest=manifest, factories={"buyer": _noop_factory})

        result_manifest, result_factories = load_from_path("fake.commerce")

        assert result_manifest is manifest
        assert result_factories == {"buyer": _noop_factory}

    def test_unknown_path_raises_module_load_error(self):
        with pytest.raises(ModuleLoadError, match="fake.nonexistent"):
            load_from_path("fake.nonexistent")

    def test_missing_manifest_raises_module_load_error(self):
        _make_fake_module(
            "fake.no_manifest",
            set_manifest=False,
            factories={"x": _noop_factory},
        )
        with pytest.raises(ModuleLoadError, match="AOS_MODULE_MANIFEST"):
            load_from_path("fake.no_manifest")

    def test_wrong_manifest_type_raises_module_load_error(self):
        _make_fake_module(
            "fake.bad_manifest",
            manifest="not-a-manifest",
            factories={"x": _noop_factory},
        )
        with pytest.raises(ModuleLoadError, match="AOS_MODULE_MANIFEST"):
            load_from_path("fake.bad_manifest")

    def test_missing_factories_raises_module_load_error(self):
        manifest = ModuleManifest(name="x", version="1.0", agent_types=())
        _make_fake_module("fake.no_factories", manifest=manifest, set_factories=False)
        with pytest.raises(ModuleLoadError, match="AOS_MODULE_FACTORIES"):
            load_from_path("fake.no_factories")

    def test_wrong_factories_type_raises_module_load_error(self):
        manifest = ModuleManifest(name="x", version="1.0", agent_types=())
        _make_fake_module("fake.bad_factories", manifest=manifest, factories="not-a-dict")
        with pytest.raises(ModuleLoadError, match="AOS_MODULE_FACTORIES"):
            load_from_path("fake.bad_factories")

    def test_module_load_error_is_import_error_subclass(self):
        with pytest.raises(ImportError):
            load_from_path("fake.nonexistent.again")
