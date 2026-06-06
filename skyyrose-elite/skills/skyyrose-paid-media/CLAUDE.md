<claude-mem-context>
# skyyrose-paid-media Skill — Brand Canon Guardrails

## Hard Rules (STOP-AND-SHOW required)
- Any paid spend commitment (Meta, TikTok, Google) → explicit "y" before executing
- Any Klaviyo send → explicit "y"
- Any WooCommerce write or media upload → explicit "y"

## Brand Canon
- Tagline: "Luxury Grows from Concrete." — terminal period, every time, non-negotiable
- Collections: Black Rose · Love Hurts · Signature · Kids Capsule — NEVER cross-attribute voices
- Products: by NAME only (e.g., "BLACK Rose Hoodie"). Never SKU in ad copy or briefs.
- Fabric specs: resolve from per-SKU dossier at `data/dossiers/`. Never infer or invent.
- Social proof: bracket templates only until real reviews exist: [Customer name, City] / [X]+ members
- Scarcity: real edition sizes from catalog only. No urgency timers.
- Visual DNA: Kith · Oaklandish · Culture Kings · Fear of God · Palm Angels — ONLY these five
- European luxury house references (Bottega, Rick Owens, 032c, Acne, etc.) → NEVER
- Hero names: lockup PNG assets only — never type-rendered in hero positions
- Oakland anchor: ground brand copy in Oakland
- Pre-order: ~10/33 SKUs — treat as primary case, not edge case

## API Facts (verified — do not invent alternatives)
- Meta budget: in CENTS. $50 = `daily_budget: 5000`
- Meta ROAS floor: `roas_average_floor` = ROAS × 10000. 2.0× = 20000
- Meta Advantage+: `targeting_automation.advantage_audience` 0=off 1=on
- Google budget: in MICROS. $5 = `amount_micros: 5000000`
- Google PMax: `advertising_channel_type: "PERFORMANCE_MAX"`
- Google Standard Shopping ad group type: `"SHOPPING_PRODUCT_ADS"`
- Merchant Center preorder: `availability: preorder` + `availability_date` (ISO 8601) BOTH required
- Smart Shopping: SUNSET — use Performance Max

## Catalog Source of Truth
- `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` — 33 SKUs, authoritative
- `wordpress-theme/skyyrose-flagship/data/dossiers/` — per-product specs
- AOV planning: $65–$80 (catalog mean ~$79.70); validate against live WooCommerce orders
</claude-mem-context>
