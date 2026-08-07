"""Canonical component for the SkyyRose lookbook SOT chain.

This module owns the full chain for the ``wordpress-theme/skyyrose-flagship``
``lookbook`` component: explicit source manifest -> aggregated SOT -> HTML view.
It deliberately reads only the manifest's declared collection files during the
normal path, rather than walking the repository.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COLLECTIONS_DIR = ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "collections"
DEFAULT_MANIFEST_PATH = ROOT / "scripts" / "lookbook-manifest.json"
DEFAULT_LOOKBOOK_SOT_OUT = (
    ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "lookbook-sot.json"
)
DEFAULT_SOT_PATH = DEFAULT_LOOKBOOK_SOT_OUT
DEFAULT_LOOKBOOK_HTML_OUT = ROOT / "docs" / "campaigns" / "sot-lookbook.html"
DEFAULT_ASSET_BASE = "/wp-content/themes/skyyrose-flagship/assets"


def load_manifest_sources(
    manifest_file: Path,
) -> tuple[str | None, str | None, list[dict[str, Any]]]:
    """Load the explicit, ordered collection sources for this component."""
    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest missing: {manifest_file}")

    raw: Any = json.loads(manifest_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Manifest must be an object with sources.")
    sources = raw.get("sources")
    if not isinstance(sources, list):
        raise ValueError("Manifest sources must be an array.")

    collections: list[dict[str, Any]] = []
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise TypeError(f"Manifest source #{index} must be an object.")
        slug = (source.get("slug") or source.get("collection") or "").strip()
        sot_ref = (source.get("sot") or source.get("path") or "").strip()
        if not slug:
            raise ValueError(f"Manifest source #{index} missing slug/collection.")
        if not sot_ref:
            raise ValueError(f"Manifest source #{index} ({slug}) missing sot/path.")

        sot_file = Path(sot_ref)
        if not sot_file.is_absolute():
            sot_file = ROOT / sot_file
        if not sot_file.exists():
            raise FileNotFoundError(f"Manifest source #{index} SOT missing: {sot_file}")

        payload: Any = json.loads(sot_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError(f"Manifest source #{index} did not contain JSON object: {sot_file}")
        collection = dict(payload)
        collection["collection"] = slug
        collections.append(collection)

    return raw.get("domain"), raw.get("component"), collections


def load_collections_from_manifest(
    manifest_file: Path,
) -> tuple[str | None, str | None, list[dict[str, Any]]]:
    """Compatibility alias for the manifest-led normal path."""
    return load_manifest_sources(manifest_file)


def load_collections_from_dir(collections_dir: Path) -> list[dict[str, Any]]:
    """Fallback for explicit migration use; normal builds must use a manifest."""
    if not collections_dir.exists():
        raise FileNotFoundError(f"Collections directory missing: {collections_dir}")

    collections: list[dict[str, Any]] = []
    for folder in sorted(path for path in collections_dir.iterdir() if path.is_dir()):
        sot_file = folder / "sot.json"
        if not sot_file.exists():
            continue
        payload: Any = json.loads(sot_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError(f"Invalid SOT payload in {sot_file}")
        collection = dict(payload)
        collection["collection"] = folder.name
        collections.append(collection)
    return collections


def build_lookbook_payload(
    manifest_file: Path | None,
    domain: str | None = None,
    component: str | None = None,
    collections_dir: Path | None = None,
) -> dict[str, Any]:
    """Build the aggregated, deterministic lookbook component payload."""
    manifest_domain = manifest_component = None
    collections: list[dict[str, Any]] = []
    if manifest_file is not None:
        manifest_domain, manifest_component, collections = load_manifest_sources(manifest_file)
    if not collections and collections_dir is not None:
        collections = load_collections_from_dir(collections_dir)
    if not collections:
        raise RuntimeError("No collection SOTs found to aggregate.")
    return {
        "domain": domain or manifest_domain or "wordpress-theme/skyyrose-flagship",
        "component": component or manifest_component or "lookbook",
        "collections": collections,
    }


def serialize(payload: dict[str, Any]) -> str:
    """Return the sole byte format for the generated lookbook SOT."""
    return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def resolve_asset(asset_base: str, relative_path: str | None) -> str:
    if not relative_path:
        return ""
    return f"{asset_base.rstrip('/')}/{relative_path.lstrip('/')}"


def product_cover(images: dict[str, Any]) -> str:
    for key in ("front_model_image", "image", "packshot"):
        slot = images.get(key)
        if isinstance(slot, dict):
            path = slot.get("resolved") or slot.get("path")
            if path:
                return str(path)
    for slot in images.values():
        if isinstance(slot, dict):
            path = slot.get("resolved") or slot.get("path")
            if path:
                return str(path)
    return ""


def render_collection(slug: str, data: dict[str, Any], asset_base: str) -> str:
    lockup = ""
    if isinstance(data.get("lockup"), dict):
        lockup_entry = data["lockup"]
        lockup = (
            (lockup_entry.get("display_webp") or {}).get("resolved")
            or lockup_entry.get("canonical")
            or (lockup_entry.get("source_art") or {}).get("resolved")
            or ""
        )
    lockup_img = resolve_asset(asset_base, lockup) if lockup else ""
    palette = data.get("palette") or {}
    palette_items = "".join(
        f'<li><span style="background:{esc(color)}"></span>{esc(name)} — {esc(color)}</li>'
        for name, color in palette.items()
    )

    lookbook_items = ""
    for item in (data.get("imagery") or {}).get("lookbook", []) or []:
        path = resolve_asset(asset_base, item.get("resolved") or "")
        alt = item.get("notes") or f"{slug} lookbook"
        lookbook_items += (
            '<figure class="lookbook-frame">'
            f'<img src="{esc(path)}" alt="{esc(alt)}">'
            f"<figcaption>{esc(alt)}</figcaption></figure>"
        )

    product_items = ""
    for product in data.get("products", []) or []:
        images = product.get("images", {}) if isinstance(product, dict) else {}
        cover = resolve_asset(asset_base, product_cover(images))
        if not cover:
            continue
        price_text = f"${product.get('price', '')}"
        if product.get("is_preorder"):
            price_text += " · PRE-ORDER"
        product_items += (
            '<article class="product">'
            f'<img src="{esc(cover)}" alt="{esc(product.get("name", ""))}">'
            f"<div><strong>{esc(product.get('sku', ''))} — {esc(product.get('name', ''))}</strong>"
            f"<p>{esc(price_text)} · {esc(data.get('name', slug))}</p></div>"
            "</article>"
        )

    return f"""
    <section class="collection" id="{esc(slug)}">
      <header>
        {f'<img class="lockup" src="{esc(lockup_img)}" alt="{esc(data.get("name", slug))} lockup">' if lockup_img else ''}
        <div>
          <h2>{esc(str(data.get("name", slug)).title())}</h2>
          <p>{esc((data.get("story") or {}).get("seed", ""))}</p>
        </div>
      </header>
      <div class="grid two-col">
        <div>
          <h3>Palette</h3>
          <ul class="palette">{palette_items}</ul>
        </div>
        <div>
          <h3>Lookbook</h3>
          <div class="lookbook-grid">{lookbook_items or '<p>No lookbook scenes available.</p>'}</div>
        </div>
      </div>
      <h3>Pieces</h3>
      <div class="product-grid">{product_items or '<p>No product imagery available.</p>'}</div>
    </section>
    """


def build_html(collections: list[tuple[str, dict[str, Any]]], title: str, asset_base: str) -> str:
    sections = "".join(render_collection(slug, data, asset_base) for slug, data in collections)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    :root {{ color-scheme: dark; }}
    body {{ margin: 0; padding: 48px 20px; font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background: #0a0a0a; color: #f5f5f5; }}
    .page {{ max-width: 1180px; margin: 0 auto; }}
    h1 {{ margin: 0 0 28px; font-size: clamp(2rem, 4vw, 3.2rem); }}
    .collection {{ margin: 0 0 44px; padding-bottom: 28px; border-bottom: 1px solid #2a2a2a; }}
    .collection header {{ display: grid; grid-template-columns: 160px 1fr; gap: 24px; align-items: center; margin-bottom: 18px; }}
    .collection h2 {{ margin: 0 0 6px; }}
    .lockup {{ width: 160px; max-width: 100%; border-radius: 8px; background: #111; padding: 8px; }}
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
    .palette {{ list-style: none; padding: 0; margin: 8px 0 0; display: grid; gap: 8px; }}
    .palette li {{ display: flex; align-items: center; gap: 10px; color: #d6d6d6; }}
    .palette span {{ width: 15px; height: 15px; border: 1px solid #454; border-radius: 50%; display: inline-block; }}
    .lookbook-grid, .product-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; margin-top: 8px; }}
    .lookbook-frame img, .product img {{ width: 100%; display: block; object-fit: cover; border-radius: 10px; }}
    .lookbook-frame {{ background: #111; padding: 8px; border-radius: 12px; }}
    .lookbook-frame figcaption, .product p {{ color: #b8b8b8; font-size: 0.9rem; margin-top: 6px; }}
    .product {{ display: grid; grid-template-columns: 150px 1fr; gap: 12px; align-items: center; background: #111; border: 1px solid #262626; border-radius: 10px; padding: 10px; }}
    @media (max-width: 900px) {{
      .collection header, .product {{ grid-template-columns: 1fr; }}
      .two-col {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <h1>{esc(title)}</h1>
    {sections}
  </main>
</body>
</html>
"""


def normalize_collection_entries(raw: Any) -> list[tuple[str, dict[str, Any]]]:
    collection_entries = (
        raw if isinstance(raw, list) else raw.get("collections") if isinstance(raw, dict) else None
    )
    if not isinstance(collection_entries, list):
        raise TypeError("SOT must be an array or an object with a `collections` array.")
    output: list[tuple[str, dict[str, Any]]] = []
    for entry in collection_entries:
        if not isinstance(entry, dict):
            raise TypeError("Each collection entry in SOT must be an object.")
        slug = (entry.get("collection") or entry.get("slug") or "").strip()
        if not slug:
            raise ValueError("Each collection entry must include `collection` or `slug`.")
        data = dict(entry)
        data.pop("slug", None)
        output.append((slug, data))
    if not output:
        raise ValueError("No collection entries found in SOT.")
    return output


def build_title(sot: dict[str, Any], count: int) -> str:
    domain, component = sot.get("domain", ""), sot.get("component", "")
    if domain and component:
        return f"SkyyRose Lookbook ({domain} / {component} · {count} collections)"
    if domain:
        return f"SkyyRose Lookbook ({domain} · {count} collections)"
    return f"SkyyRose Lookbook ({count} collections)"


def build_lookbook_html(raw: Any, asset_base: str | None = None) -> tuple[str, int]:
    """Build the generated HTML without touching disk."""
    sot = raw if isinstance(raw, dict) else {"collections": raw}
    collections = normalize_collection_entries(sot)
    return build_html(
        collections, build_title(sot, len(collections)), asset_base or DEFAULT_ASSET_BASE
    ), len(collections)


def run_build_lookbook_sot(
    manifest_path: Path | None,
    domain: str | None = None,
    component: str | None = None,
    out_path: Path | None = None,
    collections_dir: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    payload = build_lookbook_payload(manifest_path, domain, component, collections_dir)
    target = out_path or DEFAULT_LOOKBOOK_SOT_OUT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialize(payload), encoding="utf-8")
    return payload, target


def run_build_lookbook_from_sot(
    sot_path: Path, out_path: Path | None = None, asset_base: str | None = None
) -> tuple[int, Path]:
    raw = json.loads(sot_path.read_text(encoding="utf-8"))
    rendered, count = build_lookbook_html(raw, asset_base)
    target = out_path or DEFAULT_LOOKBOOK_HTML_OUT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    return count, target


def parse_lookbook_sot_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build one aggregated lookbook SOT from an explicit source manifest."
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH))
    parser.add_argument(
        "--collections-dir",
        default=None,
        help="Explicit migration fallback; normal builds use --manifest.",
    )
    parser.add_argument("--domain", default=None)
    parser.add_argument("--component", default=None)
    parser.add_argument("--out", default=str(DEFAULT_LOOKBOOK_SOT_OUT))
    return parser.parse_args()


def parse_lookbook_from_sot_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a lookbook page from one SOT document.")
    parser.add_argument("--sot", default=str(DEFAULT_SOT_PATH))
    parser.add_argument("--asset-base", default=DEFAULT_ASSET_BASE)
    parser.add_argument("--out", default=str(DEFAULT_LOOKBOOK_HTML_OUT))
    return parser.parse_args()
