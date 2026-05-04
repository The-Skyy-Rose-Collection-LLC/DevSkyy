---
name: KB Seed — Interview Capture (Corey, 2026-05-03)
description: Brand canon, aesthetic references, Oakland canon, engineering rules, and reality check captured directly from Corey during Phase 0 KB seed interview. This is autobiographical primary source material — treat as ground truth.
specified_by: [v2: §0.5 KB seed], [wp: §1.5 Layer 5]
phase: 0 (Phase 0 KB seed interview — Branch 3 Option C)
last_updated: 2026-05-03
last_updated_by: Phase 0 interview capture
authority: PRIMARY SOURCE — these are Corey's own words, not derived from code
---

# Interview Capture — Corey, 2026-05-03

**Context:** During Phase 0 KB seeding, the user provided four blocks of canon directly. This file captures them verbatim with light structuring. Every other KB file should defer to this when there is a conflict; this is autobiographical truth, not analysis.

**Cross-references:**
- Anti-references → integrate into [`eval/banned-elements.md`](../../eval/banned-elements.md)
- Visual references → integrate into [`eval/luxury-references.md`](../../eval/luxury-references.md)
- Brand voice/positioning → reinforces [`eval/brand-story.md`](../../eval/brand-story.md)
- Engineering rules → reinforces [`anti-patterns.md`](../lessons/anti-patterns.md)
- Reality check → drives priority for [decisions/](../decisions/)

---

## 1. Aesthetic + Brand

### Visual references (the brands SkyyRose triangulates against)

| Brand | What SkyyRose borrows |
|-------|----------------------|
| **KITH** | Editorial product storytelling, drop choreography, Ronnie Fieg's unapologetic curation |
| **Coach** | American luxury heritage reframed for street, leather craft authority |
| **Palm Angels** | Streetwear that carries through into elevated tailoring without losing identity |
| **Drake Related** | Personal narrative as product foundation, owner-as-author voice |
| **Aimé Leon Dore** | Quiet luxury, neighborhood specificity (NYC for ALD = Oakland for SkyyRose), throwback editorial |
| **Fear of God Eternal** | Restraint, monochrome, religious-grade craftsmanship language |
| **The Row** | Pure luxury minimalism — proof that quiet *is* expensive |
| **Jacquemus** | Cinematic campaigns, place-as-character (Provence for Jacquemus = Oakland for SkyyRose) |
| **Document / i-D** | Editorial photography sensibility — model is a person not a hanger |

**How to use this:** when generating imagery, copy, or layouts, ask "would this fit on KITH's product page or Aimé Leon Dore's lookbook?" If no, it's wrong. When triangulating in Phase 4 per WP §1.1 Pass 4, these are the primary three to study; the rest are tertiary.

### Anti-references (banned by default)

- **No blue** — at all. Not navy, not denim-blue, not powder. The brand palette is rose gold, dark, gold, crimson, silver. Blue breaks the canon.
- **No clichés** — luxury fashion has a vocabulary of "premium" tropes (gold filigree, marble countertops, champagne overlays, "iconic" anything). Banned.
- **No dry reveals** — product reveal animations that just slide-in or fade-in without narrative. Reveals must come with a story beat, not just a CSS transition.
- **No lackluster** — anything that feels safe, expected, brand-checklist-driven. Default mode is bold.
- **No dated** — visual language from 2015-2022 e-commerce templates is forbidden. No card-grid scroll-and-buy. No homepage hero-with-CTA-stack.

### Positioning principles

- **Gender-neutral, designed for everyone — no gendered framing ever.** Copy never says "for him" / "for her" / "men's" / "women's". Sizing exists; gendering doesn't.
- **Autobiography made wearable, not a mood board.** Collection names are memoir chapters of Corey Foster's life — not theme inspiration. "Black Rose" isn't a mood; it's a memoir entry.
- **Collection pages are cinematic editorial stories, never grids.** A collection page should read like an i-D feature, not a Shopify category page. Story → atmosphere → product as a beat in the story, never the headline.

---

## 2. Oakland Canon

The neighborhoods, places, and codes from Oakland that drive SkyyRose's geography. **These are referenced but never explained** — explaining them strips the authenticity. Either the customer knows or they don't; the ones who do feel seen, the ones who don't feel curiosity.

| Place | Status |
|-------|--------|
| **Deep East** | Canonical — East Oakland identity |
| **Oakland Hills** | Canonical — the elevation, both literal and class |
| **Stone City** | Canonical — Oakland street name |
| **The 100s** | Canonical — East Oakland numbered streets (100th Ave area) |
| **Brookfield** | Canonical — neighborhood |
| **Sobrante Park** | Canonical — neighborhood |
| **The Coliseum** | Canonical — Oakland Coliseum, A's / Raiders / Warriors history |
| **Real Oakland** | Canonical — distinguishing from gentrified Oakland |
| **The Shows** | Canonical — local code (do not gloss) |
| **Sequoyah Highlands** | Canonical — neighborhood |

**How to use this:** when writing product copy, collection narratives, founder voice, About page, or imagery direction — these names appear naturally as sentence fragments, not explained. "From The 100s." "Made for the Hills." Never "Made in The 100s, a neighborhood in East Oakland known for..." The lack of explanation IS the brand.

**Bay Area is not Oakland.** Per the hotfix branch from earlier today, "Bay Area" was scrubbed from immersive copy and replaced with "Oakland" / "The Town" in 7 places. The brand is Oakland-specific, not Bay Area-generic.

---

## 3. Engineering Rules

### Rule E1 — Identify verified source first, then execute with verified production code

**No token-wasting glob fishing.** Before writing code, read the canonical source for the data or behavior you're touching. The canonical sources are:

- Product data → `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` + `data/dossiers/{slug}.md`
- Brand canon → this file + `eval/brand-story.md`
- Architecture decisions → `knowledge-base/decisions/` + `docs/adr/`
- Locked decisions → `docs/SKYYROSE_V2_MASTER_PLAN.md` §1.1
- Per-page intent → `docs/SKYYROSE_WORDPRESS_PLAN.md` §6

If you don't know which source is canonical for what you're touching, **stop and ask**, don't grep blindly. The pattern of `grep -rn "X" .` 12 times to find one definition is exactly the waste this rule forbids.

**How to apply:** when about to start a task, write the source(s) you'll consult in one sentence first. If you can't name the source, you don't have the context to start.

### Rule E2 — Don't apologize, fix

**Silent correction, only final accurate output.** When you make a mistake:

1. Fix it. No "I apologize for the confusion."
2. The fix IS the apology. Showing the corrected output IS the acknowledgement.
3. If a one-sentence root-cause matters for the user to know, write it once, terse: "Was using stale catalog data, now reading the CSV."
4. Move on.

**How to apply:** strip every "I apologize" / "Sorry for the confusion" / "Let me clarify" / "You're right, my mistake" preamble. Just deliver the corrected work. The cerebrum + memory.md + buglog.json captures the lesson; the user doesn't need to read the apology.

This rule generalizes the existing CLAUDE.md "Communication" section — but Corey wants it sharper: the silent correction *is* the communication.

---

## 4. Reality Check (current state, 2026-05-03)

### #1 Blocker: Imagery generation

**Imagery generation is the single biggest thing keeping skyyrose.co from going live.** The product catalog has 33 SKUs but most don't have production-grade renders that match the editorial aesthetic. Until the imagery pipeline reliably produces:

- Editorial-quality product shots (not technical flats)
- Scene compositing that matches Oakland canon
- Consistent quality across all 33 SKUs
- Front + back + branding views per SKU

...the site cannot go live as a luxury brand. Every other unfinished thing (tracking, drop mechanics, AR, semantic search, WebXR) is a nice-to-have compared to "the products look like luxury products on a luxury site."

**How to apply:** when prioritizing Phase 5+ work, anything that improves imagery generation reliability or quality jumps the queue. AR try-on (5.6), product shoot replacement (parallel ML pipeline work), Compositor agent reliability, Nano Banana / GPT-Image / FLUX quality bar — these are #1, ahead of WebXR or drop mechanics.

This may shift the V2 §5 phase order. Worth surfacing as a Phase 5 sequencing question before Phase 5 begins.

### Unexpected Win: Aesthetic translation of vision

**Translating Corey's autobiographical vision into the build is the unexpected win — protect it.** The brand-story.md, the collection memoir framing, the Oakland canon, the cinematic editorial direction — these are coming through into the implementation in a way Corey didn't expect to be possible from a code agent.

**How to apply:** anywhere a decision could erode this (e.g., "let's just use a standard product grid for collections" or "let's drop the editorial story for SEO" or "let's add filters and sort options"), push back. The aesthetic translation IS the differentiator. Don't sacrifice it for conventional e-commerce patterns. The plan calls these out in WP §1.3 banned-elements and V2 §1.1 locked decisions — keep enforcing them.

---

## What this changes downstream

| Downstream artifact | What to update |
|--------------------|----------------|
| `eval/banned-elements.md` | Add: no blue, no clichés, no dry reveals, no lackluster, no dated, no gendered framing, no grid-style collection pages |
| `eval/brand-story.md` | Reinforce: autobiography made wearable, collection-as-memoir-chapter framing, Oakland-not-Bay-Area |
| `eval/luxury-references.md` | This file is Phase 4 deliverable — the 9 visual references above are the seed for triangulation; pick 3 (recommend KITH, Aimé Leon Dore, Jacquemus) for Phase 4 deep-study |
| `knowledge-base/lessons/anti-patterns.md` | Already covers most engineering anti-patterns; add an explicit AP-16 for "glob fishing instead of consulting canonical source" |
| `knowledge-base/decisions/0003-*.md` | NEW — record the imagery-as-#1-blocker decision so Phase 5 sequencing reflects it |
| `eval/critique/current-site-audit.md` | The §3 audit verdict should weight imagery quality heavier in light of the reality check |
| `wordpress-theme/skyyrose-flagship/template-parts/landing/` | Confirm all landing pages use editorial story flow, not grid-and-CTA |
| `wordpress-theme/skyyrose-flagship/template-collection-*.php` | Audit per the "never grids" rule |

I will action these downstream updates as a follow-up, with Corey's confirmation on the priority order.
