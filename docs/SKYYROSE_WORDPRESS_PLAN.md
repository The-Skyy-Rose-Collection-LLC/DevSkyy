# SKYYROSE WORDPRESS PLAN — skyyrose.co

**Scope:** The WordPress.com site only. Theme, WooCommerce, content, design, brand, conversion.
**Out of scope here:** Vercel API routes, FASHN, Pinecone, WebXR, Claude Lab. Those live in `SKYYROSE_V2_MASTER_PLAN.md`. This plan owns: Everything a customer sees and touches on skyyrose.co, and every commercial obligation that comes with running a luxury e-commerce store.

---

## 0. The Two Things This Plan Refuses to Compromise On

### 0.1 Premium isn't a coat of paint. It's a system.

A premium site is not a luxury template with the brand name dropped in. It is a coherent system where every page reinforces the same story, every interaction respects the customer's time, every visual choice has a reason, and the whole thing feels like it was built by someone who would actually wear the clothes. If any single page betrays the system, the whole brand cheapens.

### 0.2 If the site is beautiful but doesn't sell, it failed.

Aesthetic is a means. The end is revenue. Every design decision in this plan must state its commercial hypothesis — what behavior is it trying to produce, and what KPI moves if it works. "It looks nice" is not a hypothesis. "This reduces bounce on the collection page from 58% to 45% by replacing the generic grid with editorial product cards that convey craftsmanship" is.

Both have to be true at once. A site that's commercial but soulless is a Shopify dropshipper. A site that's beautiful but unprofitable is a portfolio piece. Skyyrose has to be both.

---

## 1. Operating Rules for Claude Code

### 1.1 The five mandatory thinking passes

Before any design work begins on a page or component, Claude Code runs these five passes in writing, in `eval/design-thinking/<page-slug>.md`. No skipping. No bullet-list shortcuts. Real prose.

| Pass | The question | What's required |
|------|--------------|-----------------|
| 1. Brand story coherence | If a customer landed on this page first — never having seen another page on the site — what would they understand about the brand? Does that match what we want them to understand? | 200–400 words. Names what story this page tells, what it omits, and where it contradicts the homepage or product pages. |
| 2. Commercial hypothesis | What action do we want the customer to take on this page? What's stopping them today? What design change moves that needle? | A specific KPI (e.g., add-to-cart rate, scroll depth, email signup) with a current baseline (from `eval/baselines.md`) and target. No KPI = no design work. |
| 3. Adversarial critique | What's the worst thing about what's currently here? Where does it feel generic? Where does it look like a Shopify theme? Where would a $3,000-jacket customer roll their eyes? | A bullet list of 5–10 specific complaints, named harshly. Nothing soft. If Claude Code can't find 5 problems, it isn't looking hard enough. |
| 4. Premium aesthetic triangulation | Pick three brands from the **canonical SkyyRose reference set** (`docs/brand/visual-references.md`): Kith, Oaklandish, Culture Kings, Fear of God, Palm Angels. Describe what they do that we don't. The European-luxury-house lineage (Bottega / Hedi Slimane / Rick Owens / Khaite / Bode) is locked OUT — see `docs/brand/visual-references.md` for the full lockout list. | Named brands from The Five, named pages, named techniques. Not "high-end brands use whitespace" — specifically how they use it on a specific page. |
| 5. Verified technical triangulation | For the technical implementation pattern this page requires (e.g., scroll-pinned hero, WC block cart styling, mega menu walker), what is the current canonical implementation? What does `knowledge-base/patterns/` already have on this? What does the trusted reference set (§1.5.4) say? Where does our v1 plan fall short of best practice? | Three named verified sources with URLs + accessed dates. KB entries cited if they exist. Specific technical risks called out (perf, a11y, browser support). This pass is what prevents the loop from echo-chambering. |

Only after all five passes are written does Claude Code touch design files for that page. Passes 1–4 force taste; pass 5 forces craft. Both are required for premium.

### 1.2 The mandatory critique loop after every build

After any page or component is built, before it's marked done:

```
BUILD v1 → SELF-CRITIQUE → VERIFY → REVISE → SELF-CRITIQUE → DISTILL → SHIP
                            ↑                                  ↑
                       §1.5 Layer 2                       §1.5 Layer 3
                  (verified-impl search)               (KB entry write)
```

The self-critique is written, not implicit. It answers:

1. What did I just build that I'm proud of? (max 3 things — being humble means being specific)
2. What did I just build that I'm not proud of? (minimum 3 things — being honest means naming them)
3. What did I copy from the prior version that I should have replaced? (this is the trap — laziness hides as continuity)
4. If I had to delete one thing on this page right now, what would it be? (forces ruthless editing)
5. Would Corey wear this if it were a piece of clothing? (the only taste filter that matters)
6. What's the verified canonical reference for this implementation, and does what I built match or surpass it? (cite source URL + accessed date — see §1.5 Layer 2)
7. What's the KB entry from this loop? (one pattern entry written; one lesson entry if a wrong path was taken — see §1.5 Layer 3)

If the second self-critique can't honestly say the page is stronger than the first build, revise again. If question 6 can't be answered, the build is incomplete — find the canonical reference before shipping. If question 7 isn't written, the loop didn't compound.

### 1.3 The "no generic" rule

The following are banned by default. They appear nowhere on skyyrose.co unless Claude Code can write a 100-word justification that survives the §1.1 critique pass:

- Centered hero with full-width photo + headline + "Shop Now" button
- 4-column equal-spaced product grid with white background
- Generic stock-photo style imagery
- Stock badge animations (pulsing dots, generic carousel arrows)
- "Lorem ipsum" anywhere, ever
- Default WooCommerce styling on any customer-facing surface
- Trust badge clusters at the bottom of pages (Visa/MC/Amex logos in a row)
- "Limited Time Offer!" countdown timers as a homepage element
- Stock testimonial layouts (avatar circle + name + quote in a card)
- Free shipping bars at the top of the page in a color that fights the design
- Cookie banners that take more than 3 seconds to dismiss

These are not banned because they don't work. They are banned because they are how every Shopify store on Earth looks. Premium means earning the visual moves. If the move is going to look like everyone else's, justify it or replace it.

### 1.4 Autonomous execution boundary

Claude Code drives this end-to-end. It applies the rules above without asking permission. It only stops at the three gates defined in `SKYYROSE_V2_MASTER_PLAN.md` (§0.2):

- G1: After Phase 0 evals, before code
- G2: After `/ship-check wp` SHIP, before deploy
- G3: Cost cap exceeded, prerequisite missing, or repeated failure

Per-page design choices, copy decisions, layout calls, image selections — all autonomous. Apply §1.1–§1.3.

### 1.5 The Compound Learning Loop (every loop makes the next one shorter)

**The principle:** A loop that only iterates against its own output is an echo chamber. A loop that iterates against verified canonical implementations gets smarter. Every loop in this build must produce three artifacts — not one:

1. The work itself (the page, component, function)
2. A verified-implementation citation (proof that what was built matches or surpasses a current best-practice reference)
3. A knowledge-base entry (so the next similar task starts ahead, not from scratch)

If the build's average loop count to convergence isn't decreasing over the lifetime of this project, the loop system is broken. Track it. Fix it.

#### Layer 1 — Pre-loop knowledge consult (before any thinking pass)

Before Claude Code writes a single line for a task, it runs:

1. Search `knowledge-base/patterns/` for keyword matches on the task domain
2. Search `knowledge-base/lessons/` for prior failures on similar tasks
3. Search `knowledge-base/decisions/` for ADRs that constrain this task
4. Load all matches into context as "prior art"
5. Begin §1.1 thinking pass with this prior knowledge present

The four thinking passes in §1.1 then explicitly reference what was loaded. If §1.1 pass 4 (premium reference triangulation) duplicates a reference already in the KB, that's a signal the KB entry needs to be enriched, not re-derived.

#### Layer 2 — Mid-loop verified implementation search (during iteration)

Self-critique alone produces local optima. Every iteration of the §1.2 critique loop is augmented with an active verification step before the revise step:

```
Build v1 → Self-critique → VERIFY → Revise → Self-critique again → Ship
                            ↑
                       added step
```

The VERIFY step does three things:

1. **Web-search current best practice** for the specific technical pattern. Query is task-specific: "WooCommerce 9 block cart styling 2026," "Three.js scroll-pinned camera 60fps mobile," "WordPress mega menu walker accessibility 2026." Top 3 results are scanned. If any presents a stronger pattern than v1, v1 is revised against it.
2. **Cross-check the trusted reference set** (§1.5.4 below). For the technical domain in question, the canonical source is consulted directly. The implementation must match or improve on the canonical pattern; if it diverges, the divergence is justified in writing in the KB entry.
3. **Anti-pattern check.** `knowledge-base/lessons/anti-patterns.md` is grepped against the v1 diff. If a known anti-pattern is present, it's flagged and removed.

The output of VERIFY is a single line in the KB entry: "This implementation matches/surpasses [source URL] accessed [date], with [diff] specific improvement." No source = no ship.

#### Layer 3 — Post-loop learning distillation (after convergence)

After the loop converges (final self-critique passes), Claude Code writes a KB entry. This is mandatory, not optional. Entry format:

```markdown
# knowledge-base/patterns/<domain>/<slug>.md

title: <short descriptive name>
domain: <wordpress | woocommerce | threejs | css | accessibility | seo | conversion | brand>
problem: <what problem this solves, in one sentence>
sources_consulted:
  - url: <verified canonical source>
    accessed: <YYYY-MM-DD>
    relevance: <high | medium | low>
chosen_implementation: |
  <inline code or file path reference>
why_this_over_alternatives: |
  <prose, 50-150 words, naming what was rejected and why>
when_to_use:
  - <case 1>
  - <case 2>
when_NOT_to_use:
  - <case 1>
  - <case 2>
loop_count_to_converge: <integer, 1 = first try>
related_patterns:
  - <link to other KB entries>
related_lessons:
  - <link to lessons that informed this>
```

Lessons (failed attempts, dead ends) get a parallel structure in `knowledge-base/lessons/`:

```markdown
# knowledge-base/lessons/<slug>.md

title: <what was tried that didn't work>
domain: <same domains as above>
what_was_tried: <description>
why_it_failed: <prose, with evidence>
better_alternative: <link to the patterns/ entry that replaced it>
how_to_recognize_this_trap: <signal future tasks should look for>
```

#### Layer 4 — The trusted reference set

The default authority list. These are consulted directly for their domains, not via secondary sources:

| Domain | Trusted source(s) |
|--------|-------------------|
| WordPress core | developer.wordpress.org, github.com/WordPress/wordpress-develop |
| WooCommerce | woocommerce.com/document, github.com/woocommerce/woocommerce, github.com/woocommerce/woocommerce-blocks |
| PHP standards | php.net, www.php-fig.org (PSR) |
| Three.js | threejs.org/docs, threejs-journey.com (Bruno Simon patterns) |
| React Three Fiber | docs.pmnd.rs |
| GSAP | gsap.com/docs |
| CSS / web platform | developer.mozilla.org, web.dev |
| Tailwind | tailwindcss.com/docs |
| Accessibility | w3.org/WAI/WCAG22/quickref, dequeuniversity.com |
| Performance | web.dev/vitals, web.dev/articles |
| Schema / SEO | schema.org, developers.google.com/search |
| Stripe | stripe.com/docs |
| Klaviyo | developers.klaviyo.com |
| Pinecone | docs.pinecone.io |
| FASHN | docs.fashn.ai |
| Anthropic | docs.anthropic.com |

Sources outside this list need a one-time verification before adoption. Verification = the source is referenced by at least two trusted-set sources, OR is the original maintainer of the technology in question. If neither, source is rejected; pattern is found elsewhere.

#### Layer 5 — Anti-pattern guard (seeded from project history)

`knowledge-base/lessons/anti-patterns.md` is seeded in Phase WP-0 with the patterns Corey has already named as failure modes in this project:

- Wrong assumptions presented as facts (the "I think this is X" that turns out wrong)
- Redundant tool calls — re-checking what was just verified
- Apology-over-correction responses ("sorry, let me try again" without naming what went wrong)
- Acting on unverified sources — adopting a pattern from a stack overflow answer without checking the canonical doc
- Glob-resolved image sources without manifest verification (the FASHN class of failure)
- br-001 wrong-photo
- Mocks substituting for real integration tests in final validation
- Mid-task refactors that lose context

Every loop checks against this list before VERIFY completes.

#### Layer 6 — The convergence meta-KPI

This is how we know the loop system is actually compounding:

| Metric | Captured | Target |
|--------|----------|--------|
| Avg loop count to convergence (per task type) | After every task, in KB entry | Decreasing month-over-month |
| First-try pass rate | Pulled weekly from KB entries with `loop_count_to_converge: 1` | Increasing month-over-month |
| KB entries reused (cited by later tasks) | Cross-reference count in KB | >50% of new tasks cite at least one prior entry by month 2 |
| Anti-patterns avoided pre-loop | Logged when KB pre-consult catches a known trap | Increasing as KB matures |
| New trusted-set additions | When a domain gets a verified canonical source not yet listed | Slow but steady; signals KB depth growing |

These are tracked in `eval/loop-convergence.md`, updated by `scripts/measurement/loop-stats.js` (added in Phase WP-0.5.e alongside the commercial KPI tracking).

#### Layer 7 — The connection to existing skills

This loop system doesn't replace the existing skills — it instruments them:

- `conversation-reflection` skill (already in arsenal) becomes the engine for Layer 3 KB writes — at end of every task, it generates the entry
- `eval-harness` owns the KB structure as part of `eval/` — KB is treated as eval truth-doc
- `simplify` and `verification-loop` are the existing per-edit workflow; Layer 2 VERIFY is added as the second-to-last step
- `audit` and `critique` consume KB entries as input — they know what good looks like because the KB defines it

The KB is initialized in Phase WP-0 (seeded with project history from Corey's accumulated context) and grows continuously. By Phase WP-7 (post-build critique), the KB is the strongest asset of this project — even more valuable than the shipped site, because it's what makes the next build faster.

---

## 2. The Brand Story (the document Claude Code reads first, every phase)

Before a single CSS rule is written, Claude Code internalizes this. If a design decision contradicts this story, the design is wrong, not the story.

### 2.1 The one-line version

> Skyyrose is intellectual street poetry from The Town — luxury with a pulse, not a logo.

### 2.2 The longer version (Claude Code reads this in full each phase entry)

Skyyrose is what happens when Oakland — the actual Oakland, not the Bay Area branding of it — meets the discipline of European luxury craftsmanship. It is not streetwear that aspires to luxury. It is luxury that grew up on 14th and Broadway. Every garment has a story rooted in something real: a person, a moment, a memory, a conflict. Black Rose is grief that became armor. Love Hurts is the romanticism of being from a place the world misjudges. Signature is what you wear when you've stopped explaining yourself.

The customer who buys Skyyrose is not buying a product. They are buying a thesis. They want clothes that say something — but only to people who already know. The brand doesn't shout. It doesn't overexplain. It assumes the customer's intelligence and rewards it.

The visual language follows from this:

- **Confident, never loud** — the palette is restrained; the impact comes from material, proportion, and stance
- **Cinematic, never theatrical** — motion serves the story, not the showreel
- **Editorial, never catalog** — every product is photographed like it's the only thing that matters
- **Specific, never generic** — Oakland references are named, not gestured at; cultural touchpoints are precise
- **Earned, never gifted** — luxury moves like dramatic typography, generous whitespace, and slow scrolls have to be paid for by the design — they aren't decoration

### 2.3 What the brand is NOT

Naming the negative space matters as much as naming the brand:

- **Not athleisure.** Comfortable but not gym-ready. The customer is going somewhere.
- **Not influencer streetwear.** No drop-shipped graphic tees, no overpromise, no celebrity endorsement core.
- **Not generic luxury.** Not "minimalism = sophistication." There's color, there's texture, there's grit.
- **Not aspirational in the sad sense.** The customer doesn't want to be someone else. They want to be more themselves.

### 2.4 The voice rules (banned phrases enforced by `skyyrose-brand-dna`)

- Never say "the Bay Area." Say "The Town" or "Oakland."
- Never use "iconic," "elevated," "curated," "luxe," or "drip" unless the irony is doing work.
- Never use exclamation marks in product copy or marketing.
- Never use "you deserve this" / "treat yourself" — the customer doesn't need permission.
- Never explain Oakland to a non-Oakland audience. If they don't get it, the writing is for them anyway.
- Never apologize for a price.

---

## 3. The Critique of What's Already There

Before Phase 1 begins, Claude Code performs a brutal audit of the current skyyrose.co. This is not the technical audit (orphan files, dead code) — that's Phase 2 of the master plan. This is the brand and commercial audit. Output: `eval/critique/current-site-audit.md`.

### 3.1 The forced critique structure

For each surface listed below, Claude Code answers — in writing, in prose:

1. What is this page trying to do, commercially?
2. Is it doing it? Cite measured numbers from `eval/baselines.md` (Phase WP-0.5 captures these before this critique runs). Visual reasoning supplements the data; it does not replace it.
3. What's strong about it? (be specific — exact elements, not "the layout")
4. What's weak about it? (minimum 5 weaknesses per page, named harshly)
5. What does it look like right now: a luxury site, a streetwear site, a generic Shopify, or something else?
6. What's the single change that would most improve commercial performance? Tie to a specific KPI in `baselines.md`.
7. What's the single change that would most improve brand premium-feel?

### 3.2 Surfaces to audit (ordered by commercial blast radius)

| Rank | Surface | Why this order |
|------|---------|----------------|
| 1 | Homepage | First impression; bounce rate determines everything downstream |
| 2 | Product detail page (PDP) | Highest-leverage conversion surface |
| 3 | Cart + checkout | Where revenue actually closes |
| 4 | Collection pages (4) | Discovery surface; pre-PDP qualification |
| 5 | Landing pages (3) | Campaign destinations; ad-traffic terminus |
| 6 | About | Brand story carrier; second-most-visited non-product page typically |
| 7 | Pre-order page | Drop mechanics surface — direct revenue |
| 8 | FAQ + shipping/returns | Trust-build surface; objection handling |
| 9 | Immersive experiences (3) | The differentiator — but only if customers find them |
| 10 | Header / nav / footer | The chrome; experienced on every page |

### 3.3 The mandatory verdict

After the per-page critique, Claude Code writes a 3-paragraph verdict: the current site, in honest terms, is closer to which of these archetypes — generic Shopify, decent streetwear, near-luxury, actual luxury? Where is the gap? What's the shortest path to closing it?

This verdict is the design brief for everything that follows. It is the most important paragraph in this document.

---

## 4. Commercial Protocols (the full coverage list)

A commercial-grade store has to satisfy all of these. Claude Code treats each as a mandatory deliverable, not an optional. Each row has an owner phase, a pass criterion, and lives in `eval/commercial-protocols.md`.

### 4.1 Payments & financial

| Protocol | Owner phase | Pass criterion |
|----------|-------------|----------------|
| PCI DSS SAQ-A compliance | P5 | Stripe-hosted fields; no card data on WP server; documented in `docs/compliance.md` |
| Stripe live + test mode | P5 | Test charge $0.50 succeeds in test; live key set in Vercel env (NOT WP DB) |
| 3DS / SCA strong customer auth | P5 | EU-card test triggers 3DS challenge; flow completes |
| Apple Pay / Google Pay | P5 | Buttons appear on iOS/Android in WC checkout; tap-to-pay completes |
| PayPal | P5 | PayPal Smart Button on cart + checkout; sandbox txn completes |
| Refund flow | P5 | Admin can refund from WC order screen; customer email auto-fires |
| Stripe Tax | P5 | US sales tax auto-calc on checkout based on shipping state |
| Stripe Radar (fraud) | P5 | Default rules enabled; high-risk orders flagged for review |
| Multi-currency display | P6 | USD primary; auto-detect for EU/UK/CA visitors via geolocation |
| Failed payment recovery | P6 | Klaviyo flow fires on failed charge with retry link |

### 4.2 Privacy, consent, legal

| Protocol | Owner phase | Pass criterion |
|----------|-------------|----------------|
| GDPR cookie consent | P3 | Banner with Accept / Reject / Customize; no non-essential cookies until consent |
| CCPA opt-out | P3 | "Do Not Sell My Personal Information" link in footer; honors request |
| Privacy policy | P3.3 | Reviewed for accuracy against actual data flows; lawyer-readable |
| Terms of service | P3.3 | Returns, refunds, IP, dispute resolution clauses present |
| Returns policy | P3.3 | Plain-English; window in days; condition requirements; who pays return shipping |
| Shipping policy | P3.3 | Times by region; carrier; tracking; signature requirement on high-value |
| Age verification (if applicable) | P3 | Skipped unless legally required for any product |
| Newsletter consent (CAN-SPAM, GDPR Art. 6) | P3 | Double opt-in for EU; clear unsubscribe in every email |
| Cookie audit | P6 | Every cookie listed in privacy policy with purpose and expiry |
| Data retention policy | P6 | Documented in `docs/data-retention.md`; aligned with platform defaults |

### 4.3 Accessibility (WCAG 2.2 AA — non-negotiable)

| Protocol | Owner phase | Pass criterion |
|----------|-------------|----------------|
| Color contrast 4.5:1 (normal text) | P6 | Audit every collection palette; failures fixed |
| Keyboard navigation | P6 | Every interactive element reachable + activatable via keyboard |
| Focus visible | P6 | Every focused element has a visible indicator that respects the design |
| Screen reader landmarks | P6 | Header, nav, main, footer correctly tagged; ARIA where semantic HTML insufficient |
| Alt text on every image | P6 | Decorative = `alt=""`; content = descriptive (not "image-of-") |
| Form labels | P6 | Every input has an associated label, not just placeholder |
| Skip-to-content link | P6 | Visible on focus; jumps to `<main>` |
| Motion-reduced fallback | P6 | `prefers-reduced-motion` honored on every animation |
| Heading hierarchy | P6 | One H1 per page; no skipped levels |
| Captioned video | P6 | Any video on the site has captions |

### 4.4 SEO (organic acquisition is free traffic)

| Protocol | Owner phase | Pass criterion |
|----------|-------------|----------------|
| JSON-LD: Organization | P6 | On every page, validates against schema.org |
| JSON-LD: Product | P6 | On every PDP with price, availability, SKU, images, brand |
| JSON-LD: BreadcrumbList | P6 | On every nested page |
| JSON-LD: FAQPage | P6 | On `template-faq.php` |
| JSON-LD: Review/AggregateRating | P6 | On PDPs with reviews |
| Canonical tags | P6 | Every page; collection variants point to base URL |
| XML sitemap | P6 | Auto-generated, submitted to Google Search Console |
| robots.txt | P6 | Excludes /cart, /checkout, /my-account, /wp-admin |
| OpenGraph + Twitter cards | P6 | Every page has og:title, og:description, og:image (1200x630) |
| Meta descriptions | P6 | Every page < 160 chars; written, not auto-generated |
| Image alt text doubles as SEO | P6 | Product alt text uses keyword + descriptor naturally |
| URL hierarchy | P6 | `/collections/black-rose/`, `/products/<slug>/` — no `?p=123` URLs |
| Mobile-first indexing | P6 | Mobile experience equivalent in content to desktop |

### 4.5 Performance (Core Web Vitals — Google ranking signal + UX signal)

| Protocol | Target | Measured how |
|----------|--------|--------------|
| LCP (Largest Contentful Paint) | < 2.5s mobile, < 1.8s desktop | PageSpeed Insights, real-device test |
| CLS (Cumulative Layout Shift) | < 0.1 | Same |
| INP (Interaction to Next Paint) | < 200ms | Same |
| TTFB (Time to First Byte) | < 600ms | Same |
| Initial JS budget | < 200KB compressed | Built-in Webpack analyzer |
| Initial CSS budget | < 100KB compressed | Same |
| Image budget | LCP image < 200KB; lazy-load below fold | lighthouse-ci |
| Font budget | < 100KB; `font-display: swap` | Manual audit |
| Third-party script audit | Every script has a justification; total < 300KB | `eval/scripts-audit.md` |

### 4.6 Conversion infrastructure

| Protocol | Owner phase | Pass criterion |
|----------|-------------|----------------|
| GA4 measurement | P6 | Installed via GTM; e-commerce events fire |
| Meta Pixel + CAPI | P6 | Server-side dedup with browser pixel |
| Google Ads conversion tracking | P6 | Purchase event fires on order confirmation |
| TikTok Pixel | P6 | If TikTok ads run, installed |
| Klaviyo onsite tracking | P6 | Already wired; verify view-product, add-to-cart, started-checkout fire |
| Abandoned cart recovery | P6 | 3-email Klaviyo flow live (already in `skyyrose-email-flows`) |
| Browse abandonment | P6 | Klaviyo flow live for product-viewed-no-purchase |
| Welcome flow | P6 | 5-email series (already specified) |
| Post-purchase flow | P6 | 4-email series (already specified) |
| Replenishment / re-engagement | P6 | Klaviyo flow at 30d / 60d / 90d post-purchase |
| Wishlist persistence | P6 | Logged-in users; cookie for guests |
| Email capture without lightbox | P6 | Embedded in footer + post-purchase; lightbox is allowed only after 30s scroll |
| Exit-intent capture | P6 | Desktop only; one-time per session; tasteful, not aggressive |

### 4.7 Trust signals (the unspoken commercial layer)

| Signal | Where | How it's done premium |
|--------|-------|----------------------|
| Customer reviews | PDP | NOT 5-star clusters with avatars in cards. Instead: pulled-quote editorial style; one or two reviews integrated into the product story, not stacked at the bottom |
| Press mentions | Homepage + about | Logo wall is banned. Replaced with one full-bleed editorial quote per major outlet, treated as a typographic moment |
| Founder voice | About | Corey on the page. Real photo, real words. No corporate "our story" template |
| Made-with detail | PDP | Materials, place of make, technique. Shown as editorial sidebar, not a spec sheet |
| Sustainability claims | If made | Specific or absent. No vague "eco-friendly" |
| Care instructions | PDP | Beautifully typeset, not a tag image |
| Size/fit info | PDP | Custom illustrated guide per garment. NOT a generic size chart screenshot |
| Authenticity | Header/footer | "Made in The Town" or similar — earned, not stamped |
| Customer service touchpoint | Footer + chat | Real email, real phone, real human. No "chatbot." If there's chat, it's a human or it's off |
| Returns confidence | Cart + PDP | Plain-English window stated near CTA, not buried in a /returns page |

### 4.8 Inventory & merchandising

| Protocol | Owner phase | Pass criterion |
|----------|-------------|----------------|
| Low-stock indicator | P6 | "Only 3 left" appears under stock < 5; written as fact, not pressure |
| Sold-out state | P6 | Beautiful sold-out treatment; "Notify me" CTA replaces "Add to cart" |
| Restock notification | P6 | Klaviyo flow fires when sold-out variant returns |
| Pre-order labeling | P5.4 | Clear ship date; payment timing disclosed |
| Drop countdown | P5.4 | On `template-drop-day.php`; teases without overpressure |
| Cross-sell on PDP | P6 | "Wears with" — 2-3 hand-curated, NOT algorithmic |
| Cart upsell | P6 | One thoughtful suggestion (e.g., care kit), not a wall of products |
| Abandoned cart hold | P6 | Items reserved for 1 hour; visible to customer |
| Bundle pricing | P6 | If applicable, on PDP and cart |
| Gift card | P6 | First-class product; gift card landing page; recipient email |

### 4.9 Customer experience

| Protocol | Owner phase | Pass criterion |
|----------|-------------|----------------|
| Order confirmation page | P5 | Branded, not WC default; thank-you tone matches brand voice |
| Order confirmation email | P5 | Branded HTML; not WC default; ships to inbox preview cleanly |
| Shipping notification | P5 | Tracking link + delivery estimate |
| Delivered notification | P5 | Triggers post-purchase flow |
| Return request flow | P5 | Self-serve from `/my-account/orders/`; doesn't require email |
| Account dashboard | P6 | Branded; matches site design; not default WC |
| Wishlist | P6 | Persistent; shareable URL |
| Saved addresses | P5 | One-click checkout for returning customers |
| Guest checkout | P5 | Allowed; no forced account creation |

### 4.10 Measurement & analytics provisioning (the precondition for everything else)

Without this, every KPI in §9 is a guess and every "before/after" claim is unfalsifiable. Claude Code provisions this before Phase WP-1 begins, in dedicated Phase WP-0.5. Each row has an owner: `claude-code` means autonomous; `corey-grants` means Corey must click approve in a UI Claude Code cannot reach; `both` means a request packet is generated by Claude Code and approved by Corey in one action.

| Data source | Owner | What's set up | Verification node |
|-------------|-------|---------------|-------------------|
| Google Analytics 4 | both | Service account created in GCP; account email added as Viewer in GA4 admin; Data API enabled | `scripts/measurement/verify-ga4.js` returns property ID + 30d sessions |
| Google Search Console | both | Same service account added as Restricted user on `skyyrose.co` property | `verify-gsc.js` returns indexed page count + top queries |
| Google Tag Manager | both | Container access granted; container ID stored in Vercel env | GTM container loads on `?gtm_debug=1` URL |
| WooCommerce REST API | claude-code | Read-only consumer key/secret generated via `/wp-admin/admin.php?page=wc-settings&tab=advanced&section=keys`; stored in Vercel env | `verify-wc.js` returns last 30 orders count + revenue |
| Klaviyo API | claude-code | API key already present per project history; MCP server Klaviyo already connected | `verify-klaviyo.js` returns list growth + flow performance |
| Stripe API | claude-code | Read-only key from existing Stripe dashboard; MCP server Stripe already connected | `verify-stripe.js` returns 30d charges, success rate, refund rate |
| Meta Business / Pixel + CAPI | both | System user created in Business Manager; access to ad account, pixel, page; access token generated | `verify-meta.js` returns pixel events 30d, ad spend if applicable |
| TikTok Pixel (if applicable) | both | Skip if no TikTok ads running; otherwise pixel ID + access token | `verify-tiktok.js` |
| Google Ads (if applicable) | both | Skip if no Google Ads; otherwise customer ID + manager link | `verify-gads.js` |
| Hotjar / Microsoft Clarity (heatmaps) | claude-code | One free heatmap tool installed for qualitative critique input | Tracking script fires on home + PDP |

**Where secrets live:** Vercel project env vars only. Never in WP DB, never in the WP theme repo. The bridge `inc/fastapi-client.php` calls Vercel routes; Vercel routes hold the secrets. Same architecture as FASHN/Pinecone/Stripe in the master plan.

**Auto-pull baseline script:** `scripts/measurement/pull-baselines.js` runs after all verifications pass. It writes:

- `eval/baselines.md` — every KPI in §9 with the current 30-day number, source, pulled-at timestamp
- `eval/qualitative-baselines.md` — heatmap snapshots of homepage + top 3 PDPs + cart, exported as PNG

**Ongoing monitoring setup (also in WP-0.5):**

- `scripts/measurement/weekly-report.js` runs every Monday via Vercel cron, posts a summary to a Slack webhook (or email if no Slack), tracks the 10 KPIs against targets
- Anomaly detection: if any KPI moves >20% week-over-week (positive or negative), flag in the report
- A simple Vercel-hosted dashboard at `devskyy.app/admin/measurement` shows the same data live

**Cost ceiling for measurement infra:** All tools above either free or already paid (GA4 free, GSC free, WC API free, Klaviyo + Stripe already paid, Meta free, Hotjar/Clarity free tier). If any tier needs upgrade for required data depth → G3 escalation.

---

## 5. Design System (the foundation under everything)

Before Phase 4 builds new templates, the design system must be locked. Otherwise every page reinvents itself.

### 5.1 Tokens (`assets/css/tokens.css`)

> **NOTE — repo convention:** Existing file is `assets/css/design-tokens.css` (with min + sourcemap variants). Phase 0 extends that file rather than creating a parallel `tokens.css`.

Auto-generated from the design system definition. Source: `eval/design-system.json`.

| Token group | What it covers | Constraint |
|-------------|----------------|------------|
| Color | Brand black, brand white, 3 collection accents, 5 grays, semantic (success/warning/error) | Locked. No off-system colors anywhere |
| Type scale | Display, H1–H6, body-lg, body, body-sm, caption | One serif (display) + one sans (UI). Specified weights only |
| Spacing | 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 / 96 / 128 | No arbitrary values. Margins/padding pull from this scale |
| Radius | 0, 2, 4, 8, 16, full | Most surfaces are 0 or 2. 8+ only when intentional |
| Shadow | None (default), subtle, soft, lifted | Premium = restrained shadows. No drop-shadow stacks |
| Motion | Duration: 150 / 250 / 400 / 800ms. Easing: 4 named curves | All motion uses these. No bespoke transitions |
| Breakpoints | 480 / 768 / 1024 / 1280 / 1536 | Mobile-first |
| Z-index | 1 / 10 / 100 / 1000 / 10000 | Named layers, not arbitrary numbers |

### 5.2 Component primitives (must exist before pages compose them)

| Component | What's enforced | Where |
|-----------|----------------|-------|
| Button (primary, secondary, ghost, link) | Size, padding, motion, focus state, loading state | `template-parts/components/button.php` |
| Input | Label, error state, helper text | `template-parts/components/input.php` |
| Form | Spacing, error summary, submission state | `template-parts/components/form.php` |
| Card (product, editorial, info) | Three variants only; no one-off cards | `template-parts/components/card-*.php` |
| Heading (display, section, sub) | Three variants; tied to type scale | CSS-only |
| Image (figure with caption) | Aspect ratio enforcement, lazy loading, alt | `template-parts/components/figure.php` |
| Quote (pulled, inline) | Editorial typography | `template-parts/components/quote.php` |
| Modal | Focus trap, ESC dismisses, scroll lock | `template-parts/components/modal.php` |
| Drawer (cart, mobile nav, filter) | Slide direction, transparent backdrop, scroll lock | `template-parts/components/drawer.php` |
| Toast | One at a time, auto-dismiss 4s, dismissible | JS-only |

A page that needs a "card" but isn't one of the three card variants doesn't get a new card. It uses one of the three or the design system grows by an explicit decision.

### 5.3 The "premium feel" specification (the things that compound)

These are the small moves that, individually, no one notices — but collectively make the site feel premium. They are mandatory.

1. **Typography breathes.** Line-height ≥ 1.5 on body copy. Headings get more whitespace above than below.
2. **Images are the design.** Photography is the main visual element. Text supports the photo, never competes.
3. **Whitespace is currency.** When in doubt, more space. Generic sites cram; premium sites breathe.
4. **Motion is slow.** Default duration 400ms, not 200ms. Eases are smooth, not bouncy.
5. **Hover states earn their place.** A subtle weight shift, a 1px border underline, an image fade. Not a scale + shadow + color flip.
6. **Buttons don't shout.** No gradient buttons. No box-shadows on buttons. No all-caps unless the type system asks for it.
7. **Loading states are designed.** No default browser spinner. A typographic indicator or a measured skeleton.
8. **404 and empty states have personality.** They are the signature moves. A blank empty cart is a brand miss.
9. **Form errors are graceful.** Inline, not toast. Specific, not "Something went wrong."
10. **The cursor.** A subtle custom cursor on hero areas — only if it's tasteful and only if it's optional.

Each of these has a CSS audit in `eval/premium-feel.md`. Phase 6.8 verifies all 10 are honored sitewide.

---

## 6. Page-by-Page Design Briefs

This is the substance of the design work. Each brief forces Claude Code through the four thinking passes (§1.1) before building. Briefs below are seeds — Claude Code expands them per page in `eval/design-thinking/<slug>.md`.

### 6.1 Homepage (highest commercial leverage)

**Commercial hypothesis:** Move first-time visitor to one of three destinations within 8 seconds: collection page, drop page, or about. Bounce target: < 45%. Email capture at 2.5%.

**Forced thinking prompts for Claude Code:**

- The homepage is real estate. What earns a place above the fold? What earns a place at all?
- A customer who only sees the first screen and leaves — what story did they get?
- If we removed the navigation entirely, could the homepage still drive customers to the right next page?
- What does a $3,000-jacket buyer expect on a luxury homepage? What does a $300-tee buyer expect on a streetwear homepage? Skyyrose serves both — how does the homepage hold both without picking one?

**Layout direction (subject to revision after thinking pass):**

A scroll-driven editorial homepage. Hero is one image — full-bleed, behind a single sentence of copy that names the current moment for the brand (a drop, a season, a story). No "Shop Now" button in the hero. The CTA is the scroll.

Section 2: A two-collection split (current featured + secondary) with editorial typography, not product grids. Section 3: Brand story moment — Corey on the page in some form. One photo, two sentences, no more. Section 4: Press / proof, treated as one editorial quote, not a logo wall. Section 5: Email capture — embedded as a typographic moment, not a popup form. Footer: Restrained, complete, navigation-rich.

**What's banned on this homepage:** Carousel hero. Product grid above the fold. "As seen in" logo wall. Lightbox popups in the first 30 seconds. Any element that could be described as "engagement layer."

### 6.2 Product detail page (PDP) — highest revenue surface

**Commercial hypothesis:** Move qualified visitor to add-to-cart. Add-to-cart rate target ≥ 8% on cold traffic, ≥ 18% on warm. Page time ≥ 90s.

**Forced thinking prompts:**

- PDPs typically fail because they are spec sheets pretending to be sales pages. What's the editorial version?
- The customer is one click from leaving. What sentence on this page makes them stay?
- What's the "wear" story for this garment? Where does someone go in this? What do they feel like wearing it?
- A premium PDP solves objections before they're asked. What objections does this product face? Where on the page do we answer them?

**Layout direction:**

Editorial scroll narrative (Phase 5.3 of master plan applies here). Each section is a chapter:

- Chapter 1 — Encounter: The image. Full-bleed. Customer feels the garment before reading anything.
- Chapter 2 — The piece: What it is. Materials. Make. Specific, editorial copy.
- Chapter 3 — The story: Why it exists. Origin. Pulled-quote treatment.
- Chapter 4 — The fit: How it wears. On a person. Multiple bodies, multiple moments.
- Chapter 5 — Add to cart: The decision moment. Size selector, low-stock signal if applicable, return policy stated, CTA.
- Chapter 6 — Wears with: 2-3 hand-curated, editorially treated.
- Chapter 7 — Care + craft: How it's made and how to keep it.

The standard "image left, buy box right" layout is allowed as a non-narrative fallback for products without authored chapter content. But the goal is every product gets the full narrative treatment.

### 6.3 Cart + checkout (where revenue closes)

**Commercial hypothesis:** Reduce checkout abandonment from category benchmark (~70%) toward 50%. Increase AOV via thoughtful upsell.

**Forced thinking prompts:**

- A cart abandons because something on the page seeded doubt. What seeds doubt on the current cart? Shipping cost surprise? Missing trust signal? Visual friction?
- Premium checkouts feel inevitable. What makes a checkout feel inevitable vs. fraught?
- The customer just decided to spend money. What does the page do to honor that decision?

**Layout direction:**

- Two-column on desktop: items + summary. Single-column on mobile.
- Items shown editorially — not as default WC line items. Each line shows the product photo at a respectable size, name, size, qty, line price.
- Free shipping threshold (if any) shown as progress, not pressure.
- Trust statement near the CTA: returns window, secure checkout. One line, typographic.
- Express pay (Apple Pay, Google Pay, PayPal) above the fold on cart.
- Checkout: WC blocks fully styled (Phase 5.1). Single-page, three sections (contact, shipping, payment). No multi-step.
- Order confirmation: branded, gracious, gives the customer next steps.

**Banned on cart/checkout:** Generic Visa/MC/Amex logo cluster. "Limited time offer" anything. Upsells that feel desperate. Coupon code field that's visible by default — it teaches customers to leave and search for codes.

### 6.4 Collection pages (the discovery surface)

**Commercial hypothesis:** Move visitor to a PDP. CTR to PDP target ≥ 35%. Average products viewed per session ≥ 4.

**Forced thinking prompts:**

- The collection page is the editor's voice. Every collection has a thesis. Is it being said?
- Generic collection pages are 4-column grids. What's the editorial version of a collection page that respects the thesis?
- A customer scrolling a collection page — what makes them click? What makes them keep scrolling?

**Layout direction:**

Editorial collection — already aligned with the master plan's "cinematic scroll-driven editorial story pages, not product grids" directive. Each collection page tells the collection's story:

- Hero moment: collection title, one sentence of thesis, full-bleed campaign image.
- Story sections interleaved with product reveals — products appear within the narrative, not in a grid below it.
- Multi-ethnic AI-generated models wearing the exact products, hotspots to PDP (per existing Skyyrose direction).
- End: a "view all in collection" grid for the customer who wants the standard view.

### 6.5 Landing pages (campaign destinations)

Already consolidated in Phase 3.1 of master plan. The design brief: each landing page is a campaign moment. It has a single thesis, a single primary CTA, and supports paid traffic. No nav distraction in the hero. Performance budget tighter than other pages because ad-traffic is impatient.

### 6.6 About page (the brand carrier)

**Commercial hypothesis:** Convert brand-curious visitor into email subscriber or shopper. Email capture rate ≥ 5% on this page.

**Forced thinking prompts:**

- About pages fail because they are corporate "our story" templates. What's the editorial version?
- Skyyrose is Corey's brand. How is Corey on the page in a way that's true and not vain?
- What does a customer want to feel after reading the about page that they didn't feel before?

**Layout direction:**

Long-form editorial. Photography-led. Corey on the page — not as a corporate founder portrait, but as a person. Voice is first-person where appropriate. Specific Oakland references named. The page ends with a quiet CTA: "see the work" — to current featured collection.

### 6.7 Pre-order / drop page (direct revenue)

Owned by Phase 5.4 of master plan. Brief here: every drop page is a campaign in itself. Countdown if active, story-led if pre-launch, queue-aware if live. Each collection's drop page inherits the collection's visual language.

### 6.8 FAQ + shipping/returns (objection handling)

**Commercial hypothesis:** Reduce pre-purchase support tickets by 30%. Increase confidence-to-cart by visible policy presence on PDP.

**Forced thinking prompts:**

- FAQs that don't get read fail because they look like FAQs. What does an editorial FAQ look like?
- Returns and shipping pages are trust documents. Every word matters. Are these written like a customer wrote them or like a lawyer wrote them?

**Layout direction:**

Quiet-premium info-page chrome (per Phase 3.3 of master plan). FAQ uses an accordion, but the typography and spacing make it feel like reading a thoughtful blog post, not a Zendesk article. Shipping and returns are written in plain English, generously typeset, with the most-asked questions answered in the first 200 words.

### 6.9 Immersive experiences (the differentiator)

Already specced in master plan (Phase 4 + 5.8). Brief here: these pages exist to convert brand-curious into brand-converts. Each one ends in a CTA that makes commercial sense for the immersive moment. The Black Rose immersive ends in the Black Rose collection. Otherwise it's an art piece, not a commerce surface.

### 6.10 Header / nav / footer (the chrome)

Phase 1.5 of master plan owns this. Brief here: the chrome is consistent across every page. It does not call attention to itself except where motion is intentional (sticky header on scroll, etc.). The footer is thorough — every legal page, every helpful link, social, newsletter capture, contact email, copyright. Customers go to footers for trust signals; a sparse footer reads as amateur.

---

## 7. The Critique-Implement-Critique Cycle (the quality engine)

This is how we get from "good" to "premium." It runs on every page after first build.

### 7.1 The cycle

```
Build v1
↓
Self-critique pass (the §1.2 mandatory questions, written in prose)
↓
Persona walkthrough (3 personas, written in prose — see §7.2)
↓
Premium-reference comparison (compare against the 3 chosen luxury references — be honest where ours falls short)
↓
Build v2 (revision based on critique findings)
↓
Second self-critique
↓
If v2 is honestly stronger than v1: ship.
If not: build v3.
```

### 7.2 The three personas Claude Code walks through

For every page, Claude Code writes a 150-word walkthrough as each:

1. **The $3,000 jacket buyer.** They've worn Kith, Fear of God, Aimé Leon Dore, Rhude. They are price-insensitive but taste-strict — luxury streetwear lineage, not European luxury house. Where does this page meet them? Where does it fall short? (Reference set is canonical in `docs/brand/visual-references.md`.)
2. **The Skyyrose true believer.** They follow the brand on Instagram, they know about the Oakland references, they bought their first piece a year ago. What does this page give them that's new? What does it remind them of? Where does it feel like the brand?
3. **The cold-traffic skeptic.** They clicked an ad. They've never heard of Skyyrose. They are 8 seconds from leaving. What does the page do to earn their next 15 seconds?

If any persona walks away unsatisfied, the page isn't done.

### 7.3 The "would Corey wear this?" filter

The single most important filter on every design decision. Before any UI element, copy block, or visual is shipped, Claude Code asks: would the founder, who lives in The Town and has the brand's taste, be proud to put this on a customer's screen? If the answer is "I think so," it isn't ready. If the answer is "yes, specifically because [reason]," it is.

---

## 8. Phase Plan (WordPress-only)

These phases mirror the master plan but are scoped to WordPress work. They run in parallel with the Vercel/integration phases where appropriate, with explicit handoffs.

### Phase WP-0 — Brand & critique foundation (BEFORE any code)

| Deliverable | Output location |
|-------------|----------------|
| Current-site critique | `eval/critique/current-site-audit.md` |
| Brand story canonicalized | `eval/brand-story.md` |
| Banned-elements list | `eval/banned-elements.md` |
| Design system tokens | `eval/design-system.json` + `assets/css/tokens.css` |
| Three luxury references chosen + analyzed | `eval/luxury-references.md` |
| Premium-feel checklist | `eval/premium-feel.md` |
| Commercial protocols matrix | `eval/commercial-protocols.md` |
| Knowledge base scaffold + seed | `knowledge-base/` (see below) |

**Knowledge base seeding (per §1.5):** This is the most consequential deliverable in WP-0 because it's the foundation under every loop in every later phase. Claude Code creates:

| KB artifact | Seeded with |
|-------------|-------------|
| `knowledge-base/README.md` | Schema, entry templates, how to read/write |
| `knowledge-base/patterns/` | Empty directory; populated by every loop hereafter |
| `knowledge-base/lessons/anti-patterns.md` | Seeded with the 7 project anti-patterns from §1.5 Layer 5 + lessons mined from Corey's prior project history (FASHN wrong-photo class, glob-resolved sources, mock-driven false confidence, etc.) |
| `knowledge-base/decisions/` | Seeded with ADRs for the locked decisions from `SKYYROSE_V2_MASTER_PLAN.md` §1 (architecture, hosting split, cost ceilings, avatar rig prerequisite) |
| `knowledge-base/references/trusted-set.md` | The 16 trusted-source domains from §1.5.4 with one-paragraph each on what they're authoritative for |
| `knowledge-base/INDEX.md` | Auto-generated index of all entries; regenerated on every KB write |

The seed isn't aspirational. It's a working KB on day one — every prior project decision, every prior failure mode, every reference Corey has already vetted. Phase WP-1 starts richer than from-scratch because of this seeding step.

**Exit:** All eight deliverables exist. KB has minimum 10 lessons + 5 decisions seeded. Reviewed by the user at G1.

### Phase WP-0.5 — Measurement provisioning & baseline capture (autonomous, runs after G1)

This phase exists because §3 (critique of what's already there) and §9 (KPI dashboard) are both meaningless without real numbers. Claude Code runs this immediately after G1 approval and before any other build phase begins. Output: every KPI in §9 has a real baseline, and every claim made in Phase WP-7's before/after is grounded in measured data.

**Sub-phases (sequential, each gated on the previous passing):**

**WP-0.5.a — Provisioning request packet generation.** Claude Code generates `eval/measurement-access-requests.md` — a single document Corey can act on in one sitting. It contains, for each data source in §4.10 marked `corey-grants` or `both`:

- Plain-English description of why access is needed
- Exact click-by-click steps (with screenshots from official docs where useful)
- The service account email / system user ID to add
- Required permission level (Viewer, Restricted, etc.)
- A verification command Corey can paste to confirm the grant worked

This packet is created in one shot. Corey works through it once, marks it complete, and Phase WP-0.5 continues.

**WP-0.5.b — Autonomous provisioning.** Claude Code provisions everything in §4.10 marked `claude-code`-owned: WC REST API keys via wp-admin REST (already authenticated), Klaviyo + Stripe + Hotjar via existing MCP / API access. Stores all secrets in Vercel env vars via `vercel env add`.

**WP-0.5.c — Verification sweep.** Runs every `verify-*.js` script in `scripts/measurement/`. Each must return PASS. If any fails:

- If `claude-code`-owned: Claude Code retries with corrected setup
- If `corey-grants`-owned: amend `eval/measurement-access-requests.md` with the specific failure and re-request that single grant only

WP-0.5 does not advance until verification is 100% green.

**WP-0.5.d — Baseline capture.** `scripts/measurement/pull-baselines.js` runs. Outputs:

- `eval/baselines.md` — quantitative baselines for every §9 KPI with timestamp + source + 30d/90d historical context where available
- `eval/qualitative-baselines.md` — heatmap PNGs of homepage, top 3 PDPs, cart page, checkout
- `eval/funnel-baseline.md` — full purchase funnel: sessions → product views → ATC → checkout start → checkout complete, with drop-off rates at each step

These three files become the truth doc for §3 critique and §9 dashboard.

**WP-0.5.e — Ongoing monitoring setup.**

- Vercel cron job created: weekly Monday baseline-vs-target report
- Slack webhook configured (or email fallback if no Slack)
- Dashboard route deployed at `devskyy.app/admin/measurement`
- Anomaly detection thresholds set per KPI (default ±20% WoW)

**Phase WP-0.5 exit criteria (all must PASS):**

- Every row in §4.10 either verified PASS or marked N/A with justification
- `eval/baselines.md` exists with non-empty values for all §9 KPIs
- Weekly report has been triggered manually once and delivered successfully
- Dashboard URL returns 200 and shows live data

**Failure handling:** If a data source is genuinely not provisionable (account doesn't exist, integration deprecated, etc.), Claude Code documents the gap in `eval/baselines.md` with: the missing data, the proxy used instead (if any), the confidence cost. The phase advances. Better to ship with one missing data source documented than to stall the whole build.

### Phase WP-1 — Admin cleanup + IA + nav

Mirror master plan Phase 1 + 1.5. WordPress-only scope.

### Phase WP-2 — Dead code + audit

Mirror master plan Phase 2.

### Phase WP-3 — Template consolidation

Mirror master plan Phase 3.

### Phase WP-4 — New templates

Mirror master plan Phase 4. Each template runs through §1.1 four-pass thinking and §7.1 critique cycle.

### Phase WP-5 — Commerce surfaces

Subset of master plan Phase 5 — only the WordPress-side work:

- 5.1 WC block cart/checkout fix + design
- 5.2 Native WebGL product canvas (theme-side only)
- 5.3 Editorial scroll-narrative PDP
- 5.4 Drop-mechanics templates
- 5.5 Mobile gallery patterns
- 5.10 Stripe + payments wired

(Phases 5.6 / 5.7 / 5.8 / 5.9 belong to Vercel — covered in master plan.)

### Phase WP-6 — Commercial protocols + polish

Full coverage of §4 protocols. Every row of the table moves to PASS.

### Phase WP-7 — Critique pass on the entire site

After all pages built / refactored, Claude Code runs the §3 audit again — but on the new site. The verdict paragraph is rewritten. The before/after is documented in `eval/critique/before-after.md`.

If the verdict isn't materially stronger, work isn't done.

### Phase WP-8 — Ship gate + deploy

Mirror master plan Phase 7 (G2 stop). Atomic deploy. Post-deploy verification.

---

## 9. The KPI Dashboard (how we know it worked)

After deploy, monitored for 30 days. Baselines are populated by Phase WP-0.5 (`eval/baselines.md`). Targets below are relative — Phase WP-0.5's baseline-capture replaces the "TBD" cells with measured numbers before any Phase WP-1 work begins, so every claim has a number behind it.

| KPI | Baseline (current) | 30-day target | 90-day target |
|-----|-------------------|---------------|---------------|
| Bounce rate (homepage) | from baselines.md | -10pp | -15pp |
| Add-to-cart rate (PDP) | from baselines.md | +25% relative | +50% relative |
| Cart abandonment | from baselines.md | -10pp absolute | -20pp absolute |
| Email capture rate | from baselines.md | 2.5% | 4% |
| AOV | from baselines.md | +10% | +20% |
| Conversion rate (overall) | from baselines.md | +30% relative | +60% relative |
| Mobile LCP | from baselines.md | < 2.5s | < 2.0s |
| WCAG audit issues | from baselines.md | 0 P0/P1 | 0 P0/P1 maintained |
| Customer service tickets re: shipping/returns | from baselines.md | -30% | -50% |
| Returning customer rate (90d) | from baselines.md | +15% | +30% |

These KPIs are tracked weekly via the Vercel cron report set up in Phase WP-0.5.e. The dashboard at `devskyy.app/admin/measurement` is the live view. If any KPI regresses two consecutive weeks post-launch, it's a Phase WP-7-style critique trigger — we revisit the surface most likely responsible.

---

## 10. The Single Sentence That Governs Every Decision

> Every pixel, every word, every interaction must do two things: honor a customer who knows what they're buying, and earn the price tag.

If a decision fails either half of that sentence, the decision is wrong.

---

**End of plan. Ready for G1 review.**
