#!/usr/bin/env python3
"""
inject-explore-products.py
Injects real SkyyRose product data into the 3D-Scenes explore HTML files
and applies drakerelated.com-style enhancements.
"""

import json
import re
import os
import sys

# ── Product Data ──────────────────────────────────────────────────────────────

PRODUCTS_BLACK_ROSE = [
  {"id":"br-001","name":"BLACK Rose Crewneck","collection":"BLACK ROSE","badge":"PRE-ORDER","price":"$125","desc":"Gothic luxury blooms in twilight. Embroidered with defiant elegance, a dark romance woven in every thread.","detail":"Premium Cotton • Relaxed Oversized Fit • Machine Wash Cold","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"Black","hex":"#000000"}],"image":"assets/images/products/br-001/br-001-model.jpg","x":22,"y":62},
  {"id":"br-006","name":"BLACK Rose Sherpa Jacket","collection":"BLACK ROSE","badge":"PRE-ORDER","price":"$295","desc":"Unveil your dark allure. Lustrous black satin with plush Sherpa lining, crowned by exquisite embroidered rose.","detail":"Satin Shell • Sherpa Lining • Embroidered Rose","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"Black","hex":"#000000"}],"image":"assets/images/products/br-006/br-006-model.jpg","x":50,"y":28},
  {"id":"br-003","name":"BLACK is Beautiful Jersey","collection":"BLACK ROSE","badge":"PRE-ORDER","price":"$110","desc":"Dare to bloom in defiant elegance — where gothic luxury meets a powerful message, stitched in streetwise style.","detail":"Premium Mesh • Button-Down Jersey • Sizes S–3XL","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"Last Oakland","hex":"#1B4D1B"},{"name":"Giants","hex":"#27251F"}],"image":"assets/images/products/br-003/br-003-model.jpg","x":76,"y":44},
  {"id":"br-002","name":"BLACK Rose Joggers","collection":"BLACK ROSE","badge":"PRE-ORDER","price":"$95","desc":"Twilight comfort meets gothic romance. Embroidered black roses bloom on soft fabric made for those who move in darkness.","detail":"Premium Soft-Touch Fabric • Tapered Fit • Machine Wash","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"Black","hex":"#000000"}],"image":"assets/images/products/br-002/br-002-model.jpg","x":35,"y":46},
  {"id":"br-004","name":"BLACK Rose Hoodie","collection":"BLACK ROSE","badge":"PRE-ORDER","price":"$145","desc":"Gothic luxury in twilight shadows. Intricate embroidery captures the bloom of darkness — a defiant statement.","detail":"Premium Cotton Fleece • Kangaroo Pocket • Drawstring Hood","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"Black","hex":"#000000"}],"image":"assets/images/products/br-004/br-004-model.jpg","x":63,"y":68},
  {"id":"br-008","name":"Women's BLACK Rose Hooded Dress","collection":"BLACK ROSE","badge":"PRE-ORDER","price":"$175","desc":"Unleash your inner darkness. Intricate black rose embroidery and a silhouette of gothic mystery.","detail":"Premium Fabric • Attached Hood • Embroidered Rose","sizes":["XS","S","M","L","XL","2XL"],"colors":[{"name":"Black","hex":"#000000"}],"image":"assets/images/products/br-008/br-008-model.jpg","x":86,"y":24},
]

PRODUCTS_LOVE_HURTS = [
  {"id":"lh-001","name":"The Fannie","collection":"LOVE HURTS","badge":"PRE-ORDER","price":"$65","desc":"A luxury fanny pack embodying Oakland grit, passion, and the defiant bloom of a street rose.","detail":"Premium Fabric • Adjustable Strap • Rose Embroidery","sizes":["One Size"],"colors":[{"name":"Black","hex":"#000000"}],"image":"assets/images/products/lh-001/lh-001-model.jpg","x":48,"y":50},
  {"id":"lh-002","name":"Love Hurts Joggers","collection":"LOVE HURTS","badge":"AVAILABLE","price":"$95","desc":"Where Oakland grit meets luxury. Feel the fire with the embroidered rose, a symbol of passion forged in the streets.","detail":"Premium Fabric • Tapered Fit • Zippered Ankles","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"Black","hex":"#000000"},{"name":"White","hex":"#F5F5F5"}],"image":"assets/images/products/lh-002/lh-002-model.jpg","x":18,"y":42},
  {"id":"lh-004","name":"Love Hurts Varsity Jacket","collection":"LOVE HURTS","badge":"PRE-ORDER","price":"$265","desc":"Oakland grit meets broken hearts. Black satin, fire-red script, secret rose garden. Pre-order your battle armor.","detail":"Black Satin Shell • Rose-Lined Hood • Bold Script","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"Black/Red","hex":"#1A1A1A"}],"image":"assets/images/products/lh-001/lh-001-model.jpg","x":73,"y":34},
  {"id":"lh-003","name":"Love Hurts Basketball Shorts","collection":"LOVE HURTS","badge":"AVAILABLE","price":"$75","desc":"Where street passion meets luxury. Rock these mesh shorts with a defiant rose design, born from Oakland grit.","detail":"Breathable Mesh • Elastic Waistband • Rose Design","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"Black/White","hex":"#1A1A1A"}],"image":"assets/images/products/lh-003/lh-003-model.jpg","x":30,"y":70},
  {"id":"lh-002b","name":"Love Hurts Joggers — White","collection":"LOVE HURTS","badge":"AVAILABLE","price":"$95","desc":"White colorway. Where Oakland grit meets luxury. The embroidered rose speaks for itself.","detail":"Premium Fabric • Tapered Fit • Zippered Ankles","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"White","hex":"#F5F5F5"}],"image":"assets/images/products/lh-002/lh-002-model.jpg","x":83,"y":58},
  {"id":"lh-004b","name":"Love Hurts Varsity — Battle Edition","collection":"LOVE HURTS","badge":"PRE-ORDER","price":"$265","desc":"The varsity jacket that started it all. Battle-tested satin, fire-red script, and a rose that bleeds.","detail":"Black Satin Shell • Sherpa Lining • Limited Edition","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"Black/Red","hex":"#8B0000"}],"image":"assets/images/products/lh-001/lh-001-model.jpg","x":56,"y":20},
]

PRODUCTS_SIGNATURE = [
  {"id":"sg-001","name":"The Bay Set","collection":"SIGNATURE","badge":"PRE-ORDER","price":"$225","desc":"Embody West Coast luxury. The iconic blue rose and vibrant Bay Area skyline — prestige elevated.","detail":"Premium Fabric • Tee + Shorts Set • Bay Bridge Design","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"White/Blue","hex":"#F5F5F5"}],"image":"assets/images/products/sg-001/sg-001-model.jpg","x":50,"y":52},
  {"id":"sg-006","name":"Mint & Lavender Hoodie","collection":"SIGNATURE","badge":"AVAILABLE","price":"$145","desc":"Elevated comfort where refreshing mint meets opulent lavender artistry — Bay Area luxury, effortless.","detail":"Premium Soft-Touch • Kangaroo Pocket • Ribbed Cuffs","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"Mint/Lavender","hex":"#B8E0D2"}],"image":"assets/images/products/sg-006/sg-006-model.jpg","x":24,"y":38},
  {"id":"sg-009","name":"The Sherpa Jacket","collection":"SIGNATURE","badge":"PRE-ORDER","price":"$295","desc":"Command attention. Opulent West Coast outerwear featuring signature rose embroidery. Pre-order your legacy.","detail":"Premium Shell • Sherpa Interior • Signature Rose Embroidery","sizes":["S","M","L","XL","2XL","3XL"],"colors":[{"name":"Black","hex":"#000000"}],"image":"assets/images/products/sg-009/sg-009-model.jpg","x":76,"y":34},
  {"id":"sg-003","name":"The Signature Tee — Orchid","collection":"SIGNATURE","badge":"AVAILABLE","price":"$65","desc":"Elevated everyday luxury. Showcasing SkyyRose's commitment to couture-level staples in Orchid colorway.","detail":"Premium Cotton • SR Monogram Label • Orchid Colorway","sizes":["XS","S","M","L","XL","2XL"],"colors":[{"name":"Orchid","hex":"#9B59B6"}],"image":"assets/images/products/sg-003/sg-003-model.jpg","x":38,"y":68},
  {"id":"sg-007","name":"The Signature Beanie","collection":"SIGNATURE","badge":"AVAILABLE","price":"$45","desc":"Elevate your everyday with luxurious knit, bespoke comfort, and a bold statement of West Coast prestige.","detail":"Fine Knit Yarn • Embroidered Rose Emblem • 3 Colors","sizes":["One Size"],"colors":[{"name":"Red","hex":"#C0392B"},{"name":"Purple","hex":"#7D3C98"},{"name":"Black","hex":"#1A1A1A"}],"image":"assets/images/products/sg-007/sg-007-model.jpg","x":85,"y":54},
  {"id":"sg-005","name":"Stay Golden Tee","collection":"SIGNATURE","badge":"AVAILABLE","price":"$75","desc":"West Coast ambition meets luxury. An opulent rose design in gold — for those who stay golden.","detail":"Premium Cotton • Gold Rose Print • Relaxed Fit","sizes":["XS","S","M","L","XL","2XL","3XL"],"colors":[{"name":"Gold","hex":"#D4AF37"}],"image":"assets/images/products/sg-005/sg-005-model.jpg","x":63,"y":73},
]

# ── Snippet constants ─────────────────────────────────────────────────────────

OPEN_MODAL_JS = r"""window.openModal=function(p){
  currentProduct=p;selectedSize=null;
  document.getElementById("m-tag").textContent=p.collection||"";
  document.getElementById("m-name").textContent=p.name;
  document.getElementById("m-price").textContent=p.price;
  document.getElementById("m-desc").textContent=p.desc;
  document.getElementById("m-detail").textContent=p.detail;
  // Badge
  var badge=document.getElementById("m-badge");
  if(badge){badge.textContent=p.badge||"";badge.style.display=p.badge?"inline-block":"none";}
  // Image
  var imgWrap=document.getElementById("m-img-wrap");
  var imgEl=document.getElementById("m-img");
  if(imgWrap&&imgEl&&p.image){imgEl.src=p.image;imgEl.alt=p.name;imgWrap.style.display="block";}
  else if(imgWrap){imgWrap.style.display="none";}
  // Sizes
  var sz=document.getElementById("m-sizes");sz.innerHTML="";
  p.sizes.forEach(function(s){
    var btn=document.createElement("button");btn.className="size-btn";btn.textContent=s;
    btn.addEventListener("click",function(){selectedSize=s;sz.querySelectorAll(".size-btn").forEach(function(b){b.classList.remove("selected")});btn.classList.add("selected");var c=document.getElementById("m-cart");c.textContent="Add to Cart";c.className="cart-btn ready"});
    sz.appendChild(btn);
  });
  // Colors
  var colorsEl=document.getElementById("m-colors");
  if(colorsEl){
    colorsEl.innerHTML="";
    if(p.colors&&p.colors.length>1){
      colorsEl.style.display="block";
      var cl=document.createElement("div");cl.style.cssText="font-size:9px;letter-spacing:.35em;text-transform:uppercase;color:rgba(255,255,255,.4);margin-bottom:8px";cl.textContent="COLOR";colorsEl.appendChild(cl);
      var cw=document.createElement("div");cw.style.cssText="display:flex;gap:8px;margin-bottom:16px";
      p.colors.forEach(function(col){var sw=document.createElement("div");sw.style.cssText="width:20px;height:20px;border-radius:50%;border:1px solid rgba(255,255,255,.15);cursor:pointer;background:"+col.hex;sw.title=col.name;cw.appendChild(sw);});
      colorsEl.appendChild(cw);
    }else{colorsEl.style.display="none";}
  }
  document.getElementById("m-cart").textContent="Select a Size";
  document.getElementById("m-cart").className="cart-btn waiting";
  document.getElementById("modal-backdrop").classList.add("open");
  requestAnimationFrame(function(){document.getElementById("modal").classList.add("open")});
};"""

HOTSPOT_COORD_CSS = "\n.hotspot-coord{position:absolute;top:calc(100% + 6px);left:50%;transform:translateX(-50%);font-size:8px;letter-spacing:.2em;color:rgba(255,255,255,.25);white-space:nowrap;pointer-events:none}\n"

# ── Transformation functions ──────────────────────────────────────────────────

def inject_products(html: str, products: list) -> str:
    """Replace var PRODUCTS=[...]; with real product data."""
    products_json = json.dumps(products, ensure_ascii=False, separators=(',', ':'))
    new_line = f"var PRODUCTS={products_json};"

    # Match from 'var PRODUCTS=' up to and including the closing ';'
    pattern = r'var PRODUCTS=\[.*?\];'
    result = re.sub(pattern, new_line, html, count=1, flags=re.DOTALL)
    if result == html:
        print("  WARNING: PRODUCTS array pattern not found — no replacement made")
    else:
        print("  OK: PRODUCTS array replaced")
    return result


def inject_modal_image_wrap(html: str) -> str:
    """Insert image wrap div right after <div class=\"modal-handle\"></div>."""
    old = '<div class="modal-handle"></div>'
    new = (
        '<div class="modal-handle"></div>\n'
        '    <div id="m-img-wrap" style="display:none;width:100%;height:220px;'
        'overflow:hidden;border-radius:6px;margin-bottom:16px;background:#111">'
        '<img id="m-img" src="" alt="" style="width:100%;height:100%;'
        'object-fit:cover;object-position:top center"></div>'
    )
    if old not in html:
        print("  WARNING: modal-handle not found — image wrap not injected")
        return html
    result = html.replace(old, new, 1)
    print("  OK: Image wrap injected after modal-handle")
    return result


def inject_modal_tag_id(html: str) -> str:
    """Add id=\"m-tag\" to the .modal-tag span/div if missing."""
    # The original has: <div class="modal-tag">BLACK ROSE COLLECTION</div>
    # We want: <div class="modal-tag" id="m-tag"></div>
    pattern = r'(<div class="modal-tag")[^>]*(>)[^<]*(</div>)'
    replacement = r'<div class="modal-tag" id="m-tag">\3'
    result = re.sub(pattern, replacement, html, count=1)
    if result == html:
        print("  WARNING: .modal-tag div not found or already updated")
    else:
        print("  OK: id=\"m-tag\" added to .modal-tag, content cleared (set via JS)")
    return result


def inject_modal_badge(html: str) -> str:
    """Insert <span id=\"m-badge\"> right after the m-tag div."""
    old = '<div class="modal-tag" id="m-tag"></div>'
    new = (
        '<div class="modal-tag" id="m-tag"></div>\n'
        '    <span id="m-badge" style="display:none;font-size:8px;letter-spacing:.3em;'
        'text-transform:uppercase;padding:3px 8px;border:1px solid rgba(183,110,121,.5);'
        'color:#B76E79;border-radius:2px;margin-bottom:6px;display:none"></span>'
    )
    if old not in html:
        print("  WARNING: m-tag div not found — badge span not injected")
        return html
    result = html.replace(old, new, 1)
    print("  OK: m-badge span injected after m-tag")
    return result


def inject_modal_colors(html: str) -> str:
    """Insert <div id=\"m-colors\"></div> after the m-sizes div."""
    old = '<div class="sizes-wrap" id="m-sizes"></div>'
    new = (
        '<div class="sizes-wrap" id="m-sizes"></div>\n'
        '    <div id="m-colors" style="display:none"></div>'
    )
    if old not in html:
        print("  WARNING: m-sizes div not found — colors div not injected")
        return html
    result = html.replace(old, new, 1)
    print("  OK: m-colors div injected after m-sizes")
    return result


def replace_open_modal(html: str) -> str:
    """Replace window.openModal function body with enhanced version."""
    pattern = r'window\.openModal=function\(p\)\{.*?\};'
    result = re.sub(pattern, OPEN_MODAL_JS, html, count=1, flags=re.DOTALL)
    if result == html:
        print("  WARNING: openModal function not found — not replaced")
    else:
        print("  OK: openModal function replaced with enhanced version")
    return result


def enhance_hotspot_label_css(html: str) -> str:
    """Change hotspot-label opacity from 0 to 0.5 at rest."""
    # The CSS ends with: opacity:0;transition:opacity .2s ease}
    old = 'opacity:0;transition:opacity .2s ease}'
    new = 'opacity:0.5;transition:opacity .2s ease}'
    if old not in html:
        print("  WARNING: hotspot-label opacity:0 pattern not found — CSS not updated")
        return html
    result = html.replace(old, new, 1)
    print("  OK: hotspot-label opacity changed from 0 to 0.5")
    return result


def inject_hotspot_coord_css(html: str) -> str:
    """Inject .hotspot-coord CSS rule after .hotspot-label block."""
    # Find the closing } of .hotspot-label block
    label_start = html.find('.hotspot-label{')
    if label_start == -1:
        print("  WARNING: .hotspot-label CSS not found — coord CSS not injected")
        return html
    label_end = html.find('}', label_start)
    insert_pos = label_end + 1
    result = html[:insert_pos] + HOTSPOT_COORD_CSS + html[insert_pos:]
    print("  OK: .hotspot-coord CSS injected")
    return result


def enhance_hotspot_inner_html(html: str) -> str:
    """Add coord span to hotspot innerHTML in createHotspots()."""
    old = (
        'b.innerHTML=\'<span class="hotspot-ring" style="animation-delay:\''
        '+(i*.3)+\'s"></span><span class="hotspot-dot"></span>'
        '<span class="hotspot-label">\'+p.name+" — "+p.price+"</span>";'
    )
    new = (
        'b.innerHTML=\'<span class="hotspot-ring" style="animation-delay:\''
        '+(i*.3)+\'s"></span><span class="hotspot-dot"></span>'
        '<span class="hotspot-label">\'+p.name+" — "+p.price+"</span>"'
        '+\'<span class="hotspot-coord">\'+p.x+\'°  \'+p.y+\'°</span>\';'
    )
    if old not in html:
        print("  WARNING: b.innerHTML hotspot pattern not found — coord span not added")
        return html
    result = html.replace(old, new, 1)
    print("  OK: hotspot-coord span added to createHotspots innerHTML")
    return result


# ── Main pipeline ─────────────────────────────────────────────────────────────

FILES = [
    {
        "src": "/Users/coreyfoster/Downloads/3D-Scenes/explore-black-rose.html",
        "dst": "/Users/coreyfoster/DevSkyy/skyyrose/explore-black-rose.html",
        "products": PRODUCTS_BLACK_ROSE,
        "label": "BLACK ROSE",
    },
    {
        "src": "/Users/coreyfoster/Downloads/3D-Scenes/explore-love-hurts.html",
        "dst": "/Users/coreyfoster/DevSkyy/skyyrose/explore-love-hurts.html",
        "products": PRODUCTS_LOVE_HURTS,
        "label": "LOVE HURTS",
    },
    {
        "src": "/Users/coreyfoster/Downloads/3D-Scenes/explore-signature.html",
        "dst": "/Users/coreyfoster/DevSkyy/skyyrose/explore-signature.html",
        "products": PRODUCTS_SIGNATURE,
        "label": "SIGNATURE",
    },
]


def transform(html: str, products: list, label: str) -> str:
    print(f"\n  --- Transforming {label} ---")
    html = inject_products(html, products)
    html = inject_modal_image_wrap(html)
    html = inject_modal_tag_id(html)
    html = inject_modal_badge(html)
    html = inject_modal_colors(html)
    html = replace_open_modal(html)
    html = enhance_hotspot_label_css(html)
    html = inject_hotspot_coord_css(html)
    html = enhance_hotspot_inner_html(html)
    return html


def main():
    errors = []
    for f in FILES:
        print(f"\n{'='*60}")
        print(f"Processing: {f['label']}")
        print(f"  Source: {f['src']}")
        print(f"  Output: {f['dst']}")

        if not os.path.exists(f["src"]):
            msg = f"  ERROR: Source file not found: {f['src']}"
            print(msg)
            errors.append(msg)
            continue

        with open(f["src"], "r", encoding="utf-8") as fh:
            html = fh.read()
        print(f"  Read {len(html):,} bytes")

        html = transform(html, f["products"], f["label"])

        os.makedirs(os.path.dirname(f["dst"]), exist_ok=True)
        with open(f["dst"], "w", encoding="utf-8") as fh:
            fh.write(html)

        size = os.path.getsize(f["dst"])
        print(f"  Written {size:,} bytes -> {f['dst']}")

    print(f"\n{'='*60}")
    if errors:
        print(f"DONE WITH {len(errors)} ERROR(S):")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("ALL 3 FILES PROCESSED SUCCESSFULLY")
        for f in FILES:
            print(f"  {f['dst']}")


if __name__ == "__main__":
    main()
