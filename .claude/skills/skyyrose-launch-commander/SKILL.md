---
name: skyyrose-launch-commander
description: "End-to-end product drop orchestration for SkyyRose. Coordinates the full launch timeline from T-30 to T+7 across product setup, email sequences, ad campaigns, social content, and influencer seeding. Use when planning any product drop, collection launch, restock, or seasonal event."
allowed-tools: Read Write Edit Glob Bash Grep
---

# SkyyRose Launch Commander

## When to Use This Skill

- Planning a new product drop (single product or collection)
- Orchestrating a seasonal launch (Black Friday, summer drop, holiday)
- Coordinating restock announcements
- Running a flash drop / surprise release
- Generating all launch assets (emails, ads, social, product pages) in one workflow

This is the MASTER SKILL that orchestrates: `skyyrose-product-copy`, `skyyrose-email-flows`, `skyyrose-paid-media`, `skyyrose-content-engine`, and `skyyrose-photography-brief`.

---

## Drop Types & Timelines

| Drop Type | Timeline | Emails | Social Posts | Ads |
|-----------|----------|--------|-------------|-----|
| Full Collection Launch | T-30 to T+7 | 11 emails | 15-20 posts | 3 campaigns |
| Single Product Drop | T-14 to T+5 | 7 emails | 8-10 posts | 2 campaigns |
| Flash Drop (surprise) | T-48h to T+2 | 4 emails | 5 posts | 1 campaign |
| Restock | T-7 to T+3 | 5 emails | 5 posts | 1 campaign |

---

## Full Collection Launch Timeline (T-30 to T+7)

### T-30: STRATEGY
- [ ] Define the drop: products, quantities, pricing, collection
- [ ] Set launch date and pre-order window duration
- [ ] Identify hero product (leads all creative)
- [ ] Set revenue target and ad budget
- [ ] Brief: Who is this drop for? What story does it tell?

**Deliverable:** Launch Brief document

### T-21: CONTENT PRODUCTION
- [ ] Product renders generated (invoke AI pipeline: front, back, branding per SKU)
- [ ] Lifestyle photography briefs created (use `skyyrose-photography-brief`)
- [ ] Video scripts written: 3 TikToks, 2 Reels, 1 brand story (use `skyyrose-content-engine`)
- [ ] Email copy written for all 7 launch emails (use `skyyrose-email-flows`)
- [ ] Product descriptions written for all SKUs (use `skyyrose-product-copy`)
- [ ] Ad copy and creative briefs prepared (use `skyyrose-paid-media`)

**Deliverable:** Complete content library for the drop

### T-14: WAITLIST & HYPE
- [ ] Waitlist / early-access signup page live on skyyrose.co
- [ ] Teaser posts begin on Instagram + TikTok (dark/mysterious imagery)
- [ ] Influencer seeding: ship product to 5-10 micro-creators
- [ ] Email teaser #1 sent to existing list ("something's coming")
- [ ] Countdown Stories on Instagram begin

**Deliverable:** Active hype machine running

### T-7: FINAL PREP
- [ ] WooCommerce products configured:
  - Pre-order status enabled
  - Product images uploaded (renders + lifestyle)
  - Product copy pasted in (short desc, long desc, FAQ)
  - SEO meta filled (title, description, slug)
  - Collection/category assignments
  - Price and inventory quantity set
- [ ] Klaviyo email sequences scheduled (all 7 emails with correct dates/times)
- [ ] Ad campaigns built in Meta Ads Manager (NOT launched yet)
- [ ] TikTok ad campaigns built (NOT launched yet)
- [ ] Press release distributed (if newsworthy drop)
- [ ] Social media posts scheduled for launch day
- [ ] Test: complete a test purchase on staging or with test card

**Deliverable:** Everything built, tested, and waiting for go-live

### T-1: PRE-LAUNCH CHECK
- [ ] ALL product pages live and functional
- [ ] Payment processing tested end-to-end
- [ ] Email sequences verified in Klaviyo (preview, test send)
- [ ] Ad campaigns in review / approved
- [ ] Social posts queued for publish
- [ ] Team briefed on launch day roles

### T-0: LAUNCH DAY

**10:00am PST — Subscriber Early Access**
- [ ] Send "early access is live" email (subscribers only)
- [ ] Post "early access" Story on Instagram
- [ ] Monitor: site speed, checkout function, inventory count

**12:00pm PST — Public Launch**
- [ ] Send "now live" email to full list
- [ ] Publish launch posts on Instagram, TikTok, X
- [ ] Activate ad campaigns (Meta + TikTok + Google)
- [ ] Monitor first 4 hours: orders, page views, ad spend, any errors

**Throughout Launch Day:**
- [ ] Respond to DMs and comments in real-time
- [ ] Share Stories of early orders / excitement
- [ ] Screenshot and save any organic UGC from customers

### T+1 to T+3: MOMENTUM
- [ ] Send "selling fast" email (with real % sold if >50%)
- [ ] Post customer reactions / UGC on Stories
- [ ] Adjust ad budgets: increase on winners, kill underperformers
- [ ] Share behind-the-scenes content (packing orders, production footage)

### T+5 to T+7: CLOSE & TRANSITION
- [ ] Send "last chance" email (if inventory allows)
- [ ] Final push social posts
- [ ] When sold out: send "sold out + waitlist" email
- [ ] Transition ad campaigns to retargeting only
- [ ] Begin post-launch analysis

### T+7: POST-LAUNCH REPORT
Generate using this template:

```
# [Drop Name] Launch Report

## Revenue
- Total revenue: $[X]
- Target: $[Y]
- Achievement: [X/Y]%
- Units sold: [N] of [Total available]
- Average order value: $[AOV]

## Email Performance
| Email | Open Rate | Click Rate | Revenue |
|-------|-----------|-----------|---------|
| Teaser | X% | X% | $0 |
| Announcement | X% | X% | $X |
| Early Access | X% | X% | $X |
| Public Launch | X% | X% | $X |
| Selling Fast | X% | X% | $X |
| Last Chance | X% | X% | $X |
| Sold Out | X% | X% | $0 |

## Ad Performance
| Platform | Spend | Revenue | ROAS | CPA | Top Creative |
|----------|-------|---------|------|-----|-------------|
| Meta | $X | $X | Xx | $X | [Name] |
| TikTok | $X | $X | Xx | $X | [Name] |
| Google | $X | $X | Xx | $X | [Name] |

## Social Performance
- Total impressions: [X]
- Total engagement: [X]
- New followers gained: [X]
- Top performing post: [link]
- UGC collected: [N] pieces

## Lessons Learned
1. [What worked]
2. [What didn't work]
3. [What to change for next drop]
```

---

## Single Product Drop (Compressed — T-14)

Same structure, compressed timeline:
- T-14: Strategy + begin content production
- T-10: Content complete
- T-7: Hype begins (teasers, influencer seeding)
- T-3: WooCommerce ready, emails scheduled, ads built
- T-0: Launch (same day-of structure)
- T+5: Close + report

Email sequence: 5 emails (teaser, announcement, early access, selling fast, last chance)

---

## Flash Drop (T-48 hours)

For surprise releases or limited restocks:

**T-48h:** Decide product, quantity, set up WooCommerce, write 4 emails
**T-24h:** Teaser on social ("tomorrow. that's all we'll say.")
**T-0:** Drop live. Email + social + DM to VIP customers simultaneously.
**T+24h:** "Selling fast" update
**T+48h:** Sold out or close

No ads for flash drops — organic urgency only.

---

## Restock Drop (T-7)

For bringing back sold-out products:

**T-7:** Notify waitlist ("it's coming back")
**T-3:** Email + social announcement with quantity
**T-0:** Waitlist gets 2-hour early access, then public
**T+3:** Close or continue

---

## Cross-Skill Orchestration

When running a launch, invoke skills in this order:

1. `skyyrose-product-copy` → Generate product descriptions for all SKUs
2. `skyyrose-photography-brief` → Create shot lists and render briefs
3. `skyyrose-email-flows` → Build complete email sequence
4. `skyyrose-paid-media` → Create ad campaigns and creative briefs
5. `skyyrose-content-engine` → Generate social content calendar
6. `skyyrose-seo-commerce` → Optimize product pages for search
7. `skyyrose-influencer-growth` → Brief influencer partnerships

---

## Anti-Patterns

- **DO NOT** launch without testing checkout — a broken cart on launch day is catastrophic
- **DO NOT** launch without pre-scheduled emails — manual sending leads to missed timing
- **DO NOT** discount on launch day — the product is new, it has full value
- **DO NOT** launch on Monday or Friday — Tuesday-Thursday get best email engagement
- **DO NOT** skip the post-launch report — every drop teaches something for the next one
- **DO NOT** launch multiple products without a hero — one product leads, others follow
- **DO NOT** forget to exclude purchasers from "selling fast" emails — that's insulting

## Recovery

- **Low pre-launch interest:** Increase hype content, add an exclusive early-access incentive, extend teaser period.
- **Site crashes on launch:** Have a maintenance page ready, communicate via email/social, extend the drop window.
- **Ads not approved in time:** Always submit ads for review 48+ hours before launch. Have backup static images.
- **Influencers don't post:** Don't rely on influencer timing. Your owned channels (email + social) are the primary drivers.
- **Slow sales after launch:** Pivot messaging from "new" to social proof. Feature customer reactions. Add urgency.
