"""Static HTML review gallery for OAI renders.

Scans renders/oai and emits renders/oai/_review/index.html with every render
grouped by product slug (ghost / ghost-back / on-model columns) so a human or
a Playwright-driven visual QA pass can sweep the full batch in one page.

Usage:
    python scripts/oai_render/gallery.py
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from oai_render import config
else:
    from . import config

STYLE_ORDER = ("ghost", "ghost-back", "on-model")
EXCLUDED_NAMES = {"front.png"}

_CSS = """
body { background:#0A0A0A; color:#EDEDED; font:14px/1.4 -apple-system, sans-serif;
       margin:0; padding:24px; }
h1 { color:#C9A24B; font-size:20px; margin:0 0 4px; }
.meta { color:#888; margin-bottom:24px; }
.product { margin-bottom:28px; border-bottom:1px solid #222; padding-bottom:20px; }
.product h2 { font-size:15px; color:#C9A24B; margin:0 0 10px; font-weight:600; }
.row { display:flex; gap:14px; flex-wrap:wrap; }
.card { width:230px; }
.card img { width:230px; height:288px; object-fit:contain; background:#161616;
            border:1px solid #2A2A2A; border-radius:4px; display:block; }
.card .label { color:#AAA; font-size:12px; margin-top:4px; text-align:center; }
.card .label .path { color:#555; font-size:10px; display:block; word-break:break-all; }
"""


def collect(render_root: Path) -> dict[str, list[Path]]:
    """Map product slug -> sorted list of render PNGs."""
    products: dict[str, list[Path]] = {}
    for png in sorted(render_root.glob("*/*.png")):
        if png.name in EXCLUDED_NAMES or png.parent.name.startswith("_"):
            continue
        products.setdefault(png.parent.name, []).append(png)
    return products


def _style_key(path: Path) -> int:
    stem = path.stem
    return STYLE_ORDER.index(stem) if stem in STYLE_ORDER else len(STYLE_ORDER)


def build_html(products: dict[str, list[Path]], render_root: Path) -> str:
    n_images = sum(len(v) for v in products.values())
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<title>OAI Render Review</title>",
        f"<style>{_CSS}</style></head><body>",
        "<h1>OAI Render Review Gallery</h1>",
        f"<p class='meta'>{len(products)} products &middot; {n_images} renders "
        f"&middot; source: {html.escape(str(render_root))}</p>",
    ]
    for slug in sorted(products):
        parts.append("<section class='product'>")
        parts.append(f"<h2>{html.escape(slug)}</h2><div class='row'>")
        for png in sorted(products[slug], key=_style_key):
            rel = f"../{png.parent.name}/{png.name}"
            parts.append(
                "<figure class='card' style='margin:0'>"
                f"<img loading='eager' src='{html.escape(rel)}' alt='{html.escape(slug)} {html.escape(png.stem)}'>"
                f"<figcaption class='label'>{html.escape(png.stem)}"
                f"<span class='path'>{html.escape(png.parent.name)}/{html.escape(png.name)}</span>"
                "</figcaption></figure>"
            )
        parts.append("</div></section>")
    parts.append("</body></html>")
    return "".join(parts)


def main() -> int:
    render_root = config.OUTPUT_DIR
    products = collect(render_root)
    if not products:
        print(f"No renders found under {render_root}", file=sys.stderr)
        return 1
    out_dir = render_root / "_review"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"
    out_path.write_text(build_html(products, render_root), encoding="utf-8")
    n_images = sum(len(v) for v in products.values())
    print(f"Wrote {out_path} ({len(products)} products, {n_images} renders)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
