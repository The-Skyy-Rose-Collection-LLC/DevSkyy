---
name: product-description
description: "Writes conversion-optimized product descriptions for e-commerce platforms with benefit-driven copy, SEO keywords, and platform-specific formatting for Shopify, Amazon, Etsy, and WooCommerce. Use when a user needs product listings, wants to improve existing product copy, or is launching products on an e-commerce platform."
allowed-tools: Read Write Glob Grep
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Product Description

## When to Use This Skill

Use this skill when you need to:
- Write a new product listing for Shopify, Amazon, Etsy, or WooCommerce
- Improve existing product copy that is not converting
- Launch a product across multiple e-commerce platforms with tailored descriptions
- Optimize product SEO with keyword-rich titles, bullet points, and meta descriptions
- Rewrite feature-heavy copy into benefit-driven language that sells

**DO NOT** use this skill for:
- General marketing copy or landing pages (use a copywriting skill)
- Brand voice development (use a brand voice skill)
- Product photography direction or image editing
- Pricing strategy or competitive pricing analysis
- Ad copy for paid campaigns (different format and intent)

---

## Quick Reference: Platform Specifications

| Platform | Title | Bullets | Description | Tags/Keywords |
|----------|-------|---------|-------------|---------------|
| Shopify | 255 chars | No limit | No limit | SEO title 70 chars, meta 320 chars |
| Amazon | 200 chars | 5 x 500 chars | 2,000 chars | Backend terms 250 bytes |
| Etsy | 140 chars | N/A | 10,000 chars | 13 tags, 20 chars each |
| WooCommerce | 255 chars | No limit | No limit | SEO title 60 chars, meta 160 chars |

**DEFAULT PLATFORM: Shopify** -- most common for solopreneurs and small businesses.

## Quick Reference: Description Frameworks

| Framework | Structure | Best For |
|-----------|-----------|----------|
| Feature-Benefit-Outcome | Feature > What it does for the buyer > End result | Physical products with clear specs |
| Problem-Solution | Pain point > How the product solves it > Proof | Products solving a specific frustration |
| Sensory/Lifestyle | Scene-setting > Sensory details > Emotional payoff | Handmade goods, food, candles, apparel |
| Technical Spec | Capability > Integration > Measurable result | SaaS, digital tools, electronics |

**DEFAULT FRAMEWORK: Feature-Benefit-Outcome** -- works for the widest range of products.

## Quick Reference: SEO Elements

| Element | Guidelines |
|---------|-----------|
| Title keywords | Primary keyword first, brand last, no stuffing |
| Meta description | 150-160 chars, primary keyword, end with benefit/CTA |
| Alt text | Describe image + primary keyword, under 125 chars |
| URL slug | Primary keyword, hyphens, no filler words |
| Backend keywords (Amazon) | No commas, no repeats from title, include synonyms |

## Quick Reference: Bullet Point Formula

| Position | Purpose | Template |
|----------|---------|----------|
| Bullet 1 | Primary benefit | [BIGGEST BENEFIT] -- [feature that delivers it] |
| Bullet 2 | Differentiator | [WHAT MAKES IT DIFFERENT] -- [specific proof or spec] |
| Bullet 3 | Use case / lifestyle | [WHO IT IS FOR] -- [scenario where it shines] |
| Bullet 4 | Quality / trust signal | [QUALITY INDICATOR] -- [material, process, or certification] |
| Bullet 5 | Risk reducer | [GUARANTEE / EASE] -- [return policy, setup simplicity, or warranty] |

---

## Core Workflow

EVERY PRODUCT DESCRIPTION STARTS WITH UNDERSTANDING THE PRODUCT AND THE BUYER -- NEVER WRITE COPY WITHOUT KNOWING BOTH.

### Step 1: Gather Product Intelligence

1. **Product name** -- exact name for the listing
2. **Product category** -- candle, software, t-shirt, supplement, etc.
3. **Key features/specs** -- dimensions, materials, capabilities, integrations
4. **Target buyer** -- who buys this and why
5. **Platform(s)** -- Shopify, Amazon, Etsy, WooCommerce
6. **Price point** -- calibrates tone (budget vs. premium)
7. **Brand voice** -- default: conversational and confident
8. **Existing photos** -- what the buyer can see vs. what copy must communicate
9. **Competitor positioning** -- what others say, so we say something different
10. **Top objection** -- #1 reason someone hesitates to buy

If the user provides items 1-5, proceed with defaults for the rest. **If they have an existing listing**, read it with `Read`, identify weaknesses, rewrite with improvements flagged.

**Brief template for vague requests:**

```
I'll write your product listing. Quick details:
1. Product name?
2. What type of product?
3. Key features/specs? (materials, size, what it does)
4. Who is the ideal buyer?
5. Which platform(s)?
6. Price point?
7. #1 reason someone would hesitate to buy?
```

### Step 2: Write the Listing

Generate every element of the product listing in this order:

1. **Title** -- keyword-optimized, primary keyword first, within platform character limit
2. **Bullet points** -- 5 bullets using the bullet formula (benefit first, then feature)
3. **Short description** -- 2-3 sentences for search previews and quick scanning (under 160 chars for Etsy, under 320 chars for Shopify meta)
4. **Long description** -- storytelling paragraph + specs section + social proof cues + CTA
5. **SEO meta** -- meta title, meta description, URL slug, alt text suggestions, backend keywords if Amazon
6. **Tags** -- platform-appropriate (13 tags for Etsy, backend terms for Amazon)

**WRITING RULES:**

- **LEAD EVERY BULLET WITH A BENEFIT, THEN THE FEATURE** -- not "Made with organic cotton" but "Softer on your skin -- 100% GOTS-certified organic cotton"
- **Sensory language for physical products** (texture, scent, warmth); **technical precision for SaaS** (speed, integrations, metrics)
- **Address the top objection in the long description** -- neutralize it, do not avoid it
- **Include social proof** -- stats if available; credibility cues ("small batch", "15 years experience") if not
- **End with a specific CTA** -- "Light it tonight" beats "Buy now"
- **8th-grade reading level** -- short sentences, common words, active voice
- **NEVER use unsubstantiated superlatives** -- no "best", "#1", "world-class" without proof

### Step 3: Present and Verify

1. **Show the complete listing** with all elements labeled
2. **Display character counts** next to every limited field: `Title: "..." (63/200 chars)`
3. **Flag elements within 10% of the limit** with a warning
4. **Multiple platforms**: show each version separately
5. **GATE: Ask the user to approve before saving**

### Step 4: Deliver

1. **Save** as `{product-name}-{platform}.md` in the working directory or specified location
2. **Multiple platforms**: separate files (`organic-candle-shopify.md`, `organic-candle-etsy.md`)
3. **Include a copy-paste section** at the end with raw text for pasting into the platform editor
4. **Present file location(s)** to the user

---

## Example 1: Handmade Soy Candle for Etsy

**User request:** "Etsy listing for my handmade soy candle called Midnight Garden. 8oz, soy wax, jasmine and sandalwood essential oils, cotton wick, 45-hour burn time, reusable amber glass jar. Target: women 25-40, calming evening ritual. $28. Brand: Moonlight Wicks."

### Title (138/140 chars)
```
Jasmine Sandalwood Soy Candle 8oz - Hand Poured Natural Candle - Relaxation Gift - Reusable Amber Jar - Moonlight Wicks
```

### Bullet Points
```
CALMING EVENING RITUAL IN A JAR -- Jasmine and sandalwood essential oils create a warm, grounding scent that turns your room into a spa the moment you light the wick.

BURNS FOR 45+ HOURS WITHOUT SOOT -- 100% natural soy wax and cotton wick deliver a clean, even flame with zero black residue on your walls or jar.

HAND POURED IN SMALL BATCHES -- Every candle is crafted by hand, never pulled off a factory line. You will notice the difference in scent throw and burn quality.

REUSABLE AMBER GLASS JAR -- When done, clean with warm water and use for makeup brushes, succulents, or bathroom storage. Zero waste.

THE PERFECT SELF-CARE GIFT -- Arrives ready to give with kraft paper wrap and care card. For the friend who never buys herself anything nice.
```

### Long Description (trimmed -- full version shows sensory/lifestyle framework)
```
There is a moment every evening when the day finally lets go. The laptop closes. The phone goes face-down. You reach for a match.

Midnight Garden was made for that moment.

This 8oz hand-poured soy candle fills your space with the warm, layered scent of jasmine petals and rich sandalwood -- real essential oils that bloom slowly as the wax melts, not the synthetic kind from big box stores.

The cotton wick burns clean. No soot. No black smoke. Just a steady flame that lasts 45+ hours -- six weeks of evening rituals from one candle.

When the wax is gone, the amber glass jar stays. Rinse it and use it for succulents, brushes, or storage. Nothing goes to waste.

Hand-poured in small batches in Portland, Oregon. Never more than 40 candles at a time. Your candle arrives wrapped in kraft paper with a care card -- ready to keep or give.

Light it tonight.

SPECS: 8 oz | 100% soy wax | Jasmine + sandalwood essential oils | Cotton wick | 45+ hour burn | Reusable amber glass jar | Handmade in Portland, OR
```

### SEO Tags (13/13)
```
soy candle | jasmine candle | sandalwood candle | hand poured candle | natural candle | relaxation gift | self care gift | amber jar candle | essential oil candle | clean burning candle | small batch candle | aromatherapy candle | evening ritual
```

### Alt Text
```
Image 1: "Jasmine sandalwood soy candle in amber glass jar on wooden tray"
Image 2: "Lit soy candle with warm glow on nightstand in dark room"
```

**Verification:** Title 138/140 chars | Tags 13/13, all under 20 chars | Description 1,102/10,000 chars

---

## Example 2: SaaS Project Management Tool for Shopify

**User request:** "Shopify app listing for FlowBoard. Project management for e-commerce teams -- Kanban boards, auto task creation from Shopify events, team chat, deadline tracking, Slack/Calendar/Zapier integrations. Target: store owners with 3-15 employees. $29/month. Objection: 'I already use Trello.'"

### Title (62/255 chars)
```
FlowBoard - Project Management Built for Shopify Store Teams
```

### Bullet Points
```
TURNS SHOPIFY EVENTS INTO TASKS AUTOMATICALLY -- New order creates a fulfillment task. Refund request creates a support ticket. Low inventory creates a reorder task. Zero manual entry.

BUILT FOR E-COMMERCE, NOT GENERIC TOOLS -- Unlike Trello or Asana, FlowBoard speaks Shopify natively. Boards and automations designed around orders, inventory, and customer events.

KEEP YOUR WHOLE TEAM ON ONE SCREEN -- Kanban boards, team chat, and deadline tracking in one dashboard. No switching between Slack, a spreadsheet, and a project tool.

CONNECTS TO TOOLS YOU ALREADY USE -- Slack (task notifications), Google Calendar (deadline sync), and Zapier (5,000+ apps without code).

SET UP IN 12 MINUTES, NOT 12 HOURS -- Install, connect your store, and FlowBoard auto-generates your first board from current open orders. Productive on day one.
```

### Long Description (trimmed -- full version shows technical spec framework with objection handling)
```
You opened a Shopify store, not a project management consultancy. But somehow you spend two hours a day copying order numbers into Trello, pinging your team about deadlines, and updating a spreadsheet that is already out of date.

FlowBoard replaces all of that with one dashboard built for Shopify stores.

HOW IT WORKS
- New order placed > Fulfillment task assigned to shipping team
- Refund requested > Support ticket with order details attached
- Inventory hits reorder threshold > Purchase order task with supplier info
- New product published > Marketing task for social posts and email

No manual entry. No forgotten follow-ups.

"But I already use Trello."

Trello does not know what a Shopify order is. It cannot auto-create tasks from store events or pull in order details and tracking numbers. With Trello, you are the integration. FlowBoard does it in the background so you can focus on growing your store.

INTEGRATIONS: Slack | Google Calendar | Zapier (5,000+ apps)

$29/month for your entire team. No per-seat charges. No feature gates. Try free for 14 days -- no credit card required.

Install FlowBoard and turn your Shopify chaos into a system.
```

### SEO Meta
```
SEO Title: "FlowBoard - Shopify Project Management for E-Commerce Teams" (59/70 chars)
Meta Description: "Turn Shopify events into tasks automatically. Kanban boards, team chat, and deadline tracking for store teams of 3-15. Slack and Zapier integrations. $29/mo." (157/160 chars)
URL Slug: flowboard-shopify-project-management
```

**Verification:** Title 62/255 chars | Meta 157/160 chars | SEO title 59/70 chars | 5 bullets, all under 500 chars

---

## Pre-Delivery Checklist

Run this before delivering any product listing. **DO NOT SKIP ANY ITEM.**

| Check | What to Verify |
|-------|----------------|
| Benefits lead bullets | Every bullet starts with what the buyer gets, not what the product has |
| Character limits met | Title, meta description, tags, and bullets all within platform limits |
| Top objection addressed | The long description directly neutralizes the #1 purchase hesitation |
| No unproven superlatives | Zero instances of "best", "#1", "world-class", "leading" without evidence |
| Sensory or technical language | Physical products use texture/scent/feel; digital products use speed/metrics/outcomes |
| Social proof present | Customer count, rating, certification, or credibility statement included |
| CTA at the end | Long description ends with a clear call to action |
| SEO complete | Title keywords, meta description, URL slug, alt text, and tags/backend keywords all present |
| Platform formatting correct | HTML for Shopify, plain text for Amazon bullets, tags for Etsy |
| Reading level appropriate | Short sentences, common words, no jargon the buyer would not know |
| Brand voice consistent | Tone matches across title, bullets, and description |
| File saved | Write tool confirmed successful save |

**Print the checklist after every listing and check each item before saving.**

---

## Recovery and Troubleshooting

### User Provides Minimal Product Information

1. Ask the 7-question brief template from Step 1
2. **NEVER fabricate features, specs, or claims** -- only write what the user confirms
3. If 3 clarification rounds fail, write with confirmed details and flag gaps with `[NEEDS: specific missing info]`

### Existing Listing Needs Improvement

1. Read with `Read`, identify top 3 weaknesses (feature-first bullets, missing SEO, wall of text)
2. Present before/after comparison, rewrite with improvements flagged
3. **Always show what changed and why**

### Writing for Multiple Platforms

1. Write Shopify version first (most flexible), adapt to each platform's limits and structure
2. Save separate files: `{product}-shopify.md`, `{product}-amazon.md`, `{product}-etsy.md`
3. **DO NOT copy-paste across platforms** -- each version respects that platform's rules

### User's Product Has No Clear Differentiator

1. Ask: "What do your best customers say when they recommend you?"
2. Look for differentiation in: process, origin, experience, guarantee, or specificity
3. **Every product has a differentiator -- find it and articulate it**

### Character Limit Exceeded

1. Cut filler words first (very, really, just, that, actually)
2. Consolidate redundant phrases; prioritize: primary keyword > main benefit > secondary details
3. **NEVER truncate mid-sentence or remove the primary keyword to hit a limit**

### User Disagrees with the Copy Direction

1. Ask: "What feels off -- the tone, the angle, or specific words?"
2. Present 2 alternative approaches using a different framework from the table
3. **After 3 revision rounds, ask the user for a sentence they like so you can match their voice**

---

## Anti-Patterns

- **DO NOT** list features without benefits -- "100% organic cotton" means nothing without "softer on sensitive skin"
- **DO NOT** exceed platform character limits -- always count and display counts for limited fields
- **DO NOT** use superlatives without proof -- "best candle" is empty; "rated 4.9 by 1,200 customers" is a proof point
- **DO NOT** copy competitor language -- original copy performs better for SEO and builds identity
- **DO NOT** write walls of text -- use bullets, headers, line breaks for scannable listings
- **DO NOT** use jargon without explanation -- follow "GOTS-certified" with "no pesticides, no toxic dyes"
- **DO NOT** skip the objection -- the listing must address the #1 purchase hesitation
- **DO NOT** write generic CTAs -- "Buy now" is weaker than "Light it tonight"
- **DO NOT** stuff keywords -- "soy candle organic soy candle natural soy candle" reads like spam
- **DO NOT** fabricate reviews or statistics -- only include social proof the user provides