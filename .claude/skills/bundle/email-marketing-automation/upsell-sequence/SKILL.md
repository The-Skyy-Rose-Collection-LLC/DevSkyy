---
name: upsell-sequence
description: "Builds post-purchase upsell and cross-sell email sequences that increase average order value through complementary offers, upgrades, and bundles timed to the customer journey. Use when a user wants to increase revenue from existing customers, needs a post-purchase email flow, or wants to promote upgrades, add-ons, or complementary products after an initial sale."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Upsell Sequence

## When to Use This Skill

Use this skill when you need to:
- Build a post-purchase email sequence that promotes upgrades, add-ons, or complementary products
- Increase average order value from existing customers without running new ads
- Create a cross-sell flow that pairs related products naturally after a purchase
- Design a bundle or subscription offer triggered by a one-time buy
- Write upgrade emails that move customers from a lower tier to a higher one

**DO NOT** use this skill for cold outreach to non-customers (use cold-outreach), general email sequences for non-buyers (use email-sequence), or abandoned cart recovery. This is for people who have already purchased.

---

## Core Principle

UPSELL TO PEOPLE WHO ALREADY TRUST YOU — A CUSTOMER WHO JUST BOUGHT IS 60-70% MORE LIKELY TO BUY AGAIN THAN A NEW PROSPECT IS TO BUY ONCE. EVERY EMAIL MUST DEEPEN THE VALUE OF WHAT THEY ALREADY OWN BEFORE ASKING FOR MORE.

---

## Upsell Type Reference

| Type | Definition | Best For | Example |
|------|-----------|----------|---------|
| **Upsell** | Higher-tier version of what they bought | SaaS, courses, services | Basic > Pro, self-paced course > cohort coaching |
| **Cross-sell** | Complementary product that pairs naturally | E-commerce, digital products | Running shoes > socks, course > coaching |
| **Bundle** | Package deal combining products at a discount | E-commerce, product suites | Candle + diffuser + melts at 20% off |
| **Upgrade** | Feature unlock or plan change | SaaS, memberships | Monthly > annual, free trial > paid |

## Timing Map

| Timing | Best Upsell Type | Why It Works |
|--------|-----------------|--------------|
| **Immediate (0-1 days)** | Upgrade, Bundle | Buyer is in purchase mode, momentum is high |
| **Short-term (3-5 days)** | Cross-sell | Customer has received/used the product, complements feel helpful |
| **Medium-term (7-10 days)** | Upsell | Customer hit the base product's limits, upgrade messaging lands |
| **Long-term (30+ days)** | Subscription, Bundle | Proven repeat interest, subscriptions convert well |

---

## Phase 1: Map

Gather the inputs needed to build the right upsell sequence. If the user does not provide a value, use the default in parentheses.

1. **Initial product purchased** — what did the customer buy? (ask, no default)
2. **Initial price point** — how much did they pay? (ask, no default)
3. **Upsell candidate(s)** — what product, upgrade, or bundle will you offer? (ask, no default)
4. **Upsell price point** — how much is the upsell offer? (ask, no default)
5. **Customer segment** — who is this buyer? (general buyer by default)
6. **Average order value** — current AOV if known (use initial price by default)
7. **Email platform** — ConvertKit, Mailchimp, Klaviyo, ActiveCampaign (ConvertKit by default)

### Upsell Strategy Brief

Present this to the user before writing any emails:

```
## Upsell Strategy Brief

**Initial product:** "Design Freelance Accelerator" self-paced course ($297)
**Upsell offer:** Group coaching — 6 weekly live sessions + private Slack ($997)
**Upsell type:** Upsell (higher-tier version)
**Customer segment:** Aspiring freelance designers wanting accountability
**Current AOV:** $297
**Target AOV:** $450+ (blended, assuming 15% conversion)
**Sequence:** 4 emails over 14 days
**Platform:** ConvertKit
**Trigger:** Completed purchase of self-paced course
```

**GATE: Do not proceed to Phase 2 until the user confirms the strategy brief. You must have at least one initial product and one upsell candidate before writing.**

---

## Phase 2: Write

Default sequence is 4 emails over 10-14 days. Present all emails together as a complete set.

### Email 1: Thank You + Soft Intro (Day 0-1)

**Goal:** Gratitude, quick-win tip for the product they bought, subtle seed for the next level.

**Structure:** (1) Thank them sincerely for the specific purchase. (2) Deliver a quick-win tip they can act on immediately. (3) One sentence hinting at a deeper level — no CTA, no link.

**Length:** 120-180 words. **Subject lines:** "you are in — here is your first step" / "welcome to [product] (and a quick tip)" / "your [product] is ready — start here"

**Example — Course ($297) upselling to coaching ($997):**

Subject: you are in — here is your first step
Preview text: Plus the one thing top students do in week one

```
Hey [FIRST_NAME],

You are officially enrolled in the Design Freelance Accelerator — welcome.

Your login details are in a separate email, but before you dive in,
here is the single best thing you can do this week:

Go to Module 1, Lesson 3 ("The Positioning Statement") and complete
the worksheet before you watch anything else. Students who nail their
positioning statement first land clients 2x faster than those who go
in order. Seriously — start there.

Over the next few days I will send you a couple of emails to help you
get the most out of the course. Nothing spammy, just tips from students
who got the best results.

Welcome aboard,
[YOUR NAME]

P.S. Some students tell me the biggest breakthroughs happen when they
get live feedback on their positioning. More on that soon.
```

**Example — E-commerce candle ($28) cross-selling care kit ($15):**

Subject: your candle is on its way — quick care tip
Preview text: This extends your burn time by 20+ hours

```
Hey [FIRST_NAME],

Thanks for ordering the Coastal Cedarwood candle — great pick.

Quick tip while you wait: the first burn is the most important one.
Let the wax melt all the way to the edges before you blow it out
(usually 2-3 hours). This prevents tunneling and adds 15-20 hours
of burn time.

I will check in with you in a few days to make sure everything
arrived perfectly.

Enjoy,
The Ember & Pine Team

P.S. Trimming the wick to 1/4 inch before each burn makes a bigger
difference than most people realize. More care tips soon.
```

### Email 2: Value Bridge (Day 3-5)

**Goal:** Connect the value they are getting from the initial product to a natural next step. Frame the upsell as a logical extension of progress, not a separate purchase.

**Structure:** (1) Check in on their progress with something specific. (2) Name the gap — "Now that you have done X, the next challenge is Y." (3) Bridge to the upsell as the thing that closes the gap. (4) No hard CTA — end with a question or teaser.

**Length:** 150-200 words. **Subject lines:** "now that you have [product], here is what is next" / "the one thing [product] does not include" / "where most [customer type] get stuck after [product]"

**Example — Course ($297) upselling to coaching ($997):**

Subject: where most freelancers get stuck after Module 2
Preview text: It is not what you think

```
Hey [FIRST_NAME],

By now you should be through Module 1 and working on your positioning
statement. If you are — nice work. If not, go back to my last email
and begin with Lesson 3.

Here is what I have noticed after teaching 400+ students:

The course gives you the exact frameworks and scripts you need. But
the place where most people stall is not the material — it is the
feedback loop. You write your positioning statement or draft your
first outreach message, and you are not sure if it is good enough
to send.

That uncertainty is the gap between learning the method and executing it.

The students who move fastest are the ones who get real-time feedback
from someone who has seen 500 versions of the same deliverable.

I will share how some students solve this in my next email. For now,
keep pushing through the modules.

Talk soon,
[YOUR NAME]

P.S. Reply and tell me where you are in the course — I read every one.
```

**Example — E-commerce candle ($28) cross-selling care kit ($15):**

Subject: how is the Coastal Cedarwood burning?
Preview text: One thing most candle owners skip

```
Hey [FIRST_NAME],

Your Coastal Cedarwood should have arrived by now — how is it?

Here is something most candle lovers do not realize: how you maintain
a candle between burns affects the scent throw just as much as the
wax quality. Untrimmed wicks cause soot, uneven melting, and weaker
fragrance.

The people who get 40+ hours of clean, strong-scented burn time from
a single candle treat it like a small ritual — trim, center, burn,
repeat. I put together a few things that make that ritual effortless.
More on that in a couple of days.

Enjoy the burn,
The Ember & Pine Team

P.S. If you got any tunneling on the first burn, reply and we will
help you fix it.
```

### Email 3: The Offer (Day 7)

**Goal:** Direct upsell offer with a clear benefit, social proof, and a reason to act now. This is the conversion email.

**Structure:** (1) Callback to the gap from Email 2. (2) Present the upsell — what it is, what it includes, what outcome it delivers. (3) Social proof — one specific result (name, situation, outcome). (4) Incentive — limited-time bonus or exclusive add-on for existing customers. (5) Single clear CTA — one link, one action.

**Length:** 200-300 words. **Subject lines:** "the fastest way to [result]" / "[name] went from [before] to [after]" / "an upgrade for [product] students only"

**Example — Course ($297) upselling to coaching ($997):**

Subject: an upgrade for Accelerator students only
Preview text: Live feedback, weekly calls, and a private community

```
Hey [FIRST_NAME],

In my last email I mentioned the feedback gap — that moment where you
have done the work but you are not sure if it is ready to ship.

Here is how 38 students from the last two cohorts solved it: they
joined the Group Coaching Upgrade.

What you get:
- 6 weekly live sessions where I review your positioning, portfolio,
  and outreach in real time (not pre-recorded — you ask, I answer)
- A private Slack group with other Accelerator students actively
  landing clients (accountability + shared wins)
- My personal outreach template vault — 12 additional scripts not
  in the self-paced course

Students in the coaching track land their first paying client an
average of 3 weeks faster than self-paced students.

One example: David Park joined as a self-paced student, stalled at
Module 3, then upgraded to coaching. Within 4 weeks of his first
live session, he landed a $3,800 brand identity project. His words:
"The live feedback on my portfolio made the difference."

The investment is $997 (you already paid $297 for the course, so this
is the delta for the full coaching experience).

Because you are already a student, I am including a free 1-on-1
positioning review session (normally $200) if you upgrade by
[DATE — 7 days from this email].

Upgrade here: [LINK]

Talk soon,
[YOUR NAME]

P.S. Only 15 spots per cohort. The current cohort has [X] remaining.
```

**Example — E-commerce candle ($28) cross-selling care kit ($15):**

Subject: the candle care kit (made for Coastal Cedarwood)
Preview text: Wick trimmer, snuffer, and dipper — $15

```
Hey [FIRST_NAME],

Remember the ritual I mentioned — trim, center, burn, repeat?
I put together a kit that makes it effortless:

The Ember & Pine Candle Care Kit ($15):
- Stainless steel wick trimmer (cuts to exactly 1/4 inch every time)
- Candle snuffer (stops smoke and keeps the wax clean)
- Wick dipper (centers the wick after each burn)

Customers who use the care kit report an average of 25 extra burn
hours per candle — roughly 40% more life from the same jar. Rachel M.:
"The trimmer alone fixed my tunneling problem. I have gotten two full
extra weeks from my last three candles."

Free shipping on the care kit this week as a thank-you for your order.

Add the care kit here: [LINK]

The Ember & Pine Team
```

### Email 4: Last Chance (Day 10-14)

**Goal:** Real deadline, restate the core benefit, final nudge, graceful close.

**Structure:** (1) State the deadline. (2) Restate the single strongest benefit. (3) Address the most common hesitation. (4) Final CTA. (5) Graceful close — no guilt.

**Length:** 100-150 words. **Subject lines:** "last call: [bonus] expires [day]" / "closing this out [day]" / "final reminder for [product] customers"

**Example — Course ($297) upselling to coaching ($997):**

Subject: last call — coaching spots close Friday
Preview text: The free positioning review expires with it

```
Hey [FIRST_NAME],

Quick note: the Group Coaching Upgrade closes this Friday at midnight.
The next cohort is not until [MONTH] — and the free 1-on-1 positioning
review goes away for good.

If you have been working through the course and thinking "I wish I
could get direct feedback on this" — that is exactly what coaching is for.

David landed a $3,800 project within 4 weeks. The difference was not
more content. It was real-time answers to "is this good enough to send?"

Upgrade before Friday: [LINK]

If the timing is not right, no worries. The self-paced course is
powerful on its own. But if you want the shortcut, this is the window.

Talk soon,
[YOUR NAME]
```

**Example — E-commerce candle ($28) cross-selling care kit ($15):**

Subject: free shipping ends Sunday
Preview text: The care kit is $15 — shipping is on us until then

```
Hey [FIRST_NAME],

Heads-up: free shipping on the Candle Care Kit ends Sunday night.

The kit is $15 and gives you about 25 extra burn hours from every
candle you own. If you have noticed tunneling, uneven melting, or
weak scent throw, the wick trimmer alone fixes all three.

Grab it before Sunday: [LINK]

Either way, enjoy the candle.
The Ember & Pine Team
```

**GATE: Present the full 4-email sequence to the user. Do not finalize until they approve the copy, tone, timing, and offer framing.**

---

## Phase 3: Sequence

Build the sequence map with timing, conditional exits, and revenue projections.

### Default Sequence Map (4 Emails / 10-14 Days)

```
TRIGGER: Customer completes purchase of [initial product]
  |
  v
EMAIL 1: "Thank You + Soft Intro" (Day 0-1) — CTA: None
  |  [Wait 3 days]
  v
EMAIL 2: "Value Bridge" (Day 3-5) — CTA: Soft reply/teaser
  |  [Wait 2-3 days]
  +--- IF purchased upsell ---> EXIT, move to upsell onboarding
  v
EMAIL 3: "The Offer" (Day 7) — CTA: Buy/upgrade link
  |  [Wait 3-7 days]
  +--- IF purchased upsell ---> EXIT, move to upsell onboarding
  v
EMAIL 4: "Last Chance" (Day 10-14) — CTA: Buy/upgrade link
  +--- IF purchased ---> Move to upsell onboarding
  +--- IF no purchase ---> Tag "upsell-declined," move to nurture
```

### Conditional Exit Rules

- **Customer buys the upsell:** immediately remove from remaining emails, move to upsell onboarding
- **Customer opens a support ticket:** pause until resolved — never pitch to an unhappy customer
- **Customer requests a refund:** cancel the upsell sequence permanently
- **Full sequence, no purchase:** tag "upsell-passed," do not re-send the same offer

### Revenue Projection Benchmarks

| Metric | Low | Average | Strong |
|--------|-----|---------|--------|
| Upsell email open rate | 35% | 45% | 55%+ |
| Click-through on offer email | 3% | 6% | 10%+ |
| Upsell conversion rate | 2% | 5% | 8%+ |
| Typical AOV increase | 10% | 20-30% | 40%+ |

**Course upsell projection:** 200 buyers/mo at $297 = $59,400 base. 5% convert to $997 coaching = 10 upgrades = $9,970 additional. AOV lifts from $297 to $347 (17%). Annual impact: ~$119,640.

**E-commerce cross-sell projection:** 500 orders/mo at $28 = $14,000 base. 8% convert to $15 kit = $600 additional. 3% convert to $22/mo subscription = $330/mo recurring. AOV lifts from $28 to $30.86 (10%).

---

## Phase 4: Deliver

### Delivery Format

Write to `sequences/[product]-upsell-sequence.md` with: (1) Strategy Brief, (2) Sequence Map, (3) All 4 Emails, (4) Revenue Projection, (5) Platform Notes, (6) Pre-Send Checklist.

### Platform Implementation Notes

**ConvertKit:** Visual Automation triggered by purchase event (Stripe/Gumroad/Teachable webhook). Email steps with Delay steps between. "Purchased Product" Goal step to exit on upsell purchase. Link Triggers to tag "upsell-interested" on offer clicks. Condition step after final email for routing.

**Klaviyo:** Flow triggered by "Placed Order" filtered to the initial product. Time delays between emails. "Placed Order" Flow Filter for upsell product to exit buyers. Conditional splits before Emails 3 and 4. Enable Smart Send to prevent stacking.

**Mailchimp:** Customer Journey triggered by purchase event (requires e-commerce integration). "Send Email" actions with "Time Delay" steps. "If/Else" branches checking upsell purchase before Emails 3 and 4. "Goal" exit on upsell purchase.

**ActiveCampaign:** Automation triggered by purchase tag or webhook. "Wait" conditions between emails. "If/Else" blocks before Emails 3 and 4 checking "upsell-purchased" tag. "Goal" condition to skip remaining emails on purchase. "Tag" action after final email for non-converters.

### Pre-Send Checklist

```
## Pre-Send Checklist

- [ ] Email 1 sends gratitude and value — no pitch, no CTA link
- [ ] Email 2 names a real gap, not a manufactured one
- [ ] Email 3 has one specific social proof story (name, situation, outcome)
- [ ] Email 4 has a real deadline that you will actually enforce
- [ ] Every email has exactly one CTA (Emails 1-2: soft/none; Emails 3-4: buy link)
- [ ] Subject lines are under 50 characters
- [ ] Preview text complements but does not repeat the subject line
- [ ] Conditional exit removes buyers from remaining upsell emails immediately
- [ ] Support ticket pause is configured (no upsell emails to unhappy customers)
- [ ] Refund trigger cancels the upsell sequence permanently
- [ ] Personalization tokens are correct for the platform
- [ ] The upsell offer is genuinely complementary — not a random product
- [ ] No email sends within 24 hours of the purchase confirmation email
- [ ] The incentive (bonus, free shipping) has a real expiration
```

---

## Anti-Patterns

**NEVER do these in upsell sequences:**

- **Upselling in the order confirmation email** — the confirmation is transactional. Mixing a pitch into it feels manipulative. Send the thank-you/upsell email separately, at least a few hours later.
- **Pitching before the customer has received or used the product** — if someone bought a physical product that has not arrived, an upsell email feels premature. Wait until they have it in hand.
- **Offering discounts on premium upsells** — discounting a $997 upgrade to $697 trains customers to wait for sales. Use bonuses instead (extra session, exclusive resource, early access).
- **Sending upsells to customers with open support tickets** — a customer with a shipping issue does not want your coaching pitch. Resolve the issue first.
- **Stacking upsells** — offering coaching, templates, AND a subscription in one sequence. One upsell per sequence. Offer something different in 30+ days if they decline.
- **Using guilt or shame language** — "Serious students upgrade" makes people feel manipulated. Frame as opportunity, not judgment.
- **Fake scarcity** — "Only 3 spots left" when there are 50. If you use scarcity, it must be real.
- **Ignoring purchase level** — keep upsells within 1.5-3x of initial purchase for physical, up to 3-5x for digital with clear ROI.
- **More than 4 emails** — after 4 touches you are nagging. If they did not buy, they are not buying from this sequence. Move on.

---

## Recovery

- **No upsell candidate:** Ask what customers most commonly ask about after purchasing. If no data, suggest the logical next step (course > coaching, product > accessories, one-time > subscription).
- **Only one product, nothing to upsell:** Help design one — premium version (add live support/community), complementary download (templates, bonus modules), subscription (monthly refills), or service add-on (done-for-you, 1-on-1 review).
- **User wants thank-you page upsell, not email:** Acknowledge page upsells as valid for impulse adds. Use this email sequence for the higher-consideration upsell that needs more context.
- **Low email engagement (under 20% open rate):** Recommend cleaning the list first. Only send upsell sequence to customers who opened at least 1 of their last 3 emails.
- **User wants a discount instead of a bonus:** Advise against discounting premium offers. For e-commerce, free shipping or a free sample beats a percentage off. If they insist, keep under 15% and frame as an "existing customer" rate.
- **3 revision rounds with no approval:** Stop and reassess. Ask the user to share an upsell email they liked so you can match the voice and tone.
- **High refund rate (over 10%) on initial product:** Flag the risk — upselling to unsatisfied customers accelerates refund requests on both products. Fix the initial experience first.

---

## Quick Reference: Sequence Timing

| Email | Name | Day | Length | Goal |
|-------|------|-----|--------|------|
| 1 | Thank You + Soft Intro | Day 0-1 | 120-180 words | Gratitude, quick win, plant the seed |
| 2 | Value Bridge | Day 3-5 | 150-200 words | Name the gap, connect to next level |
| 3 | The Offer | Day 7 | 200-300 words | Direct upsell with proof and incentive |
| 4 | Last Chance | Day 10-14 | 100-150 words | Deadline, final nudge, graceful close |
