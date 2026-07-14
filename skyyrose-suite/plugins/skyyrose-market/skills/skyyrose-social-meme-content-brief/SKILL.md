---
name: skyyrose-social-meme-content-brief
description: "Creates SkyyRose-specific meme content briefs — Oakland-community humor, streetwear insider takes, and brand-adjacent formats — that feel native to the platform without breaking founder canon."
allowed-tools: Read Write Edit Glob
---

# SkyyRose Social — Meme Content Brief

## When to Use This Skill

- Creating a meme brief for the weekly community/culture content slot (Wednesday rhythm)
- Building insider streetwear or Oakland-community humor that earns a share or reply
- Generating meme concepts that extend the brand's cultural credibility without breaking voice
- Briefing a social media manager or designer on brand-safe meme formats and guardrails
- Planning a short run (5-10 concepts) of meme content to test audience resonance

**DO NOT** use this for formal marketing content, product launch copy, press releases, or any meme that requires urgency or countdown language. Memes require the right moment and format — never force one on a drop announcement. Use `skyyrose-social-instagram-carousel` or `skyyrose-social-tiktok-script` for product launches.

---

## Brand Canon (non-negotiable)

- **Humor register: Oaklandish community-dry — NOT brand-tries-to-be-funny.** The meme earns a share because the audience recognizes themselves in it, not because a brand is performing humor. Corey's voice is self-possessed and specific. SkyyRose memes are specific to streetwear insiders, Bay Area culture, and Black fashion — not generic internet formats pasted with a logo.
- **Garment is the protagonist.** No meme uses a product as a punchline. The humor is about culture, context, or the streetwear world — not about poking fun at the product or the brand's own work.
- **No ironic self-mockery.** Fear of God doesn't joke about itself. Neither does SkyyRose. Self-deprecating memes about the brand's quality, pricing, or ambition are off-limits.
- **No punching down.** Memes that mock vulnerable groups, communities outside the brand's authentic orbit, or anything that requires explaining are off-limits.
- **Collection voice stays home.** A meme tied to Black Rose uses armor/defiance energy — never "the bloodline that raised me" (Love Hurts). Untagged memes are brand-level only.
- **The Five visual references** for any aesthetic direction: Kith, Oaklandish, Culture Kings, Fear of God, Palm Angels.

Full canon: `../skyyrose-content-engine/brand-guardrails.md`

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|-------------|---------|
| **Theme** | "What cultural moment, streetwear truth, or community experience is this about?" | No default — must be provided |
| **Collection / angle** | "Black Rose, Love Hurts, Signature, Kids Capsule, or brand-level?" | Brand-level |
| **Platform** | "Instagram, X/Twitter, or both?" | Both |
| **Humor style** | "Relatable insider, dry/deadpan, cultural commentary, or before/after contrast?" | Relatable insider |
| **Number of concepts** | "How many meme concepts?" | 8 |
| **Off-limits** | "Any references or topics to avoid beyond the standard guardrails?" | Standard guardrails apply |

**GATE: Confirm theme and collection angle before generating concepts. If the humor idea makes fun of the product or positions SkyyRose as self-deprecating, redirect to a different angle.**

---

## Phase 2: Outline

### SkyyRose Meme Categories

```
1. Streetwear Insider — "Only people who care about craft will get this"
2. Oakland/Town Pride — "If you're from here, you already know"
3. Before/After Contrast — expectations vs. the SkyyRose reality
4. Cultural Commentary — dry takes on fashion industry, hype culture, or luxury gatekeeping
5. Community Mirror — reflecting back what the SkyyRose audience already believes about themselves
```

**GATE: Confirm which categories to prioritize for this batch.**

---

## Phase 3: Write

### Meme Brief Format

For each meme concept:

```
## Meme [N]: [Working title — internal only]

**Category:** [Streetwear Insider / Town Pride / Before-After / Cultural Commentary / Community Mirror]
**Format:** [Text-on-image / Two-panel / Screenshot-style tweet / Reaction still / Video overlay]
**Platform:** [Instagram / X / Both]
**Register:** [Black Rose / Love Hurts / Signature / Brand-level / Oakland]

**Setup (top text / context):**
[What the viewer reads or sees first — the tension or expectation]

**Punchline (bottom text / payoff):**
[The payoff — the recognition or subversion]

**Image direction:**
[Specific: what image, still, or template — no "make it look good"]

**Caption (if needed):**
[Platform-native short caption — 10-20 words max. Optional for meme posts.]

**Brand alignment:**
[How this reinforces SkyyRose's cultural position — NOT the product, the position]

**Risk level:** Low / Medium
[Note: High-risk memes are never produced for SkyyRose. Medium = review required before posting.]
```

### SkyyRose Meme Rules

```
## DO:
- Reference specific Bay Area / Oakland experiences, places, or cultural moments
- Use streetwear insider knowledge as the source of the joke
  (fabric weight, construction details, limited runs, the "brand you find vs the brand that finds you")
- Adapt trending formats only when the format fits the content — not for the trend's reach alone
- Keep text short enough to read in 4 seconds max
- Brief the designer with specific image direction (not "use a funny meme format")
- Test one meme per week before committing to a series

## DO NOT:
- Produce a meme that requires explaining. If it needs a caption to land, it failed.
- Post a trending format more than 72 hours after peak relevance
- Use a meme to drive a purchase or link to a product page
- Make the brand the butt of the joke (ironic luxury self-mockery = wrong DNA)
- Reference European luxury houses (no "this is basically the Oakland Bottega" jokes)
- Punch down at any community
- Use broken-English caption styles or any format that mimics stereotyped speech patterns
- Make memes about scarcity or urgency — "everyone wants this" hype-format is off-brand
```

### Posting Cadence

```
## SkyyRose Meme Cadence

Recommended slot: Wednesday (Culture & Community pillar — see skyyrose-content-engine)
Frequency: 1 meme per week maximum (quality > volume)
Mix with: Value content (product story, founder moment, styling content)
Engagement: Reply to comments in the meme's own language — extend the joke, don't explain it
Approval: Medium-risk memes require one human review before posting (12-hour lead time)
```

---

## Phase 4: Polish

### Meme Brief Checklist

```
- [ ] Each meme has a clear setup and punchline — no explanation required
- [ ] Image direction is specific: image type, subject, text placement
- [ ] Humor is insider/community — not generic internet meme format pasted with a logo
- [ ] Target audience would recognize themselves in the joke without being told to
- [ ] No meme punches down or uses offensive references
- [ ] Trending formats are still within their relevance window (< 72 hours post-peak)
- [ ] Brand alignment is cultural position, not product feature
- [ ] Collection register assigned — no cross-attribution in collection-tagged memes
- [ ] No ironic self-deprecation about product quality, price, or brand ambition
- [ ] Risk level assessed — Medium-risk flagged for approval before posting
```

### Approval Workflow

Meme content moves faster than standard content — but not without a check:
- **Low-risk memes:** Social manager can post within 1 hour of creation
- **Medium-risk memes:** 12-hour review window with Corey or brand lead before posting
- **If in doubt about risk level:** Classify as Medium. The brand's credibility compounds slowly and breaks fast.

---

## Implementation

```python
from agents.social_media_agent import SocialMediaAgent

agent = SocialMediaAgent()

# Pull the brand-voice seed for the Black Rose collection (engagement register)
post = agent.generate_post("br-001", "instagram", "engagement")

print(post.caption)         # brand-voice tone to keep meme copy on-register
print(post.hashtags)        # collection-aware hashtag set
# The meme concepts + per-concept risk assessment are what THIS skill produces
# from that voice seed via the phases below — the agent does not author memes.
```

```bash
# Smoke-test the social venture for Black Rose meme output:
python -m skyyrose.elite_studio.ventures.social smoke --sku br-001
```

**Meme approval queue row:**

```json
{
  "concept_id": "meme-br-2026-06-04",
  "collection": "black-rose",
  "category": "streetwear_insider",
  "platform": ["instagram", "twitter"],
  "format": "two_panel",
  "risk_level": "medium",
  "review_required": true,
  "reviewer": "corey_foster",
  "review_deadline_utc": "2026-06-03T18:00:00Z",
  "scheduled_post_utc": "2026-06-04T19:00:00Z",
  "posted": false,
  "engagement_notes": null
}
```

---

## Example: 5 Meme Concepts — SkyyRose Black Rose + Brand Level

**Theme:** Streetwear insider knowledge + Oakland cultural identity

```
Meme 1: "The weight of it"
Category: Streetwear Insider | Format: Two-panel | Platform: Instagram + X
Register: Black Rose

Setup (top):   "When someone asks why your crewneck costs $95"
Punchline (bottom): "French terry. Embroidered. Preshrunk. 250 made.
                    [image: same energy as handing them the ingredient list]"
Image direction: Left panel — person shrugging/confused expression (stock-style reaction still).
                 Right panel — extreme close-up of the Black Rose Crewneck embroidery detail.
                 Minimal text overlay in Anton, silver on dark.
Brand alignment: Positions the price as a construction story, not a label story.
Risk level: Low

---

Meme 2: "Before/After: The Oakland fashion timeline"
Category: Town Pride | Format: Before-After two-panel | Platform: X
Register: Brand-level

Setup (top):   "Oakland fashion representation in mainstream media: 2010"
Punchline (bottom): "Oakland fashion representation in mainstream media: still catching up.
                    We didn't wait."
Image direction: Left panel — dated generic "streetwear" stock image, flat colors.
                 Right panel — SkyyRose editorial product shot (existing brand photography).
                 No logo necessary — brand photography IS the identifier.
Brand alignment: Positions SkyyRose as the answer to a real gap, not a claim about the gap.
Risk level: Low

---

Meme 3: "Every streetwear customer tier"
Category: Cultural Commentary | Format: Drake-format two-panel | Platform: Instagram
Register: Brand-level

Setup (top):    [Drake dismissive face] "Brands that explain their logo"
Punchline (bottom): [Drake approving face] "Brands where the garment does the talking"
Image direction: Standard Drake meme panels. Text in clean Anton overlay, dark background.
                 No SkyyRose branding in the meme itself — let the post account do the attribution.
Brand alignment: Reinforces "garment is the protagonist" without stating it as a brand claim.
Risk level: Low

---

Meme 4: "POV: You just pulled your SkyyRose order"
Category: Community Mirror | Format: Video overlay / text-on-black | Platform: TikTok + IG Reels
Register: Brand-level

Setup (top):    "POV: The tracking said delivered"
Punchline (bottom): [No text — reaction implied by the product reveal]
Image direction: 3-second clip: hands opening a SkyyRose package, slow pull reveal of folded crewneck.
                 Trending audio (check weekly for appropriate minimal track).
                 Text fades after setup; product reveal is the payoff, not more text.
Brand alignment: Converts the unboxing format into a brand moment — the pause IS the joke's payoff.
Risk level: Low

---

Meme 5: "Limited run math"
Category: Streetwear Insider | Format: Text-on-dark-image | Platform: X
Register: Signature

Setup:   "250 made."
Punchline: "That's not a marketing line.
            That's the run."
Image direction: Clean dark frame (#0A0A0A). Gold accent rule above the text.
                Hanken Grotesk 30pt white. No image — text is the full visual.
                Post stands alone as a statement. No further caption needed.
Brand alignment: Signature collection's "stay golden / the standard" register — quiet, factual, earned.
Risk level: Low
```

---

## Anti-Patterns

- **Brand-tries-to-be-funny voice** — a meme with a SkyyRose logo that says "When the fit is this clean 😂😂" is not a meme. It is a failed ad. The humor must come from community recognition, not brand enthusiasm.
- **Ironic self-deprecation** — "We know you can't afford it either" or "even the founder cried at the price" type self-mockery damages the brand's position. Fear of God doesn't joke about itself. We don't either.
- **Generic meme template with logo swapped in** — pasting the SkyyRose logo onto a Distracted Boyfriend or Woman Yelling at Cat template with no Oakland or streetwear specificity is low-effort and out of register.
- **Posting dead formats** — a meme format from 6 weeks ago makes the brand look out of touch. If a trending format is past its 72-hour window, skip it and use an evergreen format instead.
- **Meme as product push** — "This meme brought to you by the BLACK Rose Crewneck — link in bio" ruins the meme. Memes drive culture engagement, not direct conversion.
- **Cross-collection register in meme** — a Black Rose meme that uses Love Hurts language, or a Signature meme that uses defiance/armor framing, fails the same way it would in any other format.
- **Requiring explanation** — if the social manager has to write a three-sentence caption to explain the joke, the meme failed at the brief stage. Cut it and try a different angle.
- **European luxury reference humor** — "The Oakland Bottega" or "like if Kering but from The Town" positions the brand against the wrong DNA. Only The Five refs apply.

---

## Recovery

- **Meme gets no engagement:** Move on. Don't delete unless it's genuinely offensive — deleting for low performance signals insecurity. Post a value piece the next day and retry with a different category in week 3.
- **Meme is misread by audience:** If the misread is minor, let it go. If comments are going sideways in a harmful direction, reply with one direct clarification ("This is about X — not Y") then stop engaging with that thread.
- **Cannot keep up with trending formats:** Lean into evergreen categories: Streetwear Insider and Oakland/Town Pride always work. Trends are optional — cultural specificity is the core.
- **Corey or brand lead vetoes the meme batch:** Ask for one approved meme from the batch to understand where the line is, then recalibrate. The brief should encode that learning for the next batch.
- **Audience doesn't engage with any memes after 4 weeks of testing:** The SkyyRose audience may be in a buying-mindset phase, not a community-engagement phase. Shift to product storytelling and revisit meme cadence when community engagement metrics recover.
