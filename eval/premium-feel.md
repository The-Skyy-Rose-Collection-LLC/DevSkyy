---
name: Premium-Feel Sitewide Checklist (WP §5.3)
specified_by: [wp: §5.3]
phase: 0
test_command: node scripts/measurement/check-premium-feel.js
pass_threshold: All 10 items honored sitewide; auto-checkable items pass; subjective items reviewed
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0)
---

# Premium-Feel Sitewide Checklist

The 10 small moves that, individually, no one notices — but collectively make the site feel premium. They are mandatory. Phase 6.8 audits all 10 sitewide.

---

## The 10 items

### 1. Typography breathes

- **Rule:** Line-height ≥ 1.5 on body copy. Headings get more whitespace above than below.
- **Auto-check:** Computed style audit on representative pages — `line-height` on `body, p, li` ≥ 1.5
- **Manual check:** Visual review — does the typography feel cramped or breathing?

### 2. Images are the design

- **Rule:** Photography is the main visual element. Text supports the photo, never competes.
- **Auto-check:** None — subjective
- **Manual check:** On hero sections, can the design carry the moment without the text? On collection pages, does text ever upstage the imagery?

### 3. Whitespace is currency

- **Rule:** When in doubt, more space. Generic sites cram; premium sites breathe.
- **Auto-check:** Spacing tokens are in scale (4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96 / 128) — no arbitrary values per `assets/css/design-tokens.css`
- **Manual check:** Above-the-fold spacing on homepage, PDP, collection pages — is there room for the design to breathe?

### 4. Motion is slow

- **Rule:** Default duration 400ms, not 200ms. Eases are smooth, not bouncy.
- **Auto-check:** Computed style audit on `transition-duration` and `animation-duration` — defaults to 400ms or one of the named motion tokens (150 / 250 / 400 / 800ms)
- **Manual check:** Hover/scroll motion — does it feel rushed?

### 5. Hover states earn their place

- **Rule:** A subtle weight shift, a 1px border underline, an image fade. Not a scale + shadow + color flip.
- **Auto-check:** Audit `:hover` selector cardinality — flag any `:hover` with 3+ properties changed simultaneously
- **Manual check:** Walk through hover states on every interactive element — are they restrained?

### 6. Buttons don't shout

- **Rule:** No gradient buttons. No box-shadows on buttons. No all-caps unless the type system asks for it.
- **Auto-check:** Grep `assets/css/` for `linear-gradient` on `.btn`, `.button`, `[type=submit]`. Grep for `box-shadow` on same. Grep for `text-transform: uppercase` on same — flag if not Anton (which is designed for caps).
- **Manual check:** Are buttons quiet but clear?

### 7. Loading states are designed

- **Rule:** No default browser spinner. A typographic indicator or a measured skeleton.
- **Auto-check:** Grep JS for `<input type="submit">` without custom loading state handler; grep for default-browser loading patterns
- **Manual check:** Trigger every loading state on the site — search submit, add-to-cart, checkout, FASHN try-on — does each have a designed indicator?

### 8. 404 / empty states have personality

- **Rule:** They are the signature moves. A blank empty cart is a brand miss.
- **Auto-check:** None — subjective
- **Manual check:** Visit /404, empty cart, search with zero results, empty wishlist — each must have brand-coherent personality (a sentence in voice, an editorial visual moment, NOT a default WC empty state)

### 9. Form errors are graceful

- **Rule:** Inline, not toast. Specific, not "Something went wrong."
- **Auto-check:** Grep template-parts/components/form.php and any form handlers for toast-only error patterns
- **Manual check:** Trigger every form error on the site (checkout invalid card, contact missing field, newsletter invalid email) — each error appears inline next to the field, named specifically (not "Something went wrong")

### 10. The cursor

- **Rule:** A subtle custom cursor on hero areas — only if it's tasteful and only if it's optional.
- **Auto-check:** Grep `assets/css/` for `cursor:` rules — flag if applied broadly
- **Manual check:** Is the custom cursor (if used) tasteful, optional (toggle present), and `prefers-reduced-motion` aware?

---

## Sitewide test command

```bash
node scripts/measurement/check-premium-feel.js
```

Auto-checks items 1, 3, 4, 5, 6, 7, 9 (the rule-based ones). Items 2, 8, 10 require manual judgment by `polish` skill or `Brand Guardian` agent.

Exit 0 = all auto-checks PASS + manual judgment recorded; 1 = any auto-check FAIL; 2 = auto-checks PASS but manual judgment missing.

---

## Per-page row format (Phase 6.8)

```yaml
---
page: <slug>
item_1_typography_breathes: <PASS | FAIL: <details>>
item_2_images_are_design: <PASS | FAIL | N/A>
item_3_whitespace: <PASS | FAIL>
item_4_motion_slow: <PASS | FAIL>
item_5_hover_restrained: <PASS | FAIL>
item_6_buttons_quiet: <PASS | FAIL>
item_7_loading_designed: <PASS | FAIL | N/A>
item_8_empty_states_personality: <PASS | FAIL | N/A>
item_9_form_errors_graceful: <PASS | FAIL | N/A>
item_10_cursor: <PASS | FAIL | N/A>
last_evaluated: <YYYY-MM-DD>
agent: <Brand Guardian | polish | manual>
---

<prose: any nuance, FAIL remediation plan>
```

---

## Phase entry checklist

- Phase 0 establishes the rubric (this file)
- Phase 4/5 per-template work spot-checks the items as it goes
- Phase 6.8 brand consistency sub-phase runs all 10 sitewide
- Phase 7 ship-check re-runs the auto-checks; gate fails on any auto-check FAIL or any manual judgment recorded as FAIL
