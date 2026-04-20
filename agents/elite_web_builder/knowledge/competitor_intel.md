# Competitor Intelligence — Knowledge Base

Source of truth for `COMPETITOR_SCOUT_SPEC`. Wraps the already-built `agents/core/analytics/sub_agents/brand_intel_agent.py` (SWOT, price-gap, threat-score, style comparison) and adds ad-creative harvesting + blueprint synthesis handed off to `SOCIAL_MEDIA_SPEC` and `IMAGERY_SPEC`.

> "Dissect competitors on what they do right and what they do wrong, and feed the team the blueprint for successful ad creations."

---

## 1. Competitor target list (4 tiers)

### Tier 1 — Luxury streetwear peers (direct price/silhouette benchmark)
| Brand | HQ | Why they matter | Ad channel focus |
|---|---|---|---|
| **Fear of God / Essentials** | LA | Elevated basics, direct silhouette competitor, $80–$500 tier | Meta + newsletter |
| **Represent Clothing** | Manchester, UK | High ad velocity, drop cadence, cult following | Meta + TikTok |
| **Rhude** | LA | Campaign storytelling, racing/Americana motifs | Meta + editorial |
| **Palm Angels** | Milan | European luxury streetwear, editorial lens | Meta + PR placements |

### Tier 2 — Gothic + distressed luxury (Black Rose aesthetic peers)
| Brand | HQ | Why they matter | Ad channel focus |
|---|---|---|---|
| **Chrome Hearts** | LA | Gothic luxury silver, leather, $$$$ pricing — aspiration mirror | Owned only (no paid ads typically) |
| **Amiri** | LA | Distressed denim, celebrity seeding, $600–$2500 tier | Meta + TikTok creator partnerships |
| **Enfants Riches Déprimés** | LA | Gothic/punk luxury, provocation-led storytelling | Limited paid; owned + editorial |

### Tier 3 — DTC ad machines (creative volume + hook benchmark)
| Brand | HQ | Why they matter | Ad channel focus |
|---|---|---|---|
| **Fashion Nova** | LA | Highest ad velocity in fashion, Meta + TikTok masters | Meta + TikTok + influencer |
| **PrettyLittleThing** | Manchester, UK | Sibling of Boohoo, UGC + influencer playbook | Meta + TikTok + Snap |
| **Revolve** | LA | Multi-brand DTC, influencer + UGC ad playbook | Meta + TikTok + YouTube |

### Tier 4 — European luxury (tone + concept benchmark)
| Brand | HQ | Why they matter | Ad channel focus |
|---|---|---|---|
| **Off-White** | Milan | Editorial + lookbook standard, Virgil legacy | Editorial PR + limited paid |
| **Balenciaga** | Paris | High-concept campaign production | Editorial + OOH + limited paid |
| **Vetements** | Zurich | Subversive storytelling, anti-marketing marketing | Owned + cultural moments |

---

## 2. Teardown rubric (per competitor, per campaign)

Every competitor asset (ad, landing page, campaign lookbook) gets scored across 8 dimensions. Scores feed `brand_intel_agent.py`.

| Dimension | What to score (0–10) | How SkyyRose uses it |
|---|---|---|
| **Hook** | First 3 seconds: does it stop the thumb? | Informs TikTok/Reels hook templates |
| **Clarity** | Can a viewer name the product + price in 5s? | Informs product-card and landing copy |
| **Aspiration** | Does it make the viewer want the lifestyle? | Informs lookbook art direction |
| **Legibility** | Can all text be read on a phone? | Informs typography + safe zones |
| **Product identity** | Is the product the hero or buried in scene? | Informs composition briefs |
| **Social proof** | UGC, press, celeb, or none? | Informs handoff to SOCIAL_MEDIA for UGC seeding |
| **CTA friction** | Click to cart in ≤3 taps? | Informs landing page + checkout audit |
| **Brand cohesion** | Does the ad match the brand voice/IG feed? | Informs consistency across SkyyRose's channels |

Overall campaign score = mean of 8. Anything ≥ 8.0 becomes a "steal-worthy blueprint" and triggers `ad_blueprint_synth`.

---

## 3. Ad-creative harvest sources

### Tier A — official APIs (use first, legal + reliable)
- **Meta Ad Library API** — `graph.facebook.com/ads_archive` — pull active + inactive ads by Page, region, date
- **Google Ads Transparency Center** — public export via advertiser-id URL, scrape JSON payload
- **TikTok Creative Center** — `/top-ads` endpoint, public, returns top-performing ads

### Tier B — DOM scraping (only when Tier A unavailable)
- **Instagram @username highlights / feed** — via authenticated session only, respects rate limits
- **Brand landing pages** — HTML + screenshot, no auth required
- **YouTube ads** — embedded search via public API

### Tier C — manual (last resort)
- User uploads an ad screenshot or video; agent ingests via vision model

All scrapers live behind `SCOUT_LIVE_SCRAPE=1` env flag. Default mode uses fixtures in `tests/fixtures/competitor_ads/*.json`.

---

## 4. Ad-blueprint output schema

Every "steal-worthy" teardown produces a blueprint JSON consumed by `SOCIAL_MEDIA_SPEC` (for copy variants) and `IMAGERY_SPEC` (for visual briefs):

```json
{
  "source": {
    "brand": "Fear of God Essentials",
    "campaign": "Essentials Spring 25 launch",
    "url": "https://www.facebook.com/ads/library/?id=...",
    "harvested_at": "2026-04-20T06:30:00Z"
  },
  "scores": {
    "hook": 9,
    "clarity": 8,
    "aspiration": 9,
    "legibility": 10,
    "product_identity": 9,
    "social_proof": 6,
    "cta_friction": 8,
    "brand_cohesion": 10,
    "overall": 8.6
  },
  "blueprint": {
    "hook_pattern": "Close-up product swing → reveal wearer → tagline drop",
    "typography_rule": "Single display face, 72pt minimum on mobile, center-aligned",
    "color_grade": "Desaturated warm neutral, film grain subtle",
    "composition": "Product at rule-of-thirds intersection, negative space upper 30%",
    "copy_structure": "3-word headline + 1-line value prop + single CTA",
    "social_proof_slot": "Press quote in lower-third for 2s",
    "duration_seconds": 15,
    "aspect_ratios_tested": ["9:16", "4:5", "1:1"]
  },
  "skyyrose_adaptation": {
    "recommended_for_skus": ["br-007", "sg-005", "lh-003"],
    "collection_variant": "black-rose",
    "copy_hook": "Quiet luxury. Loud intention.",
    "handoff_to_social": true,
    "handoff_to_imagery": true,
    "estimated_cost_usd": 0.80
  }
}
```

Blueprints are written to `data/competitor_blueprints/<brand>-<campaign-slug>-<ts>.json` and are the primary handoff artifact between `COMPETITOR_SCOUT` and downstream Elite Team agents.

---

## 5. Scraping schedule (default cadence)

| Competitor tier | Cadence | Reason |
|---|---|---|
| Tier 1 peers | Weekly | Drop cadence matters — miss a campaign = miss a blueprint |
| Tier 2 gothic luxury | Monthly | Slow-burn brands, campaigns live longer |
| Tier 3 DTC machines | Daily during launch windows, weekly otherwise | High ad velocity = high blueprint volume |
| Tier 4 European luxury | Quarterly | Campaigns are editorial events, not weekly drops |

All cadence overridable via CLI arg when running `scripts/scout_run.py`.

---

## 6. Legal + ethical boundaries

- **Use official APIs wherever available.** Meta Ad Library and Google Ads Transparency are public-by-law.
- **Never scrape authenticated sessions without permission.** No Chrome-profile harvesting of private feeds.
- **Never claim another brand's creative as SkyyRose work.** Blueprints are reference-only, not reuse.
- **Attribute inspiration in internal artifacts.** The `source` block in every blueprint is mandatory and never stripped.
- **Respect robots.txt.** If Tier B scraping hits a disallowed path, abort and log.

---

## 7. Handoff contracts

### → SOCIAL_MEDIA_SPEC
- Input: blueprint `copy_structure`, `hook_pattern`, `duration_seconds`, `social_proof_slot`
- Output: 3–5 SkyyRose-voiced copy variants, A/B test hypotheses, platform-specific adaptations

### → IMAGERY_SPEC
- Input: blueprint `composition`, `color_grade`, `typography_rule`, `aspect_ratios_tested`
- Output: visual brief with style key, color grade target, composition rules, platform spec

### → brand_intel_agent.py (existing, wrapped)
- Input: full teardown scores + price data from competitor landing page
- Output: SWOT update, price-gap alert, threat-score change — fed to the brand learning loop

---

## 8. Files this agent reads / writes

**Reads:**
- `agents/core/analytics/sub_agents/brand_intel_agent.py` — wrapped competitor intel
- `services/competitive/competitor_analysis.py` — CRUD service
- `api/v1/competitors.py` — FastAPI endpoints (RBAC: strategy/marketing)
- `tests/fixtures/competitor_ads/*.json` — default fixtures when `SCOUT_LIVE_SCRAPE=0`

**Writes:**
- `data/competitor_blueprints/<brand>-<campaign-slug>-<ts>.json` — ad blueprints
- `logs/scout/<ts>.json` — harvest run logs
- Database: writes through `competitor_analysis.py` CRUD (not direct SQL)

**Never touches:** Live social APIs directly — all live scraping via `SCOUT_LIVE_SCRAPE=1` env flag and rate-limited adapters.
