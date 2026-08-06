#!/usr/bin/env python3
"""Generate a lightweight editorial lookbook from a single SOT document.

Default behavior:
  python3 scripts/build-lookbook-from-sot.py
  # reads wordpress-theme/skyyrose-flagship/data/lookbook-sot.json

The input SOT may be one of:
  1) {"collections": [ ... ]}
  2) [ ... ]
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOT_PATH = ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "lookbook-sot.json"
DEFAULT_ASSET_BASE = "/wp-content/themes/skyyrose-flagship/assets"


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def resolve_asset(asset_base: str, rel: str | None) -> str:
    if not rel:
        return ""
    return f"{asset_base.rstrip('/')}/{rel.lstrip('/')}"


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

    products = data.get("products", []) or []
    product_items = ""
    for p in products:
        images = p.get("images", {}) if isinstance(p, dict) else {}
        cover = resolve_asset(asset_base, product_cover(images))
        if not cover:
            continue
        price = p.get("price", "")
        price_text = f"${price}"
        if p.get("is_preorder"):
            price_text += " · PRE-ORDER"
        product_items += (
            '<article class="product">'
            f"<img src=\"{esc(cover)}\" alt=\"{esc(p.get('name', ''))}\">"
            f"<div><strong>{esc(p.get('sku', ''))} — {esc(p.get('name', ''))}</strong>"
            f"<p>{esc(price_text)} · {esc(data.get('name', slug))}</p></div>"
            "</article>"
        )

    return f"""
    <section class="collection" id="{esc(slug)}">
      <header>
        {f'<img class="lockup" src="{esc(lockup_img)}" alt="{esc(data.get("name", slug))} lockup">' if lockup_img else ''}
        <div>
          <h2>{esc(data.get("name", slug)).title()}</h2>
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


def build_html(
    collections: list[tuple[str, dict[str, Any]]],
    title: str,
    asset_base: str,
) -> str:
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


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate a lookbook page from one SOT document")
    p.add_argument(
        "--sot",
        default=str(DEFAULT_SOT_PATH),
        help="Single SOT JSON source containing all collections.",
    )
    p.add_argument(
        "--asset-base",
        default=DEFAULT_ASSET_BASE,
        help="Theme assets prefix used in generated image src paths.",
    )
    p.add_argument(
        "--out",
        default="docs/campaigns/sot-lookbook.html",
        help="Output HTML path.",
    )
    return p.parse_args()


def normalize_collection_entries(raw: Any) -> list[tuple[str, dict[str, Any]]]:
    if isinstance(raw, list):
        collection_entries = raw
    elif isinstance(raw, dict):
        if "collections" not in raw:
            raise ValueError("SOT must contain a `collections` array.")
        collection_entries = raw["collections"]
    else:
        raise TypeError("SOT must be JSON array or object with `collections` array.")

    if not isinstance(collection_entries, list):
        raise TypeError("SOT `collections` must be an array.")

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
    domain = sot.get("domain", "")
    component = sot.get("component", "")
    if domain and component:
        return f"SkyyRose Lookbook ({domain} / {component} · {count} collections)"
    if domain:
        return f"SkyyRose Lookbook ({domain} · {count} collections)"
    return f"SkyyRose Lookbook ({count} collections)"


def build_lookbook_html(raw: Any, asset_base: str | None = None) -> tuple[str, int]:
    """Build generated lookbook HTML without touching disk."""
    if not isinstance(raw, dict):
        raw = {"collections": raw}
    collections = normalize_collection_entries(raw)
    count = len(collections)
    title = build_title(raw, count)
    return build_html(collections, title, asset_base or DEFAULT_ASSET_BASE), count


def main() -> int:
    args = parse_args()
    out = Path(args.out)
    raw = json.loads(Path(args.sot).read_text(encoding="utf-8"))
    html, count = build_lookbook_html(raw, args.asset_base)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({count} collections)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
