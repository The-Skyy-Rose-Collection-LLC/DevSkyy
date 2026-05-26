"""Generate 14 dossier stubs for the new SKUs added 2026-05-26.

Founder rule: dossiers must be authored from real product (NO ML pre-fill).
These stubs are intentionally skeletal — TODO markers force founder
authoring before any 3D RAS pipeline call.
"""

from __future__ import annotations

from pathlib import Path

DOSSIER_DIR = Path(__file__).parent.parent / "wordpress-theme/skyyrose-flagship/data/dossiers"

STUBS = [
    # (sku, dossier_slug, name, collection, logo_reference, garment_lock, notes)
    (
        "lh-001",
        "love-hurts-fannie-pack",
        "The Fannie Pack",
        "love-hurts",
        "data/brand-logos/love-hurts-logo.md",
        "Multi-bag belt-bag pack. NOT a single fannie pack (that is lh-005). NOT a tote, NOT a backpack. Three Fannie units bundled.",
        "Pack composition: confirm bag count. Confirm colorway per bag.",
    ),
    (
        "sg-004",
        "signature-mint-lavender-hoodie-sg004",
        "Mint & Lavender Hoodie",
        "signature",
        "data/brand-logos/signature-logo.md",
        "Pullover hoodie, upper body only. NOT a crewneck (that is sg-013), NOT a zip-up, NOT a sweatshirt without hood. Hood with drawstring, kangaroo pocket.",
        "⚠ DUPLICATE NAME with sg-006. Founder confirm: variant or replacement?",
    ),
    (
        "sg-008",
        "signature-windbreaker-set-retro",
        "The Windbreaker Set — Retro",
        "signature",
        "data/brand-logos/signature-logo.md",
        "Two-piece windbreaker set (jacket + pant), retro colorway. NOT the current sg-015 (different colorway). NOT a tracksuit (lighter shell fabric).",
        "Retro colorway specification needed. Confirm vs sg-015 and sg-d01.",
    ),
    (
        "sg-010",
        "signature-bridge-golden-gate-shirt",
        "The Bridge Series 'Golden Gate' Shirt",
        "signature",
        "data/brand-logos/signature-logo.md",
        "Short-sleeve t-shirt, upper body only. NOT a long-sleeve, NOT a polo, NOT a button-down. Crew neckline.",
        "DRAFT — confirm photo-print specifics for Golden Gate Bridge front graphic.",
    ),
    (
        "sg-016",
        "signature-bridge-golden-gate-shorts",
        "The Bridge Series 'Golden Gate' Shorts",
        "signature",
        "data/brand-logos/signature-logo.md",
        "Athletic shorts, lower body. NOT joggers (no ankle cuff), NOT swim trunks. Elastic waistband with drawstring, side pockets.",
        "DRAFT — confirm photo-print specifics for Golden Gate Bridge graphic placement.",
    ),
    (
        "sg-017",
        "signature-bridge-bay-bridge-shirt-refresh",
        "The Bridge Series 'Bay Bridge' Shirt (Refresh)",
        "signature",
        "data/brand-logos/signature-logo.md",
        "Short-sleeve t-shirt, upper body only. NOT the original sg-005 (refresh version, may differ in graphic placement or print quality).",
        "DRAFT — founder confirm if this supersedes sg-005 or co-exists.",
    ),
    (
        "sg-018",
        "signature-bridge-bay-bridge-shorts-refresh",
        "The Bridge Series 'Bay Bridge' Shorts (Refresh)",
        "signature",
        "data/brand-logos/signature-logo.md",
        "Athletic shorts, lower body. NOT the original sg-001 (refresh version). NOT joggers, NOT swim trunks.",
        "DRAFT — founder confirm if this supersedes sg-001 ($195) or co-exists. Price discrepancy ($65 vs $195) needs reconciliation.",
    ),
    (
        "br-d01",
        "black-rose-hockey-jersey-teal",
        "BLACK is Beautiful Hockey Jersey — Teal",
        "black-rose",
        "data/brand-logos/black-rose-logo.md",
        "Hockey jersey, upper body, loose fit. NOT football (different cut). NOT basketball (sleeved). Mesh fabric, lace-up neck OR sewn collar (confirm).",
        "Teal colorway. Confirm jersey number (default: none, or specify).",
    ),
    (
        "br-d02",
        "black-rose-football-jersey-niners-80",
        "BLACK is Beautiful Football Jersey — Niners #80",
        "black-rose",
        "data/brand-logos/black-rose-logo.md",
        "Football jersey, upper body, shoulder-padded shape. NOT hockey, NOT basketball. Red 49ers tribute colorway, #80 on front + back.",
        "Player tribute: confirm #80 references which player (Jerry Rice? Confirm).",
    ),
    (
        "br-d03",
        "black-rose-football-jersey-last-oakland-32",
        "BLACK is Beautiful Football Jersey — Last Oakland #32",
        "black-rose",
        "data/brand-logos/black-rose-logo.md",
        "Football jersey, upper body, shoulder-padded shape. White colorway, #32 Jack Tatum tribute, Last Oakland Raiders era silver/black accents.",
        "Tatum tribute confirmed. Confirm exact silver/black accent placement.",
    ),
    (
        "br-d04",
        "black-rose-basketball-jersey-the-town",
        "BLACK is Beautiful Basketball Jersey — The Town",
        "black-rose",
        "data/brand-logos/black-rose-logo.md",
        'Basketball jersey, sleeveless, upper body. NOT football, NOT hockey. Mesh fabric. "The Town" (Oakland) tribute.',
        "Confirm jersey number, exact 'The Town' typography/placement.",
    ),
    (
        "sg-d01",
        "signature-windbreaker-set-design-variant",
        "The Windbreaker Set — Design Variant",
        "signature",
        "data/brand-logos/signature-logo.md",
        "Two-piece windbreaker set. NOT sg-015 (current), NOT sg-008 (Retro). Third variant — founder differentiator needed.",
        "Founder note: 'same' — needs explicit colorway/differentiator from the other two windbreaker SKUs.",
    ),
    (
        "sg-d03",
        "signature-mint-lavender-sweatsuit-set",
        "Mint & Lavender Sweatsuit Set",
        "signature",
        "data/brand-logos/signature-logo.md",
        "Two-piece sweatsuit (hoodie + sweatpants). NOT a windbreaker (heavier fabric). Mint top, lavender accents. Components also available individually as sg-006 (hoodie) and sg-014 (sweatpants).",
        "Confirm: is the set a third SKU, or just a marketing bundle of sg-006 + sg-014?",
    ),
    (
        "sg-d04",
        "signature-bridge-cream-shorts",
        "The Bridge Series 'Cream' Shorts",
        "signature",
        "data/brand-logos/signature-logo.md",
        "Athletic shorts, lower body, cream colorway. NOT a swim short, NOT a denim short. Elastic waistband.",
        "⚠ DRAFT — founder uncertain about reference. Confirm Bridge Series sibling or standalone product.",
    ),
]


TEMPLATE = """---
sku: {sku}
name: {name}
collection: {collection}
logo_reference: {logo_reference}
status: pre-order-draft
created: 2026-05-26
---

<!--
DRAFT STUB — generated 2026-05-26 alongside catalog row addition.
Founder must replace placeholder branding details with real product specs
before this dossier can drive any RAS pipeline call.

Authoring rules (from _template.md):
  1. Author from the actual physical product or canonical product photos.
  2. NO ML pre-fill — Gemini Flash hallucinates per-region detail.
  3. Be exhaustive on Front / Back / Sleeves / Collar / Hem / Other.
  4. The NEGATIVE section is a safety rail.
  5. Two-eyes review required before commit (Corey confirms each line).
-->

# {name}

**Garment type lock:** {garment_lock}

## Branding — exactly what IS on this product

> TODO — founder authoring required. The brand logo art is defined in
> `{logo_reference}`. Specify per-region technique + dimensions + colorway.

### Front
- **TODO front-chest** (~Xin × ~Yin): The brand logo (see logo_reference).
  **Technique:** TODO. **Color/Colorway:** TODO.

### Back
- TODO (delete heading if no back decoration).

### Sleeves / Collar / Hem / Other
- TODO (delete heading if not applicable).

## Negative — what is NOT on this product (DO NOT render)

- TODO — list every conflation to prevent.
- No printed text on chest (unless specified above).
- No back graphics (unless specified above).
- No sleeve printing (unless specified above).

## Scene direction (optional — feeds the RAS prompt)

- **Pose:** TODO (default: standing forward, three-quarter angle).
- **Setting:** Pure white studio backdrop, soft directional light, subtle drop shadow.

## Notes

{notes}
"""


def main() -> int:
    if not DOSSIER_DIR.exists():
        print(f"ERROR: dossier dir missing: {DOSSIER_DIR}")
        return 1

    created = []
    skipped = []
    for sku, slug, name, collection, logo_ref, garment_lock, notes in STUBS:
        path = DOSSIER_DIR / f"{slug}.md"
        if path.exists():
            skipped.append((sku, slug))
            continue
        path.write_text(
            TEMPLATE.format(
                sku=sku,
                name=name,
                collection=collection,
                logo_reference=logo_ref,
                garment_lock=garment_lock,
                notes=notes,
            ),
            encoding="utf-8",
        )
        created.append((sku, slug))

    print(f"Created {len(created)} dossier stubs.")
    for sku, slug in created:
        print(f"  + {sku} → {slug}.md")
    if skipped:
        print(f"\nSkipped {len(skipped)} (already exist):")
        for sku, slug in skipped:
            print(f"  - {sku} → {slug}.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
