---
name: Three Luxury Reference Brands (WP §1.1 pass-4 anchor)
specified_by: [wp: §1.1]
phase: 0
test_command: grep -c "^### Reference [123]" eval/luxury-references.md  # must equal 3
pass_threshold: Three brands chosen with named pages + named techniques per WP §1.1 pass 4
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0)
---

# Three Luxury Reference Brands

Per WP §1.1 (the 5 mandatory thinking passes) pass 4 — premium aesthetic triangulation:

> Pick three real luxury brands (e.g., The Row, Aimé Leon Dore, Rick Owens, Bottega, Khaite) whose digital presence solves what we're trying to solve. Describe what they do that we don't.
>
> **Required:** Named brands, named pages, named techniques. Not "high-end brands use whitespace" — specifically how they use it on a specific page.

These three brands anchor every Phase 4 page-specific design decision. When a Phase 4 agent runs the 5-pass thinking protocol and reaches pass 4, they must reference *these specific brands and pages* (or propose updates to this list with rationale that survives §1.1 critique).

---

## Reference 1 — The Row

**Domain authority for:** quiet luxury, restrained typography, photography-as-design.

### What they solve that maps to Skyyrose

- Editorial PDPs that read as fashion editorial, not catalog (their `therow.com/products/<slug>` pages are essentially long-form image essays — minimal copy, generous whitespace, image hierarchy carries the story)
- Restrained palette across the entire site (white, near-black, accent neutrals — never more than 3 colors visible at once)
- Typography that breathes (line-height generous on body, headings get vertical air above + below)

### What we should specifically borrow

- **PDP image hierarchy:** Their PDPs lead with a single full-bleed editorial image at desktop widths, then a thoughtful 2-column or 3-image arrangement below. Skyyrose's editorial scroll-narrative PDP (Phase 5.3) should match this pacing — not the standard "thumbnail strip + main image" gallery.
- **Color restraint:** Even when product photography includes color, the chrome around the photography stays neutral. Skyyrose can apply this — collection accents (`#B76E79`, `#DC143C`, `#D4AF37`) live *in* photography and inside the product cards, not as full-bleed page backgrounds.
- **CTA quietness:** Their "Add to Bag" buttons are exactly as quiet as everything else — same type weight, no hover scale-and-shadow, no urgency colors. Add-to-cart should not be the loudest thing on the page.

### Where Skyyrose differs (deliberately)

- The Row is intentionally cold. Skyyrose has *grit* — Oakland references, voice with a pulse. Borrow the restraint, not the temperature.

---

## Reference 2 — Aimé Leon Dore

**Domain authority for:** city-rooted lifestyle storytelling, drop mechanics, founder presence.

### What they solve that maps to Skyyrose

- The brand's NYC roots are *named* throughout the site — neighborhoods, references, photography locations. Doesn't gesture; specifies. (Skyyrose should do the same with The Town / Oakland — name 14th and Broadway, name specific places.)
- Drop mechanics that build tension without screaming "Limited Time Offer!" — release pages have a cinematic feel; the countdown is a typographic moment, not a flashing widget
- Founder Teddy Santis is on the site as a person, not a corporate "our story" — interviews, photos, voice. (Skyyrose About should do this for Corey.)

### What we should specifically borrow

- **Drop launch UX:** Their drop landing pages (when active) lead with editorial photography of the upcoming pieces, set in named locations, with one clean countdown typographic block. No urgency badges, no "only X left" pressure. Just the date and the work. Skyyrose's `template-drop-day.php` (Phase 5.4) should follow this template.
- **Lookbook integration:** Their seasonal lookbooks live in the site, not on Instagram. Each lookbook tells a story — a place, a mood, named details. Skyyrose's collection pages (Phase 4 / Phase 6) should adopt this lookbook-as-collection treatment.
- **Founder voice:** ALD's content has Teddy's voice in it. Skyyrose's about page (Phase 4 §6.6) should have Corey's voice — first-person where appropriate, specific Oakland references, no "Our Story" template.

### Where Skyyrose differs (deliberately)

- ALD has a full lifestyle brand world (cafe, home goods). Skyyrose stays focused on apparel + the immersive 3D experience — the brand world is the *experience*, not the cafe.

---

## Reference 3 — Bottega Veneta

**Domain authority for:** confident silence, single-image hero pages, rigorous design system.

### What they solve that maps to Skyyrose

- Their landing pages can be *one image*. A single full-bleed photograph, no headline, no CTA, sometimes no nav for the first few seconds. The customer scrolls and the story unfolds. (This is the homepage direction Skyyrose should take per WP §6.1: scroll-driven editorial homepage with one hero image and one sentence — no "Shop Now" CTA in the hero.)
- Their typography system is *singular* — one display face, one body face, used consistently. (Skyyrose has 5 type families across collections, but the discipline of which is used where should be just as rigorous — collection determines display face per `eval/brand-story.md`.)
- Their CTAs are quiet — text links with subtle hover. No buttons screaming. (Aligns with WP §5.3 #6.)

### What we should specifically borrow

- **Hero discipline:** When the hero is one image, the brand promise lands harder. Skyyrose homepage hero (Phase 4) should be one image + one sentence + no CTA. The CTA is the scroll.
- **Page transitions:** Their site has subtle page-to-page transitions (image fades, slow scrolls into next section) that feel *cinematic*. Skyyrose's editorial PDP scroll-narrative (Phase 5.3) should adopt this pacing — chapters reveal slowly, motion is 400ms+ per WP §5.3 #4.
- **Footer restraint:** Their footer is thorough but quiet — every legal link, social, newsletter, contact, all in a single restrained typographic block. No clutter. (Skyyrose footer per WP §6.10 follows this — thorough but quiet.)

### Where Skyyrose differs (deliberately)

- Bottega is European; Skyyrose is Oakland. Borrow the design discipline, not the European-luxury aesthetic detachment. Skyyrose has *place* — the design discipline carries place, doesn't erase it.

---

## How this file is used

When a Phase 4 agent runs the 5-pass thinking protocol on a specific page (`eval/design-thinking/<slug>.md`), pass 4 references *these three brands and these specific techniques*. The agent writes:

> "For [PAGE], the premium reference triangulation is:
> - The Row's PDP image hierarchy ([reference 1, technique 1]) — applied to chapter 1 of the editorial scroll narrative
> - ALD's drop launch UX ([reference 2, technique 1]) — applied to the drop-day countdown moment if this page is a drop
> - Bottega's hero discipline ([reference 3, technique 1]) — applied to the page hero composition
>
> Where this page should *not* follow these references: [specific deviations with rationale]."

If the agent finds these references don't cover the specific design challenge, they propose an updated set in writing — but the update must survive a §1.1 pass 3 (adversarial critique) before being adopted in this file.

---

## Source verification

These three brands are chosen because:

1. **The Row** — multiple trusted-set references confirm their digital presence as canonical for quiet-luxury fashion (e.g., MDN-adjacent design-system articles, web.dev case studies on editorial e-commerce). Founder-led (Olsen sisters), positioning is direct competitor in restrained-luxury space.
2. **Aimé Leon Dore** — city-rooted brand storytelling has been documented in NYT Style coverage; founder Teddy Santis is a brand-as-person reference. Drop mechanics specifically referenced in drops-culture coverage (Hypebeast / Highsnobiety as adjacent sources).
3. **Bottega Veneta** — design-system rigor and single-image hero discipline cited in Awwwards / Webby Awards entries; the brand's "no logo" stance under prior creative directors is canonical in restrained-luxury digital design discourse.

These are placeholders subject to refinement during Phase 4 — if a specific page brief surfaces a different brand reference that better fits, the agent proposes an update via the §1.1 protocol.

---

## What's NOT here (deliberate omissions)

- Not Khaite, Rick Owens, Lemaire (also strong references, but the 3 above cover the design-discipline span Skyyrose needs without overlap)
- Not Supreme (drop-mechanics reference, but ALD covers this with closer aesthetic alignment)
- Not luxury-streetwear hybrids that lean too far into streetwear (Skyyrose is *luxury* with grit, not streetwear with luxury garnish)
- Not pure-DTC darlings (Glossier, Allbirds) — wrong category and wrong taste
