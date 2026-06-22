"""Deprecated entry-point shim — delegates to `python -m skyyrose.elite_studio`.

The SkyyRose rendering pipeline has ONE canonical CLI:

    python -m skyyrose.elite_studio <subcommand> [args]

This module preserves the legacy `python -m renders <verb>` surface by
translating its verbs into the canonical ones and delegating. Update scripts
to call `skyyrose.elite_studio` directly when convenient; this shim will be
removed once the broken `renders/{pipeline,fashn_client,wc_client}.py`
modules are deleted.

Verb translation:

    renders sku <id>                -> skyyrose.elite_studio produce <id>
    renders collection BLACK_ROSE   -> skyyrose.elite_studio produce-batch --sku br
    renders collection LOVE_HURTS   -> skyyrose.elite_studio produce-batch --sku lh
    renders collection SIGNATURE    -> skyyrose.elite_studio produce-batch --sku sg
    renders collection KIDS_CAPSULE -> skyyrose.elite_studio produce-batch --sku kc
    renders all                     -> skyyrose.elite_studio produce-batch --all
    renders catalog                 -> skyyrose.elite_studio catalog
    renders status                  -> skyyrose.elite_studio status
    renders sync                    -> deprecated; no canonical replacement yet
    renders credits                 -> deprecated; no canonical replacement yet
"""

from __future__ import annotations

import sys
import warnings

_COLLECTION_TO_SKU_PREFIX = {
    "BLACK_ROSE": "br",
    "LOVE_HURTS": "lh",
    "SIGNATURE": "sg",
    "KIDS_CAPSULE": "kc",
}

_LEGACY_NOT_PORTED = {"sync", "credits"}


def _translate_argv(argv: list[str]) -> list[str]:
    """Translate legacy `renders` argv into canonical `skyyrose.elite_studio` argv.

    Returns a new list. Pure transformation; does not mutate the input.
    """
    if not argv:
        return argv

    verb = argv[0]
    rest = argv[1:]

    if verb == "sku":
        return ["produce", *rest]
    if verb == "collection":
        if not rest:
            print("error: `collection` requires a collection name", file=sys.stderr)
            sys.exit(2)
        collection_name = rest[0]
        prefix = _COLLECTION_TO_SKU_PREFIX.get(collection_name)
        if prefix is None:
            print(
                f"error: unknown collection {collection_name!r}; "
                f"valid: {sorted(_COLLECTION_TO_SKU_PREFIX)}",
                file=sys.stderr,
            )
            sys.exit(2)
        return ["produce-batch", "--sku", prefix, *rest[1:]]
    if verb == "all":
        return ["produce-batch", "--all", *rest]
    if verb in {"catalog", "status"}:
        return [verb, *rest]
    if verb in _LEGACY_NOT_PORTED:
        print(
            f"error: `renders {verb}` is not ported to the canonical CLI yet. "
            "FASHN credits + WC sync are tracked under the Elite Team metering sub-spec.",
            file=sys.stderr,
        )
        sys.exit(2)
    # Unknown verb — pass through; canonical CLI will produce its own error.
    return argv


def main() -> None:
    warnings.warn(
        "`python -m renders ...` is deprecated; use "
        "`python -m skyyrose.elite_studio ...` directly.",
        DeprecationWarning,
        stacklevel=2,
    )
    translated = _translate_argv(sys.argv[1:])
    from skyyrose.elite_studio.cli import main as canonical_main

    canonical_main(translated)


if __name__ == "__main__":
    main()
