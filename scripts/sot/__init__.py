"""SOT component modules.

This package owns domain-specific source-of-truth builders for catalog artifacts.
"""

from .lookbook import (
    DEFAULT_ASSET_BASE,
    DEFAULT_LOOKBOOK_SOT_OUT,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_SOT_PATH,
    build_lookbook_html,
    build_lookbook_payload,
    build_title,
    load_collections_from_dir,
    load_collections_from_manifest,
    load_manifest_sources,
    normalize_collection_entries,
    parse_lookbook_from_sot_args,
    parse_lookbook_sot_args,
    product_cover,
    run_build_lookbook_from_sot,
    run_build_lookbook_sot,
    serialize,
)

__all__ = [
    "DEFAULT_ASSET_BASE",
    "DEFAULT_LOOKBOOK_SOT_OUT",
    "DEFAULT_MANIFEST_PATH",
    "DEFAULT_SOT_PATH",
    "build_lookbook_html",
    "build_lookbook_payload",
    "build_title",
    "load_collections_from_dir",
    "load_collections_from_manifest",
    "load_manifest_sources",
    "normalize_collection_entries",
    "parse_lookbook_from_sot_args",
    "parse_lookbook_sot_args",
    "product_cover",
    "run_build_lookbook_from_sot",
    "run_build_lookbook_sot",
    "serialize",
]
