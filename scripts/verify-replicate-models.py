#!/usr/bin/env python3
"""Free Replicate model-provenance verifier (NO predictions = NO spend).

Confirms that the models we depend on actually exist on Replicate and reports
their provenance, so a model id copied from source code can never be trusted
blindly:

  • black-forest-labs/flux-1.1-pro-ultra  — the hero-scene engine (must resolve
    before any paid hero run)
  • devskyy/skyyrose-lora-v3              — the repo's claimed product LoRA
    (llm/providers/replicate.py:76), including the pinned version hash

Keys are read at runtime from .env.hf by python-dotenv — never printed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env.hf", override=False)
except Exception as exc:  # pragma: no cover
    print(f"FATAL: could not load .env.hf ({exc})", file=sys.stderr)
    raise SystemExit(2)

import replicate  # noqa: E402

# The repo-claimed product LoRA + the exact pinned version (replicate.py:76).
PRODUCT_LORA = "devskyy/skyyrose-lora-v3"
PINNED_VERSION = "64dbb859fed83670e7cde81fc161c183bd9d0607fb7028b01bfc0a000ec114b4"
HERO_ENGINE = "black-forest-labs/flux-1.1-pro-ultra"


def _line(label: str, value: object) -> None:
    print(f"    {label:<16}: {value}")


def whoami() -> None:
    token = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    print("== Replicate auth ==")
    if not token:
        print("    REPLICATE_API_TOKEN: ✗ MISSING")
        return
    print("    REPLICATE_API_TOKEN: ✓ present")
    try:
        acct = replicate.Client(api_token=token).accounts.current()
        _line("account", f"{acct.username} ({acct.type})")
    except Exception as exc:  # noqa: BLE001 — drop str(exc); SDK error chains can echo the token
        _line("account", f"could not resolve ({type(exc).__name__})")
    print()


def describe_model(ref: str, *, label: str) -> bool:
    print(f"== {label}: {ref} ==")
    try:
        model = replicate.models.get(ref)
    except Exception as exc:  # noqa: BLE001
        print(f"    ✗ DOES NOT RESOLVE — {type(exc).__name__}\n")
        return False
    _line("exists", "✓")
    _line("owner", model.owner)
    _line("visibility", model.visibility)
    _line("run_count", getattr(model, "run_count", "?"))
    desc = (model.description or "").strip()
    _line("description", (desc[:90] + "…") if len(desc) > 90 else (desc or "(none)"))
    _line("github_url", getattr(model, "github_url", None) or "(none)")
    _line("cover_image", "yes" if getattr(model, "cover_image_url", None) else "no")
    latest = getattr(model, "latest_version", None)
    _line("latest_version", latest.id if latest else "(none)")
    if latest is not None:
        _line("latest_created", getattr(latest, "created_at", "?"))
    print()
    return True


def check_pinned_version(ref: str, version_id: str) -> None:
    print(f"== Pinned version check: {ref}:{version_id[:12]}… ==")
    try:
        model = replicate.models.get(ref)
        version = model.versions.get(version_id)
    except Exception as exc:  # noqa: BLE001
        print(f"    ✗ version NOT found — {type(exc).__name__}\n")
        return
    _line("version_exists", "✓")
    _line("created_at", getattr(version, "created_at", "?"))
    schema = getattr(version, "openapi_schema", None) or {}
    title = schema.get("info", {}).get("title") if isinstance(schema, dict) else None
    _line("schema_title", title or "(none)")
    print()


def main() -> int:
    whoami()
    hero_ok = describe_model(HERO_ENGINE, label="HERO ENGINE")
    lora_ok = describe_model(PRODUCT_LORA, label="PRODUCT LORA (claimed)")
    if lora_ok:
        check_pinned_version(PRODUCT_LORA, PINNED_VERSION)

    print("== VERDICT ==")
    print(
        f"    hero engine resolves : {'✓ safe to run paid heroes' if hero_ok else '✗ FIX SLUG before paid run'}"
    )
    print(
        "    product LoRA real    : "
        + (
            "✓ model id is NOT hallucinated"
            if lora_ok
            else "✗ claimed LoRA does NOT exist under this token"
        )
    )
    return 0 if hero_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
