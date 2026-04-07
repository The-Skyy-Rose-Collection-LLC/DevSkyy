---
name: skyyrose-email-flows
description: "Complete Klaviyo email marketing system for SkyyRose luxury streetwear. Welcome sequences, pre-order drop launches, abandoned cart recovery, post-purchase flows, and seasonal campaigns. Use when creating any email content, flows, or sequences for skyyrose.co."
allowed-tools: Read Write Edit Glob
---

# SkyyRose Email Marketing System

## When to Use This Skill

- Creating welcome email sequences for new subscribers
- Building pre-order drop launch email sequences
- Writing abandoned cart recovery emails
- Designing post-purchase flows (confirmation → shipping → styling → review)
- Planning seasonal campaigns (Black Friday, holiday, summer drop)
- Writing any email content for the SkyyRose brand
- Setting up Klaviyo flows, segments, or automation logic

**Platform:** Klaviyo (integrated with WooCommerce at skyyrose.co)

---

## Brand Voice for Email

| Element | Rule |
|---------|------|
| Tone | Like a text from a friend who happens to have incredible taste |
| Subject lines | Short, intriguing, never clickbait. Lowercase preferred. |
| Preview text | Complements the subject, never repeats it |
| CTAs | One per email. Specific: "See the drop" not "Shop now" |
| Imagery | Product renders + lifestyle. Dark backgrounds for BR, warm for SIG |
| Sign-off | "— The SkyyRose Team" or "— Corey" for founder emails |
| NEVER | Discount more than 15% (luxury brands don't race to the bottom) |
| NEVER | Use "Dear customer" or generic greetings. First name or nothing. |

---

## Flow 1: Welcome Sequence (5 emails)

**Trigger:** New subscriber added to list
**Goal:** Brand introduction → emotional connection → first pre-order

### Email 1: Welcome (Immediate)
```
Subject: welcome to the concrete
Preview: luxury starts here

---

{{ first_name|default:"" }},

You just joined something different.

SkyyRose isn't another streetwear brand. It's luxury that grew from concrete — built by a single father in Oakland who turned rock bottom into runway.

Every piece is limited. Every drop is intentional. And you're now first in line.

Here's 10% off your first order as a thank you:
USE CODE: WELCOME10

[BROWSE THE COLLECTIONS →]

— Corey
Founder, The Skyy Rose Collection
```

**Klaviyo notes:** Tag subscriber as `welcome-flow-active`. Exclude from promotional sends for 7 days.

### Email 2: The Collections (Day 2)
```
Subject: find your collection
Preview: three stories, one brand

---

Every SkyyRose collection tells a different story. Which one is yours?

🖤 BLACK ROSE
Dark elegance. Oakland roots. Limited edition pieces for those who find beauty in darkness.
[Explore Black Rose →]

❤️ LOVE HURTS
Raw emotion turned wearable. Named after the founder's family — this collection is personal.
[Explore Love Hurts →]

✨ SIGNATURE
Bay Area golden hour, bottled in cotton. Everyday luxury that speaks for itself.
[Explore Signature →]

Every collection drops in limited runs. When they're gone, they're gone.
```

### Email 3: The Founder Story (Day 4)
```
Subject: the real story behind skyyrose
Preview: from losing everything to building this

---

{{ first_name|default:"" }},

Four years ago, I had nothing. A baby on the way, no drive, no direction.

My daughter Skyy Rose changed everything. I named this brand after her because she's the reason it exists. Every late night, every failed manufacturer, every website rebuild — I kept going because she was watching.

SkyyRose isn't a brand story written by a marketing team. It's a father's promise to his daughter that where you come from doesn't define where you end up.

Luxury grows from concrete. Every piece we make proves it.

— Corey

[Read the full story →]
```

### Email 4: Social Proof (Day 7)
```
Subject: what people are saying
Preview: from our community

---

We don't do influencer campaigns (yet). What we do have is a community that gets it.

[UGC image grid — 3 customer photos]

"The weight of this hoodie is insane. This isn't mall brand quality." — Marcus, Oakland

"My daughter and I got matching Kids sets. She won't take hers off." — Keisha, San Leandro

"The jersey series is collector-level. 80 pieces and you can feel why." — J, San Francisco

Join the conversation: tag us @theskyyrosecollection

[SHOP THE MOST-LOVED PIECES →]
```

### Email 5: Pre-Order Exclusivity (Day 10)
```
Subject: your early access is waiting
Preview: limited pieces, limited time

---

{{ first_name|default:"" }},

Most of what we make sells through pre-order before it ever hits the shelves.

That's intentional. We don't overproduce. We don't do restocks on every drop. When a run is done, it's done.

As a subscriber, you get first access to every drop — before social media, before the public.

Your next chance is coming soon.

Stay ready.

[VIEW CURRENT PRE-ORDERS →]
```

**Klaviyo notes:** Remove `welcome-flow-active` tag after Email 5. Add to main promotional segment.

---

## Flow 2: Pre-Order Drop Launch (7 emails)

**Trigger:** Manual send to full list (or segment) on launch calendar
**Goal:** Build hype → announce → convert → close urgency

### Email 1: Teaser (T-7 days)
```
Subject: something's coming
Preview: {{ collection_name }} drop. soon.

---

[Dark/moody product silhouette image]

{{ collection_name }}.
New drop.
{{ drop_date }}.

Details soon. But if you've been waiting — this is it.

Be first: turn on notifications or just watch your inbox.
```

### Email 2: Announcement (T-3 days)
```
Subject: the {{ product_name }} drops {{ drop_date }}
Preview: limited to {{ quantity }} pieces

---

[Hero product image — front view]

{{ product_name }}
{{ collection_name }} Collection
${{ price }}

{{ short_description }}

Limited to {{ quantity }} pieces.
Pre-order opens {{ drop_date }} at {{ time }} PST.

Subscribers get early access — 2 hours before the public.

[SET A REMINDER →]
```

### Email 3: Early Access — Subscribers Only (Drop Day, 10am)
```
Subject: early access is live — you're first
Preview: 2 hours before everyone else

---

{{ first_name|default:"" }},

This is your window. The {{ product_name }} is live for subscribers only.

Public access opens at noon PST. You're already in.

[CLAIM YOURS →]

${{ price }} · Limited to {{ quantity }} pieces · Ships in 4-6 weeks
```

### Email 4: Public Launch (Drop Day, 12pm)
```
Subject: now live: {{ product_name }}
Preview: the drop is here

---

[Lifestyle product image]

The {{ product_name }} is officially live.

{{ two_sentence_description }}

${{ price }} · Pre-order until sold out.

[SHOP THE DROP →]
```

### Email 5: Social Proof / Momentum (T+2 days)
```
Subject: selling faster than expected
Preview: {{ percent_sold }}% claimed

---

The {{ product_name }} is {{ percent_sold }}% sold.

No restock planned for this run.

If you've been thinking about it — now's the time.

[SECURE YOURS →]
```
**Klaviyo notes:** Exclude customers who already purchased this product.

### Email 6: Last Chance (T+5 days or when 80%+ sold)
```
Subject: last call: {{ product_name }}
Preview: almost gone

---

{{ remaining_quantity }} left.

We're not saying this to pressure you. We're saying it because it's true.

When this pre-order closes, this exact piece won't come back the same way.

[FINAL CHANCE →]
```

### Email 7: Sold Out / Waitlist (When sold out)
```
Subject: sold out: {{ product_name }}
Preview: but you can still get on the list

---

The {{ product_name }} just sold out.

{{ quantity }} pieces. All claimed.

If you missed it — join the waitlist. We'll notify you first if we ever bring it back or release something similar.

[JOIN THE WAITLIST →]

Up next: [tease next drop if known]
```

---

## Flow 3: Abandoned Cart Recovery (3 emails)

**Trigger:** Cart abandoned (Klaviyo WooCommerce integration)
**Goal:** Recover the sale without devaluing the brand

### Email 1: Gentle Reminder (1 hour after abandon)
```
Subject: still thinking about it?
Preview: your {{ product_name }} is waiting

---

[Product image from cart]

The {{ product_name }} is still in your cart.

We get it — some decisions need a minute. But this is a limited run, and we can't hold inventory.

[COMPLETE YOUR ORDER →]

${{ price }} · {{ collection_name }} Collection
```

### Email 2: Social Proof Push (24 hours)
```
Subject: here's why they pulled the trigger
Preview: from people who didn't wait

---

{{ first_name|default:"" }},

Still on the fence? Here's what people say after they get their SkyyRose:

"The quality is on another level. You can feel the difference." — Customer review

"I hesitated on the last drop and it sold out. Not making that mistake again."

Your {{ product_name }} is still available. For now.

[FINISH CHECKOUT →]
```

### Email 3: Scarcity + Offer (48 hours)
```
Subject: last nudge: free shipping on your cart
Preview: we covered shipping. you just have to say yes.

---

{{ first_name|default:"" }},

We don't do this often. But your cart has been sitting there for 2 days, and we'd rather see the {{ product_name }} on you than back in inventory.

Free shipping on your order. No code needed — it's already applied.

[COMPLETE YOUR ORDER →]

This offer expires in 24 hours.
```

**Klaviyo notes:** Apply free shipping automatically via Klaviyo coupon code. Do NOT offer percentage discounts — luxury brands protect their pricing.

---

## Flow 4: Post-Purchase (4 emails)

**Trigger:** Order placed (WooCommerce webhook to Klaviyo)

### Email 1: Order Confirmation (Immediate)
```
Subject: order confirmed — you're in
Preview: {{ product_name }} is yours

---

{{ first_name|default:"" }},

It's official. The {{ product_name }} is yours.

ORDER #{{ order_number }}
{{ product_name }} — {{ size }} — ${{ price }}

[VIEW ORDER STATUS →]

PRE-ORDER NOTE: Your piece is being produced as part of a limited run. Expected ship date: {{ ship_date_estimate }}. We'll send tracking the moment it leaves.

Thank you for believing in what we're building.
— The SkyyRose Team
```

### Email 2: Shipping Notification (When shipped)
```
Subject: your skyyrose is on the way
Preview: tracking inside

---

It's moving.

{{ product_name }} — {{ size }}
Tracking: {{ tracking_number }}
Carrier: {{ carrier }}
Estimated delivery: {{ delivery_estimate }}

[TRACK YOUR ORDER →]

CARE TIP: When it arrives, wash cold, inside out, tumble dry low. Your embroidery/print will thank you.
```

### Email 3: How to Style (5 days after delivery)
```
Subject: 3 ways to wear your {{ product_name }}
Preview: styled by the community

---

Your {{ product_name }} has arrived. Here's how the community is wearing theirs:

1. LAYERED — Under a bomber or over a fitted tee. The weight holds structure.
2. MONOCHROME — All black everything. Let the details do the talking.
3. CONTRAST — Pair dark pieces with light denim or bright kicks.

[Share your fit: tag @theskyyrosecollection]

WHAT'S NEXT?
[Browse complementary pieces from {{ collection_name }} →]
```

### Email 4: Review Request (14 days after delivery)
```
Subject: how's the fit?
Preview: your opinion shapes the next drop

---

{{ first_name|default:"" }},

You've had the {{ product_name }} for a couple weeks now. We want to hear it — the good, the real, all of it.

Your review helps the next person decide. And it helps us make the next drop even better.

[LEAVE A REVIEW →]

Bonus: Share a photo wearing your SkyyRose and we might feature you on the site and our socials.
```

**Klaviyo notes:** Tag reviewer as `review-submitted`. Add photo reviewers to `ugc-candidates` segment.

---

## Flow 5: Seasonal Campaign Template

Adapt this structure for Black Friday, holiday drops, summer collections, etc.

### Campaign Timeline
```
T-14: Teaser email ("something big is coming {{ date }}")
T-7:  Reveal email ("here's what's dropping")
T-3:  Reminder email ("3 days until [event]")
T-0:  Launch email (early access for subscribers)
T-0+4h: Public launch email
T+1:  Momentum email ("selling fast")
T+3:  Last chance email
T+5:  Closed/thank you email
```

### Black Friday Specific Rules
- Max 15% off — never more. SkyyRose is luxury.
- Position as "our only sale of the year" not "everything must go"
- Create a curated "Black Friday Edit" — 5-7 hero products
- Subject lines: lowercase, minimal, mysterious: "the only sale"

---

## Subject Line Formulas for SkyyRose

| Type | Formula | Example |
|------|---------|---------|
| Drop tease | something's coming | "something's coming" |
| Drop launch | now live: [product] | "now live: the varsity jacket" |
| Urgency | [number] left | "12 left" |
| Founder personal | lowercase casual | "the real story behind skyyrose" |
| Social proof | what people are saying | "what people are saying" |
| Cart recovery | question | "still thinking about it?" |
| Post-purchase | confirmation + excitement | "order confirmed — you're in" |

**Rules:** Lowercase preferred. Under 40 characters. No emojis in subject (save for preview text). Never misleading.

---

## Klaviyo Configuration Notes

### Key Segments
- `all-subscribers` — Full list
- `welcome-flow-active` — Currently in welcome sequence (exclude from promos)
- `pre-order-customers` — Have placed a pre-order (nurture differently)
- `repeat-customers` — 2+ orders (VIP treatment)
- `ugc-candidates` — Submitted photo reviews
- `lapsed-30d` — No open/click in 30 days (re-engagement target)
- Collection-specific: `interested-black-rose`, `interested-love-hurts`, etc.

### Key Tags
- `source:website`, `source:instagram`, `source:tiktok` (track acquisition)
- `purchased:{sku}` (product-level targeting)
- `collection:{name}` (collection affinity)

### Flow Priority (if subscriber qualifies for multiple flows)
1. Abandoned Cart (highest priority — revenue recovery)
2. Post-Purchase (time-sensitive)
3. Welcome Sequence
4. Drop Launch
5. Seasonal Campaign (lowest priority)

---

## Anti-Patterns

- **DO NOT** discount more than 15% — luxury brands don't race to the bottom
- **DO NOT** send generic WooCommerce transactional emails — brand every touchpoint
- **DO NOT** email more than 3x per week outside of launch windows
- **DO NOT** use "Dear Customer" — first name or skip the greeting
- **DO NOT** send the same email to all segments — personalize by collection affinity
- **DO NOT** write novels — emails should be scannable in under 30 seconds
- **DO NOT** use stock photography — only SkyyRose product renders and lifestyle shots
- **DO NOT** guilt-trip non-buyers — "we noticed you didn't buy" is passive-aggressive

## Recovery

- **Low open rates (<20%):** Test subject lines. SkyyRose formula: lowercase, short, intriguing.
- **Low click rates (<2%):** CTA is buried or unclear. One button, above the fold.
- **High unsubscribe on welcome flow:** Email 1 is too salesy. Lead with story, not offers.
- **Cart recovery not converting:** Try earlier timing (30 min instead of 1 hour) or add product social proof.
- **Small list (<500):** Focus on welcome flow quality and organic list growth. Don't buy lists.
