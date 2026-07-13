# Skyy — Brand Character System Scope

**Mission:** full-body character who walks onto the page, guides customers through skyyrose.co, talks when they need website advice, gives styling pointers, and becomes the face of the brand. NOT a chatbot widget — a living character (canon, 2026-03: "full-body walk-on, not a chatbot").

**Grounded in existing infra (verified 2026-07-02):**
- `template-parts/skyy-mascot.php` (141 L) + `assets/js/mascot.js` (411 L) + `assets/js/skyy-3d.js` (300 L) + `assets/css/mascot.css` (573 L) + `assets/css/skyy-walk.css` (159 L) — complete walk-on presentation layer, **currently dequeued** (`inc/enqueue.php:207,363` — "until art is finalized")
- `inc/ajax-handlers.php:551` `skyyrose_ajax_mascot_chat()` — AJAX seam, IP rate-limited
- Canonical face locked: `assets/images/mascot/skyy-canonical.{avif,webp,jpeg}`
- 3D state (March handoff): raw Meshy mesh (9.1MB, HF-mirrored), v1/v2 retextures rejected (wrong outfit/too dark), **v3 text-only prompt authored and ready**; rigging never done
- Walk-on choreography already defined per collection: Love Hurts=right, Black Rose=left, Signature=right; scroll-trigger 30%, squash-and-stretch, breathing idle, blink, joy-jump

---

## Pillar 1 — Character art convergence (the blocker everything waits on)

| Step | What | Cost | Gate |
|---|---|---|---|
| 1.1 | Meshy retexture **v3** — text-only prompt from handoff (warm caramel skin, LH varsity outfit: white satin body/black sleeves/"Love Hurts" chest script/white joggers w/ rose embroidery) | ~$0.50–2 | STOP-AND-SHOW |
| 1.2 | Eyes-on QC vs `skyy-canonical` face — same fidelity discipline as product renders; founder approves | free | founder y |
| 1.3 | Per-collection outfit variants (Signature gold / Black Rose silver-on-black / Kids) — LATER phase, one outfit ships first | ~$0.50 ea | deferred |

Fallback path (zero-cost, ships tomorrow): 2D sprite walk-on — `skyy-walk.css` system is already built; needs a sprite sheet rendered from the canonical face (OAI gpt-image-2, ~$0.30, STOP-AND-SHOW). 3D is the destination; 2D can launch the character while rigging finishes.

## Pillar 2 — Rig + animate (free)

1. Approved GLB → Mixamo (auto-rig) → download clips: **Walk, Breathing Idle, Wave, Point, Talk gesture, Joy jump**
2. Merge clips into one GLB (Three.js AnimationMixer track names), Draco-compress to ≤3–4MB
3. Fidelity gate on the rigged result (same `glb_fidelity.py` harness — face ΔE vs canonical)

## Pillar 3 — Walk-on presentation (theme, upgrade existing 1.6k lines)

- `skyy-3d.js` → GLTFLoader + AnimationMixer path replaces CSS sprite in `buildAvatarHotspot()` (exact step named in the March handoff)
- Entrance: walks in from the collection-assigned side on scroll-trigger; idle loop + blink; exits on dismiss
- **Perf budget (non-negotiable):** lazy-load after `requestIdleCallback` + first interaction — zero LCP/CLS impact; GLB self-hosted (no new CSP origins)
- **A11y:** `prefers-reduced-motion` → static pose fade-in; bubble text in `aria-live=polite`; ESC dismiss; never traps focus
- **Kill switch:** Customizer toggle `skyyrose_mascot_enabled` (default off until founder flips) + per-template exclusion (checkout stays clean)
- Mobile: smaller scale, bottom-corner anchor, tap-to-open (no hover)

## Pillar 4 — Guide brain (two tiers)

**Tier 1 — deterministic (free, instant, ships first):**
- Page-aware: body classes + a generated `site-guide.json` (built from WP menus + template map — **no hardcoded nav**, per standing invariant)
- Scripted intents: "where do I find X" → deep link; sizing → fit-notes/size guide; shipping/returns → policy pages; order tracking → account
- Per-page tips (1–2 lines each, Customizer/JSON-editable): e.g. pre-order page → "reserve your size now, drops ship in 4–6 weeks"
- Presented as speech bubble with typed-text effect — the character talks; no chat window

**Tier 2 — LLM advice (paid per-use, config-gated, phase 2):**
- Existing AJAX seam → FastAPI (`api/v1`) → Claude Haiku 4.5, system prompt = brand canon + from-interview voice + catalog RAG (existing `orchestration/` RAG)
- Hard caps: existing IP rate limit + daily token budget + generic-error fallback to Tier 1
- No PII collected; conversation not persisted client-side beyond session

## Pillar 5 — Styling pointers

- Data: catalog CSV + dossiers + curated `product-similarities.json` (editorial pairings, founder-approvable)
- Delivered **conversationally** ("that hoodie runs relaxed — the Black Rose beanie finishes it") — **canon boundary:** no product-grid recommendations rendered on PDP (2026-05-27: garment is protagonist). Spoken pointers = allowed surface; rendered rec-modules = not.
- Fit notes meta (batch-c metabox) feeds sizing answers

## Pillar 6 — Voice & personality

- Name: **Skyy**. Young, warm, Oakland-rooted; luxury-streetwear register from brand canon
- Copy rules: never discount-talk, never urgency timers, no corporate support-bot phrasing
- All scripted lines authored against `docs/brand/collection-stories.md` + from-interview.md (SOT-verbatim discipline)

---

## Phasing + costs

| Phase | Deliverable | Cost | Wall time |
|---|---|---|---|
| **P0** | v3 retexture + founder art approval (+ optional 2D sprite fallback) | ~$1–2 | 1 session |
| **P1** | Rig, 6 clips, merged compressed GLB, fidelity-gated | $0 | 1 session |
| **P2** | Walk-on live behind Customizer flag (GLB path in existing JS) | $0 | 1–2 sessions |
| **P3** | Guide brain Tier 1 (site-guide.json + intents + page tips) | $0 | 1 session |
| **P4** | Styling pointers data + voice copy pass | $0 | 1 session |
| **P5** | LLM Tier 2 (Haiku, capped) + per-collection outfits | per-use + ~$2 | later |

Rollout: flag-on for founder only → homepage + collections → sitewide (checkout excluded).

## Founder decisions needed

1. **Art path**: 3D-first (P0 Meshy v3, ~$1–2) vs 2D-sprite-launch-now + 3D behind it
2. **Launch surface**: homepage + 4 collections first, or everywhere at once
3. **LLM tier at launch**: on (capped) or Tier-1-only until traffic proves demand
4. Confirm v3 outfit = Love Hurts varsity as the default sitewide look
