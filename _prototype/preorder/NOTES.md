# Pre-order gateway page prototype — THROWAWAY

**Question:** What should the *whole* pre-order gateway page look like — not a section swap,
3 structurally different information architectures for the same page. Delete this directory
once a verdict is picked and folded into `template-preorder-gateway.php`.

## Run it

```bash
cd _prototype/preorder && python3 -m http.server 8912
# → http://localhost:8912/
```

Bottom bar switches variant. `←/→` also cycle. Every state is a URL: `?variant=B` — paste one
back to name a winner exactly.

## Founder-locked constraints (verified via memory search + live file before building)

- **Video hero required** — founder decision (mem #14404): the page must include a video
  element and be optimized for conversion, not just contain product photography.
- **Exactly 3 gateway collections** — Black Rose, Love Hurts, Signature. Kids Capsule is
  **excluded from the gateway** (mem #14435, confirmed against the live 8-section template —
  `grep` for `kids.?capsule`/`kc-` in this prototype returns 0 matches).
- **No fake urgency** — no reserve-count, no countdown. `skyyrose_preorder_meters_enabled`
  defaults `false` in production; this prototype never fabricates a number (`grep` for
  countdown/left/remaining/claimed patterns returns 0 matches).
- Live template today (885 lines, `preorder-gateway.css` 1150, `.js` 575) already ships 8
  sections in this order: hero → gateway (3-panel selector) → products (grids) → journey →
  lookbook → manifesto → faq → email-capture. The old `#9766` countdown/class-mismatch bug is
  confirmed resolved and not reintroduced here.

## The variants

| | A — Single-scroll spine | B — Collection-first sticky rail | C — Product-led editorial spread |
|---|---|---|---|
| **Shape** | Linear stack, closest to today's production order, rebuilt clean | Compressed hero → a **sticky** tab rail fused with the product grid in one interactive unit | Hero **splits** into video + first product immediately visible; each collection is a woven spread |
| **Collection choice** | Scroll past 3 stacked full-width bands | Click a tab, grid swaps in place, **no re-scroll** | Anchor-jump pills to 3 full spreads |
| **Trust content** | Separate "journey" timeline section | One compact strip under the grid | One strip, shown **once**, near the top |
| **Thesis** | Control baseline | Minimize scroll-distance between "see it" and "reserve it" — highest structural CRO bet | Sell product visually first; editorial + trust ride alongside, not as separate scroll-stops |

All three use the same real assets: self-hosted brand woff2, real collection logos, and the
**same already-shipped on-model photography** (`br-006`, `lh-004`, `sg-009` — copied from
`wordpress-theme/skyyrose-flagship/assets/images/products/` in the main checkout, since this
worktree is sparse-checked-out and doesn't carry product renders). **Hero video is the real
production asset** — `assets/video/preorder-hero.webm`/`.mp4` from the main checkout (65.1s,
720×1280 portrait, VP9), verified by extracting and viewing actual frames (not filename-trust):
a young man in a Black Rose satin bomber, sitting on a bench smoking at night. Because it's a
portrait clip inside a wide hero box, all 3 variants use `object-fit: contain` (not `cover`) so
the outfit is never cropped — at wide desktop widths this reads as a narrow, centered video
column with dark margins either side (visible in the screenshots below). That's a deliberate
consequence of not cropping the founder's chosen footage, not a layout bug — flagging it here so
a verdict isn't accidentally cast on that framing choice alone.

**Horizontal scroll-snap collection-logo rail** — the actual feature asked for ("the video hero
should be the hero with the guy smoking, then a more scroll-world esk type feel" / "horizontal
scroll feature of all the collection logos"). Reuses the same locked pattern as the homepage
prototype's chosen chooser (`_prototype/homepage/NOTES.md`: swipe-through rooms as true
horizontal scroll-snap, real "Enter <Collection>" CTAs). All 3 variants get a `.logo-rail` of 3
snap-aligned cards (Black Rose / Love Hurts / Signature), each a real "Enter <Collection>" link:
- **A** — sits directly under the hero, plain anchor-jump to each band (`#gateway`/`#love-hurts`/`#signature`).
- **B** — sits directly under the hero, above the sticky tab rail; clicking a card calls the
  same `selectCollection()` function the tab buttons use and smooth-scrolls to the stage — it's
  a second entry point into B's existing interactive picker, not a competing one.
- **C** — sits after the trust-row (once C has already sold the first product), replacing the
  old text-only `.jump-nav` pills with the same logo-card treatment, anchor-jumping to each
  `.spread`.

An earlier scroll-reveal (fade/rise-in) pass was built and then **removed** — see bug-310 below.

## Verification — run 2026-07-29

| Check | Result |
|---|---|
| index + tokens + section serve | **200** each `[repro]` |
| 3 named variants | **3/3** `[repro]` |
| Every asset ref (fonts, logos, product images, hero video) | **200**, none 404 `[repro]` |
| Fake urgency (countdown/left/remaining/claimed patterns) | **0** `[repro]` |
| Kids Capsule leaked into the gateway | **0** `[repro]` |
| Cut fonts (Playfair/Cormorant/Bebas/Yellowtail) in actual markup | **0** — the only matches are tokens.css's own explanatory comment documenting what was replaced `[repro]` |
| Variants genuinely differ structurally | Confirmed visually via Chrome screenshots at 1440×900 — distinct DOM shapes (A: linear `.band` stack; B: `.rail` + swappable `.product-view`; C: `.hero-split` + repeated `.spread`) `[repro]` |
| Hero video plays, portrait framing not cropped | Extracted + viewed real frames via `ffmpeg`; confirmed `object-fit: contain` renders full outfit at 1440×900 in all 3 variants `[repro]` |
| Logo rail: 3 cards, correct hrefs/handlers, no overflow at desktop width | DOM geometry check (`getBoundingClientRect()`) at 1440px — 3 equal-width cards, no scroll needed `[repro]` |
| Logo rail: B's cards drive the same tab-switch as clicking a tab | Clicked "Enter Love Hurts" card → Love Hurts tab highlighted + product panel swapped + smooth-scrolled to stage `[repro]` |
| Mobile (390×844): B vs C structural distinctness | **B** keeps its sticky tab rail as a clearly separate interactive component at any width. **C**'s `.hero-split` collapses from a side-by-side grid to a single stacked column below 860px — visually closer to A's linear shape at mobile widths than at desktop, though its "first product" panel still differs from A's gateway bands `[repro]` |
| Leaked into production | **No** — `_prototype/` sits outside `wordpress-theme/skyyrose-flagship/`; `git status` shows only `_prototype/` untracked, `template-preorder-gateway.php` untouched `[repro]` |

## Bug found and fixed during verification

**Variant B's collection tabs did nothing on click.** Root cause: the swap script was placed as
a **sibling** of `<div class="poB">` (right after its closing `</div>`), not a descendant.
`document.currentScript.closest('.poB')` walks the script element's own ancestors — a sibling
script has no such ancestor, so `closest()` silently returned `null` and every
`querySelectorAll`/`addEventListener` call below it threw before attaching a single listener.
Symptom: clicking "Love Hurts" or "Signature" visually did nothing; "Black Rose" stayed
selected forever. Fix: moved the `<script>` to be the last child **inside** `.poB`. Reproduced
with a real Chrome click before the fix (confirmed broken), re-tested after (confirmed the tab
switches and the grid swaps). This is the same class of bug as the homepage prototype's
double-execution fix — template-cloned inline scripts execute correctly, but only if they
actually live where their own DOM-relative lookups expect them to.

## Bug found and fixed: reveal animation could go permanently invisible (bug-310)

A first pass at the "scroll-world-esque cinematic feel" hid `[data-reveal]` content by default
(`opacity: 0`) and revealed it via an `IntersectionObserver`, deferred behind a
`requestAnimationFrame` call to dodge a suspected layout race. Direct DOM inspection across
repeated reloads showed inconsistent results — sometimes revealed, sometimes stuck invisible
after 8+ seconds. Debug logging proved the root cause: **`requestAnimationFrame`'s callback
never fires at all** in the Chrome DevTools MCP automation tab (consistent with rAF throttling
on a non-compositing/background tab). Any hide-until-JS-fires default is unsafe regardless of
environment — it turns "not yet revealed" into "permanently invisible" the moment its trigger
doesn't run, and this prototype exists to be *looked at*. Fix: removed the hide-by-default CSS
and the whole `IntersectionObserver`/rAF reveal pass; content now renders unconditionally.
Parallax was kept — it has no rAF/IntersectionObserver dependency, so a scroll listener that
never fires just means no drift, never invisible content.

## Kids Capsule added as a 4th gateway collection (founder direction mid-session)

The founder-locked constraint above (mem #14435, exactly 3 collections, KC excluded) was
**explicitly reversed this session** — direct instruction: "kids capsule need to be added,"
confirmed via clarifying question to use a real KC asset rather than a coming-soon placeholder.
Added to all 3 variants + all 3 logo-rails using **kids-001** (Kids Colorblock Hoodie Set —
Red/Black, real catalog SKU, $65, verified via vision against `kids-001-onmodel-v2.webp` — a real
on-model shot, not a ghost/ghost-flat like kids-002's only front image) copied from the main
checkout (present locally in this worktree despite earlier assumption of sparse-checkout absence
— verify assumptions each time, don't carry them forward). KC has no bespoke image lockup like
the other 3 (brand canon: its accent is the Grand Hotel **webfont**, not custom artwork), so its
rail card and section headers render a real `Grand Hotel` text wordmark instead of an `<img>`.
CTA color uses the existing `--accent-kids` token (= `--rose-gold`, already declared but unused
in this shared token file) with black text, matching the silver/gold lighter-background pattern.
Copy's first line ("Luxury runs in the family.") is the Brand-Guardian-approved KC tagline from
the completed "Inheritance of Elegance" campaign (2026-07-27), not invented.

Verified: all 3 variants render the 4th collection correctly (screenshots); B's rail card and
tab both drive the same `selectCollection()` function (real click, panel swapped, CTA
rose-gold) `[repro]`; at 1440px desktop the rail now *genuinely* overflows with 4 cards
(`scrollWidth` 1822 > `clientWidth` 1440, confirmed via `getBoundingClientRect`) where it didn't
with 3, so the "horizontal scroll" behavior is validated at a normal desktop width, not just
mobile `[repro]`. **Not cleanly reproduced:** A/C's native `<a href="#kids-capsule">` anchor-jump
via a real click in this Chrome DevTools MCP tab — repeated attempts hit a reproducible mismatch
between JS-reported scroll state and what the screenshot tool captured (the same class of
automation-tab quirk as bug-310's rAF issue). These are plain, unmodified anchor tags with no JS
attached in A or C — high confidence they work via ordinary browser behavior, but flagging the
gap rather than claiming a clean repro `[inferred]`.

## Known gaps

- Product images are single representative shots per collection (`br-006`/`lh-004`/`sg-009`),
  not the full per-SKU grids the live page renders from WooCommerce — this prototype is judging
  page *architecture*, not final product-grid population.
- Variant B's `black-rose-logo.webp` renders visibly stretched at `height: 48px` (the source
  lockup's native aspect doesn't match that box) — a production nit, not a structural question.
- This prototype answers the **page-design** question only. Untouched: the structural refactor
  of `template-preorder-gateway.php` (split into template-parts, fix 11 PHPStan errors) planned
  separately in `.claude/plans/glimmering-crafting-shannon.md` Phase C; and the homepage v3
  rebuild, which is uncommitted with its own Verify phase never completed.

## Verdicts — awaiting review

| Winner | Why / what to steal from the others |
|---|---|
| _(not yet picked)_ | |

Once a winner is named here, rewrite it into `template-preorder-gateway.php` (not pasted — this
markup was written under prototype constraints: no tests, no error handling, no PHP escaping,
no WooCommerce wiring). Then delete this `_prototype/preorder/` directory.
