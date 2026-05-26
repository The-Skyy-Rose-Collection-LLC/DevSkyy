"""One-shot: append 14 new pre-order SKUs to skyyrose-catalog.csv.

Date: 2026-05-26
Origin: founder-approved v5-catalog-extension-form.html submission.
Headers: 24 columns. Each row built explicitly per founder ruling.

Safety:
- Validates row count after append (expected: existing + 14)
- Validates each new SKU's collection matches its prefix
- Validates no SKU code collision
"""

from __future__ import annotations

import csv
from pathlib import Path

CATALOG = (
    Path(__file__).parent.parent / "wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv"
)

NEW_ROWS = [
    # Cat B — real products
    {
        "sku": "lh-001",
        "name": "The Fannie Pack",
        "price": "55",
        "collection": "love-hurts",
        "description": "Multi-bag pack version of The Fannie. Founder-approved 2026-05-26.",
        "badge": "Pre-Order",
        "image": "assets/images/products/lh-001-fannie-pack-front-preorder.jpeg",
        "front_model_image": "assets/images/products/lh-001-fannie-front.jpeg",
        "back_image": "assets/images/products/lh-001-fannie-back.jpeg",
        "back_model_image": "assets/images/products/lh-001-fannie-angled.jpeg",
        "sizes": "One Size",
        "color": "Black",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "Embroidered rose logo on each bag.",
        "render_output_slug": "lh-001-fannie-pack",
        "render_source_override": "lh-001-fannie-pack-techflat.jpeg",
        "render_back_source_override": "",
        "render_is_tech_flat": "0",
        "render_is_accessory": "1",
        "garment_type_lock": "accessory",
        "dossier_slug": "love-hurts-fannie-pack",
        "engine_override": "",
    },
    {
        "sku": "sg-004",
        "name": "Mint & Lavender Hoodie",
        "price": "45",
        "collection": "signature",
        "description": "DRAFT — name shared with sg-006. Founder ruling 2026-05-26 says Mint & Lavender LINE is Hoodie + Crewneck + Sweats. Confirm if sg-004 supersedes sg-006 or is a separate variant.",
        "badge": "Pre-Order",
        "image": "assets/images/products/sg-004-mint-hoodie.jpeg",
        "front_model_image": "assets/images/products/sg-004-mint-hoodie.jpeg",
        "back_image": "",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Mint",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "Original Label logo embroidered chest left.",
        "render_output_slug": "signature-mint-lavender-hoodie-sg004",
        "render_source_override": "sg-004-mint-hoodie.jpeg",
        "render_back_source_override": "",
        "render_is_tech_flat": "0",
        "render_is_accessory": "0",
        "garment_type_lock": "hoodie",
        "dossier_slug": "signature-mint-lavender-hoodie-sg004",
        "engine_override": "",
    },
    {
        "sku": "sg-008",
        "name": "The Windbreaker Set — Retro",
        "price": "95",
        "collection": "signature",
        "description": "Retro colorway variant of The Windbreaker Set. Pre-order. Distinct from sg-015 (current line) and sg-d01 (design variant).",
        "badge": "Pre-Order",
        "image": "assets/images/products/sg-008-windbreaker-set-retro-front.jpg",
        "front_model_image": "assets/images/products/sg-008-windbreaker-set-retro-front.jpg",
        "back_image": "",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Multi",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "Embroidered Original Label chest. Retro side stripes.",
        "render_output_slug": "signature-windbreaker-set-retro",
        "render_source_override": "sg-008-techflat-windbreaker.jpeg",
        "render_back_source_override": "",
        "render_is_tech_flat": "0",
        "render_is_accessory": "0",
        "garment_type_lock": "set",
        "dossier_slug": "signature-windbreaker-set-retro",
        "engine_override": "",
    },
    # sg-010 expanded into 4 Bridge Series variant SKUs (founder ruling: 4 NEW SKUs sold separately)
    {
        "sku": "sg-010",
        "name": "The Bridge Series 'Golden Gate' Shirt",
        "price": "65",
        "collection": "signature",
        "description": "Golden Gate variant of Bridge Series. 1 of 4 new Bridge SKUs (sg-010/016/017/018). DRAFT — price matches Stay Golden parity (sg-002).",
        "badge": "Pre-Order",
        "image": "assets/images/products/sg-010-golden-gate-tee-solo.jpeg",
        "front_model_image": "assets/images/products/sg-010-golden-gate-tee-solo.jpeg",
        "back_image": "",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Gold/Multi",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "Golden Gate Bridge photo print on front. Original Label tag at hem.",
        "render_output_slug": "signature-bridge-golden-gate-shirt",
        "render_source_override": "sg-010-golden-gate-tee-solo.jpeg",
        "render_back_source_override": "",
        "render_is_tech_flat": "0",
        "render_is_accessory": "0",
        "garment_type_lock": "shirt",
        "dossier_slug": "signature-bridge-golden-gate-shirt",
        "engine_override": "",
    },
    {
        "sku": "sg-016",
        "name": "The Bridge Series 'Golden Gate' Shorts",
        "price": "65",
        "collection": "signature",
        "description": "Golden Gate variant of Bridge Series shorts. 2 of 4 new Bridge SKUs. DRAFT — price matches Stay Golden Shorts (sg-003).",
        "badge": "Pre-Order",
        "image": "assets/images/products/sg-010-bridge-shorts-golden-gate.jpeg",
        "front_model_image": "assets/images/products/sg-010-bridge-shorts-golden-gate.jpeg",
        "back_image": "",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Gold/Multi",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "Golden Gate Bridge photo print. Elastic waistband with drawstring.",
        "render_output_slug": "signature-bridge-golden-gate-shorts",
        "render_source_override": "sg-010-bridge-shorts-golden-gate.jpeg",
        "render_back_source_override": "",
        "render_is_tech_flat": "0",
        "render_is_accessory": "0",
        "garment_type_lock": "shorts",
        "dossier_slug": "signature-bridge-golden-gate-shorts",
        "engine_override": "",
    },
    {
        "sku": "sg-017",
        "name": "The Bridge Series 'Bay Bridge' Shirt (Refresh)",
        "price": "65",
        "collection": "signature",
        "description": "Bay Bridge shirt refresh. DRAFT — may supersede sg-005 (existing Bay Bridge Shirt). Founder ruling needed: replacement or co-existing variant?",
        "badge": "Pre-Order",
        "image": "assets/images/products/sg-010-bay-bridge-tee-solo.jpeg",
        "front_model_image": "assets/images/products/sg-010-bay-bridge-tee-solo.jpeg",
        "back_image": "",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Multi",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "Bay Bridge nighttime photo print on front.",
        "render_output_slug": "signature-bridge-bay-bridge-shirt-refresh",
        "render_source_override": "sg-010-bay-bridge-tee-solo.jpeg",
        "render_back_source_override": "",
        "render_is_tech_flat": "0",
        "render_is_accessory": "0",
        "garment_type_lock": "shirt",
        "dossier_slug": "signature-bridge-bay-bridge-shirt-refresh",
        "engine_override": "",
    },
    {
        "sku": "sg-018",
        "name": "The Bridge Series 'Bay Bridge' Shorts (Refresh)",
        "price": "65",
        "collection": "signature",
        "description": "Bay Bridge shorts refresh. DRAFT — may supersede sg-001 (existing $195 Bay Bridge Shorts). Founder ruling needed: replacement or co-existing variant? Pricing inconsistency between sg-001 ($195) and this refresh ($65) needs reconciliation.",
        "badge": "Pre-Order",
        "image": "assets/images/products/sg-010-bridge-shorts-bay-bridge.jpeg",
        "front_model_image": "assets/images/products/sg-010-bridge-shorts-bay-bridge.jpeg",
        "back_image": "assets/images/products/sg-010-bay-bridge-set-techflat-back.jpeg",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Multi",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "Bay Bridge nighttime photo print. Elastic waistband.",
        "render_output_slug": "signature-bridge-bay-bridge-shorts-refresh",
        "render_source_override": "sg-010-bridge-shorts-bay-bridge.jpeg",
        "render_back_source_override": "sg-010-bay-bridge-set-techflat-back.jpeg",
        "render_is_tech_flat": "0",
        "render_is_accessory": "0",
        "garment_type_lock": "shorts",
        "dossier_slug": "signature-bridge-bay-bridge-shorts-refresh",
        "engine_override": "",
    },
    # Cat C — design SKUs (br-d01-04, sg-d01, sg-d03, sg-d04). sg-d02 SKIPPED per founder.
    {
        "sku": "br-d01",
        "name": "BLACK is Beautiful Hockey Jersey — Teal",
        "price": "115",
        "collection": "black-rose",
        "description": "Hockey jersey teal colorway. Variant of br-011 'The Rose (Hockey)' — same Bridge concept, teal palette.",
        "badge": "Pre-Order",
        "image": "assets/images/products/br-d01-hockey-jersey-teal-techflat.jpeg",
        "front_model_image": "assets/images/products/br-d01-hockey-jersey-teal-techflat-front.jpeg",
        "back_image": "assets/images/products/br-d01-hockey-jersey-teal-techflat-back.jpeg",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Teal",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "Embroidered Rose patch on chest. Hockey-cut jersey, mesh fabric.",
        "render_output_slug": "black-rose-hockey-jersey-teal",
        "render_source_override": "br-d01-hockey-jersey-teal-techflat-front.jpeg",
        "render_back_source_override": "br-d01-hockey-jersey-teal-techflat-back.jpeg",
        "render_is_tech_flat": "1",
        "render_is_accessory": "0",
        "garment_type_lock": "jersey",
        "dossier_slug": "black-rose-hockey-jersey-teal",
        "engine_override": "",
    },
    {
        "sku": "br-d02",
        "name": "BLACK is Beautiful Football Jersey — Niners #80",
        "price": "115",
        "collection": "black-rose",
        "description": "49ers tribute football jersey, #80 red colorway. BLACK is Beautiful series extension.",
        "badge": "Pre-Order",
        "image": "assets/images/products/br-d02-football-jersey-red-80-techflat.jpeg",
        "front_model_image": "assets/images/products/br-d02-football-jersey-red-80-techflat-front.jpeg",
        "back_image": "assets/images/products/br-d02-football-jersey-red-80-techflat-back.jpeg",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Red",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "49ers tribute. #80 jersey number on front and back. SF Niners color palette.",
        "render_output_slug": "black-rose-football-jersey-niners-80",
        "render_source_override": "br-d02-football-jersey-red-80-techflat-front.jpeg",
        "render_back_source_override": "br-d02-football-jersey-red-80-techflat-back.jpeg",
        "render_is_tech_flat": "1",
        "render_is_accessory": "0",
        "garment_type_lock": "jersey",
        "dossier_slug": "black-rose-football-jersey-niners-80",
        "engine_override": "",
    },
    {
        "sku": "br-d03",
        "name": "BLACK is Beautiful Football Jersey — Last Oakland #32",
        "price": "115",
        "collection": "black-rose",
        "description": "Tatum tribute football jersey, #32 white colorway. Last Oakland Raiders era homage.",
        "badge": "Pre-Order",
        "image": "assets/images/products/br-d03-football-jersey-white-32-techflat.jpeg",
        "front_model_image": "assets/images/products/br-d03-football-jersey-white-32-techflat-front.jpeg",
        "back_image": "assets/images/products/br-d03-football-jersey-white-32-techflat-back.jpeg",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "White",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "Jack Tatum tribute. #32 jersey number. Last Oakland Raiders silver/black accent.",
        "render_output_slug": "black-rose-football-jersey-last-oakland-32",
        "render_source_override": "br-d03-football-jersey-white-32-techflat-front.jpeg",
        "render_back_source_override": "br-d03-football-jersey-white-32-techflat-back.jpeg",
        "render_is_tech_flat": "1",
        "render_is_accessory": "0",
        "garment_type_lock": "jersey",
        "dossier_slug": "black-rose-football-jersey-last-oakland-32",
        "engine_override": "",
    },
    {
        "sku": "br-d04",
        "name": "BLACK is Beautiful Basketball Jersey — The Town",
        "price": "100",
        "collection": "black-rose",
        "description": "The Town (Oakland) basketball jersey. BLACK is Beautiful series extension.",
        "badge": "Pre-Order",
        "image": "assets/images/products/br-d04-basketball-jersey-techflat.jpeg",
        "front_model_image": "assets/images/products/br-d04-basketball-jersey-techflat-front.jpeg",
        "back_image": "assets/images/products/br-d04-basketball-jersey-techflat-back.jpeg",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Black",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "'The Town' Oakland tribute. Embroidered Rose patch. Basketball-cut, mesh fabric.",
        "render_output_slug": "black-rose-basketball-jersey-the-town",
        "render_source_override": "br-d04-basketball-jersey-techflat-front.jpeg",
        "render_back_source_override": "br-d04-basketball-jersey-techflat-back.jpeg",
        "render_is_tech_flat": "1",
        "render_is_accessory": "0",
        "garment_type_lock": "jersey",
        "dossier_slug": "black-rose-basketball-jersey-the-town",
        "engine_override": "",
    },
    {
        "sku": "sg-d01",
        "name": "The Windbreaker Set — Design Variant",
        "price": "85",
        "collection": "signature",
        "description": "Third windbreaker SKU alongside sg-008 (Retro) and sg-015 (current). Founder note: 'same'. May warrant merge or distinct colorway.",
        "badge": "Pre-Order",
        "image": "assets/images/products/sg-d01-windbreaker-set-techflat.jpg",
        "front_model_image": "assets/images/products/sg-d01-windbreaker-set-techflat.jpg",
        "back_image": "",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Multi",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "Embroidered Original Label chest.",
        "render_output_slug": "signature-windbreaker-set-design-variant",
        "render_source_override": "sg-d01-windbreaker-set-techflat.jpg",
        "render_back_source_override": "",
        "render_is_tech_flat": "1",
        "render_is_accessory": "0",
        "garment_type_lock": "set",
        "dossier_slug": "signature-windbreaker-set-design-variant",
        "engine_override": "",
    },
    {
        "sku": "sg-d03",
        "name": "Mint & Lavender Sweatsuit Set",
        "price": "95",
        "collection": "signature",
        "description": "Set version of Mint & Lavender line (sg-006 Hoodie + sg-014 Sweatpants). Founder note: 'sold separately' — set is its own SKU, components also available individually.",
        "badge": "Pre-Order",
        "image": "assets/images/products/sg-d03-mint-sweatsuit-set.jpeg",
        "front_model_image": "assets/images/products/sg-d03-mint-sweatsuit-set.jpeg",
        "back_image": "",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Mint/Lavender",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "Original Label embroidered chest on hoodie. Mint top, lavender accents.",
        "render_output_slug": "signature-mint-lavender-sweatsuit-set",
        "render_source_override": "sg-d03-mint-sweatsuit-set.jpeg",
        "render_back_source_override": "",
        "render_is_tech_flat": "0",
        "render_is_accessory": "0",
        "garment_type_lock": "set",
        "dossier_slug": "signature-mint-lavender-sweatsuit-set",
        "engine_override": "",
    },
    {
        "sku": "sg-d04",
        "name": "The Bridge Series 'Cream' Shorts",
        "price": "65",
        "collection": "signature",
        "description": "DRAFT — founder uncertain what these reference. File: sg-d04-cream-shorts.jpg. Drafted as Bridge Series sibling. Confirm or retire.",
        "badge": "Pre-Order",
        "image": "assets/images/products/sg-d04-cream-shorts.jpg",
        "front_model_image": "assets/images/products/sg-d04-cream-shorts.jpg",
        "back_image": "",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Cream",
        "edition_size": "0",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "DRAFT — branding TBD.",
        "render_output_slug": "signature-bridge-cream-shorts",
        "render_source_override": "sg-d04-cream-shorts.jpg",
        "render_back_source_override": "",
        "render_is_tech_flat": "0",
        "render_is_accessory": "0",
        "garment_type_lock": "shorts",
        "dossier_slug": "signature-bridge-cream-shorts",
        "engine_override": "",
    },
]


def main() -> int:
    # Read existing rows + header
    with CATALOG.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing_rows = list(reader)
        existing_skus = {row["sku"] for row in existing_rows}

    if fieldnames is None:
        print(f"ERROR: catalog header missing from {CATALOG}")
        return 1

    print(f"Existing catalog: {len(existing_rows)} rows. Fieldnames: {len(fieldnames)}")

    # Validate new rows
    for row in NEW_ROWS:
        if row["sku"] in existing_skus:
            print(f"ERROR: SKU collision — {row['sku']} already in catalog")
            return 1
        if set(row.keys()) != set(fieldnames):
            missing = set(fieldnames) - set(row.keys())
            extra = set(row.keys()) - set(fieldnames)
            print(f"ERROR: field mismatch for {row['sku']}. Missing: {missing}. Extra: {extra}")
            return 1
        # Collection prefix check
        prefix = row["sku"].split("-")[0]
        collection = row["collection"]
        expected = {
            "br": "black-rose",
            "lh": "love-hurts",
            "sg": "signature",
            "kids": "kids-capsule",
        }.get(prefix)
        if expected and expected != collection:
            print(
                f"ERROR: {row['sku']} prefix '{prefix}' implies '{expected}' but row has '{collection}'"
            )
            return 1

    # Append
    with CATALOG.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        for row in NEW_ROWS:
            writer.writerow(row)

    # Verify
    with CATALOG.open(newline="", encoding="utf-8") as f:
        new_total = sum(1 for _ in csv.DictReader(f))

    expected_total = len(existing_rows) + len(NEW_ROWS)
    if new_total != expected_total:
        print(f"ERROR: post-write row count {new_total} != expected {expected_total}")
        return 1

    print(f"Wrote {len(NEW_ROWS)} rows. Catalog now has {new_total} SKUs.")
    print()
    print("New SKUs added:")
    for row in NEW_ROWS:
        flag = " [DRAFT]" if "DRAFT" in row["description"] else ""
        print(
            f"  {row['sku']:8s}  ${row['price']:>4s}  {row['collection']:13s}  {row['name']}{flag}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
